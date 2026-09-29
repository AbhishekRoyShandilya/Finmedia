import { useRef, useState } from "react";
import { api, qs } from "../api";
import type { DocumentRow, SourceStatus } from "../types";
import { Err, fmtTime, useAsync } from "../ui";

export default function Sources() {
  const { data: sources, error, reload } = useAsync(() => api.get<SourceStatus[]>("/api/sources"), []);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState({ q: "", source: "", category: "" });
  const docs = useAsync(() => api.get<DocumentRow[]>("/api/documents" + qs({ ...filter, limit: 60 })), [filter]);
  const [busy, setBusy] = useState("");
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const [url, setUrl] = useState("");
  const [open, setOpen] = useState<any>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function run(id?: string) {
    setBusy(id || "all");
    setErr("");
    try {
      const r = id ? [await api.post<any>(`/api/sources/${id}/run`)] : await api.post<any[]>("/api/sources/run");
      setMsg(r.map((x) => x.ok ? `${x.source}: ${x.new} new of ${x.fetched}` : `${x.source}: FAILED ${x.error}`).join(" · ") || "Nothing ran.");
      reload();
      docs.reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy("");
    }
  }

  async function upload(f: File) {
    setBusy("upload");
    try {
      const r = await api.upload<any>(`/api/inbox?filename=${encodeURIComponent(f.name)}`, f);
      setMsg(`Saved ${r.saved}; inbox collected ${r.collect.new ?? 0} new document(s).`);
      reload();
      docs.reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy("");
    }
  }

  async function fetchUrl() {
    setBusy("fetch");
    setErr("");
    try {
      const r = await api.post<any>("/api/documents/fetch", { url });
      setMsg(`Fetched “${r.title}” (${r.total_chars} characters, document #${r.doc_id}).`);
      setUrl("");
      docs.reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    } finally {
      setBusy("");
    }
  }

  return (
    <div className="page">
      <div className="row between">
        <div><span className="eyebrow">Sources</span><h1>Collectors and documents</h1></div>
        <button className="btn pri" disabled={!!busy} onClick={() => run()}>{busy === "all" ? "Collecting…" : "Collect all now"}</button>
      </div>
      <p className="muted small">Collectors run in the background while the server is on. Primary sources (regulators, exchange filings) are what research cites; news is for finding events. Add sources in <span className="mono">config/sources.yaml</span>.</p>
      {msg && <div className="banner ok small">{msg}</div>}
      <Err msg={error || err} />

      <div className="wrap card" style={{ padding: 0 }}>
        <table className="t">
          <thead><tr><th>Source</th><th>Type</th><th>Every</th><th>Docs</th><th>Last run</th><th>Health</th><th></th></tr></thead>
          <tbody>
            {sources?.map((s) => (
              <tr key={s.id}>
                <td><b>{s.id}</b>{s.url && <div className="tiny faint mono" style={{ maxWidth: 320, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.url}</div>}</td>
                <td className="small">{s.type}<div className="tiny faint">{s.category}</div></td>
                <td className="small">{s.interval_min} min</td>
                <td>{s.documents}</td>
                <td className="small">{fmtTime(s.last_run) || "never"}{s.last_run && <div className="tiny faint">{s.last_new} new</div>}</td>
                <td className="small">{!s.enabled ? <span className="pill">off</span>
                  : s.last_error ? <span className="pill neg" title={s.last_error}>failing ×{s.fail_streak}</span>
                    : s.last_ok ? <span className="pill pos">ok</span> : <span className="pill">waiting</span>}</td>
                <td><button className="btn sm" disabled={!!busy} onClick={() => run(s.id)}>{busy === s.id ? "…" : "Run"}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {sources?.some((s) => s.last_error) && (
        <div className="small">
          {sources.filter((s) => s.last_error).map((s) => <div key={s.id} style={{ color: "var(--neg)" }}><b>{s.id}:</b> {s.last_error}</div>)}
        </div>
      )}

      <div className="grid2">
        <div className="card">
          <h3>Add a document</h3>
          <div className="row">
            <input style={{ flex: 1 }} value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://… (PDF or web page: circular, filing, speech)" />
            <button className="btn" disabled={!url || !!busy} onClick={fetchUrl}>{busy === "fetch" ? "Fetching…" : "Fetch"}</button>
          </div>
          <div className="row">
            <input ref={fileRef} type="file" accept=".pdf,.txt,.md" style={{ display: "none" }} onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])} />
            <button className="btn" disabled={!!busy} onClick={() => fileRef.current?.click()}>{busy === "upload" ? "Uploading…" : "Upload PDF / text to the inbox"}</button>
          </div>
        </div>
        <form className="card" onSubmit={(e) => { e.preventDefault(); setFilter({ ...filter, q }); }}>
          <h3>Search documents</h3>
          <div className="row">
            <input style={{ flex: 1 }} value={q} onChange={(e) => setQ(e.target.value)} placeholder="words (empty = newest)" />
            <select value={filter.category} onChange={(e) => setFilter({ ...filter, category: e.target.value })}>
              <option value="">all categories</option><option>regulator</option><option>filing</option><option>calendar</option><option>news</option><option>document</option><option>manual</option>
            </select>
            <button className="btn">Search</button>
          </div>
        </form>
      </div>

      <div className="col">
        {docs.data?.map((d) => (
          <div key={d.id} className="card" style={{ gap: 4, cursor: "pointer" }} onClick={() => api.get(`/api/documents/${d.id}`).then(setOpen)}>
            <div className="row between"><b>{d.title}</b><span className="pill">{d.source_id}</span></div>
            <div className="small muted">{d.snippet?.slice(0, 240)}</div>
            <div className="tiny faint">{d.published_at ? `published ${fmtTime(d.published_at)} · ` : ""}collected {fmtTime(d.fetched_at)}{d.symbol ? ` · ${d.symbol}` : ""}
              {d.url && <> · <a href={d.url} target="_blank" rel="noreferrer" onClick={(e) => e.stopPropagation()}>source</a></>}</div>
          </div>
        ))}
        {docs.data && docs.data.length === 0 && <div className="empty">No documents yet. Run the collectors.</div>}
      </div>

      {open && (
        <div className="card" style={{ position: "fixed", inset: "6% 6%", zIndex: 30, overflow: "auto", boxShadow: "0 10px 60px rgba(0,0,0,.35)" }}>
          <div className="row between"><h2>{open.title}</h2><button className="btn" onClick={() => setOpen(null)}>Close</button></div>
          <div className="tiny faint">{open.source_id} · {open.published_at} · {open.url && <a href={open.url} target="_blank" rel="noreferrer">{open.url}</a>}</div>
          <pre>{open.text}</pre>
        </div>
      )}
    </div>
  );
}
