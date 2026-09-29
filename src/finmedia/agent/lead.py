"""The lead researcher: an agent loop over tools, steerable mid-run, that ends with a verified Research Object.

    plan -> tools (memory, primary sources, data, PTIS quant, panel, red team, playbooks) -> submit_research
    -> provenance check (one chance to fix) -> Research Object saved, claims logged, memory updated.

Hard limits per run: steps (depth preset), rupees (depth preset), and the monthly research cap (BudgetGuard).
"""

from __future__ import annotations

import json
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from typing import Any, Callable

from pydantic import ValidationError

from .. import memory
from ..ai import AI
from ..ai.providers import ProviderError
from ..config import project_root
from ..costs import BudgetExceeded
from ..store import Store
from ..tools.ptis import PtisBridge
from .models import ResearchObject
from .objects import save_object
from .provenance import check_object, problems_text
from .tools import SUBMIT, ToolContext, available, execute, submit_spec


class RunControl:
    """Founder's controls for a running research: steer messages and stop."""

    def __init__(self) -> None:
        self._steer: list[str] = []
        self._lock = threading.Lock()
        self.stop = threading.Event()

    def steer(self, text: str) -> None:
        with self._lock:
            self._steer.append(text)

    def drain(self) -> list[str]:
        with self._lock:
            out, self._steer = self._steer, []
            return out


def _system(cfg: dict[str, Any], asof: str, depth: str, limits: dict[str, Any], off: list[dict[str, str]],
            mem_counts: dict[str, int]) -> str:
    base = (project_root() / "prompts" / "agent" / "lead.md").read_text(encoding="utf-8")
    today = date.today().isoformat()
    mode = ("LIVE research: the report date is today." if asof >= today else
            f"TIME-TRAVEL research: write as of {asof}. Tools hide later data; ignore anything you know after it.")
    offline = "; ".join(f"{o['tool']} ({o['why']})" for o in off) or "none"
    return (base + f"\n\n## This run\n- Today: {today}. Report date (asof): {asof}. {mode}\n"
            f"- Depth: {depth} - at most {limits['max_steps']} tool-using steps and about Rs {limits['budget_inr']}.\n"
            f"- Tools not available now: {offline}.\n"
            f"- Research memory holds: {json.dumps(mem_counts)}.\n")


