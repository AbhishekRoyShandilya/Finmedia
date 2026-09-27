"""Rule-based pre-filter: decides which documents are worth an LLM call."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Document


@dataclass
class PrefilterResult:
    score: int
    keep: bool
    reasons: list[str] = field(default_factory=list)


def score_document(doc: Document, rules: dict[str, Any], min_score: int) -> PrefilterResult:
    title = doc.title.lower()
    for phrase in rules.get("drop_if_title_contains", []):
        if phrase.lower() in title:
            return PrefilterResult(score=0, keep=False, reasons=[f"routine filing: '{phrase}'"])

    haystack = f"{doc.title}\n{doc.text[: rules.get('scan_chars', 4000)]}".lower()
    score = 0
    reasons: list[str] = []
    for keyword, weight in rules.get("keywords", {}).items():
        if str(keyword).lower() in haystack:
            score += int(weight)
            reasons.append(f"+{weight} {keyword}")
    return PrefilterResult(score=score, keep=score >= min_score, reasons=reasons)
