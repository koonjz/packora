"""
Vercel Serverless Function entry point for Packora API.

Vercel routes /api/* here. The path arriving at this ASGI handler
still has the /api prefix (Vercel does NOT strip it), so FastAPI
must handle both:
  - /api/commodities   (via routers mounted with prefix="/api")
  - /health            (for local dev or direct call)
"""
from __future__ import annotations

import sys
from pathlib import Path

# Ensure backend/ directory is on sys.path so `app.*` imports resolve
root_dir = Path(__file__).parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

# Import the pre-built FastAPI app (ASGI) — Vercel calls this directly
from app.main import app  # noqa: E402

__all__ = ["app"]
