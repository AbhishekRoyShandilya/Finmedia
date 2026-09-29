"""LLM providers behind one small interface, so the research agent runs on Claude, on any OpenAI-compatible API
(Groq, OpenAI, OpenRouter, Together, a local Ollama...), or on a scripted DEMO provider with no key.

Conversation format shared by every provider (the agent loop only ever sees this):
    {"role": "user", "content": str}
    {"role": "assistant", "text": str, "tool_calls": [{"id", "name", "args"}], "native": <provider blob or None>}
    {"role": "tool", "results": [{"id", "name", "content": str, "is_error": bool}]}
`native` keeps the provider's own assistant content (for Claude: thinking blocks with their signatures), which must
be sent back unchanged on the next turn.
"""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal, get_args, get_origin

import httpx
from pydantic import BaseModel

from ..costs import Usage
from ..env import get_key


class ProviderError(RuntimeError):
    """The provider failed, refused, or returned something unusable."""


class ProviderNotConfigured(ProviderError):
    """The API key for the chosen provider is missing."""


@dataclass
class ChatResult:
    text: str
    tool_calls: list[dict[str, Any]]
    native: Any
    usage: Usage
    model: str
    stop_reason: str = "end_turn"          # end_turn | tool_use | max_tokens
    thinking: str = ""                     # readable summary of the model's reasoning, when the provider exposes it


@dataclass
class ToolSpec:
    name: str
    description: str
    schema: dict[str, Any]
    extra: dict[str, Any] = field(default_factory=dict)


def inline_refs(schema: dict[str, Any]) -> dict[str, Any]:
    """Resolve $ref/$defs from a Pydantic JSON schema into one self-contained schema (portable across providers)."""
    schema = copy.deepcopy(schema)
    defs = schema.pop("$defs", {})

    def walk(node: Any) -> Any:
        if isinstance(node, dict):
            if "$ref" in node:
                name = node["$ref"].split("/")[-1]
                merged = {**walk(copy.deepcopy(defs[name])), **{k: v for k, v in node.items() if k != "$ref"}}
                return merged
            return {k: walk(v) for k, v in node.items()}
        if isinstance(node, list):
            return [walk(v) for v in node]
        return node

    return walk(schema)


