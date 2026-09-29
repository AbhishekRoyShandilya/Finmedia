"""Workspace tests: memory, provenance, the agent loop, providers, content gate, collectors, API and MCP.
No network and no paid calls: providers are scripted or mocked."""

from __future__ import annotations

import io
import json
import sys
from datetime import date, timedelta
from types import SimpleNamespace
from typing import Any

import httpx
import pytest

from finmedia import collectors, memory
from finmedia.agent import tools as agent_tools
from finmedia.agent.lead import RunControl, run_agent, sanitize_history
from finmedia.agent.objects import get_object, save_object
from finmedia.agent.provenance import check_object
from finmedia.ai import AI
from finmedia.ai.providers import (AnthropicProvider, ChatResult, OpenAICompatProvider, ToolSpec, demo_instance,
                                   inline_refs)
from finmedia.content import engine as content
from finmedia.costs import Usage
from finmedia.models import Document
from finmedia.sources.market import _nse_date, html_to_text

TODAY = date.today().isoformat()


def base_object(**over: Any) -> dict[str, Any]:
    obj = {
        "title": "Test object", "question": "q", "mode": "other", "executive_summary": ["Rate cut of 25 bps"],
        "verdict": "not_applicable", "verdict_conditions": "",
        "sections": [{"heading": "h", "body": "Repo rate cut by 25 basis points to 5.25 percent.", "evidence_refs": ["E1"]}],
        "claims": [], "persona_views": [], "risks": [], "what_would_change_view": [], "data_limits": [],
        "sources": [{"ref": "E1", "title": "RBI statement", "url": "https://rbi.org.in/x", "published_at": "", "primary": True}],
        "what_it_means_for_our_books": "", "memory_updates": {"events": [], "findings": [], "structure_changes": []},
    }
    obj.update(over)
    return obj


EVIDENCE = {"E1": {"tool": "fetch_document", "args": {"url": "https://rbi.org.in/x"},
                   "result": {"text": "The policy repo rate is reduced by 25 basis points to 5.25 per cent."}, "ok": True}}


# ------------------------------------------------------------------------------------------------ memory
def test_memory_point_in_time_and_supersede(store):
    old = memory.add_record(store, "finding", "ORB works on midcaps", tags=["setup:orb", "universe:midcap"],
                            known_at="2025-01-10T10:00:00", status="supported")
    memory.add_record(store, "finding", "ORB edge gone after 2025 costs", tags=["setup:orb"], supersedes=old,
                      known_at="2026-03-01T10:00:00", status="killed")
    # as of mid-2025 only the old finding was known
    past = memory.search(store, "ORB", asof="2025-06-30")
    assert [r["title"] for r in past] == ["ORB works on midcaps"]
    # today the correction supersedes it
    now_rows = memory.search(store, "ORB")
    assert [r["title"] for r in now_rows] == ["ORB edge gone after 2025 costs"]
    assert len(memory.search(store, "ORB", include_superseded=True)) == 2
    sim = memory.similar_by_tags(store, ["setup:orb", "universe:midcap"], asof="2025-06-30")
    assert sim and sim[0]["shared_tags"] == ["setup:orb", "universe:midcap"]
    with pytest.raises(ValueError):
        memory.add_record(store, "rumour", "x")


def test_documents_search_respects_asof(store):
    store.add_document(Document(source_id="sebi_rss", title="Circular on expiry rules", text="expiry",
                                category="regulator", published_at=date.today() - timedelta(days=3)))
    assert memory.search_documents(store, "expiry")
    assert memory.search_documents(store, "expiry", asof=(date.today() - timedelta(days=10)).isoformat()) == []


# ------------------------------------------------------------------------------------------------ provenance
def test_provenance_accepts_supported_and_rejects_fabricated():
    good = check_object(base_object(), EVIDENCE)
    assert good["ok"], good
    bad = check_object(base_object(executive_summary=["Rate cut of 50 bps, GDP 7.8"]), EVIDENCE)
    assert not bad["ok"]
    assert {u["number"] for u in bad["unsupported_numbers"]} == {"50", "7.8"}
    refs = check_object(base_object(sections=[{"heading": "h", "body": "no numbers", "evidence_refs": ["E9"]}]), EVIDENCE)
    assert refs["bad_refs"] == ["E9"]
    src = check_object(base_object(sources=[{"ref": "E1", "title": "t", "url": "https://made.up/doc", "published_at": "",
                                             "primary": True}]), EVIDENCE)
    assert src["unfetched_sources"] == ["https://made.up/doc"]


