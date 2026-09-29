"""
Packora Ranking Model — Tier 2: ML scoring within valid option set
==================================================================

PURPOSE
-------
The rule engine (rule_engine.py) eliminates packaging materials that
violate hard physical constraints. This module ranks the *surviving* materials
by a composite fit score, using a trained scikit-learn model.

DESIGN CONTRACT (per PROJECT_BRIEF.md §2.3 and §4):
  - Tree-based models (RandomForest / GradientBoosting) are intentional —
    not a placeholder for "something better later." Feature importances give us
    the explainability story for judges.
  - The model is trained on ~100–150 curated commodity–material pairs from
    the commodity_packaging_map table.
  - This module must be independently callable without rule_engine.py or the DB.
  - The composite score also incorporates user-adjustable weights (cost,
    sustainability, shelf-life extension).

MODEL LIFECYCLE
---------------
1. train_and_save()  — run once on the full commodity_packaging_map data.
   Saves model to MODEL_PATH using joblib.
2. load_model()      — called at app startup; cached in memory.
3. score_material()  — called per surviving material during a recommendation.

To retrain after adding new curated data:
    python -m app.ranking_model  (calls train_and_save from __main__)
"""
from __future__ import annotations

import logging
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor

from app.rule_engine import CommodityProps, MaterialProps

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).parent / "models" / "packora_ranker.joblib"
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

# Feature names in the exact order used during training — must not change
# without retraining. Logged at startup for traceability.
FEATURE_NAMES: list[str] = [
    "moisture_pct",
    "water_activity",
    "fat_content",
    "fragility",
    "light_sensitivity",
    "wvtr",
    "otr",
    "biodegradability_score",
    "cost_per_unit",
    "crush_resistance",
    "light_blocking",
    "target_shelf_life_days",
]


# ---------------------------------------------------------------------------
# Feature extraction
# ---------------------------------------------------------------------------


def build_feature_vector(
    commodity: CommodityProps,
    material: MaterialProps,
    target_shelf_life_days: int,
) -> np.ndarray:
    """
    Build a 1-D feature vector for the (commodity, material, conditions) triple.
    Order must exactly match FEATURE_NAMES.
    """
    return np.array(
        [
            commodity.moisture_pct,
            commodity.water_activity,
            commodity.fat_content,
            commodity.fragility,
            float(commodity.light_sensitivity),
            material.wvtr,
            material.otr,
            material.biodegradability_score,
            material.cost_per_unit,
            material.crush_resistance,
            float(material.light_blocking),
            float(target_shelf_life_days),
        ],
        dtype=float,
    )


# ---------------------------------------------------------------------------
# Model persistence
# ---------------------------------------------------------------------------

_cached_model: RandomForestRegressor | None = None


def load_model() -> RandomForestRegressor | None:
    """
    Load the trained model from disk into memory. Returns None if no model
    file exists yet (first-time run before training).

    Called once at app startup; result is cached in module-level _cached_model.
    """
    global _cached_model
    if _cached_model is not None:
        return _cached_model
    if not MODEL_PATH.exists():
        logger.warning(
            "Ranking model not found at %s. "
            "Falling back to heuristic scoring. "
            "Run `python -m app.ranking_model` to train.",
            MODEL_PATH,
        )
        return None
    _cached_model = joblib.load(MODEL_PATH)
    logger.info("Ranking model loaded from %s (features: %s)", MODEL_PATH, FEATURE_NAMES)
    return _cached_model


def train_and_save(training_data: list[dict]) -> None:
    """
    Train and persist the ranking model.

    training_data: list of dicts, each with keys matching FEATURE_NAMES
                   plus 'suitability_score' (the target label, 0–1).

    Called from the CLI entry point or a management script after curating new data.
    """
    import pandas as pd

    df = pd.DataFrame(training_data)
    X = df[FEATURE_NAMES].to_numpy()
    y = df["suitability_score"].to_numpy()

    model = RandomForestRegressor(
        n_estimators=200,
        max_depth=8,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X, y)

    joblib.dump(model, MODEL_PATH)
    logger.info("Model trained and saved to %s", MODEL_PATH)

    # Log feature importances (the explainability story)
    importances = dict(zip(FEATURE_NAMES, model.feature_importances_))
    sorted_importances = sorted(importances.items(), key=lambda x: -x[1])
    logger.info("Feature importances: %s", sorted_importances)

    global _cached_model
    _cached_model = model