# ------------------------------------------------------------------------------------------------ Anthropic
class AnthropicProvider:
    name = "anthropic"
    FALLBACK_BETA = "server-side-fallback-2026-07-01"

    def __init__(self, client: Any | None = None, effort: dict[str, str] | None = None, fallbacks: bool = True):
        self._client = client
        self.effort = effort or {}
        self.fallbacks = fallbacks

    @property
    def client(self) -> Any:
        if self._client is None:
            if not get_key("ANTHROPIC_API_KEY"):
                raise ProviderNotConfigured("ANTHROPIC_API_KEY is not set (put it in .env or the environment)")
            import anthropic
            self._client = anthropic.Anthropic(api_key=get_key("ANTHROPIC_API_KEY"))
        return self._client

    @staticmethod
    def _messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []

        def add_user_blocks(blocks: list[dict[str, Any]]) -> None:
            if out and out[-1]["role"] == "user":
                prev = out[-1]["content"]
                out[-1]["content"] = (prev if isinstance(prev, list) else [{"type": "text", "text": prev}]) + blocks
            else:
                out.append({"role": "user", "content": blocks})

        for m in messages:
            if m["role"] == "user":
                add_user_blocks([{"type": "text", "text": m["content"]}])
            elif m["role"] == "assistant":
                if m.get("native"):
                    content = m["native"]
                else:
                    content = ([{"type": "text", "text": m["text"]}] if m.get("text") else []) + [
                        {"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["args"]}
                        for c in m.get("tool_calls", [])]
                out.append({"role": "assistant", "content": content or [{"type": "text", "text": "(no text)"}]})
            elif m["role"] == "tool":
                add_user_blocks([{"type": "tool_result", "tool_use_id": r["id"], "content": r["content"],
                                  "is_error": bool(r.get("is_error"))} for r in m["results"]])
        return out

    @staticmethod
    def _usage(u: Any) -> Usage:
        return Usage(input_tokens=getattr(u, "input_tokens", 0) or 0, output_tokens=getattr(u, "output_tokens", 0) or 0,
                     cache_write_tokens=getattr(u, "cache_creation_input_tokens", 0) or 0,
                     cache_read_tokens=getattr(u, "cache_read_input_tokens", 0) or 0)

    def chat(self, model: str, system: str, messages: list[dict[str, Any]], tools: list[ToolSpec],
             max_tokens: int, role: str) -> ChatResult:
        tool_defs = [{"name": t.name, "description": t.description, "input_schema": t.schema} for t in tools]
        if tool_defs:
            tool_defs[-1] = {**tool_defs[-1], "cache_control": {"type": "ephemeral"}}
        kwargs: dict[str, Any] = dict(
            model=model, max_tokens=max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=self._messages(messages), tools=tool_defs,
            thinking={"type": "adaptive"}, output_config={"effort": self.effort.get(role, "high")},
            cache_control={"type": "ephemeral"},          # automatic caching of the growing conversation
        )
        resp = self.client.messages.create(**kwargs)
        if resp.stop_reason == "refusal":
            raise ProviderError(f"{role}: the model declined this request")
        text, thinking, calls, native = [], [], [], []
        for block in resp.content:
            data = block.model_dump(mode="json", exclude_none=True)
            native.append(data)
            if block.type == "text":
                text.append(block.text)
            elif block.type == "thinking":
                thinking.append(getattr(block, "thinking", "") or "")
            elif block.type == "tool_use":
                calls.append({"id": block.id, "name": block.name, "args": block.input or {}})
        return ChatResult(text="\n".join(t for t in text if t), tool_calls=calls, native=native,
                          usage=self._usage(resp.usage), model=getattr(resp, "model", model) or model,
                          stop_reason=resp.stop_reason or "end_turn", thinking="\n".join(t for t in thinking if t))

    def structured(self, model: str, system: str, user: str, output_model: type[BaseModel], max_tokens: int,
                   role: str) -> tuple[BaseModel, Usage, str]:
        kwargs: dict[str, Any] = dict(
            model=model, max_tokens=max_tokens,
            system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
            messages=[{"role": "user", "content": user}], output_format=output_model,
            output_config={"effort": self.effort.get(role, "high")}, thinking={"type": "adaptive"},
        )
        if self.fallbacks:
            kwargs["betas"] = [self.FALLBACK_BETA]
            kwargs["fallbacks"] = "default"
        resp = self.client.beta.messages.parse(**kwargs)
        usage = self._usage(resp.usage)
        if resp.stop_reason == "refusal":
            raise ProviderError(f"{role}: the model declined this request")
        if resp.stop_reason == "max_tokens":
            raise ProviderError(f"{role}: output hit max_tokens={max_tokens}; raise agent.max_tokens in settings.yaml")
        parsed = getattr(resp, "parsed_output", None)
        if parsed is None:
            raise ProviderError(f"{role}: no structured output returned")
        return parsed, usage, getattr(resp, "model", model) or model


# ------------------------------------------------------------------------------------------ OpenAI-compatible
class OpenAICompatProvider:
    name = "openai_compat"

    def __init__(self, base_url: str, http: httpx.Client | None = None, timeout: float = 180.0):
        self.base_url = base_url.rstrip("/")
        self._http = http
        self.timeout = timeout

    def _post(self, body: dict[str, Any]) -> dict[str, Any]:
        key = get_key("OPENAI_COMPAT_API_KEY")
        if not key and "localhost" not in self.base_url and "127.0.0.1" not in self.base_url:
            raise ProviderNotConfigured("OPENAI_COMPAT_API_KEY is not set (put it in .env or the environment)")
        http = self._http or httpx.Client(timeout=self.timeout)
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = f"Bearer {key}"
        r = http.post(f"{self.base_url}/chat/completions", json=body, headers=headers)
        if r.status_code >= 400:
            raise ProviderError(f"{self.base_url} returned {r.status_code}: {r.text[:400]}")
        return r.json()

    def _tokens_field(self) -> str:
        return "max_completion_tokens" if "api.openai.com" in self.base_url else "max_tokens"

    @staticmethod
    def _messages(system: str, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = [{"role": "system", "content": system}]
        for m in messages:
            if m["role"] == "user":
                out.append({"role": "user", "content": m["content"]})
            elif m["role"] == "assistant":
                msg: dict[str, Any] = {"role": "assistant", "content": m.get("text") or None}
                if m.get("tool_calls"):
                    msg["tool_calls"] = [{"id": c["id"], "type": "function",
                                          "function": {"name": c["name"], "arguments": json.dumps(c["args"])}}
                                         for c in m["tool_calls"]]
                out.append(msg)
            elif m["role"] == "tool":
                out += [{"role": "tool", "tool_call_id": r["id"], "content": r["content"]} for r in m["results"]]
        return out

    @staticmethod
    def _usage(data: dict[str, Any]) -> Usage:
        u = data.get("usage") or {}
        return Usage(input_tokens=int(u.get("prompt_tokens") or 0), output_tokens=int(u.get("completion_tokens") or 0))

    def chat(self, model: str, system: str, messages: list[dict[str, Any]], tools: list[ToolSpec],
             max_tokens: int, role: str) -> ChatResult:
        body: dict[str, Any] = {"model": model, "messages": self._messages(system, messages),
                                self._tokens_field(): max_tokens}
        if tools:
            body["tools"] = [{"type": "function", "function": {"name": t.name, "description": t.description,
                                                               "parameters": t.schema}} for t in tools]
            body["tool_choice"] = "auto"
        data = self._post(body)
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        calls = []
        for i, c in enumerate(msg.get("tool_calls") or []):
            fn = c.get("function") or {}
            try:
                args = json.loads(fn.get("arguments") or "{}")
            except json.JSONDecodeError:
                args = {"_unparsed_arguments": fn.get("arguments")}
            calls.append({"id": c.get("id") or f"call_{i}", "name": fn.get("name", ""), "args": args})
        finish = choice.get("finish_reason") or "stop"
        return ChatResult(text=msg.get("content") or "", tool_calls=calls, native=None, usage=self._usage(data),
                          model=data.get("model") or model,
                          stop_reason={"length": "max_tokens", "tool_calls": "tool_use"}.get(finish, "end_turn"),
                          thinking=msg.get("reasoning") or msg.get("reasoning_content") or "")

    def structured(self, model: str, system: str, user: str, output_model: type[BaseModel], max_tokens: int,
                   role: str) -> tuple[BaseModel, Usage, str]:
        schema = inline_refs(output_model.model_json_schema())
        body = {"model": model, self._tokens_field(): max_tokens,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
                "tools": [{"type": "function", "function": {"name": "answer", "description": "Return the answer.",
                                                            "parameters": schema}}],
                "tool_choice": {"type": "function", "function": {"name": "answer"}}}
        data = self._post(body)
        msg = ((data.get("choices") or [{}])[0].get("message") or {})
        calls = msg.get("tool_calls") or []
        raw = calls[0]["function"]["arguments"] if calls else (msg.get("content") or "")
        try:
            parsed = output_model.model_validate(json.loads(_strip_fences(raw)))
        except Exception as exc:  # noqa: BLE001
            raise ProviderError(f"{role}: could not parse structured output: {exc}") from exc
        return parsed, self._usage(data), data.get("model") or model


def _strip_fences(text: str) -> str:
    m = re.search(r"```(?:json)?\s*(.*?)```", text, re.S)
    return m.group(1) if m else text


# ---------------------------------------------------------------------------------------------------- DEMO
def demo_instance(model: type[BaseModel], hint: str = "") -> BaseModel:
    """A valid instance of any strict output model, filled with clearly-labelled placeholder values."""

    def value(annotation: Any, name: str) -> Any:
        origin = get_origin(annotation)
        if origin is Literal:
            return get_args(annotation)[0]
        if origin in (list, tuple, set):
            return []
        if origin is dict:
            return {}
        if origin is not None and type(None) in get_args(annotation):
            return None
        if isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return demo_instance(annotation, hint)
        if annotation is bool:
            return False
        if annotation is int:
            return 0
        if annotation is float:
            return 0.0
        if isinstance(annotation, type) and hasattr(annotation, "__members__"):   # Enum
            return list(annotation.__members__.values())[0]
        return f"[DEMO {name}] {hint}".strip()

    data = {n: value(f.annotation, n) for n, f in model.model_fields.items()}
    return model.model_validate(data)


class DemoProvider:
    """No LLM. Plays a fixed script that exercises the real tools and the whole app, so everything can be checked
    before a key is added. The lead researcher: gathers from memory, a regulator feed and NSE filings, then submits
    a Research Object built only from those tool results. Its text says clearly that it is not research."""

    name = "demo"

    def chat(self, model: str, system: str, messages: list[dict[str, Any]], tools: list[ToolSpec],
             max_tokens: int, role: str) -> ChatResult:
        names = {t.name for t in tools}
        question = [m["content"] for m in messages if m["role"] == "user"][-1:] or [""]
        question = question[0].split("QUESTION:\n", 1)[-1].strip()
        last_user = max((i for i, m in enumerate(messages) if m["role"] == "user" and not m["content"].startswith("[")),
                        default=0)
        tool_turns = [m for m in messages[last_user:] if m["role"] == "tool"]
        step = len(tool_turns)
        zero = Usage()
        if step == 0:
            calls = []
            if "memory_search" in names:
                calls.append({"id": "d1", "name": "memory_search", "args": {"query": question[:80], "limit": 5}})
            if "regulator_feed" in names:
                calls.append({"id": "d2", "name": "regulator_feed", "args": {"source": "rbi", "days": 30, "limit": 5}})
            if "nse_announcements" in names:
                calls.append({"id": "d3", "name": "nse_announcements", "args": {"limit": 5}})
            return ChatResult(text="DEMO: I will look in memory, the RBI feed and NSE filings.", tool_calls=calls,
                              native=None, usage=zero, model="demo", stop_reason="tool_use")
        # step >= 1: submit, using only counts/titles that appear in the tool results
        last_results = {r["name"]: r for m in tool_turns for r in m["results"]}
        counts = {}
        for name, r in last_results.items():
            try:
                counts[name] = int(json.loads(re.sub(r"^\[E\d+\]\s*", "", r["content"])).get("count", 0))
            except Exception:  # noqa: BLE001
                counts[name] = None
        rejected = any("rejected" in r["content"].lower() for r in tool_turns[-1]["results"]
                       if r["name"] == "submit_research")
        lines = [f"{n}: {c} records" for n, c in counts.items() if c is not None and not rejected]
        refs = [r["ref"] for m in tool_turns for r in m["results"] if r.get("ref")][:3]
        obj = {
            "title": f"DEMO walk-through: {question[:60]}",
            "question": question, "mode": "other",
            "executive_summary": ["DEMO provider: this is a scripted walk-through to test the app, not research.",
                                  *lines],
            "verdict": "not_applicable", "verdict_conditions": "",
            "sections": [{"heading": "What the tools returned", "body": "; ".join(lines) or "Tool calls completed.",
                          "evidence_refs": refs}],
            "claims": [], "risks": ["Demo output; add an LLM key for real research."], "data_limits": [],
            "what_would_change_view": [], "sources": [], "what_it_means_for_our_books": "Nothing: demo only.",
            "persona_views": [], "memory_updates": {"findings": [], "events": [], "structure_changes": []},
        }
        return ChatResult(text="DEMO: submitting the walk-through.",
                          tool_calls=[{"id": f"d{10 + step}", "name": "submit_research", "args": obj}],
                          native=None, usage=zero, model="demo", stop_reason="tool_use")

    def structured(self, model: str, system: str, user: str, output_model: type[BaseModel], max_tokens: int,
                   role: str) -> tuple[BaseModel, Usage, str]:
        return demo_instance(output_model, "demo provider - not real output"), Usage(), "demo"