def sanitize_history(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Make an interrupted conversation valid again: every tool call must be followed by its result."""
    out = list(messages)
    for i, m in enumerate(out):
        if m["role"] == "assistant" and m.get("tool_calls"):
            nxt = out[i + 1] if i + 1 < len(out) else None
            have = {r["id"] for r in (nxt or {}).get("results", [])} if nxt and nxt["role"] == "tool" else set()
            missing = [c for c in m["tool_calls"] if c["id"] not in have]
            if missing:
                filler = [{"id": c["id"], "name": c["name"], "ref": "", "is_error": True,
                           "content": "Interrupted: this call did not complete."} for c in missing]
                if nxt and nxt["role"] == "tool":
                    nxt["results"] = nxt["results"] + filler
                else:
                    out.insert(i + 1, {"role": "tool", "results": filler})
    return out


def _content(ref: str, result: Any, limit: int) -> str:
    body = json.dumps(result, ensure_ascii=False, default=str)
    if len(body) > limit:
        body = body[:limit] + f' ... [truncated: {len(body)} chars in full; ask for fewer rows, a narrower range or an offset]'
    return f"[{ref}] {body}"


def run_agent(store: Store, cfg: dict[str, Any], ai: AI, *, question: str, asof: str | None = None,
              depth: str = "standard", thread_id: int | None = None, run_id: int | None = None,
              history: list[dict[str, Any]] | None = None, prior_evidence: dict[str, dict[str, Any]] | None = None,
              prior_object: dict[str, Any] | None = None, control: RunControl | None = None,
              emit: Callable[[str, dict[str, Any]], None] = lambda t, d: None,
              bridge: PtisBridge | None = None) -> dict[str, Any]:
    asof = asof or date.today().isoformat()
    control = control or RunControl()
    limits = cfg["agent"]["depth"].get(depth) or cfg["agent"]["depth"]["standard"]
    max_steps, budget = int(limits["max_steps"]), float(limits["budget_inr"])
    result_chars = int(cfg["agent"].get("tool_result_chars", 6000))

    ctx = ToolContext(store=store, cfg=cfg, asof=asof, ai=ai, bridge=bridge or PtisBridge(timeout=120),
                      question=question, run_id=run_id, emit=emit)
    if prior_evidence:
        ctx.evidence.update(prior_evidence)
        ctx.seed_refs(max((int(r[1:]) for r in prior_evidence if r[1:].isdigit()), default=0))
    bridge_ok = PtisBridge(base=ctx.bridge.base, timeout=3).reachable()
    tools, off = available(ctx, bridge_ok)
    by_name = {t.name: t for t in tools}
    specs = [t.spec() for t in tools] + [submit_spec()]
    system = _system(cfg, asof, depth, limits, off, memory.counts(store))
    emit("status", {"state": "running", "asof": asof, "depth": depth, "max_steps": max_steps, "budget_inr": budget,
                    "tools": [t.name for t in tools], "tools_off": off, "provider": ai.name})

    first = f"Report date (asof): {asof}\n\nQUESTION:\n{question}"
    if prior_object:
        shown = ("It is your last submission above." if history else
                 "It is below.\n\n" + json.dumps(prior_object["object"], ensure_ascii=False))
        first = (f"FOLLOW-UP on Research Object {prior_object['key']} v{prior_object['version']}. {shown}\n"
                 "Answer the new question and submit a REVISED complete object (it becomes the next version).\n\n"
                 + first)
    messages: list[dict[str, Any]] = sanitize_history(list(history or [])) + [{"role": "user", "content": first}]
    extra_texts = [question] + ([json.dumps(prior_object["object"], ensure_ascii=False)] if prior_object else [])

    saved: dict[str, Any] | None = None
    status, error = "running", None
    submit_attempts, nudges, forced = 0, 0, False
    step = 0
    try:
        while True:
            if control.stop.is_set():
                status = "stopped"
                break
            for s in control.drain():
                messages.append({"role": "user", "content": f"[STEER] {s}"})
                emit("steer", {"text": s})
            over_budget = ctx.cost_inr >= budget
            if step >= max_steps or over_budget:
                if forced:
                    status, error = "failed", "limit reached and the researcher did not submit"
                    break
                forced = True
                why = "the rupee budget for this run is used up" if over_budget else "the step limit is reached"
                messages.append({"role": "user", "content": f"[SYSTEM] Stop researching: {why}. Call submit_research "
                                                            "NOW with what you have; list the gaps in data_limits."})
                emit("warning", {"text": f"Limit reached ({why}); asking for submission."})
            elif step == max_steps - 3 or (ctx.cost_inr >= 0.8 * budget and not forced):
                messages.append({"role": "user", "content": "[SYSTEM] Nearly out of steps/budget: wrap up and submit soon."})

            res, inr = ai.chat("research_lead", system, messages, specs)
            ctx.add_cost(inr)
            step += 1
            messages.append({"role": "assistant", "text": res.text, "tool_calls": res.tool_calls, "native": res.native})
            emit("assistant", {"step": step, "text": res.text, "thinking": (res.thinking or "")[:3000],
                               "tool_calls": [{"name": c["name"], "args": ({} if c["name"] == SUBMIT else c["args"])}
                                              for c in res.tool_calls], "cost_inr": round(ctx.cost_inr, 2)})
            if not res.tool_calls:
                nudges += 1
                if nudges > 2:
                    status, error = "failed", "the researcher stopped without submitting a Research Object"
                    break
                messages.append({"role": "user", "content": "[SYSTEM] Continue with tools, or call submit_research to finish."
                                 + (" Your last answer was cut off (max tokens): continue." if res.stop_reason == "max_tokens" else "")})
                continue

            results: list[dict[str, Any]] = []
            normal = [c for c in res.tool_calls if c["name"] != SUBMIT]
            submits = [c for c in res.tool_calls if c["name"] == SUBMIT]

            def run_one(call: dict[str, Any]) -> dict[str, Any]:
                tool = by_name.get(call["name"])
                emit("tool_call", {"id": call["id"], "name": call["name"], "args": call["args"]})
                if tool is None:
                    ref = ctx.next_ref()
                    out = {"error": f"unknown or unavailable tool {call['name']!r}"}
                    ctx.evidence[ref] = {"tool": call["name"], "args": call["args"], "result": out, "ok": False}
                    ok = False
                else:
                    ref, ok, out = execute(ctx, tool, call["args"])
                preview = json.dumps(out, ensure_ascii=False, default=str)
                emit("tool_result", {"id": call["id"], "ref": ref, "name": call["name"], "ok": ok,
                                     "count": out.get("count") if isinstance(out, dict) else None,
                                     "chars": len(preview), "preview": preview[:1500]})
                return {"id": call["id"], "name": call["name"], "ref": ref, "content": _content(ref, out, result_chars),
                        "is_error": not ok}

            if normal:
                with ThreadPoolExecutor(max_workers=int(cfg["agent"].get("parallel_tools", 4))) as ex:
                    results += list(ex.map(run_one, normal))

            for call in submits:
                if saved:
                    results.append({"id": call["id"], "name": SUBMIT, "ref": "", "is_error": False,
                                    "content": "Ignored: an object was already accepted in this turn."})
                    continue
                try:
                    obj = ResearchObject.model_validate(call["args"]).model_dump()
                except ValidationError as exc:
                    msg = "REJECTED: the object does not match the schema: " + "; ".join(
                        f"{'.'.join(str(p) for p in e['loc'])}: {e['msg']}" for e in exc.errors()[:15])
                    results.append({"id": call["id"], "name": SUBMIT, "ref": "", "content": msg, "is_error": True})
                    emit("warning", {"text": msg[:500]})
                    continue
                check = check_object(obj, ctx.evidence, extra_texts)
                if not check["ok"] and submit_attempts == 0:
                    submit_attempts += 1
                    msg = "REJECTED by the provenance check. Fix and submit again:\n" + problems_text(check)
                    results.append({"id": call["id"], "name": SUBMIT, "ref": "", "content": msg, "is_error": True})
                    emit("provenance", {"ok": False, "attempt": 1, **{k: check[k] for k in (
                        "numbers_checked", "unsupported_numbers", "bad_refs", "unfetched_sources")}})
                    continue
                check["attempts"] = submit_attempts + 1
                saved = save_object(store, obj, check, asof=asof, thread_id=thread_id, run_id=run_id,
                                    evidence=ctx.evidence)
                emit("provenance", {"ok": check["ok"], "attempt": submit_attempts + 1,
                                    **{k: check[k] for k in ("numbers_checked", "unsupported_numbers", "bad_refs",
                                                             "unfetched_sources", "directional_claims",
                                                             "stock_level_claims")}})
                emit("object", {"key": saved["key"], "version": saved["version"], "status": saved["status"],
                                "title": obj["title"], "claims": saved["claims"], "memory_written": saved["memory_written"]})
                results.append({"id": call["id"], "name": SUBMIT, "ref": "",
                                "content": f"Accepted as {saved['key']} v{saved['version']} ({saved['status']}).",
                                "is_error": False})

            messages.append({"role": "tool", "results": results})
            if saved:
                status = "done"
                break
    except BudgetExceeded as exc:
        status, error = "failed", f"monthly budget: {exc}"
    except ProviderError as exc:
        status, error = "failed", f"LLM provider: {exc}"
    except Exception as exc:  # noqa: BLE001
        status, error = "failed", f"{type(exc).__name__}: {exc}"

    emit(status, {"error": error, "cost_inr": round(ctx.cost_inr, 2), "steps": step,
                  "object": {"key": saved["key"], "version": saved["version"]} if saved else None})
    return {"status": status, "error": error, "cost_inr": ctx.cost_inr, "steps": step, "messages": messages,
            "evidence": ctx.evidence, "object": saved}
