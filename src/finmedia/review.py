"""Human review sheet for the approval gates (G2 facts, G3 script)."""

from __future__ import annotations

from typing import Any


def render_review(plan: dict[str, Any], lint: dict[str, Any], brief: dict[str, Any]) -> str:
    status = "✅ PASSED automatic checks" if lint.get("passed") else "❌ FAILED automatic checks"
    lines = [
        f"# Reel review: {plan.get('series', '')}",
        "",
        f"**{status}** · estimated length ~{lint.get('estimated_seconds', 0)} s · "
        f"compliance tier {plan.get('compliance_tier')}",
        "",
    ]
    if lint.get("errors"):
        lines += ["## Errors (must fix)", *[f"- {e}" for e in lint["errors"]], ""]
    if lint.get("warnings"):
        lines += ["## Warnings", *[f"- {w}" for w in lint["warnings"]], ""]

    lines += [
        "## Facts from the brief (check these first: Gate G2)",
        f"**Status:** {brief.get('status_note', '')}",
        "",
    ]
    for fact in brief.get("facts", []):
        lines.append(f"- {fact.get('claim')}  \n  > {fact.get('source_quote')}")
    lines += ["", f"**Hook:** {plan.get('hook_text', '')}", "", "## Scenes", "",
              "| # | Visual | Narration (Hindi) | On screen | Visual spec |", "|---|---|---|---|---|"]
    for s in plan.get("scenes", []):
        cells = [s.get("id", ""), s.get("visual", ""), s.get("narration", ""),
                 s.get("on_screen_text", ""), s.get("visual_spec", "")]
        lines.append("| " + " | ".join(str(c).replace("|", "/").replace("\n", " ") for c in cells) + " |")

    lines += ["", "## Packaging", "**Title variants:**", *[f"- {t}" for t in plan.get("title_variants", [])],
              "", "**Caption:**", "", plan.get("caption", ""), "",
              "**Hashtags:** " + " ".join(plan.get("hashtags", [])), "",
              f"**Disclosure:** {plan.get('disclosure', '')}", "",
              "**Sources:**", *[f"- {src}" for src in plan.get("sources", [])], "",
              "## Approval (Gate G3)", "- [ ] Facts checked against the source",
              "- [ ] Narration sounds like an expert explaining, not a news anchor",
              "- [ ] No advice, tips or promises", "- [ ] AI label will be switched on at upload",
              "- [ ] Approved by: ____________"]
    return "\n".join(lines) + "\n"
