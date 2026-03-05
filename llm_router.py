import os
import asyncio
from dotenv import load_dotenv
from google import genai

load_dotenv()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


async def call_gemini(prompt):
    await asyncio.sleep(2)  # avoid free-tier rate limits
    response = gemini_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()


# Aliases so rest of project works without changes
async def call_gpt(prompt):
    return await call_gemini(prompt)


async def call_claude(prompt):
    return await call_gemini(prompt)
