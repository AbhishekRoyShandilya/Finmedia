"""Run manager: conversations (threads) of research runs executed in background threads, with a live event stream
(persisted, so a page opened later replays everything), steering and stop."""

from __future__ import annotations

import json
import queue
import threading
from datetime import date
from typing import Any, Callable

from . import notify
from .agent.lead import RunControl, run_agent
from .agent.objects import get_object
from .ai import AI
from .store import Store, now


class EventBus:
    def __init__(self, store: Store):
        self.store = store
        self._subs: dict[int, list[queue.Queue]] = {}
        self._seq: dict[int, int] = {}
        self._lock = threading.Lock()

    def publish(self, run_id: int, etype: str, data: dict[str, Any]) -> None:
        with self._lock:
            if run_id not in self._seq:
                row = self.store.q1("SELECT MAX(seq) AS s FROM run_events WHERE run_id = ?", (run_id,))
                self._seq[run_id] = int(row["s"] or 0)
            self._seq[run_id] += 1
            seq = self._seq[run_id]
            subs = list(self._subs.get(run_id, []))
        ev = {"seq": seq, "ts": now(), "type": etype, "data": data}
        self.store.ex("INSERT INTO run_events (run_id, seq, ts, type, data_json) VALUES (?, ?, ?, ?, ?)",
                      (run_id, seq, ev["ts"], etype, json.dumps(data, ensure_ascii=False, default=str)))
        for q in subs:
            q.put(ev)

    def subscribe(self, run_id: int) -> queue.Queue:
        q: queue.Queue = queue.Queue()
        with self._lock:
            self._subs.setdefault(run_id, []).append(q)
        return q

    def unsubscribe(self, run_id: int, q: queue.Queue) -> None:
        with self._lock:
            if q in self._subs.get(run_id, []):
                self._subs[run_id].remove(q)

    def history(self, run_id: int, after: int = 0) -> list[dict[str, Any]]:
        return [{"seq": r["seq"], "ts": r["ts"], "type": r["type"], "data": json.loads(r["data_json"])}
                for r in self.store.q("SELECT * FROM run_events WHERE run_id = ? AND seq > ? ORDER BY seq", (run_id, after))]


TERMINAL = {"done", "failed", "stopped"}


