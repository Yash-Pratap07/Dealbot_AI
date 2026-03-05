from llm_router import call_gemini


async def evaluate_deal(context):
    prompt = f"""
    Rate fairness 0-10 and explain:
    {context}
    """
    return await call_gemini(prompt)
