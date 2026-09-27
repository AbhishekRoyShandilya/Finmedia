"""Deterministic verification: every number must trace back to the source.

The LLM is never trusted as a source of facts. These checks run on its
output before a human ever sees it.
"""

from __future__ import annotations

import json
import re
from typing import Any, Iterable

_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")
_SCALES = {"हज़ार": 1e3, "हजार": 1e3, "लाख": 1e5, "करोड़": 1e7, "करोड": 1e7}


def _normalize_number(token: str) -> str:
    value = token.replace(",", "")
    if "." in value:
        value = value.rstrip("0").rstrip(".")
    return value


def numbers_in(text: str) -> set[str]:
    """All numbers in a text, normalized (commas removed, trailing zeros dropped)."""
    text = (text or "").translate(_DEVANAGARI_DIGITS)
    return {_normalize_number(m.group()) for m in _NUMBER_RE.finditer(text)}


def _fmt(value: float) -> str:
    return _normalize_number(f"{value:.6f}")


def spoken_numbers(text: str) -> list[tuple[str, set[str]]]:
    """Numbers in Hindi narration with the values they may stand for.

    "61 हज़ार करोड़" can stand for 61 or 61000 (the crore unit is kept on both
    sides), so either form in the brief counts as support.
    """
    text = (text or "").translate(_DEVANAGARI_DIGITS)
    found = []
    for m in _NUMBER_RE.finditer(text):
        raw = _normalize_number(m.group())
        candidates = {raw}
        following = text[m.end(): m.end() + 12].strip().split(" ")[0] if m.end() < len(text) else ""
        scale = _SCALES.get(following)
        if scale:
            try:
                candidates.add(_fmt(float(raw) * scale))
                if scale == 1e7:  # "करोड़" is usually kept as the unit
                    candidates.add(raw)
            except ValueError:
                pass
        found.append((raw, candidates))
    return found


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip().lower()


# Brief fields that hold questions for later research, not claims; numbers
# there (e.g. "T+60") are not required to appear in the source document.
NON_CLAIM_FIELDS = {"history_questions", "what_would_change_view"}


def _all_strings(obj: Any) -> Iterable[str]:
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k in NON_CLAIM_FIELDS:
                continue
            yield from _all_strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from _all_strings(v)


def verify_brief(brief: dict[str, Any], doc_text: str) -> dict[str, Any]:
    """Check that quotes exist in the document and every number is supported by it."""
    doc_norm = _normalize_space(doc_text)
    doc_numbers = numbers_in(doc_text)

    missing_quotes = []
    for fact in brief.get("facts", []):
        quote = _normalize_space(fact.get("source_quote", ""))
        if quote and quote not in doc_norm:
            missing_quotes.append(fact.get("source_quote", ""))

    unsupported = sorted(
        {n for s in _all_strings(brief) for n in numbers_in(s) if n not in doc_numbers}
    )
    return {
        "ok": not missing_quotes and not unsupported,
        "missing_quotes": missing_quotes,
        "unsupported_numbers": unsupported,
    }


def brief_numbers(brief: dict[str, Any]) -> set[str]:
    return {n for s in _all_strings(brief) for n in numbers_in(s)}


def dumps(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)
