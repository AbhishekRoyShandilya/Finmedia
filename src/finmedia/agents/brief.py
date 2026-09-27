"""Research brief agent: facts with quotes, mechanism, exposures, open questions."""

from __future__ import annotations

import json
from typing import Any

from ..llm import LLM
from ..models import ResearchBrief
from ..playbooks import load_playbooks
from ..verify import verify_brief
from .prompts import system_prompt
from .triage import document_block


def write_brief(llm: LLM, doc: Any, triage: dict[str, Any], settings: dict[str, Any]
                ) -> tuple[ResearchBrief, dict[str, Any]]:
    playbook = load_playbooks().get(triage["playbook_id"], {})
    max_chars = int(settings["llm"]["max_doc_chars"]["brief"])
    user = (
        f"Playbook: {playbook.get('id')} — {playbook.get('name')}\n"
        f"Key question: {playbook.get('key_question')}\n"
        f"Signature analysis: {json.dumps(playbook.get('signature_analysis', []), ensure_ascii=False)}\n\n"
        f"Triage summary: {triage.get('summary')}\n"
        f"Why it matters (triage): {triage.get('why_it_matters')}\n\n"
        f"{document_block(doc, max_chars)}"
    )
    brief = llm.structured("brief", system_prompt("brief_system"), user, ResearchBrief)
    verification = verify_brief(brief.model_dump(mode="json"), doc["text"] or "")
    return brief, verification
