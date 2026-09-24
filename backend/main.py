"""
Category-Aware News Sentiment & Opposition Opinion Generator
--------------------------------------------------------------
Backend: FastAPI with Groq LLM integration

Features:
- Multi-category classification (Politics, Sports, Technology & AI, Economy & Business, Science & Climate, Society & Culture)
- Granular sentiment polarity scoring (-100 to +100) and rationale
- Multi-dimensional opposing viewpoint generation (Main counter-take, Steelman arguments, Common ground, Critical thinking questions)
- Perspective modes: 'balanced', 'steelman', 'challenger'
- Curated preset sample headlines endpoint (/presets)
- Resilient connection-pooled HTTP client via FastAPI lifespan
- Seamless offline demo fallback when no API key is configured
- Robust JSON sanitization & defensive schema parsing
- Intelligent input safety moderation
"""

import os
import json
import re
from typing import Literal, List, Optional
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "").strip()
if GROQ_API_KEY in ("your_key_here", "your_groq_api_key_here", "<your_key_here>"):
    GROQ_API_KEY = ""

GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

SAFETY_DISCLAIMER = (
    "This is an AI-generated alternative perspective designed to encourage balanced "
    "critical thinking and nuance. It does not constitute a factual claim, verified reporting, "
    "or personal endorsement of any real individual or organization."
)

# Curated presets for instant 1-click testing
PRESET_SAMPLES = [
    {
        "id": "politics-zoning",
        "title": "Urban Zoning & 15-Minute Cities",
        "category": "Politics",
        "badge": "Urban Policy",
        "text": "City council officially approves controversial 15-minute city zoning regulations, restricting private vehicle access in downtown corridors while subsidizing high-density micro-apartments to combat carbon emissions.",
    },
    {
        "id": "sports-underdog",
        "title": "Championship Heartbreak & Penalty Drama",
        "category": "Sports",
        "badge": "Football / Soccer",
        "text": "Underdog FC suffers heartbreaking 2-1 defeat in the final stoppage minutes after referee awards a contested penalty against their captain, sparking furious protests from fans and team management.",
    },
    {
        "id": "tech-ai-workplace",
        "title": "Enterprise AI Workforce Automation",
        "category": "Technology & AI",
        "badge": "Artificial Intelligence",
        "text": "Major tech conglomerate replaces 30% of entry-level customer support and copywriting workforce with autonomous LLM agents, reporting record quarterly operating margins and faster turnaround times.",
    },
    {
        "id": "economy-rate-hike",
        "title": "Central Bank Benchmark Rate Hike",
        "category": "Economy & Business",
        "badge": "Monetary Policy",
        "text": "Federal Reserve raises benchmark interest rates by 50 basis points to curb persistent inflation, drawing sharp criticism from housing developers and small business associations fearing severe recession.",
    },
    {
        "id": "science-nuclear-energy",
        "title": "Next-Gen SMR Nuclear Energy Push",
        "category": "Science & Climate",
        "badge": "Clean Energy",
        "text": "Energy ministry greenlights $5B funding for next-generation small modular nuclear reactors (SMRs) as the primary baseline power solution for phasing out coal plants by 2030.",
    },
    {
        "id": "society-remote-work",
        "title": "Mandatory 5-Day Office Return Policy",
        "category": "Society & Culture",
        "badge": "Workplace Culture",
        "text": "Fortune 500 financial institution mandates strict 5-day in-office attendance with badge tracking, warning that non-compliance will directly impact performance reviews and promotion eligibility.",
    },
]

