# PROJECT BRIEF — Packora: Intelligent Food Packaging Recommendation System

> **Single source of truth.** Any AI coding assistant working on this codebase should read this
> file in full before making changes, and treat it as the contract for scope, architecture, naming,
> and conventions. If a future instruction conflicts with this file, flag the conflict instead of
> silently picking one.

---

## 1. What this product is

**Name:** Packora — Intelligent Food Packaging Recommendation System
**Tagline:** *Packaging, chosen by science.*

**One-line pitch:** An AI-assisted decision-support tool that tells food processors and MSMEs which
packaging material actually fits a given food commodity, and explains why.

**Competition context:** Smart India Hackathon 2026, Problem Statement SIH26236.
Sponsor: Ministry of Food Processing Industries (MoFPI).
Theme: Agriculture, FoodTech & Rural Development. Category: Software.

**Who it's for:** MSMEs, FPOs, and packaging decision-makers without an in-house food scientist.

**What the system does, end to end:**
1. User selects/searches a food commodity and enters target shelf life, storage conditions,
   and transport conditions.
2. Backend looks up the commodity's known properties (moisture %, water activity, respiration rate,
   fat content, light sensitivity, fragility).
3. **Rule engine** filters packaging materials to those satisfying hard physical constraints
   (WVTR, OTR thresholds).
4. **ML ranking layer** scores surviving candidates on a composite fit score.
5. Output: top 2–3 recommendations with comparison table and plain-language explanation.
6. **Optional LLM call** generates natural-language explanation — degrades gracefully to a
   templated sentence if offline. Core recommendation never depends on an external API.

**Honest pitch for judges:** "Rule engine for hard constraints (reliable, explainable) + ML for
ranking within the valid option set (where data-driven scoring beats fixed weights)."
Never turn hard constraints into 'the model figures it out.'

---

## 2. Non-negotiable design principles

1. **Explainability by design.** Every recommendation must trace to specific rules and score
   components. Never replace the rule engine with a single opaque model call.
2. **Offline-first demo reliability.** Full stack runs via Docker Compose with zero internet.
   External API features must have local fallbacks; must never block core recommendation flow.
3. **Small, curated dataset assumption.** ~100–150 labeled commodity-material pairs.
   Tree-based models (RandomForest/GBM) are correct and intentional, not a placeholder.
4. **Domain-knowledge sourcing is manual curation.** Data from FSSAI packaging guidelines,
   BIS (IS-code) standards, and published food-science shelf-life studies — not auto-scraped.

---

## 3. Tech stack (exact — do not substitute without updating this file)

| Layer | Technology | Notes |
|---|---|---|
| Database | **PostgreSQL** | commodities, packaging_materials, commodity_packaging_map |
| Backend / API | **Python + FastAPI** | Swagger docs used live in demos |
| ORM | **SQLAlchemy + Alembic** | Migrations tracked in `alembic/` |
| Rule engine | **Plain Python** (`backend/app/rule_engine.py`) | Tier 1; zero ML dependency |
| ML ranking | **scikit-learn** (`backend/app/ranking_model.py`) | RandomForest / GBM; feature importances = explainability |
| Optional LLM | Any hosted model via API call | Templated-sentence fallback required |
| Optional CV | **TensorFlow/PyTorch + MobileNetV3** (`ENABLE_CV_FEATURE` flag) | Behind feature flag; never blocks core flow |
| Frontend | **React + Tailwind CSS** | `frontend/` directory |
| Infra | **Docker Compose** | `docker-compose.yml` at repo root |
| Hosting | **Render** (backend/DB) + **Vercel** (frontend) | Free tier; warm up before demo |

**Core database tables (minimum viable schema):**
```sql
commodities(id, name, moisture_pct, water_activity, respiration_rate,
            fat_content, light_sensitivity, fragility)

packaging_materials(id, name, wvtr, otr, cost_per_unit,
                    biodegradability_score, typical_use_case)

commodity_packaging_map(commodity_id, material_id, suitability_score, notes)
```

**Core API endpoints:**
- `POST /recommend` — commodity + conditions → ranked packaging options + full reasoning trace
- `GET /commodities` — search/autocomplete over commodity table
- `GET /materials` — reference lookup over packaging materials table

---

## 4. Conventions for multi-AI development

- **This file is the spec.** Re-read the relevant section before implementing any feature.
- **Stack changes** require an explicit team decision recorded in this file first.
- **`rule_engine.py` and `ranking_model.py` must stay separate** and independently testable.
- **Every `/recommend` response must include a structured reasoning trace** (rules passed/failed,
  score components) — the plain-language sentence is generated *from* this trace.
- **Naming:** `snake_case` functions/variables, `PascalCase` classes.
  Files named for what they contain (`rule_engine.py`, not `logic2.py`).
  API routes: plural nouns (`/commodities`, not `/getCommodity`).
- **New external dependencies** must be called out explicitly (offline-demo constraint).
- **Commit messages** describe *why*, not just *what*.

---

## 5. MVP definition of done

- [ ] `docker compose up` runs Postgres + FastAPI + frontend with zero internet access
- [ ] Knowledge base: ≥ 100 curated commodities, full packaging materials table
- [ ] `POST /recommend` returns ranked list with barrier properties, cost, sustainability score,
      and plain-language reason for at least one real end-to-end example
- [ ] Rule engine demonstrable in isolation (Swagger UI or script) rejecting a wrong material
- [ ] Frontend: non-technical user can pick commodity, enter conditions, see recommendation + explanation
- [ ] LLM failure degrades gracefully to templated sentence (tested with network disabled)
- [ ] Photo upload works behind `ENABLE_CV_FEATURE` flag; disabled state does not crash the app

---

## 6. Resolved open decisions

| Decision | Resolution |
|---|---|
| Product name | **Packora — Intelligent Food Packaging Recommendation System** |
| Tagline | *Packaging, chosen by science.* |
| Frontend | **React + Tailwind CSS** |
| Photo-based commodity ID (CV) | **In MVP, behind `ENABLE_CV_FEATURE` feature flag** |
| Live hosting | **Render** (backend/DB) + **Vercel** (frontend) |
| First build priority | Project scaffold |
