"""
Category-Aware News Sentiment & Opposition Opinion Generator
--------------------------------------------------------------
Backend: FastAPI

Flow:
  1. Client sends a news headline/article (POST /analyze).
  2. We build ONE carefully-structured prompt and send it to Groq's
     free LLM API (OpenAI-compatible chat completions endpoint).
  3. The model returns strict JSON with:
       - category        ("Politics" or "Sports")
       - sentiment        (Positive / Negative / Neutral + short reason)
       - opposition       (a respectful counter-viewpoint)
       - disclaimer       (always included, non-negotiable)
  4. We validate/parse that JSON and return it to the frontend.

Why one LLM call instead of three?
  Fewer network round-trips, and it's cheaper/faster on a free tier.
  The tradeoff is we must be strict about the output format, so the
  prompt forces JSON and we defensively parse it.
"""

import os
import json
import re
from typing import Literal

from dotenv import load_dotenv
load_dotenv()  # reads GROQ_API_KEY from a local .env file if present

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
# Llama 3.3 70B is currently free on Groq and strong enough for this task.
# If it's ever retired, swap the model string here.
GROQ_MODEL = "llama-3.3-70b-versatile"

app = FastAPI(title="News Sentiment & Opposition Generator")

# Allow the React dev server (localhost:5173 for Vite, 3000 for CRA) to call this API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten this to your actual frontend URL before deploying publicly
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=4000, description="News headline or article body")


class AnalyzeResponse(BaseModel):
    category: Literal["Politics", "Sports"]
    sentiment: str
    sentiment_reason: str
    opposition_opinion: str
    disclaimer: str


# ---------------------------------------------------------------------------
# Safety controls (this is the part your README will point to)
# ---------------------------------------------------------------------------

SAFETY_DISCLAIMER = (
    "This is an AI-generated alternative perspective meant to encourage balanced "
    "thinking, not a factual claim or personal attack. It does not represent the "
    "views of any real individual or organization."
)

# Words/patterns we refuse to generate opposition content for -- if the
# input itself is inflammatory or targets a protected group, we short-circuit
# before ever calling the LLM.
BLOCKED_PATTERNS = [
    r"\bkill\b", r"\bnazi\b", r"\bterroris", r"\bslur\b",
]


def is_input_safe(text: str) -> bool:
    lowered = text.lower()
    return not any(re.search(pattern, lowered) for pattern in BLOCKED_PATTERNS)


# ---------------------------------------------------------------------------
# The prompt: this is where "category-aware" + "respectful opposition" lives
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a careful, neutral news-analysis assistant. Given a news \
headline or short article, you do three things:

1. CATEGORY: Classify it as exactly "Politics" or "Sports". If it is neither, \
pick whichever is the closer fit -- never invent a third category.

2. SENTIMENT: Classify the overall sentiment/tone of the article as "Positive", \
"Negative", or "Neutral", and give one short sentence explaining why.

3. OPPOSITION OPINION: Write a short (3-5 sentence) counter-viewpoint that \
respectfully disagrees with or complicates the article's framing. Rules for \
this section, which you must follow strictly:
   - Never use insults, slurs, or inflammatory language.
   - Never attack a person's character -- engage with ideas/arguments/events only.
   - Acknowledge the original viewpoint's validity before offering the counter-angle.
   - If the article is Sports, the "opposition" is a rival-fan or alternate-analysis \
     take (e.g. defending the losing side's performance), not political commentary.
   - If the article is Politics, present the strongest good-faith opposing policy \
     argument, not a caricature of it. Do not mention specific real politicians by \
     name if you can avoid it -- focus on the policy or event itself.
   - If genuinely no reasonable opposing view exists (e.g. a factual sports score), \
     say so honestly instead of inventing one.

Respond with ONLY valid JSON, no markdown fences, no commentary, in exactly this shape:
{"category": "...", "sentiment": "...", "sentiment_reason": "...", "opposition_opinion": "..."}
"""


async def call_groq(article_text: str) -> dict:
    if not GROQ_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="GROQ_API_KEY is not set on the server. Get a free key at https://console.groq.com/keys",
        )

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": article_text},
        ],
        "temperature": 0.4,
        "response_format": {"type": "json_object"},
    }
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(GROQ_API_URL, json=payload, headers=headers)

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail=f"Groq API error: {resp.text}")

    data = resp.json()
    raw_content = data["choices"][0]["message"]["content"]

    try:
        parsed = json.loads(raw_content)
    except json.JSONDecodeError:
        raise HTTPException(status_code=502, detail="Model did not return valid JSON.")

    return parsed


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest):
    if not is_input_safe(req.text):
        raise HTTPException(
            status_code=400,
            detail="Input contains content this tool won't process. Please submit a standard news headline or article.",
        )

    result = await call_groq(req.text)

    # Defensive fallback in case the model mislabels the category
    category = result.get("category", "Politics")
    if category not in ("Politics", "Sports"):
        category = "Politics"

    return AnalyzeResponse(
        category=category,
        sentiment=result.get("sentiment", "Neutral"),
        sentiment_reason=result.get("sentiment_reason", ""),
        opposition_opinion=result.get("opposition_opinion", ""),
        disclaimer=SAFETY_DISCLAIMER,
    )
