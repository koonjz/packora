"""
Pydantic schemas for Packora API request and response bodies.

Design rules:
  - Request schemas live as *Request or *Input.
  - Response schemas live as *Response or *Out.
  - The RecommendationResponse always includes a structured reasoning_trace
    (rules_applied, score_breakdown) — the plain_language_reason is generated
    FROM that trace, never a substitute for it (per PROJECT_BRIEF.md §4).
"""
from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared / reference types
# ---------------------------------------------------------------------------


class StorageCondition(str, Enum):
    ambient = "ambient"
    refrigerated = "refrigerated"
    frozen = "frozen"


class TransportCondition(str, Enum):
    standard = "standard"
    cold_chain = "cold_chain"
    controlled_atmosphere = "controlled_atmosphere"


# ---------------------------------------------------------------------------
# Commodity schemas
# ---------------------------------------------------------------------------


class CommodityOut(BaseModel):
    id: int
    name: str
    moisture_pct: float
    water_activity: float
    respiration_rate: Optional[float] = None
    fat_content: float
    light_sensitivity: bool
    fragility: int
    category: Optional[str] = None
    description: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Packaging material schemas
# ---------------------------------------------------------------------------


class PackagingMaterialOut(BaseModel):
    id: int
    name: str
    wvtr: float
    otr: float
    cost_per_unit: float
    biodegradability_score: int
    typical_use_case: Optional[str] = None
    light_blocking: bool
    crush_resistance: int
    description: Optional[str] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Recommendation request
# ---------------------------------------------------------------------------


class RecommendRequest(BaseModel):
    commodity_id: int = Field(..., description="ID from the commodities table")
    target_shelf_life_days: int = Field(..., ge=1, description="Desired shelf life in days")
    storage_condition: StorageCondition = Field(default=StorageCondition.ambient)
    transport_condition: TransportCondition = Field(default=TransportCondition.standard)

    # User-adjustable weights (must sum to 1.0 — validated in the router)
    weight_cost: float = Field(default=0.33, ge=0.0, le=1.0)
    weight_sustainability: float = Field(default=0.33, ge=0.0, le=1.0)
    weight_shelf_life: float = Field(default=0.34, ge=0.0, le=1.0)

    # Optional CV: base64-encoded commodity photo (only used when ENABLE_CV_FEATURE=true)
    commodity_image_b64: Optional[str] = Field(
        default=None, description="Base64-encoded JPEG/PNG for commodity identification (optional)"
    )


# ---------------------------------------------------------------------------
# Reasoning trace — structured output that plain-language reason is built from
# ---------------------------------------------------------------------------


class RuleResult(BaseModel):
    rule_name: str
    passed: bool
    reason: str  # technical description, e.g. "WVTR 2.1 ≤ threshold 5.0 g/m²/day ✓"


class ScoreBreakdown(BaseModel):
    base_ml_score: float = Field(..., description="Raw ML model score (0–1)")
    cost_score: float = Field(..., description="Normalized cost component (0–1, higher = cheaper)")
    sustainability_score: float = Field(..., description="Biodegradability score component (0–1)")
    shelf_life_score: float = Field(..., description="Estimated shelf-life extension component (0–1)")
    composite_score: float = Field(..., description="Weighted composite fit score (0–1)")


class ReasoningTrace(BaseModel):
    rules_applied: list[RuleResult]
    rules_passed: int
    rules_failed: int
    score_breakdown: ScoreBreakdown
    explanation_source: str = Field(
        ..., description="'llm' | 'template' — indicates whether the plain-language reason came from LLM or fallback"
    )


# ---------------------------------------------------------------------------
# Single recommendation item
# ---------------------------------------------------------------------------


class RecommendationItem(BaseModel):
    rank: int
    material: PackagingMaterialOut
    reasoning_trace: ReasoningTrace
    plain_language_reason: str  # generated FROM reasoning_trace, not a substitute


# ---------------------------------------------------------------------------
# Full recommendation response
# ---------------------------------------------------------------------------


class RecommendResponse(BaseModel):
    commodity: CommodityOut
    request: RecommendRequest
    recommendations: list[RecommendationItem]
    total_materials_evaluated: int
    total_materials_passing_rules: int
    warning: Optional[str] = Field(
        default=None,
        description="Non-fatal warning (e.g. 'LLM unavailable — using templated explanation')",
    )
