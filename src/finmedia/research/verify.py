"""Numbers in the analysts' output must come from the quant pack or the cited facts - never from the model.

A number written with d decimals is SUPPORTED if some allowed value rounds to it at d decimals (sign ignored:
"3.2% lower" may quote -3.16). Dates and years are stripped before checking. This is a guard, not a proof: a
fabricated small integer can collide with some allowed value, so the report also lists every checked number.
"""

from __future__ import annotations

import re
from typing import Any, Iterable

from ..verify import _normalize_space  # reuse the brief verifier's whitespace rule

_NUM = re.compile(r"(?<![A-Za-z])-?\d[\d,]*(?:\.\d+)?")
_MONTHS = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*"
_DATE_PATTERNS = [re.compile(p, re.I) for p in (
    r"\d{4}-\d{2}-\d{2}", r"\b\d{1,2}\s+" + _MONTHS + r"(?:\s+\d{4})?", _MONTHS + r"\s+\d{1,2}(?:,\s*\d{4})?",
    r"\b(?:19|20)\d{2}(?:-\d{2})?\b", r"\bT\+\d+\b", r"\bFY\s?\d{2,4}\b", r"\bH[0-3]\b",
    # horizon labels and standard indicator / index names are vocabulary, not claims
    r"\b(?:1|3|6|12)[- ]months?\b", r"\b1[- ]week\b", r"\b52[- ]week\b",
    r"\b(?:20|50|100|200)[- ]?(?:DMA|day|EMA|SMA)\b", r"\bNIFTY\s?(?:50|100|500)\b", r"\bMidcap\s?(?:100|150)\b",
    r"\b(?:1|5|20|60)\s+sessions?\b")]
NON_CLAIM_KEYS = {"evidence", "what_would_change_view", "dates_to_watch", "persona"}


def allowed_values(pack: dict[str, Any], facts: list[dict[str, Any]] | None = None) -> list[float]:
    vals: list[float] = []

    def walk(o: Any) -> None:
        if isinstance(o, bool):
            return
        if isinstance(o, (int, float)):
            vals.append(float(o))
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif isinstance(o, str):
            for m in _NUM.finditer(o):
                try:
                    vals.append(float(m.group().replace(",", "")))
                except ValueError:
                    pass
    walk(pack)
    for f in facts or []:
        walk(f.get("claim", "")); walk(f.get("source_quote", ""))
    return vals


def _strings(obj: Any) -> Iterable[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k not in NON_CLAIM_KEYS:
                yield from _strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v)


def _supported(token: str, allowed: list[float]) -> bool:
    t = token.replace(",", "")
    d = len(t.split(".")[1]) if "." in t else 0
    x = abs(float(t))
    return any(round(abs(v), d) == round(x, d) for v in allowed)


def check_numbers(output: dict[str, Any], allowed: list[float]) -> dict[str, Any]:
    checked, bad = [], []
    for s in _strings(output):
        text = s
        for p in _DATE_PATTERNS:
            text = p.sub(" ", text)
        for m in _NUM.finditer(text):
            tok = m.group()
            checked.append(tok)
            if not _supported(tok, allowed):
                bad.append(tok)
    return {"ok": not bad, "checked": len(checked), "unsupported": sorted(set(bad))}


def quotes_present(facts: list[dict[str, Any]], doc_text: str) -> list[str]:
    norm = _normalize_space(doc_text)
    return [f["source_quote"] for f in facts if _normalize_space(f.get("source_quote", "")) not in norm]
