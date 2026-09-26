"""
Packora Explainer — structured reasoning trace + plain-language reason
======================================================================

PURPOSE
-------
Builds the structured ReasoningTrace and generates the plain_language_reason
that is shown to non-technical users.

DESIGN CONTRACT (per PROJECT_BRIEF.md §4):
  - The plain_language_reason is ALWAYS generated from the structured
    reasoning_trace — never written directly by the LLM without the trace.
  - If the LLM call fails or is disabled, a templated sentence is used.
    The core recommendation flow is never blocked by LLM availability.
  - explanation_source field on the trace indicates 'llm' or 'template'
    so the frontend can show a small indicator.
"""
from __future__ import annotations

from app.rule_engine import CommodityProps, MaterialProps, RuleResult
from app.schemas import ReasoningTrace
from app.schemas import RuleResult as SchemaRuleResult
from app.schemas import ScoreBreakdown


def build_reasoning_trace(
    rule_results: list[RuleResult],
    score_breakdown: dict[str, float],
    plain_language_reason: str,
    explanation_source: str,
) -> ReasoningTrace:
    """Convert internal rule results and score dict into the API schema object."""
    schema_rules = [
        SchemaRuleResult(rule_name=r.rule_name, passed=r.passed, reason=r.reason)
        for r in rule_results
    ]
    return ReasoningTrace(
        rules_applied=schema_rules,
        rules_passed=sum(1 for r in rule_results if r.passed),
        rules_failed=sum(1 for r in rule_results if not r.passed),
        score_breakdown=ScoreBreakdown(**score_breakdown),
        explanation_source=explanation_source,
    )


def build_templated_reason(
    commodity_name: str,
    material_name: str,
    rule_results: list[RuleResult],
    score_breakdown: dict[str, float],
) -> str:
    """
    Construct a readable plain-language sentence from the structured trace.
    Used when LLM is disabled or unavailable.
    """
    passed_rules = [r.rule_name for r in rule_results if r.passed]
    composite = score_breakdown.get("composite_score", 0.0)
    sustainability = score_breakdown.get("sustainability_score", 0.0)
    cost = score_breakdown.get("cost_score", 0.0)

    strength = "strong" if composite >= 0.75 else ("moderate" if composite >= 0.50 else "marginal")
    eco = "eco-friendly" if sustainability >= 0.6 else ("moderately sustainable" if sustainability >= 0.4 else "conventional")
    cost_desc = "cost-effective" if cost >= 0.6 else ("mid-range in cost" if cost >= 0.3 else "premium-priced")

    rules_text = ", ".join(passed_rules) if passed_rules else "all evaluated criteria"

    return (
        f"{material_name} is a {strength} match for {commodity_name}. "
        f"It passes the {rules_text} requirements, is {eco}, and is {cost_desc} "
        f"with a composite fit score of {composite:.0%}."
    )
