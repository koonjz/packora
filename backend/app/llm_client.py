"""
Packora LLM Client — optional plain-language explanation generator
==================================================================

This module makes a single API call to an LLM to turn the structured
reasoning trace into a natural, readable sentence for non-technical users.

DESIGN CONTRACT (per PROJECT_BRIEF.md §2.2):
  - This call has a hard timeout (LLM_TIMEOUT_SECONDS from settings).
  - On ANY failure (network, timeout, API key missing, rate limit, etc.),
    it returns None — the caller (recommend router) then uses the templated
    sentence from explainer.py.
  - Never raise an exception from this module — always return None on error.
  - The core recommendation flow must never wait on this call if it is slow.
"""
from __future__ import annotations

import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


async def generate_llm_explanation(
    commodity_name: str,
    material_name: str,
    rule_summaries: list[str],
    score_breakdown: dict[str, float],
) -> str | None:
    """
    Ask the configured LLM to produce a single plain-language sentence
    explaining why this packaging material was recommended.

    Returns the explanation string on success, or None on any failure.
    Caller MUST have a templated fallback ready.
    """
    if not settings.enable_llm_explanation:
        return None

    if not settings.llm_api_key:
        logger.info("LLM API key not configured — skipping LLM explanation (using template)")
        return None

    prompt = (
        f"You are a food packaging advisor. In one or two plain sentences, "
        f"explain to a small food business owner why {material_name} is recommended "
        f"for packaging {commodity_name}.\n\n"
        f"Technical reasoning:\n"
        + "\n".join(f"- {r}" for r in rule_summaries)
        + f"\n\nFit score: {score_breakdown.get('composite_score', 0):.0%} "
        f"(cost: {score_breakdown.get('cost_score', 0):.0%}, "
        f"sustainability: {score_breakdown.get('sustainability_score', 0):.0%})\n\n"
        f"Use simple language. Do not mention technical terms like WVTR or OTR. "
        f"Keep it under 60 words."
    )

    try:
        if settings.llm_provider == "openai":
            return await _call_openai(prompt)
        elif settings.llm_provider == "anthropic":
            return await _call_anthropic(prompt)
        else:
            logger.warning("Unknown LLM provider '%s' — skipping", settings.llm_provider)
            return None
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM call failed (%s: %s) — falling back to template", type(exc).__name__, exc)
        return None


async def _call_openai(prompt: str) -> str | None:
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.llm_api_key}"},
            json={
                "model": settings.llm_model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 100,
                "temperature": 0.3,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()


async def _call_anthropic(prompt: str) -> str | None:
    async with httpx.AsyncClient(timeout=settings.llm_timeout_seconds) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": settings.llm_api_key,
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": settings.llm_model,
                "max_tokens": 100,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"].strip()
