import { useState } from "react";
import { api, qs } from "../api";
import type { ContentItem } from "../types";
import { Err, fmtTime, go, useAsync } from "../ui";

const STATUSES = ["", "draft", "approved", "published", "stale"];

function statusPill(s: string) {
  const cls = s === "approved" || s === "published" ? "pos" : s === "stale" ? "warn" : "";
  return <span className={`pill ${cls}`}>{s}</span>;
}

function Scenes({ draft, kind }: { draft: any; kind: string }) {
  if (kind === "reel") {
    return (
      <div className="col">
        <div><b>Hook:</b> {draft.hook_text}</div>
        {draft.scenes?.map((s: any) => (
          <div key={s.id} className="scene">
            <div className="row"><span className="pill acc">{s.visual}</span> <span className="small muted">{s.visual_spec}</span></div>
            <div style={{ whiteSpace: "pre-wrap" }}>{s.narration}</div>
            {s.on_screen_text && <div className="small"><b>On screen:</b> {s.on_screen_text}</div>}
          </div>
        ))}
        <div className="small"><b>Caption:</b> <span style={{ whiteSpace: "pre-wrap" }}>{draft.caption}</span></div>
        <div className="small">{draft.hashtags?.join(" ")}</div>
      </div>
    );
  }
  if (kind === "youtube") {
    return (
      <div className="col">
        <div><b>Thumbnail:</b> {draft.thumbnail_text}</div>
        <div><b>Hook:</b> <span style={{ whiteSpace: "pre-wrap" }}>{draft.hook}</span></div>
        {draft.chapters?.map((c: any, i: number) => (
          <div key={i} className="scene">
            <b>{i + 1}. {c.heading}</b>
            <div style={{ whiteSpace: "pre-wrap" }}>{c.narration}</div>
            {c.on_screen_text && <div className="small"><b>On screen:</b> {c.on_screen_text}</div>}
            <div className="row">{c.visuals?.map((v: any, j: number) => <span key={j} className="pill" title={v.spec}>{v.visual}: {v.spec.slice(0, 60)}</span>)}</div>
          </div>
        ))}
        <div className="banner info"><b>Verdict card:</b> {draft.verdict_card}</div>
        <div><b>Takeaway:</b> {draft.takeaway}</div>
        <div className="small"><b>Description:</b> <span style={{ whiteSpace: "pre-wrap" }}>{draft.description}</span></div>
      </div>
    );
  }
  if (kind === "carousel") {
    return (
      <div className="grid4">
        {draft.slides?.map((s: any, i: number) => (
          <div key={i} className="card" style={{ minHeight: 150 }}>
            <span className="tiny faint">slide {i + 1}</span>
            <b>{s.headline}</b>
            <div className="small">{s.body}</div>
            <div className="tiny faint">{s.visual_spec}</div>
          </div>
        ))}
        <div className="card small"><b>Caption</b><span style={{ whiteSpace: "pre-wrap" }}>{draft.caption}</span><span>{draft.hashtags?.join(" ")}</span></div>
      </div>
    );
  }
  return (
    <div className="col">
      <div><b>Subject:</b> {draft.subject} <span className="faint small">· {draft.preheader}</span></div>
      <p style={{ whiteSpace: "pre-wrap" }}>{draft.intro}</p>
      {draft.sections?.map((s: any, i: number) => (
        <div key={i}><h3>{s.heading}</h3><p style={{ whiteSpace: "pre-wrap" }}>{s.body}</p></div>
      ))}
      <div className="banner info"><b>Takeaway:</b> {draft.takeaway}</div>
    </div>
  );
}

