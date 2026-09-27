"""Thin wrapper around the Claude API for structured, budget-guarded calls.

Every call:
  1. checks the monthly budget (worst case) before running,
  2. caches the stable system prompt,
  3. asks for a validated structured output (Pydantic model),
  4. records the actual token usage and cost in the ledger.
"""

from __future__ import annotations

from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel

from .costs import BudgetGuard, Usage

T = TypeVar("T", bound=BaseModel)

FALLBACK_BETA = "server-side-fallback-2026-07-01"


class LLMRefusal(RuntimeError):
    """The model (and any fallback) declined the request."""


class LLMIncomplete(RuntimeError):
    """The response was cut off or did not contain a valid structured output."""


class LLM:
    def __init__(self, guard: BudgetGuard, settings: dict[str, Any], client: Any | None = None):
        self.guard = guard
        self.cfg = settings["llm"]
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            self._client = anthropic.Anthropic()
        return self._client

    def structured(self, role: str, system: str, user: str, output_model: type[T]) -> T:
        model = self.cfg["models"][role]
        max_tokens = int(self.cfg["max_tokens"][role])
        effort = self.cfg["effort"][role]

        self.guard.check(model, len(system) + len(user), max_tokens, role=role)

        kwargs: dict[str, Any] = dict(
            model=model,
            max_tokens=max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}],
            output_format=output_model,
            output_config={"effort": effort},
            thinking={"type": "adaptive"},
        )
        if self.cfg.get("refusal_fallbacks", True):
            kwargs["betas"] = [FALLBACK_BETA]
            kwargs["fallbacks"] = "default"

        response = self.client.beta.messages.parse(**kwargs)

        usage = response.usage
        self.guard.record(
            role,
            getattr(response, "model", model) or model,
            Usage(
                input_tokens=usage.input_tokens or 0,
                output_tokens=usage.output_tokens or 0,
                cache_write_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
                cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            ),
        )

        if response.stop_reason == "refusal":
            details = getattr(response, "stop_details", None)
            raise LLMRefusal(f"{role}: request declined ({getattr(details, 'category', None)})")
        if response.stop_reason == "max_tokens":
            raise LLMIncomplete(f"{role}: output hit max_tokens={max_tokens}; raise it in settings.yaml")
        parsed = getattr(response, "parsed_output", None)
        if parsed is None:
            raise LLMIncomplete(f"{role}: no structured output returned")
        return parsed