# ---------------------------------------------------------------------------
# Heuristic fallback (used when no trained model is available)
# ---------------------------------------------------------------------------


def _heuristic_base_score(
    commodity: CommodityProps,
    material: MaterialProps,
    target_shelf_life_days: int,
) -> float:
    """
    Simple domain-knowledge heuristic score (0–1).
    Used as fallback when the ML model hasn't been trained yet.
    Lower WVTR and OTR relative to commodity needs = higher score.
    This is intentionally simple and not a substitute for a trained model.
    """
    # Normalise WVTR: score = 1 - (wvtr / 100), clamped to [0, 1]
    wvtr_score = max(0.0, 1.0 - (material.wvtr / 100.0))
    # Normalise OTR: score = 1 - (otr / 500), clamped to [0, 1]
    otr_score = max(0.0, 1.0 - (material.otr / 500.0))
    return (wvtr_score + otr_score) / 2.0


# ---------------------------------------------------------------------------
# Composite score calculation
# ---------------------------------------------------------------------------


def score_material(
    commodity: CommodityProps,
    material: MaterialProps,
    target_shelf_life_days: int,
    weight_cost: float = 0.33,
    weight_sustainability: float = 0.33,
    weight_shelf_life: float = 0.34,
) -> dict[str, float]:
    """
    Compute the composite fit score for a (commodity, material) pair.

    Returns a dict with individual score components and the composite score,
    so the explainer can surface them in the reasoning trace.

    Component scores are all normalised to [0, 1] where 1 is best.
    """
    model = load_model()

    # --- ML base score (or heuristic fallback) ---
    if model is not None:
        feature_vector = build_feature_vector(commodity, material, target_shelf_life_days)
        base_ml_score = float(model.predict(feature_vector.reshape(1, -1))[0])
        base_ml_score = float(np.clip(base_ml_score, 0.0, 1.0))
    else:
        base_ml_score = _heuristic_base_score(commodity, material, target_shelf_life_days)

    # --- Cost score: lower cost = higher score ---
    # Normalise against a rough ₹100 ceiling; clamp to [0, 1]
    cost_score = float(np.clip(1.0 - (material.cost_per_unit / 100.0), 0.0, 1.0))

    # --- Sustainability score: higher biodegradability = higher score ---
    sustainability_score = (material.biodegradability_score - 1) / 4.0  # scale 1–5 → 0–1

    # --- Shelf-life score: proxy from the base ML score (barrier quality) ---
    shelf_life_score = base_ml_score  # refined once we have real outcome data

    # --- Composite (user-weighted) ---
    composite = (
        weight_cost * cost_score
        + weight_sustainability * sustainability_score
        + weight_shelf_life * shelf_life_score
    )
    composite = float(np.clip(composite, 0.0, 1.0))

    return {
        "base_ml_score": round(base_ml_score, 4),
        "cost_score": round(cost_score, 4),
        "sustainability_score": round(sustainability_score, 4),
        "shelf_life_score": round(shelf_life_score, 4),
        "composite_score": round(composite, 4),
    }


