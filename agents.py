from llm_router import call_claude, call_gpt


class BuyerAgent:
    def __init__(self, max_price, model="gemini"):
        self.max_price = max_price
        self.model = model

    async def propose(self, context):
        prompt = f"""
        You are a strategic buyer.
        Maximum budget: {self.max_price}.
        Respond ONLY with a number.
        Context:
        {context}
        """
        if self.model == "claude":
            return await call_claude(prompt)
        return await call_gpt(prompt)


class SellerAgent:
    def __init__(self, min_price, model="gemini"):
        self.min_price = min_price
        self.model = model

    async def counter(self, context):
        prompt = f"""
        You are a seller.
        Minimum acceptable price: {self.min_price}.
        Respond ONLY with a number.
        Context:
        {context}
        """
        if self.model == "claude":
            return await call_claude(prompt)
        return await call_gpt(prompt)