# Preset mock data for instant offline demonstration
OFFLINE_DEMO_RESPONSES = {
    "politics-zoning": {
        "category": "Politics",
        "sentiment": "Neutral",
        "sentiment_score": 12,
        "sentiment_reason": "The report presents the council's legislative decision alongside contrasting climate objectives and public controversy.",
        "key_claims": [
            "Council passed 15-minute city zoning restricting private vehicles in downtown zones",
            "High-density micro-apartments are being subsidized to reduce transport emissions",
            "The measure faces ongoing local opposition regarding access and mobility",
        ],
        "opposition_opinion": "While reducing carbon footprint and improving walkability are laudable municipal goals, sudden private vehicle restrictions can disproportionately isolate suburban commuters, elderly residents, and service workers who lack viable rapid transit alternatives. Subsidizing micro-apartments without expanding essential public services like clinics, grocery hubs, and schools risks creating claustrophobic urban enclaves rather than vibrant, accessible communities.",
        "counter_arguments": [
            "Restricting vehicle access without first establishing comprehensive transit infrastructure harms low-income suburban shift workers.",
            "Micro-apartment developments often cater to transient singles, potentially pricing out long-term working-class families.",
            "Top-down zoning mandates risk reducing commercial foot traffic for specialized local retailers who rely on regional visitors.",
        ],
        "common_ground": "Both advocates and critics share the common goal of creating livable, economically vibrant, and accessible cities with lower environmental strain.",
        "critical_questions": [
            "How can municipal planners ensure mobility equity for peripheral residents who cannot afford downtown housing?",
            "What metrics should define whether transit infrastructure is sufficiently mature before private vehicle restrictions take effect?",
        ],
    },
    "sports-underdog": {
        "category": "Sports",
        "sentiment": "Negative",
        "sentiment_score": -65,
        "sentiment_reason": "Frames the outcome as an agonizing defeat compounded by contentious officiating controversy.",
        "key_claims": [
            "Underdog FC lost 2-1 during stoppage time",
            "A late penalty call against the captain determined the match outcome",
            "The decision prompted intense backlash from fans and management",
        ],
        "opposition_opinion": "Although stoppage-time penalties feel emotionally devastating for the underdog, match officials must enforce the letter of the law regardless of game narrative or clock status. From a defensive tactical perspective, committing a reckless tackle inside the penalty area while fatigued reflects poor situational game management rather than an officiating conspiracy. The winning team maintained tactical composure to exploit that split-second lapse.",
        "counter_arguments": [
            "Video replays frequently confirm minor contact that technically warrants a penalty under current IFAB guidelines.",
            "Fatigue-induced lapses in defensive discipline during stoppage time are legitimate footballing errors that winning teams capitalize upon.",
            "Referees cannot adjust rule strictness based on sympathy for underdog narratives or game timestamps.",
        ],
        "common_ground": "Both fanbases value fair rule enforcement, player safety, and transparent, consistent officiating standards in high-stakes matches.",
        "critical_questions": [
            "Does the current threshold for VAR interventions adequately balance flow with objective fairness?",
            "How can teams better train late-game emotional discipline to avoid giving referees difficult penalty decisions?",
        ],
    },
    "tech-ai-workplace": {
        "category": "Technology & AI",
        "sentiment": "Positive",
        "sentiment_score": 58,
        "sentiment_reason": "Emphasizes record profit margins and productivity improvements stemming from LLM automation.",
        "key_claims": [
            "30% of entry-level customer support and copywriters replaced with AI agents",
            "Company achieved record quarterly operating margins",
            "Turnaround times for customer service improved significantly",
        ],
        "opposition_opinion": "While autonomous agents offer immediate margin expansion and rapid response throughput, hollowing out entry-level roles eliminates the foundational training pipeline where future senior domain leaders develop expertise. Furthermore, algorithmic customer support often struggles with complex edge cases and genuine human empathy, risking customer goodwill and exposing firms to hallucinated commitments or brand degradation over time.",
        "counter_arguments": [
            "Eliminating junior roles destroys the institutional mentorship funnel that cultivates future senior leadership.",
            "Automated agents lack contextual judgment and emotional intelligence during sensitive customer escalations.",
            "Short-term margin gains may be offset by long-term customer churn due to impersonal customer support experiences.",
        ],
        "common_ground": "Both business leaders and workforce advocates prioritize sustainable organizational productivity, customer satisfaction, and technological competitiveness.",
        "critical_questions": [
            "How will organizations train the next generation of senior experts if entry-level cognitive tasks are fully automated?",
            "What is the true lifetime cost of customer dissatisfaction when automated interactions fail on nuanced inquiries?",
        ],
    },
    "economy-rate-hike": {
        "category": "Economy & Business",
        "sentiment": "Negative",
        "sentiment_score": -45,
        "sentiment_reason": "Highlights widespread fears of recession, borrowing pain, and industry pushback against monetary tightening.",
        "key_claims": [
            "Federal Reserve implemented a 50 bps benchmark rate hike",
            "Action is aimed at curbing persistent consumer price inflation",
            "Housing developers and small businesses voice urgent recession warnings",
        ],
        "opposition_opinion": "While higher interest rates undeniably create acute borrowing friction for housing and small enterprises, unchecked runaway inflation represents a far more pernicious tax on low- and middle-income families. Allowing inflation expectations to become permanently unanchored would inflict prolonged economic scarring. Decisive central bank action preserves long-term currency credibility and price stability.",
        "counter_arguments": [
            "Unchecked inflation erodes purchasing power and real wage gains faster than temporary interest rate friction.",
            "Artificially suppressing rates during high inflation risks stagflation and asset bubbles that require harsher corrections later.",
            "Central bank independence and credibility depend on prioritizing macro price stability over short-term political pressures.",
        ],
        "common_ground": "Both central bankers and industry leaders agree that durable, sustainable economic growth requires predictable prices and stable purchasing power.",
        "critical_questions": [
            "Where is the precise tipping point where interest rate medicine inflicts more systemic damage than the inflation illness?",
            "How can targeted fiscal relief protect vulnerable small businesses while monetary policy remains restrictive?",
        ],
    },
    "science-nuclear-energy": {
        "category": "Science & Climate",
        "sentiment": "Positive",
        "sentiment_score": 62,
        "sentiment_reason": "Frames SMR funding as a proactive, clean baseline solution to replace fossil fuel plants.",
        "key_claims": [
            "$5 billion committed to small modular nuclear reactor (SMR) development",
            "SMRs positioned as primary baseline power to phase out coal by 2030",
            "Ministry prioritizes grid reliability alongside carbon reduction",
        ],
        "opposition_opinion": "While small modular reactors promise dispatchable, carbon-free baseline power, the commercial SMR technology remains largely unproven at scale within the urgent 2030 decarbonization timeline. SMR projects historically face significant capital cost overruns, regulatory delays, and unresolved high-level waste disposal strategies, whereas mature renewable solar, wind, and battery storage solutions can be deployed immediately at lower cost per megawatt-hour.",
        "counter_arguments": [
            "SMR supply chains and commercial licensing remain nascent, making 2030 deployment targets highly speculative.",
            "Capital-intensive nuclear investments could divert critical funding away from rapidly deployable solar, wind, and grid storage.",
            "Nuclear waste lifecycle management and long-term security costs remain substantial externalities.",
        ],
        "common_ground": "Both nuclear proponents and renewable advocates share the paramount objective of decarbonizing the energy grid and securing reliable power.",
        "critical_questions": [
            "Can SMR manufacturing scale quickly enough to meet urgent 2030 emissions benchmarks compared to modular battery storage?",
            "What is the optimal grid mix ratio between intermittent renewables and baseload clean power?",
        ],
    },
    "society-remote-work": {
        "category": "Society & Culture",
        "sentiment": "Negative",
        "sentiment_score": -52,
        "sentiment_reason": "Highlights employee discontent and punitive measures surrounding mandatory in-office enforcement.",
        "key_claims": [
            "Mandatory 5-day in-office return policy enacted with badge tracking",
            "Non-compliance tied directly to performance ratings and promotions",
            "Aimed at revitalizing corporate culture and team collaboration",
        ],
        "opposition_opinion": "From executive and organizational design perspectives, physical co-location accelerates spontaneous cross-departmental problem solving, strengthens apprenticeships for junior talent, and deepens social capital that digital channels struggle to replicate. Furthermore, clear, unified attendance standards eliminate friction around perceived fairness across departments that cannot operate remotely.",
        "counter_arguments": [
            "In-person collaboration fosters spontaneous brainstorming and tacit knowledge transfer that scheduled video calls miss.",
            "Junior staff and new hires benefit exponentially from observing senior colleagues in natural workplace environments.",
            "Consistent in-person standards prevent team fragmentation and foster unified corporate culture.",
        ],
        "common_ground": "Both leadership and employees desire high-performing, collaborative teams where individual contributions are recognized and work-life boundaries respected.",
        "critical_questions": [
            "How can companies measure whether in-person presence truly produces superior innovation compared to asynchronous work?",
            "What hybrid arrangements provide meaningful face-to-face mentorship without sacrificing schedule autonomy?",
        ],
    },
}

