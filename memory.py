from llm_router import call_gemini


async def compress_memory(context):
    prompt = f"Summarize negotiation preserving numbers:\n{context}"
    return await call_gemini(prompt)
