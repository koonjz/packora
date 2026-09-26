"""
SQLAlchemy ORM models for Packora.

Three core tables (per PROJECT_BRIEF.md §3):
  - Commodity           — food commodities and their physical properties
  - PackagingMaterial   — packaging materials and their barrier properties
  - CommodityPackagingMap — curated suitability scores linking the two

Do NOT add new columns without updating the corresponding Alembic migration.
"""
from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database import Base


class Commodity(Base):
    """A food commodity and its physical / chemical properties."""

    __tablename__ = "commodities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)

    # Physical properties used by the rule engine
    moisture_pct = Column(Float, nullable=False, comment="Moisture content (%)")
    water_activity = Column(Float, nullable=False, comment="Water activity (aw, 0–1)")
    respiration_rate = Column(
        Float, nullable=True, comment="Respiration rate (mL CO₂/kg·h) — relevant for fresh produce"
    )
    fat_content = Column(Float, nullable=False, comment="Fat content (%)")
    light_sensitivity = Column(
        Boolean, nullable=False, default=False, comment="True if product degrades under light"
    )
    fragility = Column(
        Integer,
        nullable=False,
        default=1,
        comment="Fragility score 1 (robust) to 5 (extremely fragile)",
    )
    # Optional metadata
    category = Column(String(100), nullable=True, comment="e.g. Dairy, Spice, Grain, Fresh Produce")
    description = Column(Text, nullable=True)

    mappings = relationship("CommodityPackagingMap", back_populates="commodity")


class PackagingMaterial(Base):
    """A packaging material and its barrier / cost / sustainability properties."""

    __tablename__ = "packaging_materials"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, unique=True, index=True)

    # Barrier properties (key inputs to the rule engine)
    wvtr = Column(
        Float,
        nullable=False,
        comment="Water Vapor Transmission Rate (g/m²/day) — lower = better moisture barrier",
    )
    otr = Column(
        Float,
        nullable=False,
        comment="Oxygen Transmission Rate (cc/m²/day) — lower = better oxygen barrier",
    )

    # Cost & sustainability
    cost_per_unit = Column(Float, nullable=False, comment="Approximate cost per unit (₹)")
    biodegradability_score = Column(
        Integer,
        nullable=False,
        default=3,
        comment="Biodegradability 1 (non-biodegradable) to 5 (fully compostable)",
    )

    # Descriptive
    typical_use_case = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    light_blocking = Column(
        Boolean, nullable=False, default=False, comment="True if material blocks light (opaque)"
    )
    crush_resistance = Column(
        Integer,
        nullable=False,
        default=3,
        comment="Crush-resistance score 1–5; used to match fragile commodities",
    )

    mappings = relationship("CommodityPackagingMap", back_populates="material")


class CommodityPackagingMap(Base):
    """
    Curated suitability data for a (commodity, material) pair.

    This table is the training dataset for the ML ranking layer.
    Each row represents expert knowledge (from FSSAI/BIS/food-science literature)
    about how well a particular material works for a particular commodity.
    """

    __tablename__ = "commodity_packaging_map"
    __table_args__ = (
        UniqueConstraint("commodity_id", "material_id", name="uq_commodity_material"),
    )

    id = Column(Integer, primary_key=True, index=True)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False, index=True)
    material_id = Column(Integer, ForeignKey("packaging_materials.id"), nullable=False, index=True)

    # Ground-truth label used to train the ML ranker
    suitability_score = Column(
        Float,
        nullable=False,
        comment="Expert-assigned suitability score 0.0–1.0 (1.0 = ideal match)",
    )

    # Optional curated notes (shown in the explanation output)
    notes = Column(Text, nullable=True, comment="Source citation or curation note")

    commodity = relationship("Commodity", back_populates="mappings")
    material = relationship("PackagingMaterial", back_populates="mappings")
