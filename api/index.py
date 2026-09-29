"""
Vercel Serverless Function entry point for Packora API.
Imports FastAPI app from backend/app/main.py.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add backend directory to sys.path
root_dir = Path(__file__).parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

__all__ = ["app"]
