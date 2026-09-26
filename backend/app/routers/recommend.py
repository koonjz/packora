"""
POST /recommend — core recommendation endpoint
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cv_client import identify_commodity
from app.database import get_db
from app.explainer import build_reasoning_trace, build_templated_reason
from app.llm_client import generate_llm_explanation
from app.models import Commodity, CommodityPackagingMap, PackagingMaterial
from app.ranking_model import score_material
from app.rule_engine import (
    CommodityProps,
    MaterialProps,
    filter_materials,
)
from app.schemas import (
    CommodityOut,
    PackagingMaterialOut,
    RecommendRequest,
    RecommendResponse,
    RecommendationItem,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/recommend", tags=["Recommendations"])

MAX_RECOMMENDATIONS = 3


@router.post("", response_model=RecommendResponse, summary="Get packaging recommendations")
async def recommend(
    request: RecommendRequest,
    db: AsyncSession = Depends(get_db),
) -> RecommendResponse:
    """
    Core recommendation endpoint.

    Pipeline:
    1. (Optional) If commodity_image_b64 is provided and ENABLE_CV_FEATURE=true,
       attempt to identify the commodity via MobileNetV3 — override commodity_id
       if confident.
    2. Load commodity properties from the DB.
    3. Load all packaging materials from the DB.
    4. Apply rule engine → filter to valid materials.
    5. Score valid materials via ML ranker (or heuristic fallback).
    6. Build structured reasoning trace for each.
    7. (Optional) Call LLM for plain-language reason — fall back to template.
    8. Return top-N recommendations.
    """
    # ------------------------------------------------------------------
    # Step 1: Optional CV commodity identification
    # ------------------------------------------------------------------
    cv_identified_name: str | None = None
    if request.commodity_image_b64:
        cv_identified_name = await identify_commodity(request.commodity_image_b64)
        if cv_identified_name:
            logger.info("CV identified commodity as: %s", cv_identified_name)

    # ------------------------------------------------------------------
    # Step 2: Load commodity
    # ------------------------------------------------------------------
    commodity_row = await db.get(Commodity, request.commodity_id)
    if commodity_row is None:
        raise HTTPException(status_code=404, detail=f"Commodity {request.commodity_id} not found")

    commodity_props = CommodityProps(
        moisture_pct=commodity_row.moisture_pct,
        water_activity=commodity_row.water_activity,
        respiration_rate=commodity_row.respiration_rate,
        fat_content=commodity_row.fat_content,
        light_sensitivity=commodity_row.light_sensitivity,
        fragility=commodity_row.fragility,
    )

    # ------------------------------------------------------------------
    # Step 3: Load all packaging materials
    # ------------------------------------------------------------------
    result = await db.execute(select(PackagingMaterial))
    all_materials = result.scalars().all()

    if not all_materials:
        raise HTTPException(status_code=503, detail="Packaging materials table is empty — run seed_db first")

    material_props_list = [
        MaterialProps(
            material_id=m.id,
            name=m.name,
            wvtr=m.wvtr,
            otr=m.otr,
            cost_per_unit=m.cost_per_unit,
            biodegradability_score=m.biodegradability_score,
            light_blocking=m.light_blocking,
            crush_resistance=m.crush_resistance,
        )
        for m in all_materials
    ]

    # ------------------------------------------------------------------
    # Step 4: Apply rule engine
    # ------------------------------------------------------------------
    valid_pairs = filter_materials(
        commodity_props,
        material_props_list,
        request.target_shelf_life_days,
        request.storage_condition.value,
        request.transport_condition.value,
    )

    total_evaluated = len(all_materials)
    total_passing = len(valid_pairs)

    # ------------------------------------------------------------------
    # Step 5 & 6: Score + build reasoning trace
    # ------------------------------------------------------------------
    scored: list[tuple[float, MaterialProps, list, dict]] = []
    for material_props, rule_results in valid_pairs:
        score_dict = score_material(
            commodity_props,
            material_props,
            request.target_shelf_life_days,
            weight_cost=request.weight_cost,
            weight_sustainability=request.weight_sustainability,
            weight_shelf_life=request.weight_shelf_life,
        )
        scored.append((score_dict["composite_score"], material_props, rule_results, score_dict))

    # Sort by composite score descending
    scored.sort(key=lambda t: -t[0])
    top_n = scored[:MAX_RECOMMENDATIONS]

    # ------------------------------------------------------------------
    # Step 7 & 8: Build recommendation items with explanation
    # ------------------------------------------------------------------
    recommendations: list[RecommendationItem] = []
    llm_warning: str | None = None

    for rank, (composite_score, material_props, rule_results, score_dict) in enumerate(top_n, start=1):
        # Try LLM explanation first
        rule_summaries = [r.reason for r in rule_results if r.passed]
        llm_reason = await generate_llm_explanation(
            commodity_name=commodity_row.name,
            material_name=material_props.name,
            rule_summaries=rule_summaries,
            score_breakdown=score_dict,
        )

        if llm_reason:
            plain_reason = llm_reason
            explanation_source = "llm"
        else:
            plain_reason = build_templated_reason(
                commodity_name=commodity_row.name,
                material_name=material_props.name,
                rule_results=rule_results,
                score_breakdown=score_dict,
            )
            explanation_source = "template"
            if rank == 1:  # only warn once
                llm_warning = "LLM explanation unavailable — using templated explanation"

        reasoning_trace = build_reasoning_trace(
            rule_results=rule_results,
            score_breakdown=score_dict,
            plain_language_reason=plain_reason,
            explanation_source=explanation_source,
        )

        # Fetch full ORM object for the response schema
        material_row = await db.get(PackagingMaterial, material_props.material_id)

        recommendations.append(
            RecommendationItem(
                rank=rank,
                material=PackagingMaterialOut.model_validate(material_row),
                reasoning_trace=reasoning_trace,
                plain_language_reason=plain_reason,
            )
        )

    return RecommendResponse(
        commodity=CommodityOut.model_validate(commodity_row),
        request=request,
        recommendations=recommendations,
        total_materials_evaluated=total_evaluated,
        total_materials_passing_rules=total_passing,
        warning=llm_warning,
    )
