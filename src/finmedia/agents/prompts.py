"""Load system prompts from prompts/ (kept stable so they can be cached)."""

from __future__ import annotations

from functools import lru_cache

from ..config import project_root
from ..playbooks import catalog_text


@lru_cache(maxsize=None)
def system_prompt(name: str) -> str:
    text = (project_root() / "prompts" / f"{name}.md").read_text(encoding="utf-8")
    if "{PLAYBOOK_CATALOG}" in text:
        text = text.replace("{PLAYBOOK_CATALOG}", catalog_text())
    return text
