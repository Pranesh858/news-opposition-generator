# DialecticAI — Category-Aware News Sentiment & Steelman Opposition Generator

An AI-powered dialectical reasoning platform that analyzes news headlines and articles, classifies categories and granular sentiment polarity, and generates good-faith **steelman counter-arguments**, **common ground**, and **critical reflection questions** to counter cognitive polarization.

---

## Key Features

- **Multi-Category Classification:** Categorizes news across *Politics*, *Sports*, *Technology & AI*, *Economy & Business*, *Science & Climate*, and *Society & Culture*.
- **Visual Sentiment Polarity Gauge:** Computes a normalized polarity score (`-100` to `+100`) with an explicit sentiment rationale.
- **Three Dialectical Perspective Modes:**
  - **Balanced Synthesis:** Fair, measured multi-angle counter-weight.
  - **Steelman Stance:** The absolute strongest, most coherent philosophical & structural defense of the counter-position.
  - **Critical Challenger:** Interrogates hidden assumptions, trade-offs, and second-order unintended costs.
- **Deep Dialectical Breakdown:**
  - 🎯 **Primary Nuanced Counter-Take** (Hero viewpoint)
  - 📑 **Original Key Claims** vs. 🛡️ **Structured Counter-Arguments** (Side-by-side comparative cards)
  - 🤝 **Foundational Common Ground** (Shared underlying human/policy priorities)
  - ❓ **Critical Thinking Probes** (Reflective questions for readers)
- **1-Click Curated Presets:** Instant testing across diverse news topics (Urban Zoning, Penalty Drama, AI Workforce, Interest Rates, SMR Nuclear, Office Mandates).
- **Offline Demo Engine Fallback:** Works immediately even without an API key, and seamlessly upgrades to live ultra-fast LLM inference when `GROQ_API_KEY` is configured.
- **Modern UI / UX:** Sleek glassmorphism, responsive layout, Dark/Light mode toggle, export/copy markdown report, and session history in `localStorage`.

---

## Architecture

```
frontend/  React (Vite) + Lucide Icons + Modern Glassmorphic CSS System
backend/   FastAPI      — /analyze, /presets, /health endpoints with Groq LLM
```

The frontend never communicates with LLMs directly — all requests route through the FastAPI backend with connection-pooled HTTP clients, regex safety moderation, and structured JSON parsing.

---

## Setup & Running

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Optional: Add your free key from https://console.groq.com/keys to .env
uvicorn main:app --reload --port 8000
```

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in your browser.

---

## API Reference

### `GET /health`
Returns backend health, active model, and configuration status.

### `GET /presets`
Returns curated 1-click sample headlines.

### `POST /analyze`
**Request Body:**
```json
{
  "text": "Federal Reserve raises benchmark interest rates by 50 basis points to curb persistent inflation...",
  "perspective_mode": "steelman"
}
```

**Response (`AnalyzeResponse`):**
```json
{
  "category": "Economy & Business",
  "category_icon": "TrendingUp",
  "sentiment": "Negative",
  "sentiment_score": -45,
  "sentiment_reason": "Highlights widespread fears of recession and borrowing pain.",
  "key_claims": [
    "Federal Reserve implemented a 50 bps benchmark rate hike",
    "Action is aimed at curbing persistent consumer price inflation"
  ],
  "opposition_opinion": "While higher interest rates create borrowing friction...",
  "counter_arguments": [
    "Unchecked inflation erodes purchasing power faster than interest rate friction.",
    "Decisive action preserves long-term currency credibility."
  ],
  "common_ground": "Both agree that durable economic growth requires predictable prices.",
  "critical_questions": [
    "Where is the tipping point where rate hikes inflict more systemic damage than inflation?",
    "How can targeted fiscal relief protect vulnerable small businesses?"
  ],
  "perspective_mode": "steelman",
  "disclaimer": "This is an AI-generated alternative perspective...",
  "is_demo_mode": false,
  "source_model": "openai/gpt-oss-120b"
}
```

---

## Safety & Ethics

1. **Pre-LLM Filter:** Blocks violent, hateful, or abusive prompts before hitting the model.
2. **System Prompt Constraints:** Strict instructions to avoid ad hominem attacks, slurs, or caricatures, critiquing structural positions rather than attacking people.
3. **Mandatory Disclaimer:** Fixed disclaimer on all AI-generated perspectives ensuring transparency.