# ------------------------------------------------------------------------------------------------ agent loop
class ScriptProvider:
    """Plays a list of turns; each turn is a list of tool calls (or text only)."""

    name = "script"

    def __init__(self, turns: list[list[dict[str, Any]]]):
        self.turns = turns
        self.seen: list[list[dict[str, Any]]] = []

    def chat(self, model, system, messages, tools, max_tokens, role):
        self.seen.append([dict(m) for m in messages])
        calls = self.turns.pop(0) if self.turns else []
        return ChatResult(text="thinking out loud", tool_calls=calls, native=None, usage=Usage(1000, 200), model="claude-opus-5-5",
                          stop_reason="tool_use" if calls else "end_turn")

    def structured(self, model, system, user, output_model, max_tokens, role):
        return demo_instance(output_model), Usage(500, 100), "claude-opus-5-5"


def fake_tool(monkeypatch, name="regulator_feed", result=None):
    result = result or {"items": [{"title": "Repo rate reduced by 25 basis points to 5.25 per cent",
                                   "url": "https://rbi.org.in/x"}]}
    for t in agent_tools.registry():
        pass

    orig = agent_tools.registry

    def reg():
        out = orig()
        for t in out:
            if t.name == name:
                t.handler = lambda ctx, a: result
        return out
    monkeypatch.setattr(agent_tools, "registry", reg)


def test_agent_rejects_then_accepts_and_saves(store, cfg, monkeypatch):
    fake_tool(monkeypatch)
    bad = base_object(executive_summary=["Cut of 50 bps"])
    good = base_object()
    prov = ScriptProvider([
        [{"id": "c1", "name": "regulator_feed", "args": {"source": "rbi"}}],
        [{"id": "c2", "name": "submit_research", "args": bad}],
        [{"id": "c3", "name": "submit_research", "args": good}],
    ])
    ai = AI(store, cfg, provider=prov, provider_name="anthropic")
    thread_id = store.ex("INSERT INTO threads (title, created_at, updated_at) VALUES ('t', ?, ?)", (TODAY, TODAY))
    events = []
    out = run_agent(store, cfg, ai, question="What did RBI do?", thread_id=thread_id,
                    emit=lambda t, d: events.append((t, d)))
    assert out["status"] == "done", out["error"]
    types = [t for t, _ in events]
    assert types.count("provenance") == 2 and "object" in types
    first_prov = [d for t, d in events if t == "provenance"][0]
    assert not first_prov["ok"] and first_prov["unsupported_numbers"][0]["number"] == "50"
    ro = get_object(store, out["object"]["key"])
    assert ro["status"] == "final" and ro["version"] == 1
    # the rejection text reached the model
    assert "REJECTED by the provenance check" in json.dumps(prov.seen[-1])
    assert out["cost_inr"] > 0


def test_agent_steer_and_limits(store, cfg, monkeypatch):
    fake_tool(monkeypatch)
    cfg = {**cfg, "agent": {**cfg["agent"], "depth": {"quick": {"max_steps": 2, "budget_inr": 1000}}}}
    prov = ScriptProvider([[{"id": f"c{i}", "name": "regulator_feed", "args": {"source": "rbi"}}] for i in range(10)])
    ai = AI(store, cfg, provider=prov, provider_name="anthropic")
    control = RunControl()
    control.steer("focus on PSU banks")
    out = run_agent(store, cfg, ai, question="q", depth="quick", control=control)
    assert out["status"] == "failed" and "did not submit" in out["error"]
    blob = json.dumps(prov.seen)
    assert "[STEER] focus on PSU banks" in blob and "Stop researching" in blob


def test_agent_stop(store, cfg):
    prov = ScriptProvider([])
    ai = AI(store, cfg, provider=prov, provider_name="anthropic")
    control = RunControl()
    control.stop.set()
    out = run_agent(store, cfg, ai, question="q", control=control)
    assert out["status"] == "stopped"


