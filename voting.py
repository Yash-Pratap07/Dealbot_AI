from llm_router import call_gpt, call_gemini


async def majority_vote(context):

    g1 = await call_gpt("Accept or Reject?\n" + context)
    g2 = await call_gpt("Accept or Reject?\n" + context)
    m = await call_gemini("Accept or Reject?\n" + context)

    votes = [g1.strip(), g2.strip(), m.strip()]
    return votes
