import { useState } from "react";
import { api, qs } from "../api";
import type { MemoryRecord } from "../types";
import { Err, fmtTime, useAsync } from "../ui";

const KINDS = ["event", "expectation", "reaction", "structure_change", "finding", "note"];

function Record({ r }: { r: MemoryRecord }) {
  return (
    <div className="card">
      <div className="row between">
        <div className="row"><span className="pill acc">{r.kind.replace("_", " ")}</span>
          {r.kind === "finding" && <span className={`pill ${r.status === "supported" ? "pos" : r.status === "killed" ? "neg" : "warn"}`}>{r.status}</span>}
          <b>{r.title}</b></div>
        <span className="tiny faint">#{r.id}</span>
      </div>
      {r.body && <p className="small" style={{ whiteSpace: "pre-wrap" }}>{r.body}</p>}
      <div className="row tiny">
        {r.tags.map((t) => <span key={t} className="pill">{t}</span>)}
        {r.entities.map((t) => <span key={t} className="pill acc">{t}</span>)}
      </div>
      <div className="tiny faint">
        {r.event_date ? `happened/effective ${r.event_date} · ` : ""}known {fmtTime(r.known_at)} · {r.source_ref} · by {r.created_by}
        {r.supersedes ? ` · corrects #${r.supersedes}` : ""}
      </div>
    </div>
  );
}

export default function Memory() {
  const [q, setQ] = useState("");
  const [kinds, setKinds] = useState<string[]>([]);
  const [asof, setAsof] = useState("");
  const [search, setSearch] = useState({ q: "", kinds: "", asof: "" });
  const { data, error, reload } = useAsync(
    () => (search.q || search.kinds || search.asof)
      ? api.get<MemoryRecord[]>("/api/memory/search" + qs(search))
      : api.get<MemoryRecord[]>("/api/memory/timeline"),
    [search],
  );
  const [form, setForm] = useState({ kind: "structure_change", title: "", body: "", tags: "", entities: "", event_date: "", status: "hypothesis", supersedes: "" });
  const [err, setErr] = useState("");
  const [adding, setAdding] = useState(false);

  async function add() {
    setErr("");
    try {
      await api.post("/api/memory", {
        kind: form.kind, title: form.title, body: form.body,
        tags: form.tags.split(",").map((s) => s.trim()).filter(Boolean),
        entities: form.entities.split(",").map((s) => s.trim()).filter(Boolean),
        event_date: form.event_date || null, status: form.kind === "finding" ? form.status : "active",
        supersedes: form.supersedes ? Number(form.supersedes) : null,
      });
      setForm({ ...form, title: "", body: "", tags: "", entities: "", event_date: "", supersedes: "" });
      setAdding(false);
      reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="page">
      <div className="row between">
        <div><span className="eyebrow">Research memory</span><h1>What the firm knows, and when it knew it</h1></div>
        <button className="btn" onClick={() => setAdding(!adding)}>+ Add record</button>
      </div>
      <p className="muted small">Append-only and point-in-time: a search “as of” a date sees only what was known then. Corrections are new records that supersede old ones. Mechanism tags (e.g. <span className="mono">channel:rates</span>, <span className="mono">who-pays:consumers</span>, <span className="mono">stage:proposal</span>) find events that work alike.</p>

      {adding && (
        <div className="card">
          <div className="row">
            <label className="f">Kind<select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })}>{KINDS.map((k) => <option key={k}>{k}</option>)}</select></label>
            {form.kind === "finding" && (
              <label className="f">Status<select value={form.status} onChange={(e) => setForm({ ...form, status: e.target.value })}>
                <option>hypothesis</option><option>supported</option><option>killed</option></select></label>
            )}
            <label className="f" style={{ flex: 1 }}>Title<input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} /></label>
            <label className="f">Date it happened / takes effect<input type="date" value={form.event_date} onChange={(e) => setForm({ ...form, event_date: e.target.value })} /></label>
          </div>
          <label className="f">Details<textarea rows={4} value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} /></label>
          <div className="row">
            <label className="f" style={{ flex: 1 }}>Mechanism tags (comma separated)<input value={form.tags} onChange={(e) => setForm({ ...form, tags: e.target.value })} placeholder="channel:costs, affects:intraday, stage:final" /></label>
            <label className="f" style={{ flex: 1 }}>Entities / affects<input value={form.entities} onChange={(e) => setForm({ ...form, entities: e.target.value })} placeholder="NIFTY, F&O traders, momentum sleeve" /></label>
            <label className="f">Corrects record #<input value={form.supersedes} onChange={(e) => setForm({ ...form, supersedes: e.target.value })} style={{ width: 90 }} /></label>
          </div>
          <div className="row"><button className="btn pri" disabled={!form.title.trim()} onClick={add}>Save to memory</button></div>
        </div>
      )}

      <form className="card" onSubmit={(e) => { e.preventDefault(); setSearch({ q, kinds: kinds.join(","), asof }); }}>
        <div className="row">
          <input style={{ flex: 1 }} value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search memory (empty = latest timeline)" />
          <label className="f">As of<input type="date" value={asof} onChange={(e) => setAsof(e.target.value)} /></label>
          <button className="btn pri">Search</button>
        </div>
        <div className="row small">
          {KINDS.map((k) => (
            <label key={k} className="row" style={{ gap: 4 }}>
              <input type="checkbox" checked={kinds.includes(k)} onChange={(e) => setKinds(e.target.checked ? [...kinds, k] : kinds.filter((x) => x !== k))} />{k.replace("_", " ")}
            </label>
          ))}
        </div>
      </form>
      <Err msg={error || err} />
      <div className="col">
        {data?.map((r) => <Record key={r.id} r={r} />)}
        {data && data.length === 0 && <div className="empty">Nothing found. Research runs add events, findings and structure changes here automatically.</div>}
      </div>
    </div>
  );
}