def test_sanitize_history_fills_missing_results():
    msgs = [{"role": "user", "content": "q"},
            {"role": "assistant", "text": "", "tool_calls": [{"id": "a", "name": "x", "args": {}}], "native": None}]
    fixed = sanitize_history(msgs)
    assert fixed[-1]["role"] == "tool" and fixed[-1]["results"][0]["id"] == "a"


def test_object_versions_mark_content_stale_and_skip_memory_in_time_travel(store, cfg):
    tid = store.ex("INSERT INTO threads (title, created_at, updated_at) VALUES ('t', ?, ?)", (TODAY, TODAY))
    upd = {"events": [{"title": "Repo cut", "event_date": TODAY, "event_type": "policy", "stage": "happened",
                       "entities": ["RBI"], "mechanism_tags": ["channel:rates"], "summary": "cut", "evidence_refs": ["E1"]}],
           "findings": [], "structure_changes": []}
    s1 = save_object(store, base_object(memory_updates=upd), {"ok": True}, asof=TODAY, thread_id=tid, run_id=None, evidence=EVIDENCE)
    assert s1["memory_written"] == 1
    store.ex("""INSERT INTO content_items (object_key, object_version, kind, title, status, created_at, updated_at, json,
                lint_json) VALUES (?, 1, 'reel', 't', 'draft', ?, ?, '{}', '{}')""", (s1["key"], TODAY, TODAY))
    s2 = save_object(store, base_object(), {"ok": True}, asof="2024-01-01", thread_id=tid, run_id=None, evidence=EVIDENCE)
    assert s2["version"] == 2 and s2["memory_skipped_time_travel"]
    assert store.q1("SELECT status FROM content_items")["status"] == "stale"


# ------------------------------------------------------------------------------------------------ providers
class Block:
    def __init__(self, **kw):
        self.__dict__.update(kw)

    def model_dump(self, **_):
        return dict(self.__dict__)


def test_anthropic_provider_roundtrip():
    captured = {}

    def create(**kw):
        captured.update(kw)
        return SimpleNamespace(
            content=[Block(type="thinking", thinking="plan", signature="sig"), Block(type="text", text="Looking."),
                     Block(type="tool_use", id="tu1", name="memory_search", input={"query": "rbi"})],
            stop_reason="tool_use", model="claude-opus-5-5",
            usage=SimpleNamespace(input_tokens=10, output_tokens=5, cache_creation_input_tokens=0, cache_read_input_tokens=3))

    client = SimpleNamespace(messages=SimpleNamespace(create=create))
    p = AnthropicProvider(client=client)
    history = [{"role": "user", "content": "q"},
               {"role": "assistant", "text": "", "tool_calls": [{"id": "t0", "name": "x", "args": {}}],
                "native": [{"type": "tool_use", "id": "t0", "name": "x", "input": {}}]},
               {"role": "tool", "results": [{"id": "t0", "name": "x", "content": "[E1] {}", "is_error": False}]},
               {"role": "user", "content": "[STEER] narrower"}]
    res = p.chat("claude-opus-5-5", "sys", history, [ToolSpec("memory_search", "d", {"type": "object", "properties": {}})],
                 1000, "research_lead")
    assert res.tool_calls == [{"id": "tu1", "name": "memory_search", "args": {"query": "rbi"}}]
    assert res.thinking == "plan" and res.native[0]["signature"] == "sig"
    msgs = captured["messages"]
    # tool result and the steer are merged into ONE user turn after the assistant turn
    assert [m["role"] for m in msgs] == ["user", "assistant", "user"]
    assert msgs[2]["content"][0]["type"] == "tool_result" and msgs[2]["content"][1]["text"] == "[STEER] narrower"
    assert captured["thinking"] == {"type": "adaptive"} and captured["tools"][-1]["cache_control"]