function Item({ id }: { id: string }) {
  const { data: item, error, reload, setData } = useAsync(() => api.get<ContentItem>(`/api/content/${id}`), [id]);
  const [tab, setTab] = useState("view");
  const [json, setJson] = useState("");
  const [appr, setAppr] = useState({ name: "", role: "editor", note: "" });
  const [url, setUrl] = useState("");
  const [err, setErr] = useState("");
  const [msg, setMsg] = useState("");

  if (!item) return <div className="page"><Err msg={error} />{!error && <span className="muted">Loading…</span>}</div>;
  const lint = item.lint;

  async function act(fn: () => Promise<ContentItem>, ok: string) {
    setErr("");
    setMsg("");
    try {
      setData(await fn());
      setMsg(ok);
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="page">
      <div className="row between">
        <button className="btn sm" onClick={() => go("content")}>← Content studio</button>
        <button className="btn sm" onClick={() => go(`object/${item.object_key}/${item.object_version}`)}>Research Object {item.object_key} v{item.object_version}</button>
      </div>
      <div className="row between">
        <div>
          <span className="eyebrow">{item.kind}</span>
          <h1>{item.title}</h1>
        </div>
        {statusPill(item.status)}
      </div>
      {item.status === "stale" && <div className="banner warn">The Research Object has a newer version. This draft may be out of date: generate a new one from the latest version.</div>}

      <div className="card">
        <h3>Automatic checks</h3>
        {lint.passed ? <div className="banner ok">Passed: numbers all trace to the Research Object; voice and disclosure rules met.</div>
          : <div className="banner bad"><b>Must fix before approval:</b><ul className="clean">{lint.errors.map((x, i) => <li key={i}>{x}</li>)}</ul></div>}
        {lint.warnings.length > 0 && <div className="small"><b>Warnings:</b><ul className="clean">{lint.warnings.map((x, i) => <li key={i}>{x}</li>)}</ul></div>}
        {lint.compliance_items.length > 0 ? (
          <div className="banner warn">
            <b>Compliance items (kept visible, not hidden):</b>
            <ul className="clean">{lint.compliance_items.map((x, i) => <li key={i}>{x}</li>)}</ul>
            Publishing needs a sign-off by a <b>compliance</b> or <b>RA</b> reviewer.
          </div>
        ) : <div className="small muted">No compliance items: an editor's approval is enough.</div>}
      </div>

      <div className="tabs">
        {["view", "edit", "approve"].map((t) => (
          <button key={t} className={tab === t ? "on" : ""} onClick={() => { setTab(t); if (t === "edit") setJson(JSON.stringify(item.draft, null, 2)); }}>
            {t === "view" ? "Script" : t === "edit" ? "Edit" : "Approve & publish"}
          </button>
        ))}
      </div>

      {tab === "view" && item.draft && (
        <div className="card">
          <div className="row">{item.draft.title_variants?.map((t: string, i: number) => <span key={i} className="pill acc">{t}</span>)}</div>
          <Scenes draft={item.draft} kind={item.kind} />
          <div className="small"><b>Disclosure:</b> {item.draft.disclosure}</div>
          <div className="small"><b>Sources:</b><ul className="clean">{item.draft.sources?.map((s: string, i: number) => <li key={i}>{s}</li>)}</ul></div>
          <div className="tiny faint">Compliance tier {item.draft.compliance_tier}{lint.cost_inr !== undefined ? ` · generation cost ₹${lint.cost_inr}` : ""}</div>
        </div>
      )}

      {tab === "edit" && (
        <div className="card">
          <p className="small muted">Edit the draft as JSON. Saving re-runs the checks and clears earlier approvals.</p>
          <textarea className="mono" rows={24} value={json} onChange={(e) => setJson(e.target.value)} />
          <div className="row">
            <button className="btn pri" onClick={() => {
              let parsed: unknown;
              try { parsed = JSON.parse(json); } catch (e) { setErr("Not valid JSON: " + (e as Error).message); return; }
              act(() => api.put<ContentItem>(`/api/content/${item.id}`, parsed), "Saved and re-checked.");
            }}>Save</button>
          </div>
        </div>
      )}

      {tab === "approve" && (
        <div className="card">
          <h3>Approvals</h3>
          {item.approvals.length === 0 && <p className="small muted">None yet.</p>}
          <ul className="clean small">{item.approvals.map((a, i) => <li key={i}><b>{a.name}</b> ({a.role}) · {fmtTime(a.at)} {a.note && `· ${a.note}`}</li>)}</ul>
          {item.status !== "published" && item.status !== "stale" && (
            <div className="row">
              <label className="f">Your name<input value={appr.name} onChange={(e) => setAppr({ ...appr, name: e.target.value })} /></label>
              <label className="f">Role
                <select value={appr.role} onChange={(e) => setAppr({ ...appr, role: e.target.value })}>
                  <option value="editor">editor</option><option value="compliance">compliance</option><option value="ra">RA (registered)</option>
                </select>
              </label>
              <label className="f" style={{ flex: 1 }}>Note<input value={appr.note} onChange={(e) => setAppr({ ...appr, note: e.target.value })} /></label>
              <button className="btn pri" disabled={!appr.name.trim()} onClick={() => act(() => api.post<ContentItem>(`/api/content/${item.id}/approve`, appr), "Approval recorded.")}>Approve</button>
            </div>
          )}
          {item.status === "approved" && (
            <div className="row">
              <label className="f" style={{ flex: 1 }}>Published URL (optional)<input value={url} onChange={(e) => setUrl(e.target.value)} /></label>
              <button className="btn pri" onClick={() => act(() => api.post<ContentItem>(`/api/content/${item.id}/publish`, { url }), "Marked published.")}>Mark published</button>
            </div>
          )}
          <p className="tiny faint">Publish gate: RA registration, or until then a compliance reviewer's sign-off. Every approval is recorded with name and time.</p>
        </div>
      )}
      {msg && <div className="banner ok">{msg}</div>}
      <Err msg={err} />
      <button className="btn sm" style={{ alignSelf: "flex-start" }} onClick={reload}>Reload</button>
    </div>
  );
}

export default function Content({ id }: { id?: string }) {
  const [status, setStatus] = useState("");
  const { data, error } = useAsync(() => api.get<ContentItem[]>("/api/content" + qs({ status })), [status]);
  if (id) return <Item id={id} />;
  return (
    <div className="page">
      <div><span className="eyebrow">Content studio</span><h1>Drafts, approvals and publishing</h1></div>
      <p className="muted small">Content only renders a Research Object: every number is checked against it. Directional views stay in and are marked for the compliance sign-off.</p>
      <div className="tabs">
        {STATUSES.map((s) => <button key={s} className={status === s ? "on" : ""} onClick={() => setStatus(s)}>{s || "all"}</button>)}
      </div>
      <Err msg={error} />
      <div className="wrap">
        <table className="t">
          <thead><tr><th>Kind</th><th>Title</th><th>Object</th><th>Checks</th><th>Status</th><th>Updated</th></tr></thead>
          <tbody>
            {data?.map((c) => (
              <tr key={c.id} style={{ cursor: "pointer" }} onClick={() => go(`content/${c.id}`)}>
                <td>{c.kind}</td>
                <td>{c.title}</td>
                <td className="mono small">{c.object_key} v{c.object_version}</td>
                <td>{c.lint.passed ? <span className="pill pos">passed</span> : <span className="pill neg">{c.lint.errors.length} error(s)</span>}
                  {c.lint.needs_signoff && <span className="mark" style={{ marginLeft: 4 }}>SIGN-OFF</span>}</td>
                <td>{statusPill(c.status)}</td>
                <td className="small">{fmtTime(c.updated_at)}</td>
              </tr>
            ))}
            {data && data.length === 0 && <tr><td colSpan={6} className="empty">No content yet. Open a Research Object and use “Make content”.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
