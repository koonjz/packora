"""
GET /materials — reference lookup over the packaging materials table
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import PackagingMaterial
from app.schemas import PackagingMaterialOut

router = APIRouter(prefix="/materials", tags=["Materials"])


@router.get("", response_model=list[PackagingMaterialOut], summary="List packaging materials")
async def list_materials(
    q: str | None = Query(default=None, description="Search by name or use case"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> list[PackagingMaterialOut]:
    stmt = select(PackagingMaterial).order_by(PackagingMaterial.name)
    if q:
        stmt = stmt.where(PackagingMaterial.name.ilike(f"%{q}%"))
    stmt = stmt.limit(limit)
    result = await db.execute(stmt)
    return [PackagingMaterialOut.model_validate(row) for row in result.scalars().all()]


@router.get("/{material_id}", response_model=PackagingMaterialOut, summary="Get material by ID")
async def get_material(
    material_id: int,
    db: AsyncSession = Depends(get_db),
) -> PackagingMaterialOut:
    from fastapi import HTTPException

    row = await db.get(PackagingMaterial, material_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Material not found")
    return PackagingMaterialOut.model_validate(row)
