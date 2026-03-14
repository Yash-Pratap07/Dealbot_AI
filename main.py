from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import json, traceback, asyncio, re

from orchestrator import run_negotiation, negotiate_stream
from database import get_db, User, Deal, init_db
from pipeline import run_pipeline, shopping_assistant, product_link_analyzer
from payment import payment_system, SUPPORTED_METHODS
from auth import (
    hash_password, verify_password, create_access_token, get_current_user,
    verify_google_token, verify_facebook_token, send_phone_otp, verify_phone_otp,
)
from blockchain.hash_log import hash_transcript
from blockchain.contract import generate_contract
from blockchain.agent_identity import get_all_agent_identities, AgentRegistry
from blockchain.settlement import settle_from_result, _is_chain_available

app = FastAPI(title="DealBot AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:3001", "http://127.0.0.1:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.on_event("startup")
def on_startup():
    init_db()


# ─── Schemas ──────────────────────────────────────────────────────────────────

class RegisterSchema(BaseModel):
    username: str
    email: str
    password: str

class GoogleAuthSchema(BaseModel):
    credential: str          # Google ID token from Sign In With Google

class FacebookAuthSchema(BaseModel):
    access_token: str        # Facebook user access token

class PhoneSendSchema(BaseModel):
    phone: str               # E.164 or local format: +923001234567

class PhoneVerifySchema(BaseModel):
    phone: str
    code: str                # 6-digit OTP


# ─── Auth ─────────────────────────────────────────────────────────────────────

@app.post("/auth/register")
def register(body: RegisterSchema, db: Session = Depends(get_db)):
    if db.query(User).filter((User.username == body.username) | (User.email == body.email)).first():
        raise HTTPException(status_code=400, detail="Username or email already exists")
    user = User(
        username=body.username,
        email=body.email,
        hashed_password=hash_password(body.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@app.post("/auth/login")
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username}


@app.get("/auth/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id":           current_user.id,
        "username":     current_user.username,
        "email":        current_user.email,
        "phone":        current_user.phone,
        "display_name": current_user.display_name,
        "avatar_url":   current_user.avatar_url,
        "auth_provider":current_user.auth_provider,
    }


# ─── Google OAuth ─────────────────────────────────────────────────────────────

@app.post("/auth/google")
def google_auth(body: GoogleAuthSchema, db: Session = Depends(get_db)):
    """Verify Google ID token (from Sign In With Google button) and return a DealBot JWT."""
    info = verify_google_token(body.credential)
    google_id = info["google_id"]
    email     = info["email"]
    name      = info["name"]
    picture   = info["picture"]

    # Find existing user by google_id or email
    user = db.query(User).filter(User.google_id == google_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if user:
        # Link google_id if not already linked
        if not user.google_id:
            user.google_id = google_id
        if not user.avatar_url and picture:
            user.avatar_url = picture
        if not user.display_name and name:
            user.display_name = name
        db.commit()
    else:
        # Create new user from Google profile
        base = re.sub(r'[^a-zA-Z0-9_]', '', name.lower().replace(' ', '_')) or 'user'
        username = base
        suffix = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base}{suffix}"; suffix += 1
        user = User(
            username=username,
            email=email or None,
            hashed_password=None,
            google_id=google_id,
            display_name=name,
            avatar_url=picture,
            auth_provider="google",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username,
            "display_name": user.display_name, "avatar_url": user.avatar_url}


# ─── Facebook OAuth ───────────────────────────────────────────────────────────

@app.post("/auth/facebook")
def facebook_auth(body: FacebookAuthSchema, db: Session = Depends(get_db)):
    """Verify Facebook user access token and return a DealBot JWT."""
    info = verify_facebook_token(body.access_token)
    fb_id   = info["facebook_id"]
    email   = info["email"]
    name    = info["name"]
    picture = info["picture"]

    user = db.query(User).filter(User.facebook_id == fb_id).first()
    if not user and email:
        user = db.query(User).filter(User.email == email).first()

    if user:
        if not user.facebook_id:
            user.facebook_id = fb_id
        if not user.avatar_url and picture:
            user.avatar_url = picture
        if not user.display_name and name:
            user.display_name = name
        db.commit()
    else:
        base = re.sub(r'[^a-zA-Z0-9_]', '', name.lower().replace(' ', '_')) or 'user'
        username = base
        suffix = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base}{suffix}"; suffix += 1
        user = User(
            username=username,
            email=email or None,
            hashed_password=None,
            facebook_id=fb_id,
            display_name=name,
            avatar_url=picture,
            auth_provider="facebook",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username,
            "display_name": user.display_name, "avatar_url": user.avatar_url}


# ─── Phone OTP ────────────────────────────────────────────────────────────────

@app.post("/auth/phone/send-otp")
def phone_send_otp(body: PhoneSendSchema):
    """Send a 6-digit OTP to the given phone number via Twilio Verify."""
    status_str = send_phone_otp(body.phone)
    return {"status": status_str, "message": f"OTP sent to {body.phone}"}


@app.post("/auth/phone/verify-otp")
def phone_verify_otp(body: PhoneVerifySchema, db: Session = Depends(get_db)):
    """Verify the OTP and return a DealBot JWT. Creates user on first login."""
    approved = verify_phone_otp(body.phone, body.code)
    if not approved:
        raise HTTPException(status_code=401, detail="Invalid or expired OTP")

    phone = re.sub(r'[^\d+]', '', body.phone)
    if not phone.startswith("+"):
        phone = "+" + phone

    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        # Create user from phone number (username = phone digits)
        username = "ph" + re.sub(r'\D', '', phone)
        suffix = 1
        base = username
        while db.query(User).filter(User.username == username).first():
            username = f"{base}_{suffix}"; suffix += 1
        user = User(
            username=username,
            phone=phone,
            phone_verified=True,
            hashed_password=None,
            auth_provider="phone",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    else:
        if not user.phone_verified:
            user.phone_verified = True
            db.commit()

    token = create_access_token({"sub": user.username})
    return {"access_token": token, "token_type": "bearer", "username": user.username,
            "phone": user.phone}


# ─── Negotiate (REST) ─────────────────────────────────────────────────────────

@app.get("/negotiate")
async def negotiate(
    max_price:    float,
    min_price:    float,
    product:      Optional[str]   = "item",
    market_price: Optional[float] = None,
    strategy:     Optional[str]   = "balanced",
    buyer_model:  Optional[str]   = "gemini",
    seller_model: Optional[str]   = "gemini",
    current_user: User = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    try:
        result = await run_negotiation(
            max_price=max_price,
            min_price=min_price,
            strategy=strategy,
            buyer_model=buyer_model,
            seller_model=seller_model,
            market_price=market_price,
            product=product,
        )
        contract_hash = None
        if result.get("agreement"):
            history       = result.get("history", [])
            contract_hash = hash_transcript(history)
            contract      = generate_contract(
                buyer=current_user.username,
                seller="seller_agent",
                price=result["final_price"],
                transcript_hash=contract_hash,
                rounds=history,
            )
            result["contract_hash"] = contract_hash
            result["contract"]      = contract

        deal = Deal(
            user_id=current_user.id,
            max_price=max_price,
            min_price=min_price,
            final_price=result.get("final_price"),
            agreement=result.get("agreement", False),
            contract_hash=contract_hash,
            history=json.dumps(result.get("history", [])),
            product=product,
            market_price=market_price,
            fraud_flags=json.dumps(result.get("fraud_flags", [])),
            strategy=strategy,
            rounds_taken=result.get("rounds_taken"),
            evaluation=json.dumps(result.get("evaluation", {})),
            votes=json.dumps(result.get("votes", {})),
        )
        db.add(deal)
        db.commit()
        return result
    except Exception as e:
        return {"error": str(e), "traceback": traceback.format_exc()}


# ─── WebSocket (real-time negotiation) ───────────────────────────────────────

@app.websocket("/ws/negotiate")
async def ws_negotiate(websocket: WebSocket):
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        max_price    = float(data.get("max_price",    1000))
        min_price    = float(data.get("min_price",    500))
        strategy     = data.get("strategy",     "balanced")
        buyer_model  = data.get("buyer_model",  "gemini")
        seller_model = data.get("seller_model", "gemini")
        product      = data.get("product",      "item")
        market_price = data.get("market_price", None)
        token        = data.get("token")           # optional JWT for deal saving
        if market_price is not None:
            market_price = float(market_price)

        async for chunk in negotiate_stream(
            max_price=max_price,
            min_price=min_price,
            strategy=strategy,
            buyer_model=buyer_model,
            seller_model=seller_model,
            market_price=market_price,
            product=product,
        ):
            if chunk["type"] == "round":
                await websocket.send_json(chunk)
                await asyncio.sleep(0.9)   # pacing for live feel

            elif chunk["type"] == "done":
                # Attach contract if deal reached
                contract_hash = None
                if chunk.get("agreement"):
                    history       = chunk.get("history", [])
                    contract_hash = hash_transcript(history)
                    contract      = generate_contract(
                        buyer="buyer_agent",
                        seller="seller_agent",
                        price=round(chunk["final_price"], 2),
                        transcript_hash=contract_hash,
                        rounds=history,
                    )
                    chunk["contract_hash"] = contract_hash
                    chunk["contract"]      = contract

                # Save deal to database if user token provided
                if token:
                    try:
                        from jose import jwt as _jwt
                        from auth import SECRET_KEY, ALGORITHM
                        payload = _jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                        username = payload.get("sub")
                        if username:
                            db = next(get_db())
                            user = db.query(User).filter(User.username == username).first()
                            if user:
                                deal = Deal(
                                    user_id=user.id,
                                    max_price=max_price,
                                    min_price=min_price,
                                    final_price=chunk.get("final_price"),
                                    agreement=chunk.get("agreement", False),
                                    contract_hash=contract_hash,
                                    history=json.dumps(chunk.get("history", [])),
                                    product=product,
                                    market_price=market_price,
                                    fraud_flags=json.dumps(chunk.get("fraud_flags", [])),
                                    strategy=strategy,
                                    rounds_taken=chunk.get("rounds_taken"),
                                    evaluation=json.dumps(chunk.get("evaluation", {})),
                                    votes=json.dumps(chunk.get("votes", {})),
                                )
                                db.add(deal)
                                db.commit()
                                db.close()
                    except Exception:
                        pass  # best-effort save

                await websocket.send_json(chunk)
                break

    except WebSocketDisconnect:
        pass


# ─── Deals history ───────────────────────────────────────────────────────────

@app.get("/deals")
def get_deals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    deals = db.query(Deal).filter(Deal.user_id == current_user.id).order_by(Deal.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "product": d.product or "item",
            "max_price": d.max_price,
            "min_price": d.min_price,
            "final_price": d.final_price,
            "agreement": d.agreement,
            "contract_hash": d.contract_hash,
            "created_at": str(d.created_at)
        }
        for d in deals
    ]


# ─── Web4: Agent Identities ──────────────────────────────────────────────────

@app.get("/agents/identities")
def list_agent_identities():
    """Return all AI agent wallet addresses registered on WeilChain."""
    return {
        "agents": get_all_agent_identities(),
        "chain_live": _is_chain_available(),
        "network": "WeilChain",
    }


@app.get("/agents/{agent_type}/identity")
def get_agent_identity_endpoint(agent_type: str):
    """Return a single agent's on-chain identity (no private key)."""
    from blockchain.agent_identity import get_agent_identity, AGENT_TYPES
    if agent_type not in AGENT_TYPES:
        raise HTTPException(status_code=404, detail=f"Unknown agent: {agent_type}")
    identity = get_agent_identity(agent_type)
    return {k: v for k, v in identity.items() if k != "private_key"}


# ─── Web4: Wallet endpoints ───────────────────────────────────────────────────

@app.get("/wallet/balance")
def get_wallet_balance(address: str):
    """
    Get WUSD balance for a wallet address.
    Returns live balance if chain is configured, else simulated value.
    """
    if _is_chain_available():
        try:
            from blockchain.wusd_transfer import get_balance
            bal = get_balance(address)
            return {"address": address, "balance_wusd": bal, "source": "live"}
        except Exception as e:
            pass
    # Simulated balance for dev
    import hashlib
    sim_bal = (int(hashlib.sha256(address.encode()).hexdigest(), 16) % 50000) / 100
    return {"address": address, "balance_wusd": round(sim_bal, 2), "source": "simulated"}


@app.get("/wallet/deals")
def get_wallet_deals(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return all deals with settlement info for the current user."""
    deals = db.query(Deal).filter(Deal.user_id == current_user.id).order_by(Deal.created_at.desc()).all()
    result = []
    for d in deals:
        history = json.loads(d.history or "[]")
        contract_hash = d.contract_hash or hash_transcript(history) if history else None
        settlement = None
        if d.agreement and contract_hash:
            from blockchain.settlement import _simulated_settle
            sim = _simulated_settle(contract_hash, int((d.final_price or 0) * 100), None, None)
            settlement = {
                "wusd_tx_hash":     sim["wusd_tx_hash"],
                "registry_tx_hash": sim["registry_tx_hash"],
                "deal_id_onchain":  sim["deal_id_onchain"],
                "settlement_mode":  "simulated" if not _is_chain_available() else "live",
            }
        result.append({
            "id":              d.id,
            "product":         getattr(d, "product", "item"),
            "max_price":       d.max_price,
            "min_price":       d.min_price,
            "final_price":     d.final_price,
            "agreement":       d.agreement,
            "contract_hash":   contract_hash,
            "settlement":      settlement,
            "created_at":      str(d.created_at),
        })
    return result


@app.get("/wallet/chain-status")
def get_chain_status():
    """Return WeilChain connection status and platform info."""
    import os
    live = _is_chain_available()
    return {
        "chain_live":          live,
        "network":             "WeilChain",
        "rpc_configured":      bool(os.getenv("WEB3_RPC_URL", "").strip()),
        "contract_configured": bool(os.getenv("CONTRACT_ADDRESS", "").strip()),
        "wusd_configured":     bool(os.getenv("WUSD_ADDRESS", "").strip()),
        "mode":                "live" if live else "simulation",
        "agent_count":         len(get_all_agent_identities()),
    }


@app.post("/wallet/settle/{deal_id}")
def manually_settle_deal(
    deal_id: int,
    buyer_address: str = None,
    seller_address: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually trigger autonomous settlement for a completed deal."""
    deal = db.query(Deal).filter(Deal.id == deal_id, Deal.user_id == current_user.id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    if not deal.agreement:
        raise HTTPException(status_code=400, detail="Deal has no agreement — cannot settle")
    history = json.loads(deal.history or "[]")
    result = {
        "agreement":     True,
        "final_price":   deal.final_price,
        "history":       history,
        "contract_hash": deal.contract_hash,
        "votes":         {},
        "product":       getattr(deal, "product", "item"),
        "vote_result":   "ACCEPT",
    }
    settlement = settle_from_result(result, buyer_address=buyer_address, seller_address=seller_address)
    return {"deal_id": deal_id, "settlement": settlement}


# ─── Pipeline ───────────────────────────────────────────────────────────────

class PipelineSearchQuery(BaseModel):
    q: str
    limit: Optional[int] = 6


@app.get("/pipeline/search")
def pipeline_search(
    q: str,
    limit: int = 6,
    currency: str = "INR",
    current_user: User = Depends(get_current_user),
):
    """
    Full pre-negotiation pipeline:
      Product Discovery → Price Comparison → Trust Analysis → AI Ranking
    Returns ranked seller listings ready for Human Selection.
    """
    try:
        result = run_pipeline(q, limit=min(limit, 10), currency=currency)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/pipeline/search/public")
def pipeline_search_public(q: str, limit: int = 6, currency: str = "INR"):
    """Unauthenticated pipeline search for demo / landing page."""
    try:
        return run_pipeline(q, limit=min(limit, 10), currency=currency)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── AI Shopping Assistant & Link Analyzer ───────────────────────────────────────

class AssistantParseSchema(BaseModel):
    query: str

class AssistantDiscoverSchema(BaseModel):
    query: str
    preferences: dict
    limit: int = 6

class LinkAnalyzeSchema(BaseModel):
    url: str
    limit: int = 5
    currency: str = "INR"


@app.post("/pipeline/assistant/parse")
def assistant_parse(
    body: AssistantParseSchema,
    current_user: User = Depends(get_current_user),
):
    """
    Parse a natural-language shopping query.
    Returns detected category, budget, currency, and preference questions.
    """
    parsed    = shopping_assistant.parse_query(body.query)
    questions = shopping_assistant.get_preference_questions(parsed["category"])
    return {**parsed, "preference_questions": questions}


@app.post("/pipeline/assistant/discover")
def assistant_discover(
    body: AssistantDiscoverSchema,
    current_user: User = Depends(get_current_user),
):
    """Run full pipeline with preferences applied. Returns AI-ranked listings."""
    try:
        return shopping_assistant.run_assisted_discovery(
            query=body.query,
            preferences=body.preferences,
            limit=min(body.limit, 10),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/pipeline/analyze-link")
def analyze_link(
    body: LinkAnalyzeSchema,
    current_user: User = Depends(get_current_user),
):
    """
    Analyze a product URL:
      - Fetches and scrapes the product page for real name, price, specs, rating
      - Detects platform (Amazon, Flipkart, eBay, etc.)
      - Searches other stores for cheaper alternatives via the full pipeline
    """
    if not body.url.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="URL must start with http:// or https://")
    try:
        product      = product_link_analyzer.analyze_url(body.url)
        alternatives = product_link_analyzer.find_alternatives(
            product["name"],
            product["platform_price"],
            limit=min(body.limit, 8),
            currency=product.get("currency", body.currency),
        )
        return {"product": product, "alternatives": alternatives}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ─── Payment ───────────────────────────────────────────────────────────────

class PaymentInitSchema(BaseModel):
    deal_id: int
    amount: float
    method: str
    contract_hash: Optional[str] = None
    currency: str = "INR"

class PaymentCompleteSchema(BaseModel):
    payment_id: str

class PaymentRefundSchema(BaseModel):
    payment_id: str


@app.get("/payment/methods")
def get_payment_methods():
    """Return supported payment methods."""
    from payment import _METHOD_LABELS
    return {"methods": [{"id": m, "label": _METHOD_LABELS[m]} for m in SUPPORTED_METHODS]}


@app.post("/payment/initiate")
def initiate_payment(
    body: PaymentInitSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Initiate a payment for a completed deal."""
    deal = db.query(Deal).filter(Deal.id == body.deal_id, Deal.user_id == current_user.id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    try:
        result = payment_system.initiate(
            deal_id=body.deal_id,
            amount=body.amount,
            method=body.method,
            contract_hash=body.contract_hash,
            currency=body.currency,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/payment/complete")
def complete_payment(
    body: PaymentCompleteSchema,
    current_user: User = Depends(get_current_user),
):
    """Mark a pending payment as completed."""
    try:
        return payment_system.complete(body.payment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/payment/refund")
def refund_payment(
    body: PaymentRefundSchema,
    current_user: User = Depends(get_current_user),
):
    """Refund a completed payment."""
    try:
        return payment_system.refund(body.payment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/payment/status/{payment_id}")
def payment_status(
    payment_id: str,
    current_user: User = Depends(get_current_user),
):
    """Get current status of a payment."""
    try:
        return payment_system.get_status(payment_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/payment/deal/{deal_id}")
def payments_for_deal(
    deal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return all payments for a specific deal."""
    deal = db.query(Deal).filter(Deal.id == deal_id, Deal.user_id == current_user.id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return {"deal_id": deal_id, "payments": payment_system.list_by_deal(deal_id)}


# ─── Static / fallback ───────────────────────────────────────────────────────

@app.get("/")
def home():
    return FileResponse("static/index.html")
