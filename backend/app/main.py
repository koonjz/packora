"""
Packora FastAPI application factory.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.ranking_model import load_model
from app.routers import commodities, materials, recommend

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
    )

    # CORS — allow the Vite dev server and production Vercel frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers (include under both root and /api for seamless proxying/rewrites)
    app.include_router(recommend.router)
    app.include_router(commodities.router)
    app.include_router(materials.router)
    app.include_router(recommend.router, prefix="/api")
    app.include_router(commodities.router, prefix="/api")
    app.include_router(materials.router, prefix="/api")

    @app.on_event("startup")
    async def on_startup():
        logger.info("Packora API starting up …")
        logger.info("  ENABLE_CV_FEATURE        = %s", settings.enable_cv_feature)
        logger.info("  ENABLE_LLM_EXPLANATION   = %s", settings.enable_llm_explanation)

        # Automatic DB table creation & idempotent seeding (no Pre-Deploy command required!)
        try:
            import app.models  # noqa: F401 - ensure models are registered
            from app.database import AsyncSessionLocal, Base, engine
            from app.seed_db import seed_commodities, seed_materials

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            async with AsyncSessionLocal() as session:
                await seed_commodities(session)
                await seed_materials(session)
            logger.info("  Database auto-init & seed check completed ✓")
        except Exception as e:
            logger.warning("  Database auto-init warning: %s", e)

        # Pre-load the ranking model so the first request isn't slow
        model = load_model()
        if model is None:
            logger.warning("  Ranking model NOT loaded — using heuristic fallback")
        else:
            logger.info("  Ranking model loaded ✓")

    @app.get("/health", tags=["Health"], summary="Health check")
    @app.get("/api/health", tags=["Health"], summary="Health check")
    async def health():
        return {"status": "ok", "service": "packora-api"}

    return app


app = create_app()
