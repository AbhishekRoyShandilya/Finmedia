"""Minimal MCP server (stdio, JSON-RPC 2.0) exposing the research tools to Claude Code / Claude Desktop.

Add to a project's .mcp.json:
    {"mcpServers": {"finmedia": {"command": "<path>/.venv/Scripts/finmedia.exe", "args": ["mcp"]}}}

Only data tools are exposed (memory, primary sources, data, PTIS quant, calculators). Paid LLM tools (panel, red
team, playbooks) stay inside the web app's research runs, where the budget guard and provenance check apply.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from typing import Any

from .agent.tools import ToolContext, execute, registry
from .config import path_setting, settings
from .env import get_key, load_env
from .store import Store

PROTOCOL = "2025-06-18"
EXCLUDED_GROUPS = {"analysis", "playbook"}


def _tools() -> dict[str, Any]:
    out = {}
    for t in registry():
        if t.group in EXCLUDED_GROUPS:
            continue
        if t.needs_key and not any(get_key(k) for k in t.needs_key):
            continue
        out[t.name] = t
    return out


def serve() -> None:
    load_env()
    cfg = settings()
    store = Store(path_setting("db_path"))
    tools = _tools()
    ctx = ToolContext(store=store, cfg=cfg, asof=date.today().isoformat())

    def reply(msg_id: Any, result: Any = None, error: dict[str, Any] | None = None) -> None:
        msg: dict[str, Any] = {"jsonrpc": "2.0", "id": msg_id}
        if error is not None:
            msg["error"] = error
        else:
            msg["result"] = result
        sys.stdout.write(json.dumps(msg, ensure_ascii=False) + "\n")
        sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        method, msg_id, params = req.get("method"), req.get("id"), req.get("params") or {}
        if msg_id is None:            # notification (e.g. notifications/initialized)
            continue
        if method == "initialize":
            reply(msg_id, {"protocolVersion": params.get("protocolVersion") or PROTOCOL,
                           "capabilities": {"tools": {"listChanged": False}},
                           "serverInfo": {"name": "finmedia-research", "version": "0.2.0"},
                           "instructions": "Indian-markets research tools: research memory (point-in-time), NSE filings "
                                           "and results, RBI/SEBI/PIB/Fed releases, official documents, macro data and "
                                           "PTIS quant history. Primary sources first; news is secondary."})
        elif method == "ping":
            reply(msg_id, {})
        elif method == "tools/list":
            reply(msg_id, {"tools": [{"name": t.name, "description": t.description,
                                      "inputSchema": t.spec().schema} for t in tools.values()]})
        elif method == "tools/call":
            tool = tools.get(params.get("name", ""))
            if tool is None:
                reply(msg_id, error={"code": -32602, "message": f"unknown tool {params.get('name')!r}"})
                continue
            args = dict(params.get("arguments") or {})
            ctx.asof = args.pop("asof", None) or date.today().isoformat()
            ref, ok, out = execute(ctx, tool, args)
            reply(msg_id, {"content": [{"type": "text", "text": f"[{ref}] " + json.dumps(out, ensure_ascii=False, default=str)}],
                           "isError": not ok})
        else:
            reply(msg_id, error={"code": -32601, "message": f"method {method!r} not supported"})
