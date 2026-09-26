packora/
├── PROJECT_BRIEF.md          # ← this file is the spec (single source of truth)
├── docker-compose.yml        # orchestrates postgres + backend + frontend
├── .env.example              # template; copy to .env and fill in secrets
├── .gitignore
├── README.md
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       └── 0001_initial_schema.py
│   └── app/
│       ├── main.py           # FastAPI app factory + router registration
│       ├── config.py         # settings (env vars, feature flags)
│       ├── database.py       # SQLAlchemy engine + session
│       ├── models.py         # ORM models (Commodity, PackagingMaterial, Map)
│       ├── schemas.py        # Pydantic request/response schemas
│       ├── routers/
│       │   ├── recommend.py  # POST /recommend
│       │   ├── commodities.py# GET  /commodities
│       │   └── materials.py  # GET  /materials
│       ├── rule_engine.py    # Tier 1: hard-constraint filter (zero ML dependency)
│       ├── ranking_model.py  # Tier 2: ML ranking within valid option set
│       ├── explainer.py      # builds structured reasoning trace + templated sentence
│       ├── llm_client.py     # optional LLM call with offline fallback
│       ├── cv_client.py      # optional MobileNetV3 CV (behind ENABLE_CV_FEATURE)
│       └── seed/
│           ├── commodities.json
│           └── packaging_materials.json
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tailwind.config.js
    ├── postcss.config.js
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── App.jsx
        ├── index.css
        ├── api/
        │   └── packora.js    # axios wrappers for all 3 API endpoints
        ├── components/
        │   ├── CommoditySearch.jsx
        │   ├── ConditionsForm.jsx
        │   ├── RecommendationCard.jsx
        │   ├── ComparisonTable.jsx
        │   ├── ReasoningTrace.jsx
        │   ├── PhotoUpload.jsx   # ENABLE_CV_FEATURE gated
        │   └── LoadingSpinner.jsx
        └── pages/
            ├── HomePage.jsx
            └── ResultsPage.jsx