class RunManager:
    def __init__(self, store: Store, cfg: dict[str, Any], ai_factory: Callable[[], AI]):
        self.store = store
        self.cfg = cfg
        self.ai_factory = ai_factory
        self.bus = EventBus(store)
        self.controls: dict[int, RunControl] = {}
        self._threads: dict[int, threading.Thread] = {}

    # ---------------------------------------------------------------- lifecycle
    def recover(self) -> int:
        """Runs left 'running' by a previous server process can never finish: mark them failed."""
        rows = self.store.q("SELECT id FROM runs WHERE status IN ('queued', 'running')")
        for r in rows:
            self.store.ex("UPDATE runs SET status = 'failed', error = 'server restarted during the run', finished_at = ? "
                          "WHERE id = ?", (now(), r["id"]))
        return len(rows)

    def create_thread(self, title: str, asof: str | None = None) -> int:
        return self.store.ex("INSERT INTO threads (title, created_at, updated_at, asof) VALUES (?, ?, ?, ?)",
                             (title[:120] or "Untitled", now(), now(), asof))

    def start_research(self, question: str, *, thread_id: int | None = None, asof: str | None = None,
                       depth: str = "standard", wait: bool = False) -> dict[str, Any]:
        question = question.strip()
        if not question:
            raise ValueError("empty question")
        if depth not in self.cfg["agent"]["depth"]:
            raise ValueError(f"depth must be one of {list(self.cfg['agent']['depth'])}")
        ai = self.ai_factory()
        st = ai.status()
        if not st["ready"]:
            raise RuntimeError(st["note"] or "LLM provider is not configured")
        if thread_id is None:
            thread_id = self.create_thread(question, asof)
        thread = self.store.q1("SELECT * FROM threads WHERE id = ?", (thread_id,))
        if thread is None:
            raise ValueError(f"no conversation {thread_id}")
        busy = self.store.q1("SELECT id FROM runs WHERE thread_id = ? AND status IN ('queued','running')", (thread_id,))
        if busy:
            raise RuntimeError(f"run {busy['id']} is still working in this conversation; steer or stop it first")
        asof = asof or thread["asof"] or date.today().isoformat()

        prev = self.store.q1("SELECT * FROM runs WHERE thread_id = ? AND kind = 'research' ORDER BY id DESC LIMIT 1",
                             (thread_id,))
        history = json.loads(prev["messages_json"]) if prev else []
        prior_evidence: dict[str, Any] = {}
        for r in self.store.q("SELECT tool_log_json FROM runs WHERE thread_id = ? AND kind = 'research' ORDER BY id",
                              (thread_id,)):
            prior_evidence.update(json.loads(r["tool_log_json"] or "{}") or {})
        prior_object = get_object(self.store, thread["object_key"]) if thread["object_key"] else None

        run_id = self.store.ex("""INSERT INTO runs (thread_id, kind, question, status, depth, asof, started_at)
                                  VALUES (?, 'research', ?, 'running', ?, ?, ?)""",
                               (thread_id, question, depth, asof, now()))
        self.store.ex("UPDATE threads SET updated_at = ? WHERE id = ?", (now(), thread_id))
        control = RunControl()
        self.controls[run_id] = control
        self.bus.publish(run_id, "question", {"text": question, "asof": asof, "depth": depth})

        def work() -> None:
            try:
                out = run_agent(self.store, self.cfg, ai, question=question, asof=asof, depth=depth,
                                thread_id=thread_id, run_id=run_id, history=history, prior_evidence=prior_evidence,
                                prior_object=prior_object, control=control,
                                emit=lambda t, d: self.bus.publish(run_id, t, d))
            except Exception as exc:  # noqa: BLE001 - never leave a run hanging
                out = {"status": "failed", "error": f"{type(exc).__name__}: {exc}", "cost_inr": 0, "messages": history,
                       "evidence": {}, "object": None}
                self.bus.publish(run_id, "failed", {"error": out["error"]})
            self.store.ex("""UPDATE runs SET status = ?, finished_at = ?, cost_inr = ?, error = ?, messages_json = ?,
                             tool_log_json = ?, result_json = ? WHERE id = ?""",
                          (out["status"], now(), float(out.get("cost_inr") or 0), out.get("error"),
                           json.dumps(out["messages"], ensure_ascii=False, default=str),
                           json.dumps(out["evidence"], ensure_ascii=False, default=str),
                           json.dumps({"object": out.get("object"), "steps": out.get("steps")}, default=str), run_id))
            self.store.ex("UPDATE threads SET updated_at = ? WHERE id = ?", (now(), thread_id))
            self.controls.pop(run_id, None)
            obj = out.get("object")
            notify.send(f"Finmedia research {out['status']}: {question[:80]}"
                        + (f"\nObject {obj['key']} v{obj['version']} ({obj['status']})" if obj else "")
                        + (f"\nError: {out['error']}" if out.get("error") else "")
                        + f"\nCost Rs {float(out.get('cost_inr') or 0):.0f}")

        t = threading.Thread(target=work, name=f"run-{run_id}", daemon=True)
        self._threads[run_id] = t
        t.start()
        if wait:
            t.join()
        return {"thread_id": thread_id, "run_id": run_id}

    def start_playbook(self, topic: str, asof: str, sectors: list[str] | None = None) -> dict[str, Any]:
        """The milestone-1 budget / policy sector study as a tracked run (no agent loop)."""
        from .agent.tools import ToolContext, t_run_budget_study

        ai = self.ai_factory()
        if not ai.status()["ready"]:
            raise RuntimeError(ai.status()["note"])
        thread_id = self.create_thread(f"Budget study: {topic}", asof)
        run_id = self.store.ex("""INSERT INTO runs (thread_id, kind, question, status, asof, started_at)
                                  VALUES (?, 'playbook', ?, 'running', ?, ?)""", (thread_id, topic, asof, now()))
        self.bus.publish(run_id, "question", {"text": f"Budget / policy sector study: {topic}", "asof": asof})
        self.bus.publish(run_id, "status", {"state": "running", "asof": asof, "playbook": "budget_study"})
        control = RunControl()
        self.controls[run_id] = control

        def work() -> None:
            ctx = ToolContext(store=self.store, cfg=self.cfg, asof=asof, ai=ai, question=topic)
            try:
                out = t_run_budget_study(ctx, {"topic": topic, "sectors": sectors or []})
                status, err = "done", None
                self.bus.publish(run_id, "playbook_result", out)
            except Exception as exc:  # noqa: BLE001
                out, status, err = None, "failed", f"{type(exc).__name__}: {exc}"
            self.bus.publish(run_id, status, {"error": err, "cost_inr": round(ctx.cost_inr, 2)})
            self.store.ex("UPDATE runs SET status = ?, finished_at = ?, cost_inr = ?, error = ?, result_json = ? WHERE id = ?",
                          (status, now(), ctx.cost_inr, err, json.dumps(out, ensure_ascii=False, default=str), run_id))
            self.controls.pop(run_id, None)

        threading.Thread(target=work, name=f"playbook-{run_id}", daemon=True).start()
        return {"thread_id": thread_id, "run_id": run_id}

    def steer(self, run_id: int, text: str) -> None:
        c = self.controls.get(run_id)
        if c is None:
            raise RuntimeError("that run is not running")
        c.steer(text.strip())

    def stop(self, run_id: int) -> None:
        c = self.controls.get(run_id)
        if c is None:
            raise RuntimeError("that run is not running")
        c.stop.set()

    def is_active(self, run_id: int) -> bool:
        return run_id in self.controls

    # ---------------------------------------------------------------- queries
    def list_threads(self, limit: int = 100) -> list[dict[str, Any]]:
        rows = self.store.q("""SELECT t.*, (SELECT status FROM runs r WHERE r.thread_id = t.id ORDER BY r.id DESC LIMIT 1) AS last_status,
                               (SELECT COALESCE(SUM(cost_inr), 0) FROM runs r WHERE r.thread_id = t.id) AS cost_inr,
                               (SELECT COUNT(*) FROM runs r WHERE r.thread_id = t.id) AS n_runs
                               FROM threads t ORDER BY t.updated_at DESC LIMIT ?""", (limit,))
        return [dict(r) for r in rows]

    def get_thread(self, thread_id: int) -> dict[str, Any] | None:
        t = self.store.q1("SELECT * FROM threads WHERE id = ?", (thread_id,))
        if t is None:
            return None
        runs = [dict(r) for r in self.store.q(
            "SELECT id, kind, question, status, depth, asof, started_at, finished_at, cost_inr, error, result_json "
            "FROM runs WHERE thread_id = ? ORDER BY id", (thread_id,))]
        for r in runs:
            r["result"] = json.loads(r.pop("result_json") or "null")
            r["active"] = self.is_active(r["id"])
        obj = get_object(self.store, t["object_key"]) if t["object_key"] else None
        return {**dict(t), "runs": runs, "object": obj}

    def delete_thread(self, thread_id: int) -> None:
        if self.store.q1("SELECT id FROM runs WHERE thread_id = ? AND status = 'running'", (thread_id,)):
            raise RuntimeError("stop the running research first")
        with self.store.tx() as c:
            ids = [r["id"] for r in c.execute("SELECT id FROM runs WHERE thread_id = ?", (thread_id,))]
            for rid in ids:
                c.execute("DELETE FROM run_events WHERE run_id = ?", (rid,))
            c.execute("DELETE FROM runs WHERE thread_id = ?", (thread_id,))
            c.execute("DELETE FROM threads WHERE id = ?", (thread_id,))
        # Research Objects, claims and memory records are kept: they are the firm's record.
