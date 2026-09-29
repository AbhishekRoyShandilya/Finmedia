"""One budget-guarded entry point to whichever LLM provider settings.yaml selects (agent.provider).

Every call is checked against the monthly cap BEFORE it runs (worst case) and recorded in the cost ledger after.
Roles starting with `research_` spend from the research pool; everything else from the media pool.
"""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel

from ..costs import BudgetGuard, Usage
from ..env import get_key
from ..store import Store
from .providers import (AnthropicProvider, ChatResult, DemoProvider, OpenAICompatProvider, ProviderError,
                        ProviderNotConfigured, ToolSpec)

__all__ = ["AI", "ChatResult", "ToolSpec", "ProviderError", "ProviderNotConfigured"]


class AI:
    def __init__(self, store: Store, cfg: dict[str, Any], provider: Any | None = None, provider_name: str | None = None):
        self.cfg = cfg
        self.agent = cfg["agent"]
        self.name = provider_name or (provider.name if provider is not None else self.agent.get("provider", "anthropic"))
        self.guard = BudgetGuard(store, cfg)
        self.guard.prices = {**self.guard.prices, **(self.agent.get("openai_compat", {}).get("prices_usd_per_mtok") or {})}
        self.guard.prices.setdefault("demo", [0.0, 0.0])
        self.provider = provider if provider is not None else self._make(self.name)

    def _make(self, name: str) -> Any:
        if name == "anthropic":
            a = self.agent.get("anthropic", {})
            return AnthropicProvider(effort=a.get("effort"), fallbacks=bool(self.cfg["llm"].get("refusal_fallbacks", True)))
        if name == "openai_compat":
            return OpenAICompatProvider(self.agent["openai_compat"]["base_url"])
        if name == "demo":
            return DemoProvider()
        raise ValueError(f"Unknown agent.provider {name!r} (use anthropic, openai_compat or demo)")

    # ------------------------------------------------------------------ status
    def status(self) -> dict[str, Any]:
        key = {"anthropic": "ANTHROPIC_API_KEY", "openai_compat": "OPENAI_COMPAT_API_KEY"}.get(self.name)
        base = self.agent.get("openai_compat", {}).get("base_url", "")
        local = self.name == "openai_compat" and ("localhost" in base or "127.0.0.1" in base)
        ready = self.name == "demo" or local or bool(key and get_key(key))
        return {"provider": self.name, "ready": ready, "key": key, "models": self.models(),
                "note": ("DEMO mode: scripted walk-through, not research." if self.name == "demo" else
                         "" if ready else f"Add {key} to .env to enable research and content generation.")}

    def models(self) -> dict[str, str]:
        if self.name == "demo":
            return {r: "demo" for r in ("research_lead", "research_panel", "content_writer")}
        return dict(self.agent.get(self.name, {}).get("models", {}))

    def model_for(self, role: str) -> str:
        return self.models()[role]

    def max_tokens(self, role: str) -> int:
        return int(self.agent["max_tokens"][role])

    # ------------------------------------------------------------------ calls
    def _check(self, role: str, chars: int) -> str:
        model = self.model_for(role)
        self.guard.check(model, chars, self.max_tokens(role), role=role)
        return model

    def _record(self, role: str, model: str, usage: Usage) -> float:
        return self.guard.record(role, model, usage)

    def chat(self, role: str, system: str, messages: list[dict[str, Any]], tools: list[ToolSpec]) -> tuple[ChatResult, float]:
        chars = len(system) + len(json.dumps(messages, ensure_ascii=False, default=str)) + \
            sum(len(t.description) + len(json.dumps(t.schema)) for t in tools)
        model = self._check(role, chars)
        result = self.provider.chat(model, system, messages, tools, self.max_tokens(role), role)
        inr = self._record(role, result.model or model, result.usage)
        return result, inr

    def structured(self, role: str, system: str, user: str, output_model: type[BaseModel]) -> tuple[BaseModel, float]:
        model = self._check(role, len(system) + len(user))
        parsed, usage, used = self.provider.structured(model, system, user, output_model, self.max_tokens(role), role)
        inr = self._record(role, used or model, usage)
        return parsed, inr