# ---------------------------------------------------------------------------
# Lifespan: Shared HTTP Client Connection Pool
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.http_client = httpx.AsyncClient(
        timeout=httpx.Timeout(45.0, connect=10.0),
        limits=httpx.Limits(max_keepalive_connections=20, max_connections=50),
    )
    yield
    await app.state.http_client.aclose()


app = FastAPI(
    title="News Sentiment & Opposition Generator API",
    description="Category-aware sentiment classifier and respectful opposition viewpoint engine",
    version="2.1.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request & Response Schemas
# ---------------------------------------------------------------------------

class AnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=5, max_length=10000, description="News headline or article text")
    perspective_mode: Optional[Literal["balanced", "steelman", "challenger"]] = Field(
        default="balanced",
        description="Mode for the counter-viewpoint (balanced, steelman, or challenger)",
    )


class AnalyzeResponse(BaseModel):
    category: str
    category_icon: str
    sentiment: Literal["Positive", "Negative", "Neutral"]
    sentiment_score: int = Field(description="Polarity score from -100 to +100")
    sentiment_reason: str
    key_claims: List[str]
    opposition_opinion: str
    counter_arguments: List[str]
    common_ground: str
    critical_questions: List[str]
    perspective_mode: str
    disclaimer: str
    is_demo_mode: bool = False
    source_model: Optional[str] = None