def test_openai_compat_provider_with_mock_transport(monkeypatch):
    monkeypatch.setenv("OPENAI_COMPAT_API_KEY", "test-key")
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        seen["body"] = body
        seen["auth"] = request.headers.get("authorization")
        if body.get("tool_choice") == "auto":
            msg = {"role": "assistant", "content": None, "tool_calls": [
                {"id": "call_1", "type": "function", "function": {"name": "nse_results", "arguments": '{"symbol": "TCS"}'}}]}
            return httpx.Response(200, json={"model": "m", "choices": [{"message": msg, "finish_reason": "tool_calls"}],
                                             "usage": {"prompt_tokens": 12, "completion_tokens": 3}})
        args = json.dumps({"headline": "h", "points": [], "views": [], "risks": [], "missing_evidence": [],
                           "what_would_change_view": []})
        msg = {"role": "assistant", "tool_calls": [{"id": "c", "type": "function", "function": {"name": "answer", "arguments": args}}]}
        return httpx.Response(200, json={"model": "m", "choices": [{"message": msg, "finish_reason": "tool_calls"}], "usage": {}})

    p = OpenAICompatProvider("https://api.example.com/v1", http=httpx.Client(transport=httpx.MockTransport(handler)))
    res = p.chat("m", "sys", [{"role": "user", "content": "q"}],
                 [ToolSpec("nse_results", "d", {"type": "object", "properties": {"symbol": {"type": "string"}}})], 100, "r")
    assert res.tool_calls[0]["args"] == {"symbol": "TCS"} and res.stop_reason == "tool_use"
    assert seen["auth"] == "Bearer test-key" and seen["body"]["messages"][0]["role"] == "system"
    from finmedia.agent.models import PanelNote
    parsed, usage, _ = p.structured("m", "sys", "u", PanelNote, 100, "research_panel")
    assert parsed.headline == "h"
    assert "$defs" not in json.dumps(seen["body"]["tools"][0]["function"]["parameters"])


def test_inline_refs_removes_defs():
    from finmedia.agent.models import ResearchObject
    schema = inline_refs(ResearchObject.model_json_schema())
    assert "$ref" not in json.dumps(schema) and "$defs" not in schema


