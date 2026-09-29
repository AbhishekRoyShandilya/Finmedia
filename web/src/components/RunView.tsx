import { useEffect, useMemo, useRef, useState } from "react";
import { api, withToken } from "../api";
import type { ResearchObject, RunEvent, RunInfo } from "../types";
import { Busy, inr } from "../ui";
import ObjectCard from "./ObjectCard";

const TYPES = ["question", "status", "assistant", "tool_call", "tool_result", "steer", "warning", "provenance",
  "object", "done", "failed", "stopped", "playbook_result"];
const TERMINAL = new Set(["done", "failed", "stopped"]);

function short(v: unknown, n = 140): string {
  const s = typeof v === "string" ? v : JSON.stringify(v);
  return s.length > n ? s.slice(0, n) + "…" : s;
}

function pretty(s: string): string {
  try {
    return JSON.stringify(JSON.parse(s), null, 1);
  } catch {
    return s;
  }
}

function ObjectLoader({ objKey, version, aiReady }: { objKey: string; version: number; aiReady: boolean }) {
  const [ro, setRo] = useState<ResearchObject | null>(null);
  const [err, setErr] = useState("");
  useEffect(() => {
    api.get<ResearchObject>(`/api/objects/${objKey}?version=${version}`).then(setRo, (e) => setErr(e.message));
  }, [objKey, version]);
  if (err) return <div className="banner bad">{err}</div>;
  if (!ro) return <Busy label="Loading the Research Object…" />;
  return <ObjectCard ro={ro} compact aiReady={aiReady} />;
}