# ---------------------------------------------------------------------------
# Safety Moderation
# ---------------------------------------------------------------------------

BLOCKED_PATTERNS = [
    r"\b(?:hate\s+speech|kill\s+all|exterminate|genocide|lynch)\b",
    r"\b(?:nazi|white\s+supremac|terrorist\s+manifesto)\b",
    r"\b(?:how\s+to\s+(?:build\s+a\s+bomb|make\s+explosives|commit\s+suicide))\b",
]

def is_input_safe(text: str) -> bool:
    lowered = text.lower()
    return not any(re.search(pattern, lowered) for pattern in BLOCKED_PATTERNS)


CATEGORY_ICONS = {
    "Politics": "Landmark",
    "Sports": "Trophy",
    "Technology & AI": "Cpu",
    "Technology": "Cpu",
    "Economy & Business": "TrendingUp",
    "Economy": "TrendingUp",
    "Science & Climate": "FlaskConical",
    "Science": "FlaskConical",
    "Society & Culture": "Users",
    "Society": "Users",
    "General": "Newspaper",
}

# ---------------------------------------------------------------------------
# Prompt Engineering
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert news analyst and dialectical reasoning assistant. Given a news headline or article excerpt, your task is to objectively categorize it, evaluate its sentiment, and craft a rigorous, balanced, and respectful opposing perspective.

Perspective Mode Guidelines:
- "balanced": Provide a fair, measured counter-weight acknowledging valid points on both sides.
- "steelman": Present the absolute strongest, most coherent good-faith philosophical/policy argument for the opposing stance.
- "challenger": Actively interrogate assumptions, highlighting trade-offs, overlooked costs, and alternative interpretations.

Category Rules:
- Accurately determine the best-fit category from: "Politics", "Sports", "Technology & AI", "Economy & Business", "Science & Climate", "Society & Culture", or "General".
- For "Sports": The opposition MUST represent an informed rival fan perspective, tactical alternative, or defense of the losing/underperforming side (never political).
- For "Politics" & "Economy": Focus strictly on structural principles, trade-offs, fiscal/societal outcomes, and avoid ad hominem character attacks on individuals.
- For "Technology & Science": Balance innovation hype against safety, labor, ethics, environmental, or empirical reproducibility concerns.

General Opposition Rules:
1. Always acknowledge the core validity or intent of the original article before introducing counter-arguments.
2. Maintain a respectful, intellectual, and constructive tone — no hostility, slurs, or caricatures.
3. Identify 2-3 specific key claims made by the original text.
4. Provide 2-3 structured counter-arguments.
5. Identify a point of "Common Ground" where both viewpoints share an underlying priority.
6. Provide 2 thought-provoking "Critical Questions" for readers.