def test_ai_status_reports_missing_key(store, cfg, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr("finmedia.ai.get_key", lambda k: None)
    st = AI(store, cfg, provider_name="anthropic").status()
    assert not st["ready"] and "ANTHROPIC_API_KEY" in st["note"]
    assert AI(store, cfg, provider_name="demo").status()["ready"]


# ------------------------------------------------------------------------------------------------ content gate
def test_content_lint_and_signoff_gate(store, cfg):
    tid = store.ex("INSERT INTO threads (title, created_at, updated_at) VALUES ('t', ?, ?)", (TODAY, TODAY))
    claims = [{"target": "stock:HDFCBANK", "direction": "positive", "horizon": "3 months", "confidence": "medium",
               "rationale": "r", "evidence_refs": ["E1"]}]
    s = save_object(store, base_object(claims=claims), {"ok": True}, asof=TODAY, thread_id=tid, run_id=None, evidence=EVIDENCE)
    obj = get_object(store, s["key"])["object"]
    draft = {"subject": "RBI cut", "preheader": "p", "intro": "The repo rate fell 25 bps; we like HDFCBANK.",
             "sections": [{"heading": "h", "body": "It is now 5.25 percent, not 6.1."}], "takeaway": "t",
             "disclosure": "Research, not advice.", "sources": ["RBI"], "compliance_tier": "RA"}
    lint = content.lint_content("newsletter", draft, obj)
    assert not lint["passed"] and any("6.1" in e for e in lint["errors"])
    assert lint["needs_signoff"] and any("HDFCBANK" in c for c in lint["compliance_items"])

    item = content.generate(store, AI(store, cfg, provider_name="demo"), s["key"], "newsletter")
    assert item["status"] == "draft"
    assert "No sources listed" in item["lint"]["errors"]          # the demo draft lists no sources: blocked
    with pytest.raises(content.ContentError):
        content.approve(store, item["id"], "Asha", "editor")
    item = content.update_draft(store, item["id"], {**item["draft"], "sources": ["RBI statement"]})
    assert item["lint"]["passed"]
    # the research contains a directional view -> an editor alone cannot approve
    assert item["lint"]["needs_signoff"]
    after_editor = content.approve(store, item["id"], "Asha", "editor")
    assert after_editor["status"] == "draft"
    with pytest.raises(content.ContentError):
        content.mark_published(store, item["id"])
    signed = content.approve(store, item["id"], "Ravi", "compliance")
    assert signed["status"] == "approved"
    assert content.mark_published(store, item["id"], "https://youtube.com/x")["status"] == "published"


# ------------------------------------------------------------------------------------------------ collectors
def test_collector_success_and_failure_streak(store, monkeypatch):
    monkeypatch.setattr(collectors, "fetch_source", lambda s, inbox_dir=None: [
        Document(source_id=s["id"], title="A", text="x", category="news")])
    src = {"id": "newsy", "type": "rss", "url": "u", "enabled": True}
    assert collectors.run_source(store, src)["new"] == 1
    assert collectors.run_source(store, src)["new"] == 0          # duplicates are ignored

    def boom(s, inbox_dir=None):
        raise ConnectionError("down")
    monkeypatch.setattr(collectors, "fetch_source", boom)
    sent = []
    monkeypatch.setattr(collectors.notify, "send", lambda t: sent.append(t))
    for _ in range(3):
        collectors.run_source(store, src, alert_after=3)
    row = store.q1("SELECT * FROM collector_state WHERE source_id = 'newsy'")
    assert row["fail_streak"] == 3 and "down" in row["last_error"] and len(sent) == 1


def test_parsers():
    title, text = html_to_text("<html><head><title>T</title><script>x=1</script></head><body><p>Hello</p><p>World</p></body></html>")
    assert title == "T" and "Hello" in text and "x=1" not in text
    assert _nse_date("30-JUN-2026") == "2026-06-30" and _nse_date("-") is None


# ------------------------------------------------------------------------------------------------ API
def test_api_end_to_end_demo(store):
    from fastapi.testclient import TestClient
    from finmedia.server.app import create_app

    app = create_app(store=store, provider="demo", start_scheduler=False)
    c = TestClient(app)
    assert c.get("/api/status").json()["ai"]["ready"]
    r = c.post("/api/threads", json={"question": "Test question", "depth": "quick"})
    assert r.status_code == 200
    run_id = r.json()["run_id"]
    app.state.manager._threads[run_id].join(timeout=60)
    ev = c.get(f"/api/runs/{run_id}/events").json()
    assert ev["status"] == "done" and ev["events"][-1]["type"] == "done"
    key = c.get("/api/objects").json()[0]["key"]
    assert "Test question" in c.get(f"/api/objects/{key}/memo").text
    assert c.post("/api/threads", json={"question": "  "}).status_code == 400
    assert c.post("/api/threads", json={"question": "x", "asof": "31-12-2024"}).status_code == 400
    m = c.post("/api/memory", json={"kind": "structure_change", "title": "STT on futures raised", "tags": ["channel:costs"]})
    assert m.status_code == 200 and c.get("/api/memory/search?q=STT").json()[0]["title"] == "STT on futures raised"
    assert c.get("/api/scoreboard").json()["total_claims"] == 0


def test_api_token(store, monkeypatch):
    from fastapi.testclient import TestClient
    from finmedia.server.app import create_app

    monkeypatch.setenv("FINMEDIA_APP_TOKEN", "s3cret")
    c = TestClient(create_app(store=store, provider="demo", start_scheduler=False))
    assert c.get("/api/threads").status_code == 401
    assert c.get("/api/threads", headers={"Authorization": "Bearer s3cret"}).status_code == 200
    assert c.get("/api/threads?token=s3cret").status_code == 200


# ------------------------------------------------------------------------------------------------ MCP
def test_mcp_server_lists_and_calls_tools(monkeypatch, tmp_path):
    from finmedia import mcp_server

    monkeypatch.setattr(mcp_server, "path_setting", lambda k: tmp_path / "m.db")
    lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
             {"jsonrpc": "2.0", "method": "notifications/initialized"},
             {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
             {"jsonrpc": "2.0", "id": 3, "method": "tools/call", "params": {"name": "memory_search", "arguments": {"query": "x"}}}]
    monkeypatch.setattr(sys, "stdin", io.StringIO("\n".join(json.dumps(x) for x in lines) + "\n"))
    out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", out)
    mcp_server.serve()
    replies = [json.loads(x) for x in out.getvalue().splitlines()]
    assert replies[0]["result"]["serverInfo"]["name"] == "finmedia-research"
    names = {t["name"] for t in replies[1]["result"]["tools"]}
    assert "nse_results" in names and "consult_panel" not in names and "submit_research" not in names
    assert replies[2]["result"]["isError"] is False
