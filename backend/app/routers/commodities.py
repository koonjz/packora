"""
GET /commodities — search and autocomplete over the commodities table
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Commodity
from app.schemas import CommodityOut

router = APIRouter(prefix="/commodities", tags=["Commodities"])


@router.get("", response_model=list[CommodityOut], summary="Search commodities")
async def list_commodities(
    q: str | None = Query(default=None, description="Search term (name, category)"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[CommodityOut]:
    """
    Return a list of commodities, optionally filtered by a search term.
    Used for the commodity search / autocomplete in the frontend.
    """
    stmt = select(Commodity).order_by(Commodity.name)
    if q:
        stmt = stmt.where(
            Commodity.name.ilike(f"%{q}%")
        )
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return [CommodityOut.model_validate(row) for row in result.scalars().all()]


@router.get("/{commodity_id}", response_model=CommodityOut, summary="Get commodity by ID")
async def get_commodity(
    commodity_id: int,
    db: AsyncSession = Depends(get_db),
) -> CommodityOut:
    from fastapi import HTTPException

    row = await db.get(Commodity, commodity_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Commodity not found")
    return CommodityOut.model_validate(row)
