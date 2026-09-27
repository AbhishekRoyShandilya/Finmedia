"""Triage agent: classify a document and route it to a playbook."""

from __future__ import annotations

from typing import Any

from ..llm import LLM
from ..models import TriageResult
from ..playbooks import FALLBACK_PLAYBOOK, playbook_ids
from .prompts import system_prompt


def document_block(doc: Any, max_chars: int) -> str:
    text = (doc["text"] or "")[:max_chars]
    return (
        f"Source: {doc['source_id']} ({doc['regulator'] or doc['category']})\n"
        f"Published: {doc['published_at'] or 'unknown'}\n"
        f"Title: {doc['title']}\n"
        f"URL: {doc['url']}\n\n"
        f"<document>\n{text}\n</document>"
    )


def triage_document(llm: LLM, doc: Any, settings: dict[str, Any]) -> TriageResult:
    max_chars = int(settings["llm"]["max_doc_chars"]["triage"])
    result = llm.structured("triage", system_prompt("triage_system"), document_block(doc, max_chars), TriageResult)
    if result.playbook_id not in playbook_ids():
        # Unknown playbook from the model: route to the verification gate and flag it.
        result.playbook_id = FALLBACK_PLAYBOOK
        result.needs_human_now = True
    return result
