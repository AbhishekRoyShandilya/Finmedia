import { useState } from "react";
import { api, qs } from "../api";
import type { ObjectListItem } from "../types";
import { Err, StatusDot, VERDICT, fmtTime, go, useAsync } from "../ui";

export default function Library() {
  const [q, setQ] = useState("");
  const [term, setTerm] = useState("");
  const { data, error, loading } = useAsync(() => api.get<ObjectListItem[]>("/api/objects" + qs({ q: term })), [term]);

  return (
    <div className="page">
      <div className="row between">
        <div>
          <span className="eyebrow">Library</span>
          <h1>Research Objects</h1>
        </div>
        <form className="row" onSubmit={(e) => { e.preventDefault(); setTerm(q); }}>
          <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search titles and content" />
          <button className="btn">Search</button>
        </form>
      </div>
      <p className="muted small">Every finished research is one verified object (latest version shown). Content, memos and claims are built from these.</p>
      <Err msg={error} />
      {loading && <div className="muted small">Loading…</div>}
      <div className="col">
        {data?.map((o) => (
          <div key={o.key} className="card" style={{ cursor: "pointer" }} onClick={() => go(`object/${o.key}`)}>
            <div className="row between">
              <div className="row"><StatusDot status={o.status} /><b>{o.title}</b></div>
              <div className="row">
                {VERDICT[o.verdict] && <span className="pill acc">{VERDICT[o.verdict]}</span>}
                <span className="pill">{o.mode?.replace(/_/g, " ")}</span>
                <span className="pill">{o.n_claims} claims</span>
                <span className="pill">v{o.version}</span>
              </div>
            </div>
            <div className="small muted">{o.summary}</div>
            <div className="tiny faint">{o.key} · as of {o.asof} · {fmtTime(o.created_at)}{o.status === "flagged" ? " · provenance flagged" : ""}</div>
          </div>
        ))}
        {data && data.length === 0 && <div className="empty">No Research Objects yet. Start one from Research.</div>}
      </div>
    </div>
  );
}
