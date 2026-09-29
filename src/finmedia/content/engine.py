"""Content engine: one Research Object -> YouTube script, Reel, carousel, newsletter.

Every draft is checked before a human sees it:
- numbers must appear in the Research Object (the content never adds a number);
- no news-anchor phrases; video formats must disclose the AI voice/avatar; sources must be listed;
- COMPLIANCE ITEMS (not hidden, by the founder's decision): directional views, stocks named with a view, and
  recommendation/promise language. Any compliance item means publishing needs a sign-off by a `compliance` or `ra`
  reviewer. An editor's approval is enough only when there are none.
When the object gets a new version, drafts built on older versions become `stale`.
"""

from __future__ import annotations

import json
import re
from typing import Any

from ..agent.objects import get_object
from ..agent.provenance import numbers_in_text
from ..ai import AI
from ..config import load_yaml, project_root
from ..lint import lint_reel
from ..models import ReelPlan
from ..research.verify import _supported, allowed_values
from ..store import Store, now
from .models import Carousel, Newsletter, YouTubeScript

KINDS: dict[str, dict[str, Any]] = {
    "youtube": {"model": YouTubeScript, "prompt": "youtube", "label": "YouTube research video", "video": True},
    "reel": {"model": ReelPlan, "prompt": "reel", "label": "Reel / Short", "video": True},
    "carousel": {"model": Carousel, "prompt": "carousel", "label": "Carousel", "video": False},
    "newsletter": {"model": Newsletter, "prompt": "newsletter", "label": "Newsletter", "video": False},
}
ROLES = ("editor", "compliance", "ra")
INTERNAL_KEYS = ("what_it_means_for_our_books", "memory_updates")


class ContentError(RuntimeError):
    pass


def public_view(obj: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in obj.items() if k not in INTERNAL_KEYS}


def _texts(o: Any, skip: tuple[str, ...] = ("sources", "hashtags", "visual_spec", "spec")) -> list[str]:
    out: list[str] = []
    if isinstance(o, str):
        out.append(o)
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in skip:
                out += _texts(v, skip)
    elif isinstance(o, list):
        for v in o:
            out += _texts(v, skip)
    return out


def lint_content(kind: str, draft: dict[str, Any], obj: dict[str, Any]) -> dict[str, Any]:
    rules = load_yaml("config/lint_rules.yaml")
    errors: list[str] = []
    warnings: list[str] = []
    compliance: list[str] = []
    everything = " ".join(_texts(draft))
    low = everything.lower()

    if kind == "reel":
        rep = lint_reel(draft, rules, brief=None, ra_approved=True)   # recommendation phrases handled below
        errors += [e for e in rep.errors if not e.startswith("Tier RA")]
        warnings += rep.warnings
    else:
        for phrase in rules["banned_anchor_phrases"]:
            if phrase.lower() in low:
                errors.append(f"News-anchor phrase: '{phrase}'")
        if KINDS[kind]["video"] and not all(k.lower() in (draft.get("disclosure") or "").lower()
                                            for k in rules["required_disclosure_keywords"]):
            errors.append("Disclosure must state that an AI voice/avatar is used")
        if not draft.get("sources"):
            errors.append("No sources listed")

    allowed = allowed_values(public_view(obj))
    bad = sorted({t for text in _texts(draft) for t in numbers_in_text(text) if not _supported(t, allowed)})
    if bad:
        errors.append(f"Numbers not in the Research Object: {bad}")

    for phrase in rules["recommendation_phrases"]:
        if phrase.lower() in low:
            compliance.append(f"Recommendation/promise language: '{phrase}'")
    directional = [c for c in obj.get("claims", []) if c.get("direction") in ("positive", "negative")]
    if directional:
        compliance.append(f"The research contains {len(directional)} directional view(s)")
    for c in directional:
        t = str(c.get("target", ""))
        if t.startswith("stock:"):
            sym = t.split(":", 1)[1]
            if re.search(rf"\b{re.escape(sym)}\b", everything, re.I):
                compliance.append(f"Names {sym} with a {c['direction']} view ({c['horizon']})")
    if draft.get("compliance_tier") == "RA" or any(c.startswith("Names ") for c in compliance):
        compliance.append("Tier RA: stock-specific research (needs RA registration or compliance sign-off)")
    return {"passed": not errors, "errors": errors, "warnings": warnings, "compliance_items": compliance,
            "needs_signoff": bool(compliance)}


def _row(r: Any) -> dict[str, Any]:
    d = dict(r)
    d["draft"] = json.loads(d.pop("json"))
    d["lint"] = json.loads(d.pop("lint_json"))
    d["approvals"] = json.loads(d.pop("approvals_json"))
    return d


