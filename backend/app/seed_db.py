"""
seed_db.py — load curated seed data into the database on first run.

Called by docker-compose.yml startup command:
    python -m app.seed_db

Idempotent: skips tables that already have rows.
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path

from sqlalchemy import func, select

from app.database import AsyncSessionLocal
from app.models import Commodity, PackagingMaterial

logger = logging.getLogger(__name__)

SEED_DIR = Path(__file__).parent / "seed"


async def seed_commodities(session) -> None:
    count = (await session.execute(select(func.count()).select_from(Commodity))).scalar_one()
    if count > 0:
        logger.info("Commodities table already has %d rows — skipping seed", count)
        return

    data = json.loads((SEED_DIR / "commodities.json").read_text())
    for item in data:
        session.add(Commodity(**item))
    await session.commit()
    logger.info("Seeded %d commodities", len(data))


async def seed_materials(session) -> None:
    count = (await session.execute(select(func.count()).select_from(PackagingMaterial))).scalar_one()
    if count > 0:
        logger.info("PackagingMaterials table already has %d rows — skipping seed", count)
        return

    data = json.loads((SEED_DIR / "packaging_materials.json").read_text())
    for item in data:
        session.add(PackagingMaterial(**item))
    await session.commit()
    logger.info("Seeded %d packaging materials", len(data))


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    async with AsyncSessionLocal() as session:
        await seed_commodities(session)
        await seed_materials(session)


if __name__ == "__main__":
    asyncio.run(main())
