"""Test WebSocket negotiation streaming."""
import asyncio, json

async def test_ws():
    try:
        import websockets
    except ImportError:
        print("Installing websockets...")
        import subprocess
        subprocess.check_call(["py", "-m", "pip", "install", "websockets", "-q"])
        import websockets

    uri = "ws://127.0.0.1:8000/ws/negotiate"
    async with websockets.connect(uri) as ws:
        await ws.send(json.dumps({
            "max_price": 1000, "min_price": 500,
            "product": "Laptop", "market_price": 750,
            "strategy": "balanced", "buyer_model": "gemini", "seller_model": "gemini",
        }))
        rounds = 0
        while True:
            msg = json.loads(await ws.recv())
            if msg["type"] == "round":
                rounds += 1
                r = msg["round"]
                b = msg["buyer"]
                s = msg["seller"]
                g = msg["gap"]
                print(f"  Round {r}: Buyer={b:.2f}  Seller={s:.2f}  Gap={g:.2f}")
            elif msg["type"] == "done":
                agr = msg["agreement"]
                fp = msg.get("final_price")
                rt = msg.get("rounds_taken")
                print(f"  DONE: agreement={agr}  price={fp}  rounds={rt}")
                stl = msg.get("settlement")
                if stl:
                    mode = stl.get("settlement_mode")
                    tx = (stl.get("wusd_tx_hash") or "")[:20]
                    print(f"  Settlement: mode={mode}  tx={tx}...")
                votes = msg.get("votes")
                if votes and isinstance(votes, dict):
                    dec = votes.get("decision")
                    ac = votes.get("accept_count")
                    print(f"  Votes: decision={dec}  accepts={ac}")
                break
        print(f"  WebSocket test PASSED ({rounds} rounds streamed)")

asyncio.run(test_ws())
