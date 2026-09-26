# Packora — Intelligent Food Packaging Recommendation System
### *Packaging, chosen by science.*

> Smart India Hackathon 2026 · Problem Statement SIH26236  
> Ministry of Food Processing Industries (MoFPI) · Agriculture, FoodTech & Rural Development

---

## What is Packora?

Packora is an AI-assisted decision-support tool that tells food processors and MSMEs exactly which
packaging material fits a given food commodity — and explains why, in plain language — replacing
"pick packaging by habit" with "pick packaging by science."

The core insight: hard constraints (a food with high water activity **cannot** go in a
moisture-permeable wrapper) are solved by an explicit, auditable **rule engine**. Ranking among
the materials that *already pass* those constraints — where historical outcome data shows one
material extends shelf life further — is where the **ML layer** genuinely adds value.

---

## Architecture at a glance

```
User Input
    │
    ▼
┌───────────────┐     ┌─────────────────────────────────┐
│ React frontend│────▶│ FastAPI  POST /recommend          │
│ (Tailwind CSS)│     │                                  │
└───────────────┘     │  1. Rule Engine  (rule_engine.py)│
                      │     hard-constraint filter        │
                      │     → eliminates invalid options  │
                      │                                  │
                      │  2. ML Ranking   (ranking_model.py)
                      │     RandomForest / GBM            │
                      │     → scores valid candidates     │
                      │                                  │
                      │  3. Explainer    (explainer.py)  │
                      │     structured reasoning trace    │
                      │     + templated or LLM sentence  │
                      └─────────────────────────────────┘
                                    │
                               PostgreSQL
                          (commodities, materials, map)
```

---

## Quick start (local, fully offline)

```bash
# 1. Clone and enter
git clone <repo-url>
cd packora

# 2. Configure environment
cp .env.example .env
# Edit .env — set POSTGRES_PASSWORD at minimum. Everything else has sensible defaults.

# 3. Start everything
docker compose up --build

# 4. Open the app
open http://localhost:5173          # React frontend
open http://localhost:8000/docs     # FastAPI Swagger UI
```

No internet required once images are built.

---

## Running without Docker (development)

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
# Ensure PostgreSQL is running and DATABASE_URL is set in .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev    # serves on http://localhost:5173
```

---

## Project structure

See [STRUCTURE.md](./STRUCTURE.md) for the full annotated directory tree.

Key files:
| File | Purpose |
|---|---|
| `backend/app/rule_engine.py` | Tier-1 hard-constraint filter — testable with zero ML/DB |
| `backend/app/ranking_model.py` | Tier-2 ML ranking (scikit-learn RandomForest/GBM) |
| `backend/app/explainer.py` | Builds structured reasoning trace + plain-language output |
| `backend/app/llm_client.py` | Optional LLM call with offline fallback |
| `backend/app/cv_client.py` | Optional MobileNetV3 photo ID (gated by `ENABLE_CV_FEATURE`) |
| `backend/app/seed/` | Curated JSON seed data (commodities + packaging materials) |
| `PROJECT_BRIEF.md` | **The spec — read before making any changes** |

---

## API surface

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/recommend` | Core endpoint — returns ranked packaging options with full reasoning trace |
| `GET` | `/commodities` | Search / autocomplete commodity list |
| `GET` | `/materials` | Reference lookup of all packaging materials |

Full interactive docs at `/docs` (Swagger UI) and `/redoc` (ReDoc).

---

## Feature flags

| Flag | Default | What it controls |
|---|---|---|
| `ENABLE_CV_FEATURE` | `false` | Photo-upload commodity identification (MobileNetV3) |
| `ENABLE_LLM_EXPLANATION` | `true` | LLM-generated plain-language explanation (falls back to template if disabled or API unreachable) |

---

## Data sourcing

All knowledge-base data is manually curated from:
- **FSSAI** packaging guidelines
- **BIS** (Bureau of Indian Standards) IS-code specifications
- Published food-science shelf-life studies

Do **not** auto-scrape or generate synthetic data for the knowledge base.

---

## Deployment

| Service | Platform | Notes |
|---|---|---|
| Backend + DB | **Render** | Free tier; warm up 2–3 min before demo |
| Frontend | **Vercel** | Auto-deploys from `main` branch |
| Offline backup | Docker Compose | Primary demo mode — no internet required |

---

## Tech stack

Python · FastAPI · SQLAlchemy · Alembic · PostgreSQL · scikit-learn · React · Tailwind CSS · Docker Compose

---

*Competition brief: SIH26236 — "AI-Based Intelligent Food Packaging Material Recommendation System
for Food Commodities" — Ministry of Food Processing Industries, Smart India Hackathon 2026.*
