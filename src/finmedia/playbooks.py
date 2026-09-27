"""Access to system/event_playbooks.yaml."""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from .config import load_yaml

FALLBACK_PLAYBOOK = "rumour_unverified"


@lru_cache(maxsize=1)
def load_playbooks() -> dict[str, dict[str, Any]]:
    data = load_yaml("system/event_playbooks.yaml")
    return {p["id"]: p for p in data["playbooks"]}


def playbook_ids() -> list[str]:
    return list(load_playbooks())


def catalog_text() -> str:
    """Compact, stable description of all playbooks for LLM prompts."""
    lines = []
    for pid, p in load_playbooks().items():
        examples = ", ".join(str(e) for e in p.get("examples", []))
        lines.append(
            f"- {pid}: {p['name']} | horizon {p.get('horizon')} | "
            f"key question: {p.get('key_question')} | examples: {examples}"
        )
    return "\n".join(lines)