def generate_training_data_from_seed() -> list[dict]:
    """
    Generate domain-based synthetic training data from seed files if DB mapping is empty.
    Creates 400 (commodity, material) training pairs scored with domain food-science heuristics.
    """
    import json
    from pathlib import Path

    seed_dir = Path(__file__).parent / "seed"
    commodities_file = seed_dir / "commodities.json"
    materials_file = seed_dir / "packaging_materials.json"

    if not commodities_file.exists() or not materials_file.exists():
        return []

    commodities = json.loads(commodities_file.read_text())
    materials = json.loads(materials_file.read_text())

    records = []
    for c in commodities:
        for m in materials:
            # Domain heuristic score calculation (0.0 to 1.0)
            score = 0.5

            # Moisture / WVTR compatibility
            if c["water_activity"] > 0.6 or c["moisture_pct"] > 15:
                score += 0.25 if m["wvtr"] <= 10.0 else -0.20
            else:
                score += 0.10 if m["wvtr"] <= 30.0 else 0.0

            # Light sensitivity compatibility
            if c["light_sensitivity"]:
                score += 0.20 if m["light_blocking"] else -0.25

            # Oxygen sensitivity & Respiration compatibility
            if c.get("respiration_rate") and c["respiration_rate"] > 10:
                # Fresh produce needs oxygen exchange
                score += 0.25 if m["otr"] >= 1000.0 else -0.30
            elif c["fat_content"] > 15.0:
                # Fat-rich foods need low OTR to prevent rancidity
                score += 0.25 if m["otr"] <= 100.0 else -0.25

            # Fragility vs Crush Resistance
            if c["fragility"] >= 3:
                score += 0.15 if m["crush_resistance"] >= 3 else -0.15

            # Clamp score to [0.1, 0.98]
            suitability_score = round(max(0.1, min(0.98, score)), 2)

            for target_shelf_life in [30, 90, 180]:
                records.append(
                    {
                        "moisture_pct": float(c["moisture_pct"]),
                        "water_activity": float(c["water_activity"]),
                        "fat_content": float(c["fat_content"]),
                        "fragility": int(c["fragility"]),
                        "light_sensitivity": float(c["light_sensitivity"]),
                        "wvtr": float(m["wvtr"]),
                        "otr": float(m["otr"]),
                        "biodegradability_score": float(m["biodegradability_score"]),
                        "cost_per_unit": float(m["cost_per_unit"]),
                        "crush_resistance": float(m["crush_resistance"]),
                        "light_blocking": float(m["light_blocking"]),
                        "target_shelf_life_days": float(target_shelf_life),
                        "suitability_score": suitability_score,
                    }
                )

    return records


# ---------------------------------------------------------------------------
# CLI entry point — retrain the model
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    """
    Usage: python -m app.ranking_model
    Loads training data from the DB or seed data and retrains the model.
    """
    import asyncio
    import os

    records: list[dict] = []

    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            from sqlalchemy import select
            from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

            async def _fetch_training_data() -> list[dict]:
                from app.models import Commodity, CommodityPackagingMap, PackagingMaterial

                engine = create_async_engine(db_url)
                session_factory = async_sessionmaker(engine, class_=AsyncSession)
                async with session_factory() as session:
                    result = await session.execute(
                        select(CommodityPackagingMap, Commodity, PackagingMaterial)
                        .join(Commodity, CommodityPackagingMap.commodity_id == Commodity.id)
                        .join(PackagingMaterial, CommodityPackagingMap.material_id == PackagingMaterial.id)
                    )
                    rows = result.all()

                db_records = []
                for mapping, commodity, material in rows:
                    db_records.append(
                        {
                            "moisture_pct": commodity.moisture_pct,
                            "water_activity": commodity.water_activity,
                            "fat_content": commodity.fat_content,
                            "fragility": commodity.fragility,
                            "light_sensitivity": float(commodity.light_sensitivity),
                            "wvtr": material.wvtr,
                            "otr": material.otr,
                            "biodegradability_score": material.biodegradability_score,
                            "cost_per_unit": material.cost_per_unit,
                            "crush_resistance": material.crush_resistance,
                            "light_blocking": float(material.light_blocking),
                            "target_shelf_life_days": 90.0,
                            "suitability_score": mapping.suitability_score,
                        }
                    )
                return db_records

            records = asyncio.run(_fetch_training_data())
        except Exception as err:
            logger.warning("Could not fetch DB mappings (%s). Using seed data.", err)

    if not records:
        print("Using domain seed dataset for model training …")
        records = generate_training_data_from_seed()

    print(f"Training on {len(records)} records …")
    train_and_save(records)
    print(f"Model saved to {MODEL_PATH}")

