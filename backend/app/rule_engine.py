"""
Packora Rule Engine — Tier 1: hard-constraint filtering
========================================================

PURPOSE
-------
This module is the reliability foundation of the recommendation system.
It filters the full packaging materials list down to only those that
satisfy *hard physical constraints* for a given commodity + conditions.

DESIGN CONTRACT (per PROJECT_BRIEF.md §2.1 and §4):
  - This module must be callable and testable with ZERO database, ML, or
    network dependency.
  - Every rule is a named function that returns (passed: bool, reason: str).
  - The reason string must be specific and quantitative — not "failed" but
    "WVTR 12.3 > threshold 5.0 g/m²/day — material is too moisture-permeable
    for water activity 0.93 over 60-day shelf life."
  - Do NOT collapse rules into a single model call. Each rule stays separate
    so judges (and the next developer) can follow the reasoning.

ADDING A NEW RULE
-----------------
1. Write a function matching the RuleCheckFn signature below.
2. Register it in RULE_REGISTRY at the bottom of this file.
3. Add a test in tests/test_rule_engine.py.
4. Commit with a message like "add OTR rule for high-fat commodities".
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


# ---------------------------------------------------------------------------
# Data classes (intentionally plain — no SQLAlchemy dependency here)
# ---------------------------------------------------------------------------


@dataclass
class CommodityProps:
    """
    Snapshot of a commodity's physical properties, extracted from the DB
    before calling the rule engine. Keeping this as a plain dataclass means
    the rule engine has zero DB dependency and can be unit-tested trivially.
    """

    moisture_pct: float
    water_activity: float  # 0.0 – 1.0
    respiration_rate: float | None  # mL CO₂/kg·h; None for non-respiring products
    fat_content: float  # %
    light_sensitivity: bool
    fragility: int  # 1 (robust) – 5 (very fragile)


@dataclass
class MaterialProps:
    """
    Snapshot of a packaging material's barrier and structural properties.
    Same reasoning: pure data, no ORM dependency, easily unit-testable.
    """

    material_id: int
    name: str
    wvtr: float  # g/m²/day — lower = better moisture barrier
    otr: float  # cc/m²/day — lower = better oxygen barrier
    cost_per_unit: float  # ₹
    biodegradability_score: int  # 1–5
    light_blocking: bool
    crush_resistance: int  # 1–5


@dataclass
class RuleResult:
    rule_name: str
    passed: bool
    reason: str  # always quantitative — include the actual vs. threshold values


# ---------------------------------------------------------------------------
# Rule-check function type
# ---------------------------------------------------------------------------

RuleCheckFn = Callable[
    [CommodityProps, MaterialProps, int, str, str], RuleResult
]
"""
Signature: (commodity, material, target_shelf_life_days, storage_condition, transport_condition)
           → RuleResult
