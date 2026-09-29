"""Provenance check for a Research Object: the LLM never supplies a number or a source.

- Every number in the object's prose must round-match a number that appeared in a tool result of this run (or in
  the question / an earlier verified version of the object). Dates, years, horizon labels and indicator names are
  vocabulary, not claims (the milestone-1 rules in research/verify.py).
- Every evidence ref must exist in the run's evidence log.
- Every source URL must have come back from a tool in this run.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..research.verify import _DATE_PATTERNS, _NUM, _supported, allowed_values

# Keys whose values are references / metadata, not prose claims.
SKIP_KEYS = {"evidence_refs", "ref", "url", "published_at", "event_date", "effective_date", "review_after",
             "horizon", "target", "entities", "mechanism_tags", "tags", "persona", "mode", "verdict", "stage",
             "direction", "confidence", "status", "event_type", "primary"}
_REF = re.compile(r"^E\d+$")


def _prose(obj: Any, path: str = "") -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    if isinstance(obj, str):
        out.append((path, obj))
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if k not in SKIP_KEYS:
                out += _prose(v, f"{path}.{k}" if path else k)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _prose(v, f"{path}[{i}]")
    return out


def numbers_in_text(text: str) -> list[str]:
    for p in _DATE_PATTERNS:
        text = p.sub(" ", text)
    return [m.group() for m in _NUM.finditer(text)]


def allowed_from_evidence(evidence: dict[str, dict[str, Any]], extra_texts: list[str] | None = None) -> list[float]:
    vals: list[float] = []
    for e in evidence.values():
        vals += allowed_values({"r": e.get("result"), "a": e.get("args")})
    for t in extra_texts or []:
        vals += allowed_values({"t": t})
    return vals


def check_object(obj: dict[str, Any], evidence: dict[str, dict[str, Any]], extra_texts: list[str] | None = None,
                 allowed: list[float] | None = None) -> dict[str, Any]:
    allowed = allowed if allowed is not None else allowed_from_evidence(evidence, extra_texts)
    unsupported: list[dict[str, str]] = []
    checked = 0
    for path, text in _prose(obj):
        for tok in numbers_in_text(text):
            checked += 1
            if not _supported(tok, allowed):
                unsupported.append({"number": tok, "where": path, "text": text[:160]})

    refs: set[str] = set()

    def collect(o: Any) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "evidence_refs" and isinstance(v, list):
                    refs.update(str(x) for x in v)
                elif k == "ref" and isinstance(v, str):
                    refs.add(v)
                else:
                    collect(v)
        elif isinstance(o, list):
            for v in o:
                collect(v)
    collect(obj)
    bad_refs = sorted(r for r in refs if r not in evidence)

    blob = json.dumps({k: {"r": v.get("result"), "a": v.get("args")} for k, v in evidence.items()},
                      ensure_ascii=False, default=str)
    unfetched = [s.get("url") for s in obj.get("sources", []) if s.get("url") and s.get("url") not in blob]

    directional = [c for c in obj.get("claims", []) if c.get("direction") in ("positive", "negative")]
    stock_level = [c for c in obj.get("claims", []) if str(c.get("target", "")).startswith("stock:")]
    ok = not unsupported and not bad_refs and not unfetched
    return {"ok": ok, "numbers_checked": checked, "unsupported_numbers": unsupported, "bad_refs": bad_refs,
            "unfetched_sources": unfetched, "directional_claims": len(directional),
            "stock_level_claims": len(stock_level),
            "compliance_markers": {"directional": len(directional) > 0, "stock_level": len(stock_level) > 0}}


def problems_text(check: dict[str, Any]) -> str:
    lines = []
    if check["unsupported_numbers"]:
        nums = sorted({u["number"] for u in check["unsupported_numbers"]})
        where = "; ".join(f"{u['number']} in {u['where']}" for u in check["unsupported_numbers"][:12])
        lines.append(f"Numbers not found in any tool result of this run: {nums} ({where}). Quote them exactly as a "
                     "tool returned them, or say it in words, or remove them.")
    if check["bad_refs"]:
        lines.append(f"Evidence refs that do not exist: {check['bad_refs']}. Use only refs shown on tool results.")
    if check["unfetched_sources"]:
        lines.append(f"Source URLs that no tool returned in this run: {check['unfetched_sources']}. Fetch them or "
                     "drop them.")
    return "\n".join(lines)
