import { useEffect, useState } from "react";
import { api } from "../api";
import type { Status, Thread } from "../types";
import { Err, StatusDot, fmtTime, go, inr } from "../ui";
import RunView from "../components/RunView";

const EXAMPLES = [
  "What did the latest RBI policy change for bank and NBFC stocks, and what is already priced in?",
  "Is the failure of opening-range breakouts in Indian midcaps a temporary phase or a permanent shift?",
  "How do algos make money from retail F&O traders in India? Use the SEBI studies.",
  "TCS: what changed between the last two quarterly results, from the filings?",
];

export default function Research({ threadId, status }: { threadId?: string; status: Status | null }) {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [thread, setThread] = useState<Thread | null>(null);
  const [question, setQuestion] = useState("");
  const [asof, setAsof] = useState("");
  const [depth, setDepth] = useState("standard");
  const [steer, setSteer] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [showList, setShowList] = useState(false);
  const [playbook, setPlaybook] = useState(false);
  const [pb, setPb] = useState({ topic: "Union Budget 2027", asof: "", sectors: "" });
  const id = threadId ? Number(threadId) : null;

  const loadThreads = () => api.get<Thread[]>("/api/threads").then(setThreads, (e) => setErr(e.message));
  const loadThread = () => {
    if (id) api.get<Thread>(`/api/threads/${id}`).then(setThread, (e) => setErr(e.message));
    else setThread(null);
  };
  useEffect(() => { loadThreads(); }, []);
  useEffect(() => { loadThread(); setErr(""); setShowList(false); }, [id]);

  const active = thread?.runs?.find((r) => r.active);
  const aiReady = !!status?.ai.ready;

  async function ask() {
    if (!question.trim()) return;
    setBusy(true);
    setErr("");
    try {
      const body = { question, asof: asof || null, depth };
      const r = id
        ? await api.post<{ thread_id: number }>(`/api/threads/${id}/ask`, body)
        : await api.post<{ thread_id: number }>("/api/threads", body);
      setQuestion("");
      await loadThreads();
      if (r.thread_id === id) loadThread();
      else go(`research/${r.thread_id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function sendSteer() {
    if (!active || !steer.trim()) return;
    try {
      await api.post(`/api/runs/${active.id}/steer`, { text: steer });
      setSteer("");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function stop() {
    if (!active) return;
    try {
      await api.post(`/api/runs/${active.id}/stop`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  async function runPlaybook() {
    setBusy(true);
    setErr("");
    try {
      const r = await api.post<{ thread_id: number }>("/api/playbooks/budget", {
        topic: pb.topic, asof: pb.asof || status?.today, sectors: pb.sectors.split(",").map((s) => s.trim()).filter(Boolean),
      });
      setPlaybook(false);
      await loadThreads();
      go(`research/${r.thread_id}`);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    if (!thread || !confirm("Delete this conversation? Its Research Objects, claims and memory stay.")) return;
    try {
      await api.del(`/api/threads/${thread.id}`);
      await loadThreads();
      go("research");
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="research">
      <aside className={`threads ${showList ? "show" : ""}`}>
        <div className="head">
          <button className="btn pri" onClick={() => go("research")}>+ New research</button>
          <button className="btn sm" onClick={() => setPlaybook(!playbook)}>Budget / policy study…</button>
        </div>
        {threads.map((t) => (
          <div key={t.id} className={`thread ${t.id === id ? "on" : ""}`} onClick={() => go(`research/${t.id}`)}>
            <span className="t">{t.title}</span>
            <span className="row tiny faint"><StatusDot status={t.last_status} /> {fmtTime(t.updated_at)} · {t.n_runs} run(s) · {inr(t.cost_inr)}</span>
          </div>
        ))}
        {threads.length === 0 && <div className="empty small">No research yet.</div>}
      </aside>

      <section className="chat">
        <div className="chat-body">
          <div className="row between">
            <button className="btn sm menu-btn" onClick={() => setShowList(!showList)}>Conversations</button>
            {thread && (
              <div className="row" style={{ marginLeft: "auto" }}>
                {thread.object_key && <button className="btn sm" onClick={() => go(`object/${thread.object_key}`)}>Open Research Object</button>}
                <button className="btn sm danger" onClick={remove}>Delete</button>
              </div>
            )}
          </div>

          {status && !status.ai.ready && (
            <div className="banner warn">{status.ai.note || "The LLM provider is not configured."} See Settings for how to add a key.</div>
          )}
          {status?.ai.provider === "demo" && <div className="banner info">DEMO provider: runs are scripted walk-throughs that call real tools. Not research.</div>}

          {playbook && (
            <div className="card">
              <h3>Budget / policy sector study (playbook)</h3>
              <p className="small muted">Scoper → cited facts → PTIS event-study pack over past budgets → 7-seat panel → skeptic → CIO. Needs the PTIS bridge.</p>
              <div className="row">
                <label className="f">Topic<input value={pb.topic} onChange={(e) => setPb({ ...pb, topic: e.target.value })} /></label>
                <label className="f">As of<input type="date" value={pb.asof} onChange={(e) => setPb({ ...pb, asof: e.target.value })} /></label>
                <label className="f" style={{ flex: 1 }}>Sectors (optional, comma separated)<input value={pb.sectors} onChange={(e) => setPb({ ...pb, sectors: e.target.value })} /></label>
              </div>
              <div className="row">
                <button className="btn pri" disabled={busy || !status?.bridge.reachable} onClick={runPlaybook}>Run study</button>
                {!status?.bridge.reachable && <span className="small muted">PTIS bridge is offline.</span>}
              </div>
            </div>
          )}

          {!thread && (
            <div className="col" style={{ maxWidth: 760, margin: "30px auto", width: "100%" }}>
              <h1>What should the desk research?</h1>
              <p className="muted">Ask an open question. The lead researcher plans, pulls primary sources (NSE filings, RBI, SEBI, PIB, the Fed, official data), checks the research memory and PTIS history, consults the analyst panel, red-teams itself and returns one verified Research Object. You can steer it while it works.</p>
              <div className="col">
                {EXAMPLES.map((x) => (
                  <button key={x} className="btn" style={{ textAlign: "left", whiteSpace: "normal" }} onClick={() => setQuestion(x)}>{x}</button>
                ))}
              </div>
            </div>
          )}

          {thread?.runs?.map((r) => (
            <RunView key={r.id} run={r} aiReady={aiReady} onFinished={() => { loadThread(); loadThreads(); }} />
          ))}
          <Err msg={err} />
        </div>

        <div className="composer">
          {active ? (
            <>
              <div className="row small muted">The researcher is working. Steer it (it reads your note at its next step) or stop it.</div>
              <textarea value={steer} onChange={(e) => setSteer(e.target.value)} placeholder="e.g. Focus on PSU banks only, and check the RBI's last two statements" rows={2}
                onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) sendSteer(); }} />
              <div className="row">
                <button className="btn pri" onClick={sendSteer} disabled={!steer.trim()}>Send steer</button>
                <button className="btn danger" onClick={stop}>Stop</button>
              </div>
            </>
          ) : (
            <>
              <textarea value={question} onChange={(e) => setQuestion(e.target.value)} rows={3}
                placeholder={thread ? "Ask a follow-up (the object is revised into a new version)…" : "Ask a research question…"}
                onKeyDown={(e) => { if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) ask(); }} />
              <div className="row">
                <label className="f">Depth
                  <select value={depth} onChange={(e) => setDepth(e.target.value)}>
                    {Object.entries(status?.depths || { quick: { max_steps: 12, budget_inr: 150 }, standard: { max_steps: 25, budget_inr: 400 }, deep: { max_steps: 45, budget_inr: 1000 } })
                      .map(([k, v]) => <option key={k} value={k}>{k} (≤{v.max_steps} steps, ≤₹{v.budget_inr})</option>)}
                  </select>
                </label>
                <label className="f" title="Time-travel: research as if it were this date. Nothing after it is used.">As of (optional)
                  <input type="date" value={asof} onChange={(e) => setAsof(e.target.value)} />
                </label>
                <button className="btn pri" style={{ marginLeft: "auto" }} disabled={busy || !question.trim() || !aiReady} onClick={ask}>
                  {busy ? "Starting…" : thread ? "Ask follow-up" : "Research"}
                </button>
              </div>
            </>
          )}
        </div>
      </section>
    </div>
  );
}
