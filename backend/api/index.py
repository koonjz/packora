"""
Vercel Serverless Function entry point for Packora FastAPI backend.
"""
import sys
from pathlib import Path

# Add backend root directory to sys.path so 'app' module can be imported in Vercel Serverless Functions
backend_dir = Path(__file__).parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.main import app

__all__ = ["app"]
