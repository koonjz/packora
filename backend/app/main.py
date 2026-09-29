"""
Packora FastAPI application factory.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ranking_model import load_model
from app.routers import commodities, materials, recommend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# DB / seed lazy-init  (called on first request in serverless, not only startup)
# ──────────────────────────────────────────────────────────────────────────────
_db_initialised = False


async def _ensure_db_ready() -> None:
    """Idempotent: create tables + seed on cold-start or first request."""
    global _db_initialised
    if _db_initialised:
        return
    try:
        import app.models  # noqa: F401  — registers ORM classes with Base
        from app.database import AsyncSessionLocal, Base, engine
        from app.seed_db import seed_commodities, seed_materials

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        async with AsyncSessionLocal() as session:
            await seed_commodities(session)
            await seed_materials(session)

        logger.info("Database auto-init & seed check completed ✓")
    except Exception as exc:
        logger.warning("Database auto-init warning: %s", exc)
    _db_initialised = True


async def _ensure_model_ready() -> None:
    """Load or auto-train the ML ranking model once per process."""
    model = load_model()
    if model is None:
        logger.info("No pre-trained model — auto-training ML ranker from seed dataset …")
        try:
            from app.ranking_model import generate_training_data_from_seed, train_and_save
            records = generate_training_data_from_seed()
            if records:
                train_and_save(records)
                logger.info("ML ranking model auto-trained and saved ✓")
        except Exception as err:
            logger.warning(
                "Could not auto-train ranking model (%s) — using heuristic fallback", err
            )
    else:
        logger.info("Ranking model loaded ✓")


# ──────────────────────────────────────────────────────────────────────────────
# Application factory
# ──────────────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup tasks (runs at ASGI lifespan startup)."""
    logger.info("Packora API starting up …")
    logger.info("  ENABLE_CV_FEATURE        = %s", settings.enable_cv_feature)
    logger.info("  ENABLE_LLM_EXPLANATION   = %s", settings.enable_llm_explanation)
    await _ensure_db_ready()
    await _ensure_model_ready()
    yield
    logger.info("Packora API shutting down.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Packora API — Intelligent Food Packaging Recommendation System",
        description=(
            "**Packaging, chosen by science.**\n\n"
            "AI-assisted packaging material recommendations for food MSMEs and FPOs.\n\n"
            "Smart India Hackathon 2026 · Problem Statement SIH26236 · MoFPI"
        ),
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # CORS — allow all origins in production (frontend is same Vercel domain)
    # For tighter security, set ALLOWED_ORIGINS env var to your domain list.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routers ──────────────────────────────────────────────────────────────
    # Mounted at BOTH root and /api prefix:
    #   - Root prefix  → used by local dev (Vite proxy strips /api)
    #   - /api prefix  → used by Vercel (passes full /api/* path to this ASGI app)
    for prefix in ("", "/api"):
        app.include_router(recommend.router, prefix=prefix)
        app.include_router(commodities.router, prefix=prefix)
        app.include_router(materials.router, prefix=prefix)

    # ── Health checks ─────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"], summary="Health check")
    @app.get("/api/health", tags=["Health"], summary="Health check (API prefix)")
    async def health():
        await _ensure_db_ready()   # also initialise on /health cold-start
        return {"status": "ok", "service": "packora-api"}

    # ── Debug endpoint (safe — API key is masked) ─────────────────────────────
    @app.get("/api/debug", tags=["Health"], summary="Config debug (key masked)")
    async def debug_config():
        """Returns effective runtime config so you can verify Vercel env vars."""
        key = settings.llm_api_key
        key_preview = (key[:6] + "…" + key[-4:]) if len(key) > 10 else ("(set, short)" if key else "(empty — LLM disabled)")
        db_url = settings.database_url
        db_preview = db_url[:30] + "…" if len(db_url) > 30 else db_url
        return {
            "app_env": settings.app_env,
            "enable_llm_explanation": settings.enable_llm_explanation,
            "enable_cv_feature": settings.enable_cv_feature,
            "llm_provider": settings.llm_provider,
            "llm_model": settings.llm_model,
            "llm_api_key_preview": key_preview,
            "llm_timeout_seconds": settings.llm_timeout_seconds,
            "allowed_origins": settings.allowed_origins,
            "database_url_preview": db_preview,
            "db_initialised": _db_initialised,
        }

    return app


app = create_app()
