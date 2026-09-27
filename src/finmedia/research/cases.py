"""Case library access. Analogues are strictly BEFORE the report date: a Budget 2026 report dated 2026-02-01 must
not include 2026-02-01 itself."""

from __future__ import annotations

from datetime import date
from typing import Any

from ..config import load_yaml


def union_budgets() -> list[dict[str, Any]]:
    return load_yaml("data/cases/union_budgets.yaml")["budgets"]


def analogue_dates(analogue_set: str, asof: str) -> list[str]:
    if analogue_set == "none":
        return []
    cut = date.fromisoformat(asof)
    rows = union_budgets()
    if analogue_set == "full_budgets":
        rows = [r for r in rows if r["type"] == "full"]
    elif analogue_set == "interim_budgets":
        rows = [r for r in rows if r["type"] == "interim"]
    out = []
    for r in rows:
        d = r["date"] if isinstance(r["date"], date) else date.fromisoformat(str(r["date"]))
        if d < cut:
            out.append(d.isoformat())
    return out