def generate(store: Store, ai: AI, key: str, kind: str, notes: str = "", version: int | None = None) -> dict[str, Any]:
    if kind not in KINDS:
        raise ContentError(f"kind must be one of {list(KINDS)}")
    ro = get_object(store, key, version)
    if ro is None:
        raise ContentError(f"no Research Object {key}")
    spec = KINDS[kind]
    base = project_root() / "prompts" / "content"
    system = (base / "house_rules.md").read_text(encoding="utf-8") + "\n\n" + \
        (base / f"{spec['prompt']}.md").read_text(encoding="utf-8")
    user = ((f"Editor notes: {notes}\n\n" if notes else "") + "RESEARCH OBJECT (the only source of facts and numbers):\n"
            + json.dumps(public_view(ro["object"]), ensure_ascii=False, indent=1))
    draft_model, inr = ai.structured("content_writer", system, user, spec["model"])
    draft = draft_model.model_dump(mode="json")
    lint = lint_content(kind, draft, ro["object"])
    title = draft.get("title_variants", [None])[0] if draft.get("title_variants") else \
        draft.get("subject") or (draft.get("slides") or [{}])[0].get("headline") or ro["title"]
    item_id = store.ex("""INSERT INTO content_items (object_key, object_version, kind, title, status, created_at,
                          updated_at, json, lint_json) VALUES (?, ?, ?, ?, 'draft', ?, ?, ?, ?)""",
                       (key, ro["version"], kind, str(title)[:200], now(), now(), json.dumps(draft, ensure_ascii=False),
                        json.dumps({**lint, "cost_inr": round(inr, 2)}, ensure_ascii=False)))
    return get_item(store, item_id)


def get_item(store: Store, item_id: int) -> dict[str, Any] | None:
    r = store.q1("SELECT * FROM content_items WHERE id = ?", (item_id,))
    return _row(r) if r else None


def list_items(store: Store, status: str | None = None, key: str | None = None) -> list[dict[str, Any]]:
    sql, params = "SELECT * FROM content_items WHERE 1=1", []
    if status:
        sql += " AND status = ?"
        params.append(status)
    if key:
        sql += " AND object_key = ?"
        params.append(key)
    out = []
    for r in store.q(sql + " ORDER BY updated_at DESC", params):
        d = _row(r)
        d.pop("draft")
        out.append(d)
    return out


def update_draft(store: Store, item_id: int, draft: dict[str, Any]) -> dict[str, Any]:
    """A human edit. It re-runs the checks and clears earlier approvals (they approved different words)."""
    item = get_item(store, item_id)
    if item is None:
        raise ContentError("no such content item")
    if item["status"] == "published":
        raise ContentError("published items cannot be edited; generate a new draft")
    model = KINDS[item["kind"]]["model"]
    draft = model.model_validate(draft).model_dump(mode="json")
    ro = get_object(store, item["object_key"], item["object_version"])
    lint = lint_content(item["kind"], draft, ro["object"])
    status = "stale" if item["status"] == "stale" else "draft"
    store.ex("UPDATE content_items SET json = ?, lint_json = ?, approvals_json = '[]', status = ?, updated_at = ? WHERE id = ?",
             (json.dumps(draft, ensure_ascii=False), json.dumps(lint, ensure_ascii=False), status, now(), item_id))
    return get_item(store, item_id)


def approve(store: Store, item_id: int, name: str, role: str, note: str = "") -> dict[str, Any]:
    item = get_item(store, item_id)
    if item is None:
        raise ContentError("no such content item")
    if role not in ROLES:
        raise ContentError(f"role must be one of {ROLES}")
    if not name.strip():
        raise ContentError("the approver's name is required")
    if item["status"] in ("stale", "published"):
        raise ContentError(f"cannot approve a {item['status']} item")
    if not item["lint"]["passed"]:
        raise ContentError("fix the check errors first: " + "; ".join(item["lint"]["errors"][:5]))
    approvals = item["approvals"] + [{"name": name.strip(), "role": role, "note": note, "at": now()}]
    signed = any(a["role"] in ("compliance", "ra") for a in approvals)
    status = "approved" if (signed or not item["lint"]["needs_signoff"]) else "draft"
    store.ex("UPDATE content_items SET approvals_json = ?, status = ?, updated_at = ? WHERE id = ?",
             (json.dumps(approvals, ensure_ascii=False), status, now(), item_id))
    return get_item(store, item_id)


def mark_published(store: Store, item_id: int, url: str = "") -> dict[str, Any]:
    item = get_item(store, item_id)
    if item is None:
        raise ContentError("no such content item")
    if item["status"] != "approved":
        raise ContentError("only approved items can be marked published (the publish gate)")
    approvals = item["approvals"] + [{"name": "system", "role": "published", "note": url, "at": now()}]
    store.ex("UPDATE content_items SET status = 'published', approvals_json = ?, updated_at = ? WHERE id = ?",
             (json.dumps(approvals, ensure_ascii=False), now(), item_id))
    return get_item(store, item_id)
