from datetime import datetime, timedelta, timezone
import os, re, httpx
import bcrypt as _bcrypt
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db, User

# ─── Config ──────────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "dealbot-secret-key-change-in-production-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

GOOGLE_CLIENT_ID  = os.getenv("GOOGLE_CLIENT_ID",  "")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN",  "")
TWILIO_VERIFY_SID  = os.getenv("TWILIO_VERIFY_SID",  "")

# ─── Password (direct bcrypt — compatible with bcrypt 4.x / 5.x) ─────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


# ─── JWT ──────────────────────────────────────────────────────────────────────
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_exception
    return user


# ─── Google OAuth ─────────────────────────────────────────────────────────────
def verify_google_token(id_token_str: str) -> dict:
    """
    Verify a Google ID token (from Sign In With Google / One Tap).
    Returns dict with: google_id, email, name, picture
    """
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(status_code=503, detail="Google auth not configured on server")
    try:
        from google.oauth2 import id_token as google_id_token
        from google.auth.transport import requests as google_requests
        idinfo = google_id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            GOOGLE_CLIENT_ID,
        )
        return {
            "google_id": idinfo["sub"],
            "email":     idinfo.get("email", ""),
            "name":      idinfo.get("name", ""),
            "picture":   idinfo.get("picture", ""),
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Invalid Google token: {e}")


# ─── Facebook OAuth ───────────────────────────────────────────────────────────
def verify_facebook_token(access_token: str) -> dict:
    """
    Verify a Facebook user access token via Graph API.
    Returns dict with: facebook_id, email, name
    """
    resp = httpx.get(
        "https://graph.facebook.com/me",
        params={"fields": "id,name,email,picture", "access_token": access_token},
        timeout=10,
    )
    data = resp.json()
    if "error" in data:
        raise HTTPException(status_code=401, detail=f"Invalid Facebook token: {data['error']['message']}")
    return {
        "facebook_id": data["id"],
        "email":       data.get("email", ""),
        "name":        data.get("name", ""),
        "picture":     data.get("picture", {}).get("data", {}).get("url", ""),
    }


# ─── Phone OTP (Twilio Verify) ────────────────────────────────────────────────
_TWILIO_PLACEHOLDERS = ("xxx", "your_", "ACxxx", "VAxxx", "xxxxxxx")


def _is_twilio_configured() -> bool:
    """Return True only when all three Twilio env vars are present and non-placeholder."""
    for val in [TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_VERIFY_SID]:
        if not val:
            return False
        if any(p in val for p in _TWILIO_PLACEHOLDERS):
            return False
    return True


def _normalize_phone(phone: str) -> str:
    """Ensure E.164 format (+<digits>)."""
    phone = re.sub(r"[^\d+]", "", phone)
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


def send_phone_otp(phone: str) -> str:
    """Send OTP via Twilio Verify. Returns Twilio status string (e.g. 'pending')."""
    if not _is_twilio_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Phone authentication is not configured. "
                "Add real TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_VERIFY_SID "
                "to your .env file. Get them at https://console.twilio.com → Verify."
            ),
        )
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        verification = client.verify.v2.services(TWILIO_VERIFY_SID).verifications.create(
            to=_normalize_phone(phone),
            channel="sms",
        )
        return verification.status          # "pending" on success
    except TwilioRestException as e:
        if e.status == 401:
            raise HTTPException(status_code=503, detail="Twilio credentials are invalid. Check .env.")
        raise HTTPException(status_code=500, detail=f"Twilio error {e.status}: {e.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send OTP: {e}")


def verify_phone_otp(phone: str, code: str) -> bool:
    """Verify OTP via Twilio Verify. Returns True if approved."""
    if not _is_twilio_configured():
        raise HTTPException(
            status_code=503,
            detail=(
                "Phone authentication is not configured. "
                "Add real TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, and TWILIO_VERIFY_SID "
                "to your .env file."
            ),
        )
    from twilio.rest import Client
    from twilio.base.exceptions import TwilioRestException
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        check = client.verify.v2.services(TWILIO_VERIFY_SID).verification_checks.create(
            to=_normalize_phone(phone),
            code=code,
        )
        return check.status == "approved"
    except TwilioRestException as e:
        if e.status == 401:
            raise HTTPException(status_code=503, detail="Twilio credentials are invalid. Check .env.")
        raise HTTPException(status_code=500, detail=f"Twilio error {e.status}: {e.msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OTP verification failed: {e}")
