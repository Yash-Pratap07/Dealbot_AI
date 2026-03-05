from fastapi import FastAPI
from orchestrator import run_negotiation

app = FastAPI()

@app.get("/")
def home():
    return {"message": "DealBot AI Running"}

@app.get("/negotiate")
async def negotiate(max_price: float, min_price: float):
    return await run_negotiation(max_price, min_price)