export default function RunView({ run, onFinished, aiReady }: { run: RunInfo; onFinished: () => void; aiReady: boolean }) {
  const [events, setEvents] = useState<RunEvent[]>([]);
  const [live, setLive] = useState(run.active);
  const seen = useRef<Set<number>>(new Set());
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    seen.current = new Set();
    setEvents([]);
    let es: EventSource | null = null;
    let closed = false;
    const add = (ev: RunEvent) => {
      if (seen.current.has(ev.seq)) return;
      seen.current.add(ev.seq);
      setEvents((prev) => [...prev, ev]);
      if (TERMINAL.has(ev.type)) {
        setLive(false);
        es?.close();
        if (!closed) onFinished();
      }
    };
    if (run.active) {
      es = new EventSource(withToken(`/api/runs/${run.id}/stream`));
      TYPES.forEach((t) => es!.addEventListener(t, (m) => add(JSON.parse((m as MessageEvent).data))));
      es.onerror = () => {
        // stream dropped: fall back to the stored log
        api.get<{ events: RunEvent[]; active: boolean }>(`/api/runs/${run.id}/events`).then((r) => {
          r.events.forEach(add);
          if (!r.active) {
            setLive(false);
            es?.close();
          }
        });
      };
    } else {
      api.get<{ events: RunEvent[] }>(`/api/runs/${run.id}/events`).then((r) => r.events.forEach(add));
    }
    return () => {
      closed = true;
      es?.close();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [run.id]);

  useEffect(() => {
    if (live) endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [events.length, live]);

  const results = useMemo(() => {
    const m: Record<string, RunEvent> = {};
    events.forEach((e) => { if (e.type === "tool_result") m[e.data.id] = e; });
    return m;
  }, [events]);

  const lastCost = [...events].reverse().find((e) => e.data && typeof e.data.cost_inr === "number")?.data.cost_inr;

  return (
    <div className="timeline">
      {events.map((e) => {
        const d = e.data;
        switch (e.type) {
          case "question":
            return (
              <div key={e.seq} className="bubble">
                {d.text}
                <div className="tiny" style={{ opacity: 0.8, marginTop: 4 }}>as of {d.asof}{d.depth ? ` · ${d.depth}` : ""}</div>
              </div>
            );
          case "steer":
            return <div key={e.seq} className="steerb">↪ Steer: {d.text}</div>;
          case "status":
            return (
              <div key={e.seq} className="small muted">
                Research started with {d.provider || "the playbook"}{d.max_steps ? ` · up to ${d.max_steps} steps / ${inr(d.budget_inr)}` : ""}
                {d.tools_off && d.tools_off.length > 0 && (
                  <span title={d.tools_off.map((o: { tool: string; why: string }) => `${o.tool}: ${o.why}`).join("\n")}>
                    {" "}· {d.tools_off.length} tool(s) unavailable
                  </span>
                )}
              </div>
            );
          case "assistant":
            return (
              <div key={e.seq} className="step">
                {d.thinking && (
                  <details><summary className="tiny faint">reasoning</summary><div className="thinking">{d.thinking}</div></details>
                )}
                {d.text && <div className="say">{d.text}</div>}
              </div>
            );
          case "tool_call": {
            const r = results[d.id];
            const ok = r ? r.data.ok : undefined;
            return (
              <details key={e.seq} className="tool" style={{ marginLeft: 14 }}>
                <summary>
                  <span className={`dot ${r === undefined ? "run" : ok ? "ok" : "bad"}`} />
                  <b className="mono">{d.name}</b>
                  <span className="faint mono">{short(d.args, 110)}</span>
                  {r && <span className="pill">{r.data.ref}{typeof r.data.count === "number" ? ` · ${r.data.count} rows` : ""}</span>}
                </summary>
                {r ? <pre>{pretty(r.data.preview)}{r.data.chars > 1500 ? `\n… (${r.data.chars} chars in full)` : ""}</pre> : <pre>working…</pre>}
              </details>
            );
          }
          case "warning":
            return <div key={e.seq} className="banner warn small">{d.text}</div>;
          case "provenance":
            return d.ok ? (
              <div key={e.seq} className="small" style={{ color: "var(--pos)" }}>✓ Provenance check passed: {d.numbers_checked} numbers traced to tool results.</div>
            ) : (
              <div key={e.seq} className="banner warn small">
                Provenance check {d.attempt === 1 ? "rejected the draft (one revision allowed)" : "still found problems: saved as FLAGGED"}:{" "}
                {d.unsupported_numbers?.length || 0} unsupported number(s){d.bad_refs?.length ? `, bad refs ${d.bad_refs.join(", ")}` : ""}
                {d.unfetched_sources?.length ? `, ${d.unfetched_sources.length} unfetched source(s)` : ""}.
              </div>
            );
          case "object":
            return <ObjectLoader key={e.seq} objKey={d.key} version={d.version} aiReady={aiReady} />;
          case "playbook_result":
            return (
              <div key={e.seq} className="card">
                <span className="eyebrow">Budget study result</span>
                <h3>{d.cio?.title}</h3>
                <p>{d.cio?.summary}</p>
                <div className="row">
                  {d.report_paths?.internal && <a className="btn sm" href={withToken(`/api/files?path=${encodeURIComponent(d.report_paths.internal)}`)} target="_blank" rel="noreferrer">Internal report</a>}
                  {d.report_paths?.public && <a className="btn sm" href={withToken(`/api/files?path=${encodeURIComponent(d.report_paths.public)}`)} target="_blank" rel="noreferrer">Public draft</a>}
                </div>
              </div>
            );
          case "done":
          case "failed":
          case "stopped":
            return (
              <div key={e.seq} className={`small ${e.type === "failed" ? "" : "muted"}`} style={e.type === "failed" ? { color: "var(--neg)" } : {}}>
                {e.type === "done" ? "Finished" : e.type === "stopped" ? "Stopped by you" : "Failed"}
                {d.steps ? ` after ${d.steps} steps` : ""} · cost {inr(d.cost_inr)}{d.error ? ` · ${d.error}` : ""}
              </div>
            );
          default:
            return null;
        }
      })}
      {live && <Busy label={`Researching…${typeof lastCost === "number" ? ` (${inr(lastCost)} so far)` : ""}`} />}
      <div ref={endRef} />
    </div>
  );
}
