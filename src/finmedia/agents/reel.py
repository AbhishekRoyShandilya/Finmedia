"""Reel script agent: research brief -> Hindi scene plan for Instagram."""

from __future__ import annotations

import json
from typing import Any

from ..llm import LLM
from ..models import ReelPlan
from .prompts import system_prompt

SERIES = {
    "strategy_decay": "पुरानी Strategy, नया Market",
    "strategy_test": "5-Minute Strategy Test",
    "transfer": "The Transfer",
    "event": "Event Explainer",
}


def write_reel(llm: LLM, brief: dict[str, Any], series: str = "event", notes: str = "") -> ReelPlan:
    user = (
        f"Series: {SERIES.get(series, series)}\n"
        + (f"Editor notes: {notes}\n" if notes else "")
        + "\nApproved research brief (the only source of facts and numbers):\n"
        + f"<brief>\n{json.dumps(brief, ensure_ascii=False, indent=2)}\n</brief>"
    )
    return llm.structured("reel_script", system_prompt("reel_system"), user, ReelPlan)
