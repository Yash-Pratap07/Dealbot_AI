from agents import BuyerAgent, SellerAgent
from evaluation import evaluate_deal
from voting import majority_vote
from memory import compress_memory


async def run_negotiation(max_price, min_price):

    buyer = BuyerAgent(max_price, model="gemini")
    seller = SellerAgent(min_price, model="gemini")

    context = ""
    history = []

    for round in range(6):

        buyer_offer = await buyer.propose(context)
        seller_offer = await seller.counter(context + buyer_offer)

        history.append({
            "round": round + 1,
            "buyer": buyer_offer,
            "seller": seller_offer
        })

        context += f"Buyer: {buyer_offer}\nSeller: {seller_offer}\n"

        if round % 3 == 2:
            context = await compress_memory(context)

        if abs(float(buyer_offer) - float(seller_offer)) < 100:
            final_price = (float(buyer_offer) + float(seller_offer)) / 2

            evaluation = await evaluate_deal(context)
            votes = await majority_vote(context)

            return {
                "agreement": True,
                "final_price": final_price,
                "evaluation": evaluation,
                "votes": votes,
                "history": history
            }

    return {"agreement": False, "history": history}