You MUST reply with ONLY a single valid JSON object, without markdown formatting or commentary, matching this exact schema:
{
  "category": "Politics | Sports | Technology & AI | Economy & Business | Science & Climate | Society & Culture | General",
  "sentiment": "Positive | Negative | Neutral",
  "sentiment_score": <-100 to 100 integer representing polarity>,
  "sentiment_reason": "One concise sentence explaining why the article leans this way.",
  "key_claims": ["Claim 1 from original text", "Claim 2 from original text"],
  "opposition_opinion": "3 to 5 sentences articulating the nuanced opposing viewpoint.",
  "counter_arguments": [
    "First structured counter-argument or overlooked trade-off",
    "Second structured counter-argument or alternative interpretation"
  ],
  "common_ground": "One sentence explaining shared underlying values or goals between both perspectives.",
  "critical_questions": [
    "First probing question to challenge assumptions",
    "Second probing question for deeper inquiry"
  ]
}
"""


def clean_and_parse_json(raw_text: str) -> dict:
    """Robustly cleans LLM response of markdown fences or surrounding noise."""
    cleaned = raw_text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE).strip()
    
    json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if json_match:
        cleaned = json_match.group(0)
    
    return json.loads(cleaned)


def generate_heuristic_offline_response(text: str, perspective_mode: str) -> dict:
    """Generates a high quality contextual offline analysis when API key is not configured."""
    # Check if text matches any preset
    lowered = text.lower()
    for preset_id, data in OFFLINE_DEMO_RESPONSES.items():
        preset_sample = next((p for p in PRESET_SAMPLES if p["id"] == preset_id), None)
        if preset_sample and (preset_sample["text"].lower() in lowered or lowered in preset_sample["text"].lower()):
            resp = dict(data)
            resp["perspective_mode"] = perspective_mode
            return resp

    # Keyword detection for category
    category = "General"
    if any(k in lowered for k in ["court", "senate", "parliament", "election", "policy", "vote", "council", "mayor", "minister", "legislation"]):
        category = "Politics"
    elif any(k in lowered for k in ["fc", "cup", "match", "tournament", "score", "game", "referee", "player", "championship", "coach", "league"]):
        category = "Sports"
    elif any(k in lowered for k in ["ai", "software", "tech", "algorithm", "chip", "cyber", "robot", "cloud", "model", "apple", "google"]):
        category = "Technology & AI"
    elif any(k in lowered for k in ["inflation", "market", "bank", "stock", "rate", "fed", "recession", "revenue", "dollar", "trade", "fund"]):
        category = "Economy & Business"
    elif any(k in lowered for k in ["climate", "nuclear", "energy", "study", "research", "carbon", "planet", "emission", "vaccine", "biology"]):
        category = "Science & Climate"
    elif any(k in lowered for k in ["workplace", "remote", "school", "community", "culture", "health", "family", "housing", "social"]):
        category = "Society & Culture"

    # Polarity estimation
    pos_words = ["gain", "record", "growth", "breakthrough", "success", "win", "approved", "triumph", "boost", "positive"]
    neg_words = ["loss", "crisis", "fall", "defeat", "dispute", "protest", "risk", "criticism", "slump", "fear", "warning"]
    
    pos_count = sum(1 for w in pos_words if w in lowered)
    neg_count = sum(1 for w in neg_words if w in lowered)
    
    if pos_count > neg_count:
        sentiment = "Positive"
        sentiment_score = min(75, 30 + pos_count * 15)
        reason = "The text emphasizes positive achievements, advancements, or optimistic projections."
    elif neg_count > pos_count:
        sentiment = "Negative"
        sentiment_score = max(-80, -35 - neg_count * 15)
        reason = "The text highlights conflict, potential vulnerabilities, or adverse consequences."
    else:
        sentiment = "Neutral"
        sentiment_score = 5
        reason = "The text reports factual developments and competing considerations in a balanced manner."

    return {
        "category": category,
        "sentiment": sentiment,
        "sentiment_score": sentiment_score,
        "sentiment_reason": reason,
        "key_claims": [
            f"Primary report on {text[:60].strip()}...",
            "Contextual focus on current outcomes and stakeholder reactions",
        ],
        "opposition_opinion": f"While this report highlights important immediate developments regarding this issue, a comprehensive assessment requires examining secondary trade-offs, implementation hurdles, and alternative interpretations that may not be immediately apparent. Good-faith dialogue requires balancing immediate outcomes with broader structural impacts over time.",
        "counter_arguments": [
            "Consider whether short-term benefits overlook long-term unintended economic or systemic friction.",
            "Examine how stakeholders with differing priorities might interpret these developments and baseline metrics.",
            "Evaluate whether alternative policy or tactical choices could yield more equitable and resilient results.",
        ],
        "common_ground": "All participating stakeholders share a fundamental interest in stability, transparency, and evidence-based decision making.",
        "critical_questions": [
            "What unstated assumptions underpin the primary framing of this development?",
            "What measurable indicators would indicate whether this approach succeeds or requires adjustment?",
        ],
    }


async def call_groq(client: httpx.AsyncClient, article_text: str, perspective_mode: str = "balanced") -> tuple[dict, str]:
    if not GROQ_API_KEY:
        # Fallback to local heuristic engine
        return generate_heuristic_offline_response(article_text, perspective_mode), "offline-demo-engine"

    user_message = f"Perspective Mode: {perspective_mode}\n\nArticle / Headline:\n{article_text}"

    # Verified Groq production models with fallbacks
    candidate_models = [
        GROQ_MODEL,
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "qwen/qwen3.8-27b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]
    models_to_try = list(dict.fromkeys(m for m in candidate_models if m))

    last_error = None
    for model_name in models_to_try:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            "temperature": 0.35,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        }

        try:
            resp = await client.post(GROQ_API_URL, json=payload, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                raw_content = data["choices"][0]["message"]["content"]
                parsed = clean_and_parse_json(raw_content)
                return parsed, model_name
            elif resp.status_code in (400, 404) or "model_not_found" in resp.text:
                last_error = resp.text
                continue
            elif resp.status_code == 401:
                # Invalid API key -> fallback to demo mode rather than crash
                return generate_heuristic_offline_response(article_text, perspective_mode), "offline-demo-engine"
            else:
                last_error = resp.text
                continue
        except (json.JSONDecodeError, KeyError):
            last_error = "Model returned invalid JSON structure."
            continue
        except httpx.RequestError as exc:
            last_error = str(exc)
            continue

    # If all models failed or network issue, fallback to offline heuristic engine
    return generate_heuristic_offline_response(article_text, perspective_mode), "offline-demo-fallback"


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok",
        "groq_configured": bool(GROQ_API_KEY),
        "active_model": GROQ_MODEL if GROQ_API_KEY else "offline-demo-engine",
        "version": "2.1.0",
        "supported_categories": list(CATEGORY_ICONS.keys()),
        "perspective_modes": ["balanced", "steelman", "challenger"],
    }


@app.get("/presets")
def get_presets():
    """Returns curated headline samples for quick 1-click exploration."""
    return {"presets": PRESET_SAMPLES}


def get_http_client(request: Request) -> httpx.AsyncClient:
    if hasattr(request.app.state, "http_client") and request.app.state.http_client:
        return request.app.state.http_client
    if not hasattr(request.app.state, "_lazy_http_client"):
        request.app.state._lazy_http_client = httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=10.0))
    return request.app.state._lazy_http_client


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(req: AnalyzeRequest, request: Request):
    if not is_input_safe(req.text):
        raise HTTPException(
            status_code=400,
            detail="Input contains blocked or sensitive content. Please submit standard news reporting, headlines, or opinion articles.",
        )

    http_client = get_http_client(request)
    mode = req.perspective_mode or "balanced"

    result, source_model = await call_groq(http_client, req.text, perspective_mode=mode)

    # Normalize category
    category = result.get("category", "General")
    matched_cat = "General"
    for cat_key in CATEGORY_ICONS:
        if cat_key.lower() == category.lower() or cat_key.lower() in category.lower() or category.lower() in cat_key.lower():
            matched_cat = cat_key
            break
    category = matched_cat
    category_icon = CATEGORY_ICONS.get(category, "Newspaper")

    # Normalize sentiment
    sentiment = result.get("sentiment", "Neutral")
    if sentiment not in ("Positive", "Negative", "Neutral"):
        sentiment = "Neutral"

    sentiment_score = result.get("sentiment_score", 0)
    try:
        sentiment_score = int(sentiment_score)
        sentiment_score = max(-100, min(100, sentiment_score))
    except (ValueError, TypeError):
        sentiment_score = 0

    is_demo = bool("offline-demo" in source_model or not GROQ_API_KEY)

    return AnalyzeResponse(
        category=category,
        category_icon=category_icon,
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        sentiment_reason=result.get("sentiment_reason", "Analysis of overall article tone and framing."),
        key_claims=result.get("key_claims", []) or ["Core framing from source article"],
        opposition_opinion=result.get("opposition_opinion", "Alternative perspective could not be generated."),
        counter_arguments=result.get("counter_arguments", []) or ["Consider alternative structural trade-offs."],
        common_ground=result.get("common_ground", "Both perspectives share an interest in constructive outcomes."),
        critical_questions=result.get("critical_questions", []) or ["What long-term systemic consequences might unfold?"],
        perspective_mode=mode,
        disclaimer=SAFETY_DISCLAIMER,
        is_demo_mode=is_demo,
        source_model=source_model,
    )
