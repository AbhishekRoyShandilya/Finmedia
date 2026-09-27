"""Script linter: checks a Reel plan against our voice, effort and compliance rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .verify import spoken_numbers

_SENTENCE_SPLIT = re.compile(r"[।.?!…]+")
_BEAT = "[beat]"


@dataclass
class LintReport:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    estimated_seconds: float = 0.0

    @property
    def passed(self) -> bool:
        return not self.errors

    def as_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "estimated_seconds": round(self.estimated_seconds, 1),
            "errors": self.errors,
            "warnings": self.warnings,
        }


def _contains(text: str, phrase: str) -> bool:
    return phrase.lower() in text.lower()


def lint_reel(plan: dict[str, Any], rules: dict[str, Any], brief: dict[str, Any] | None = None,
              ra_approved: bool = False) -> LintReport:
    report = LintReport()
    limits = rules["limits"]
    scenes = plan.get("scenes", [])
    narration = " ".join(s.get("narration", "") for s in scenes)
    visible_text = " ".join(
        [plan.get("hook_text", ""), plan.get("caption", "")]
        + [s.get("on_screen_text", "") for s in scenes]
        + plan.get("title_variants", [])
    )
    everything = f"{narration} {visible_text}"

    # Voice: no news-anchor phrases.
    for phrase in rules["banned_anchor_phrases"]:
        if _contains(everything, phrase):
            report.errors.append(f"News-anchor phrase: '{phrase}'")

    # Compliance: no recommendation / promise language.
    if not ra_approved:
        for phrase in rules["recommendation_phrases"]:
            if _contains(everything, phrase):
                report.errors.append(f"Recommendation/promise language: '{phrase}'")
    if plan.get("compliance_tier") == "RA" and not ra_approved:
        report.errors.append("Tier RA content needs SEBI RA approval before publishing")

    # Disclosure.
    disclosure = plan.get("disclosure", "")
    if not all(_contains(disclosure, kw) for kw in rules["required_disclosure_keywords"]):
        report.errors.append("Disclosure must state that AI voice/avatar is used")
    if not plan.get("sources"):
        report.errors.append("No sources listed")

    # Duration.
    words = len(narration.replace(_BEAT, " ").split())
    beats = narration.count(_BEAT)
    report.estimated_seconds = words / float(limits["words_per_second"]) + 0.7 * beats
    if report.estimated_seconds > limits["reel_max_seconds"]:
        report.errors.append(f"Too long: ~{report.estimated_seconds:.0f}s (max {limits['reel_max_seconds']}s)")
    elif report.estimated_seconds < limits["reel_min_seconds"]:
        report.warnings.append(f"Very short: ~{report.estimated_seconds:.0f}s")
    if beats < limits["min_beats"]:
        report.warnings.append("No [beat] pauses; add one before the key reveal")

    # Visible effort: visual variety and avatar share.
    visuals = [s.get("visual") for s in scenes]
    non_avatar = {v for v in visuals if v and v != "AVATAR"}
    if len(non_avatar) < limits["min_non_avatar_visual_types"]:
        report.errors.append(
            f"Only {len(non_avatar)} non-avatar visual type(s); need {limits['min_non_avatar_visual_types']}"
        )
    if scenes and visuals.count("AVATAR") / len(scenes) > limits["max_avatar_share"]:
        report.warnings.append("Avatar is on screen in more than half of the scenes")

    # Numbers: one per spoken sentence, and every number traceable to the brief.
    for sentence in _SENTENCE_SPLIT.split(narration.replace(_BEAT, " ")):
        count = len(spoken_numbers(sentence))
        if count > limits["max_numbers_per_sentence"]:
            report.warnings.append(f"{count} numbers in one sentence: '{sentence.strip()[:60]}…'")

    if brief is not None:
        from .verify import brief_numbers

        supported = brief_numbers(brief)
        for raw, candidates in spoken_numbers(everything):
            if not candidates & supported:
                report.errors.append(f"Number '{raw}' does not appear in the research brief")

    return report