"""


# ---------------------------------------------------------------------------
# Rule implementations
# ---------------------------------------------------------------------------


def rule_wvtr_moisture_barrier(
    commodity: CommodityProps,
    material: MaterialProps,
    target_shelf_life_days: int,
    storage_condition: str,
    transport_condition: str,
) -> RuleResult:
    """
    Rule: Water Vapor Transmission Rate (WVTR) barrier check.

    High-moisture or high-water-activity foods need low WVTR packaging.
    WVTR threshold tightens with longer shelf life or refrigerated/frozen storage.

    Sources: FSSAI packaging guidelines; published equilibrium moisture
    content studies for common Indian commodities.
    """
    rule_name = "WVTR Moisture Barrier"

    # Determine the maximum acceptable WVTR for this commodity + shelf life
    if commodity.water_activity >= 0.90:
        # High aw (e.g., fresh paneer, soft cheese, cooked rice) — very low WVTR required
        base_threshold = 5.0  # g/m²/day
    elif commodity.water_activity >= 0.75:
        # Moderate aw (e.g., jaggery, soft dried fruit)
        base_threshold = 15.0
    elif commodity.moisture_pct >= 12.0:
        # Low aw but non-trivial moisture (e.g., whole spices, dried legumes)
        base_threshold = 30.0
    else:
        # Dry products (e.g., turmeric powder, roasted snacks)
        base_threshold = 60.0

    # Scale threshold down for longer shelf lives (stricter = lower WVTR limit)
    if target_shelf_life_days > 180:
        threshold = base_threshold * 0.5
    elif target_shelf_life_days > 90:
        threshold = base_threshold * 0.7
    elif target_shelf_life_days > 30:
        threshold = base_threshold * 0.85
    else:
        threshold = base_threshold

    passed = material.wvtr <= threshold
    direction = "≤" if passed else ">"
    verdict = "✓ passes" if passed else "✗ FAILS — material too moisture-permeable"

    reason = (
        f"WVTR {material.wvtr:.1f} g/m²/day {direction} threshold {threshold:.1f} g/m²/day "
        f"(aw={commodity.water_activity}, shelf_life={target_shelf_life_days}d) — {verdict}"
    )
    return RuleResult(rule_name=rule_name, passed=passed, reason=reason)


def rule_otr_oxygen_barrier(
    commodity: CommodityProps,
    material: MaterialProps,
    target_shelf_life_days: int,
    storage_condition: str,
    transport_condition: str,
) -> RuleResult:
    """
    Rule: Oxygen Transmission Rate (OTR) barrier check.

    High-fat foods oxidize and go rancid; fresh produce needs some O₂ exchange;
    dry/low-fat products are more tolerant. This rule sets a hard ceiling on OTR
    for products where oxidation is a spoilage pathway.

    Sources: BIS IS:2798 (flexible packaging), FSSAI guidelines for fats & oils.
    """
    rule_name = "OTR Oxygen Barrier"

    if commodity.fat_content >= 15.0:
        # High-fat foods: oils, ghee, nuts, fried snacks — strict OTR required
        threshold = 10.0  # cc/m²/day
    elif commodity.fat_content >= 5.0:
        # Moderate fat: whole milk powder, biscuits
        threshold = 40.0
    else:
        # Low fat: most grains, spices, fresh produce
        threshold = 200.0

    # Extend threshold for refrigerated / frozen (slower oxidation kinetics)
    if storage_condition in ("refrigerated", "frozen"):
        threshold *= 2.0

    passed = material.otr <= threshold
    direction = "≤" if passed else ">"
    verdict = "✓ passes" if passed else "✗ FAILS — insufficient oxygen barrier for fat content"

    reason = (
        f"OTR {material.otr:.1f} cc/m²/day {direction} threshold {threshold:.1f} cc/m²/day "
        f"(fat={commodity.fat_content}%, storage={storage_condition}) — {verdict}"
    )
    return RuleResult(rule_name=rule_name, passed=passed, reason=reason)


def rule_light_blocking(
    commodity: CommodityProps,
    material: MaterialProps,
    target_shelf_life_days: int,
    storage_condition: str,
    transport_condition: str,
) -> RuleResult:
    """
    Rule: Light-blocking requirement.

    Light-sensitive foods (oils, vitamin-fortified products, coloured spices like
    saffron/turmeric) must be packaged in a light-blocking material.
    Non-light-sensitive foods pass this rule regardless.

    Sources: FSSAI Food Safety and Standards (Packaging and Labelling) Regulations.
    """
    rule_name = "Light Blocking"

    if not commodity.light_sensitivity:
        return RuleResult(
            rule_name=rule_name,
            passed=True,
            reason="Product is not light-sensitive — no light-blocking requirement ✓",
        )

    passed = material.light_blocking
    verdict = "✓ material blocks light" if passed else "✗ FAILS — light-sensitive product needs opaque packaging"

    reason = (
        f"Product is light-sensitive; material light_blocking={material.light_blocking} — {verdict}"
    )
    return RuleResult(rule_name=rule_name, passed=passed, reason=reason)


def rule_fragility_crush_resistance(
    commodity: CommodityProps,
    material: MaterialProps,
    target_shelf_life_days: int,
    storage_condition: str,
    transport_condition: str,
) -> RuleResult:
    """
    Rule: Crush resistance vs. product fragility.

    Very fragile products (biscuits, wafers, dried noodles) need rigid or
    semi-rigid packaging with adequate crush resistance. Flexible pouches alone
    are not suitable for fragility ≥ 4.

    The rule is relaxed for cold-chain transport (less vibration, controlled
    stacking) and tightened for standard truck transport.
    """
    rule_name = "Crush Resistance"

    required_resistance = commodity.fragility  # fragility 1→5 maps to minimum crush_resistance needed

    if transport_condition == "cold_chain":
        # Cold-chain vehicles are better controlled — relax by 1 level
        required_resistance = max(1, required_resistance - 1)

    passed = material.crush_resistance >= required_resistance
    direction = "≥" if passed else "<"
    verdict = "✓ adequate structural protection" if passed else "✗ FAILS — insufficient crush resistance for this product's fragility"

    reason = (
        f"Crush resistance {material.crush_resistance} {direction} required {required_resistance} "
        f"(fragility={commodity.fragility}, transport={transport_condition}) — {verdict}"
    )
    return RuleResult(rule_name=rule_name, passed=passed, reason=reason)


def rule_respiration_rate_barrier(
    commodity: CommodityProps,
    material: MaterialProps,
    target_shelf_life_days: int,
    storage_condition: str,
    transport_condition: str,
) -> RuleResult:
    """
    Rule: Respiration rate check for fresh produce.

    High-respiration commodities (fresh leafy vegetables, sprouts) require
    modified-atmosphere compatible packaging with a minimum OTR to allow
    CO₂ out and O₂ in. Packaging that is too oxygen-tight would create
    anaerobic conditions and accelerate spoilage.

    Only applied when respiration_rate is set (not None).

    Sources: FSSAI Technical Guidelines on Modified Atmosphere Packaging (MAP).
    """
    rule_name = "Respiration Rate / MAP Compatibility"

    if commodity.respiration_rate is None:
        return RuleResult(
            rule_name=rule_name,
            passed=True,
            reason="Non-respiring commodity — MAP rule not applicable ✓",
        )

    # High-respiration produce (mL CO₂/kg·h > 20) needs some O₂ permeability
    # to prevent anaerobic fermentation
    if commodity.respiration_rate > 20.0:
        minimum_otr_required = 500.0  # cc/m²/day
        passed = material.otr >= minimum_otr_required
        direction = "≥" if passed else "<"
        verdict = (
            "✓ sufficient O₂ exchange for high-respiration produce"
            if passed
            else "✗ FAILS — OTR too low; anaerobic conditions will develop"
        )
        reason = (
            f"Respiration rate {commodity.respiration_rate:.0f} mL CO₂/kg·h; "
            f"OTR {material.otr:.0f} {direction} minimum {minimum_otr_required:.0f} cc/m²/day — {verdict}"
        )
    else:
        # Low-respiration produce (≤ 20 mL CO₂/kg·h) — standard OTR rule applies
        return RuleResult(
            rule_name=rule_name,
            passed=True,
            reason=(
                f"Low respiration rate {commodity.respiration_rate:.0f} mL CO₂/kg·h "
                f"— standard OTR constraint applies; MAP rule not triggered ✓"
            ),
        )

    return RuleResult(rule_name=rule_name, passed=passed, reason=reason)


# ---------------------------------------------------------------------------
# Rule registry — the ordered list of rules applied to every (commodity, material) pair
# ---------------------------------------------------------------------------

RULE_REGISTRY: list[RuleCheckFn] = [
    rule_wvtr_moisture_barrier,
    rule_otr_oxygen_barrier,
    rule_light_blocking,
    rule_fragility_crush_resistance,
    rule_respiration_rate_barrier,
]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def apply_rules(
    commodity: CommodityProps,
    material: MaterialProps,
    target_shelf_life_days: int,
    storage_condition: str,
    transport_condition: str,
) -> list[RuleResult]:
    """
    Apply all rules in RULE_REGISTRY to a single (commodity, material) pair.

    Returns the full list of RuleResult objects — callers decide whether to
    discard the material based on any failed rule.

    This function is intentionally not async and has no DB/ML/network dependency.
    It can be called from a script, a test, or the Swagger UI with a simple dict.
    """
    return [
        rule(commodity, material, target_shelf_life_days, storage_condition, transport_condition)
        for rule in RULE_REGISTRY
    ]


def filter_materials(
    commodity: CommodityProps,
    materials: list[MaterialProps],
    target_shelf_life_days: int,
    storage_condition: str,
    transport_condition: str,
) -> list[tuple[MaterialProps, list[RuleResult]]]:
    """
    Apply all rules to every material in `materials` and return only those
    where every rule passed, together with their full rule result lists.

    Returns: list of (material, rule_results) tuples, sorted by material name.
    """
    passing = []
    for material in materials:
        results = apply_rules(
            commodity, material, target_shelf_life_days, storage_condition, transport_condition
        )
        if all(r.passed for r in results):
            passing.append((material, results))
    return sorted(passing, key=lambda t: t[0].name)
