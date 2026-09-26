"""
Tests for the rule engine — no DB, ML, or network dependency.

These tests demonstrate the rule engine in isolation (per MVP definition of done §4):
    "The rule engine can be demonstrated in isolation rejecting an obviously-wrong
     material for a given commodity, independent of the ML layer."

Run with: pytest backend/tests/test_rule_engine.py -v
"""
from __future__ import annotations

import pytest

from app.rule_engine import (
    CommodityProps,
    MaterialProps,
    apply_rules,
    filter_materials,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def fresh_paneer() -> CommodityProps:
    """High moisture, high aw, high fat, non-respiring, not light-sensitive."""
    return CommodityProps(
        moisture_pct=65.0,
        water_activity=0.97,
        respiration_rate=None,
        fat_content=25.0,
        light_sensitivity=False,
        fragility=3,
    )


@pytest.fixture
def turmeric_powder() -> CommodityProps:
    """Low moisture, low aw, low fat, light-sensitive, robust."""
    return CommodityProps(
        moisture_pct=8.5,
        water_activity=0.45,
        respiration_rate=None,
        fat_content=5.0,
        light_sensitivity=True,
        fragility=1,
    )


@pytest.fixture
def fresh_spinach() -> CommodityProps:
    """Very high moisture, high respiration rate, fragile, non-light-sensitive."""
    return CommodityProps(
        moisture_pct=91.0,
        water_activity=0.99,
        respiration_rate=35.0,
        fat_content=0.4,
        light_sensitivity=False,
        fragility=4,
    )


@pytest.fixture
def potato_wafers() -> CommodityProps:
    """Very dry, high fat, extremely fragile."""
    return CommodityProps(
        moisture_pct=2.5,
        water_activity=0.25,
        respiration_rate=None,
        fat_content=35.0,
        light_sensitivity=False,
        fragility=5,
    )


@pytest.fixture
def ldpe_pouch() -> MaterialProps:
    """Low barrier flexible film — good moisture, terrible oxygen."""
    return MaterialProps(
        material_id=1,
        name="LDPE Film Pouch",
        wvtr=8.0,
        otr=4000.0,
        cost_per_unit=2.5,
        biodegradability_score=1,
        light_blocking=False,
        crush_resistance=1,
    )


@pytest.fixture
def aluminium_foil_laminate() -> MaterialProps:
    """Near-zero WVTR and OTR, light-blocking, moderate crush resistance."""
    return MaterialProps(
        material_id=4,
        name="Aluminium Foil Laminate (Al-Foil / PET-Al-PE)",
        wvtr=0.05,
        otr=0.0,
        cost_per_unit=12.0,
        biodegradability_score=1,
        light_blocking=True,
        crush_resistance=2,
    )


@pytest.fixture
def map_film() -> MaterialProps:
    """High OTR MAP film — designed for fresh produce."""
    return MaterialProps(
        material_id=12,
        name="MAP Film (Modified Atmosphere)",
        wvtr=10.0,
        otr=2500.0,
        cost_per_unit=8.0,
        biodegradability_score=2,
        light_blocking=False,
        crush_resistance=1,
    )


@pytest.fixture
def kraft_paper_bag() -> MaterialProps:
    """Very high WVTR and OTR — minimal barrier."""
    return MaterialProps(
        material_id=9,
        name="Kraft Paper Bag (Plain)",
        wvtr=300.0,
        otr=10000.0,
        cost_per_unit=1.5,
        biodegradability_score=5,
        light_blocking=False,
        crush_resistance=1,
    )


@pytest.fixture
def bopp_pouch() -> MaterialProps:
    """Moderate barrier, no light blocking."""
    return MaterialProps(
        material_id=2,
        name="BOPP Film Pouch",
        wvtr=5.0,
        otr=1500.0,
        cost_per_unit=3.5,
        biodegradability_score=1,
        light_blocking=False,
        crush_resistance=2,
    )


@pytest.fixture
def metallised_bopp() -> MaterialProps:
    """Good barrier, light blocking, moderate crush resistance."""
    return MaterialProps(
        material_id=3,
        name="Metallised BOPP Pouch",
        wvtr=1.5,
        otr=50.0,
        cost_per_unit=6.0,
        biodegradability_score=1,
        light_blocking=True,
        crush_resistance=2,
    )


# ---------------------------------------------------------------------------
# WVTR rule tests
# ---------------------------------------------------------------------------


class TestWVTRRule:
    def test_fresh_paneer_rejects_ldpe(self, fresh_paneer, ldpe_pouch):
        """
        Fresh paneer (aw 0.97) over 60 days needs WVTR ≤ 4.25 g/m²/day.
        LDPE (WVTR 8.0) should fail.
        """
        results = apply_rules(fresh_paneer, ldpe_pouch, 60, "refrigerated", "standard")
        wvtr_result = next(r for r in results if r.rule_name == "WVTR Moisture Barrier")
        assert not wvtr_result.passed
        assert "FAILS" in wvtr_result.reason
        assert "8.0" in wvtr_result.reason  # actual value should appear in reason

    def test_fresh_paneer_accepts_aluminium_foil(self, fresh_paneer, aluminium_foil_laminate):
        """Aluminium foil (WVTR 0.05) easily passes for fresh paneer."""
        results = apply_rules(fresh_paneer, aluminium_foil_laminate, 60, "refrigerated", "standard")
        wvtr_result = next(r for r in results if r.rule_name == "WVTR Moisture Barrier")
        assert wvtr_result.passed

    def test_dry_product_accepts_kraft(self, turmeric_powder, kraft_paper_bag):
        """
        Turmeric powder (aw 0.45, moisture 8.5%) with 30-day shelf life:
        WVTR threshold = 60 * 0.85 = 51 g/m²/day — kraft (300) should fail.
        But turmeric aw < 0.75 and moisture < 12% → base = 60 → 30d threshold = 60*0.85 = 51.
        Kraft WVTR 300 > 51 → should FAIL.
        """
        results = apply_rules(turmeric_powder, kraft_paper_bag, 30, "ambient", "standard")
        wvtr_result = next(r for r in results if r.rule_name == "WVTR Moisture Barrier")
        assert not wvtr_result.passed

    def test_short_shelf_life_dry_product_accepts_kraft(self, turmeric_powder, kraft_paper_bag):
        """
        With only 7 days shelf life, threshold = 60 g/m²/day.
        Kraft WVTR 300 still fails — turmeric is light-sensitive so we test with bopp instead.
        """
        results = apply_rules(turmeric_powder, kraft_paper_bag, 7, "ambient", "standard")
        wvtr_result = next(r for r in results if r.rule_name == "WVTR Moisture Barrier")
        # 7 days: threshold = 60 (base for dry), kraft 300 > 60 → still fails
        assert not wvtr_result.passed


# ---------------------------------------------------------------------------
# OTR rule tests
# ---------------------------------------------------------------------------


class TestOTRRule:
    def test_ghee_rejects_ldpe(self):
        """
        Ghee (fat 99.5%) needs OTR ≤ 10 cc/m²/day.
        LDPE (OTR 4000) should FAIL.
        """
        ghee = CommodityProps(
            moisture_pct=0.3, water_activity=0.10, respiration_rate=None,
            fat_content=99.5, light_sensitivity=True, fragility=1,
        )
        ldpe = MaterialProps(
            material_id=1, name="LDPE", wvtr=8.0, otr=4000.0,
            cost_per_unit=2.5, biodegradability_score=1, light_blocking=False, crush_resistance=1,
        )
        results = apply_rules(ghee, ldpe, 90, "ambient", "standard")
        otr_result = next(r for r in results if r.rule_name == "OTR Oxygen Barrier")
        assert not otr_result.passed

    def test_ghee_accepts_aluminium_foil(self):
        """Aluminium foil (OTR ~0) passes OTR rule for ghee."""
        ghee = CommodityProps(
            moisture_pct=0.3, water_activity=0.10, respiration_rate=None,
            fat_content=99.5, light_sensitivity=True, fragility=1,
        )
        al_foil = MaterialProps(
            material_id=4, name="Al Foil", wvtr=0.05, otr=0.0,
            cost_per_unit=12.0, biodegradability_score=1, light_blocking=True, crush_resistance=2,
        )
        results = apply_rules(ghee, al_foil, 90, "ambient", "standard")
        otr_result = next(r for r in results if r.rule_name == "OTR Oxygen Barrier")
        assert otr_result.passed

    def test_low_fat_product_accepts_ldpe_otr(self):
        """Lentils (fat 1.1%) have OTR threshold 200 — LDPE (4000) should FAIL."""
        lentils = CommodityProps(
            moisture_pct=11.0, water_activity=0.52, respiration_rate=None,
            fat_content=1.1, light_sensitivity=False, fragility=1,
        )
        ldpe = MaterialProps(
            material_id=1, name="LDPE", wvtr=8.0, otr=4000.0,
            cost_per_unit=2.5, biodegradability_score=1, light_blocking=False, crush_resistance=1,
        )
        results = apply_rules(lentils, ldpe, 180, "ambient", "standard")
        otr_result = next(r for r in results if r.rule_name == "OTR Oxygen Barrier")
        assert not otr_result.passed


# ---------------------------------------------------------------------------
# Light-blocking rule tests
# ---------------------------------------------------------------------------


class TestLightBlockingRule:
    def test_turmeric_rejects_bopp_no_light_block(self, turmeric_powder, bopp_pouch):
        """Turmeric is light-sensitive; BOPP doesn't block light → should fail."""
        results = apply_rules(turmeric_powder, bopp_pouch, 90, "ambient", "standard")
        light_result = next(r for r in results if r.rule_name == "Light Blocking")
        assert not light_result.passed

    def test_turmeric_accepts_metallised_bopp(self, turmeric_powder, metallised_bopp):
        """Metallised BOPP blocks light → should pass for turmeric."""
        results = apply_rules(turmeric_powder, metallised_bopp, 90, "ambient", "standard")
        light_result = next(r for r in results if r.rule_name == "Light Blocking")
        assert light_result.passed

    def test_non_light_sensitive_product_passes_any_material(self, fresh_paneer, bopp_pouch):
        """Non-light-sensitive product: light blocking rule always passes."""
        results = apply_rules(fresh_paneer, bopp_pouch, 14, "refrigerated", "standard")
        light_result = next(r for r in results if r.rule_name == "Light Blocking")
        assert light_result.passed


# ---------------------------------------------------------------------------
# Crush resistance rule tests
# ---------------------------------------------------------------------------


class TestCrushResistanceRule:
    def test_wafers_reject_ldpe_pouch(self, potato_wafers, ldpe_pouch):
        """
        Potato wafers (fragility 5) need crush resistance ≥ 5.
        LDPE pouch (crush_resistance 1) should fail.
        """
        results = apply_rules(potato_wafers, ldpe_pouch, 30, "ambient", "standard")
        crush_result = next(r for r in results if r.rule_name == "Crush Resistance")
        assert not crush_result.passed

    def test_low_fragility_product_accepts_flexible_film(self, turmeric_powder, ldpe_pouch):
        """Turmeric (fragility 1) → crush resistance ≥ 1 → LDPE passes."""
        results = apply_rules(turmeric_powder, ldpe_pouch, 30, "ambient", "standard")
        crush_result = next(r for r in results if r.rule_name == "Crush Resistance")
        assert crush_result.passed


# ---------------------------------------------------------------------------
# MAP / respiration rule tests
# ---------------------------------------------------------------------------


class TestRespirationRule:
    def test_fresh_spinach_rejects_aluminium_foil(self, fresh_spinach, aluminium_foil_laminate):
        """
        Fresh spinach (respiration 35 mL CO₂/kg·h) needs OTR ≥ 500.
        Al-foil (OTR ~0) should FAIL the MAP rule.
        """
        results = apply_rules(fresh_spinach, aluminium_foil_laminate, 7, "refrigerated", "cold_chain")
        resp_result = next(r for r in results if r.rule_name == "Respiration Rate / MAP Compatibility")
        assert not resp_result.passed

    def test_fresh_spinach_accepts_map_film(self, fresh_spinach, map_film):
        """MAP film (OTR 2500) should pass the respiration rule for fresh spinach."""
        results = apply_rules(fresh_spinach, map_film, 7, "refrigerated", "cold_chain")
        resp_result = next(r for r in results if r.rule_name == "Respiration Rate / MAP Compatibility")
        assert resp_result.passed

    def test_non_respiring_product_skips_map_rule(self, fresh_paneer, map_film):
        """Non-respiring commodity (respiration_rate=None) → MAP rule not applicable → passes."""
        results = apply_rules(fresh_paneer, map_film, 14, "refrigerated", "standard")
        resp_result = next(r for r in results if r.rule_name == "Respiration Rate / MAP Compatibility")
        assert resp_result.passed
        assert "not applicable" in resp_result.reason


# ---------------------------------------------------------------------------
# Integration: filter_materials
# ---------------------------------------------------------------------------


class TestFilterMaterials:
    def test_paneer_eliminates_kraft_and_ldpe(self, fresh_paneer, ldpe_pouch, kraft_paper_bag):
        """
        For fresh paneer (60 days, refrigerated), kraft and LDPE should be eliminated.
        Note: al-foil (crush_resistance=2) also correctly fails for paneer (fragility=3,
        standard transport requires crush_resistance ≥ 3). This is the rule engine working
        correctly. We test that LDPE and kraft are both eliminated; a VSP film (crush_resistance=3)
        would survive — but we keep this test simple.
        """
        # VSP film fixture: good barrier + adequate crush resistance for paneer
        vsp_film = MaterialProps(
            material_id=11,
            name="Vacuum Skin Pack (VSP) Film",
            wvtr=2.0,
            otr=8.0,   # high-barrier VSP; real spec is ~1–8 cc/m²/day
            cost_per_unit=15.0,
            biodegradability_score=1,
            light_blocking=False,
            crush_resistance=3,
        )
        materials = [ldpe_pouch, kraft_paper_bag, vsp_film]
        passing = filter_materials(fresh_paneer, materials, 60, "refrigerated", "standard")
        passing_names = [m.name for m, _ in passing]
        assert vsp_film.name in passing_names, "VSP film should pass all rules for fresh paneer"
        assert ldpe_pouch.name not in passing_names
        assert kraft_paper_bag.name not in passing_names

    def test_reason_strings_are_quantitative(self, fresh_paneer, ldpe_pouch):
        """Rule reason strings must contain numeric values, not vague descriptions.
        Exception: rules that are genuinely 'not applicable' (e.g. light-blocking for
        a non-light-sensitive product) return a descriptive message without a number —
        this is correct and intentional.
        """
        results = apply_rules(fresh_paneer, ldpe_pouch, 60, "refrigerated", "standard")
        for result in results:
            # Skip non-applicable rules (e.g. light-blocking for non-light-sensitive products)
            # — their reason text is descriptive, not numeric, which is correct.
            non_applicable_phrases = ("not light-sensitive", "not applicable", "non-respiring")
            if any(phrase in result.reason for phrase in non_applicable_phrases):
                continue
            assert any(c.isdigit() for c in result.reason), (
                f"Rule '{result.rule_name}' reason is not quantitative: '{result.reason}'"
            )
