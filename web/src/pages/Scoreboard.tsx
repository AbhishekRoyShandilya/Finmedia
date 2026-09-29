import { useState } from "react";
import { api } from "../api";
import type { ClaimRow } from "../types";
import { DirPill, Err, go, useAsync } from "../ui";

interface Group { group: string; n: number; hits: number; hit_rate_pct: number }
interface Board {
  total_claims: number; scored: number; pending: number; overall: Group[]; by_source: Group[];
  by_horizon: Group[]; by_confidence: Group[]; last_postmortem: string | null;
}

function GroupTable({ title, rows }: { title: string; rows: Group[] }) {
  return (
    <div className="card">
      <h3>{title}</h3>
      {rows.length === 0 ? <p className="small muted">Nothing scored yet.</p> : (
        <table className="t">
          <thead><tr><th></th><th>Scored</th><th>Hits</th><th>Hit rate</th></tr></thead>
          <tbody>{rows.map((r) => <tr key={r.group}><td>{r.group}</td><td>{r.n}</td><td>{r.hits}</td><td>{r.hit_rate_pct}%</td></tr>)}</tbody>
        </table>
      )}
    </div>
  );
}

export default function Scoreboard() {
  const board = useAsync(() => api.get<Board>("/api/scoreboard"), []);
  const claims = useAsync(() => api.get<ClaimRow[]>("/api/claims"), []);
  const [msg, setMsg] = useState("");
  const [err, setErr] = useState("");
  const b = board.data;

  async function postmortem() {
    setErr("");
    try {
      const r = await api.post<any>("/api/claims/postmortem");
      setMsg(r.skipped ? `Skipped: ${r.skipped}` : `Scored ${r.scored}, still pending ${r.pending}${r.failed?.length ? `, ${r.failed.length} failed` : ""}.`);
      board.reload();
      claims.reload();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  }

  return (
    <div className="page">
      <div className="row between">
        <div><span className="eyebrow">Scoreboard</span><h1>Every call, scored against what happened</h1></div>
        <button className="btn pri" onClick={postmortem}>Score due claims now</button>
      </div>
      <p className="muted small">A claim is a hit when the realised abnormal return vs NIFTY over its horizon has the claimed sign, measured from the close on the report date. Scoring runs daily and needs the PTIS bridge for sector and stock claims. This is the desk's true out-of-sample record.</p>
      {msg && <div className="banner ok small">{msg}</div>}
      <Err msg={board.error || claims.error || err} />
      {b && (
        <div className="grid4">
          <div className="card stat"><span className="small muted">Claims logged</span><b>{b.total_claims}</b></div>
          <div className="card stat"><span className="small muted">Scored</span><b>{b.scored}</b></div>
          <div className="card stat"><span className="small muted">Waiting for horizon</span><b>{b.pending}</b></div>
          <div className="card stat"><span className="small muted">Overall hit rate</span><b>{b.overall[0] ? `${b.overall[0].hit_rate_pct}%` : "—"}</b></div>
        </div>
      )}
      {b && (
        <div className="grid2">
          <GroupTable title="By source" rows={b.by_source} />
          <GroupTable title="By horizon" rows={b.by_horizon} />
          <GroupTable title="By confidence" rows={b.by_confidence} />
        </div>
      )}
      <div className="card wrap" style={{ padding: 0 }}>
        <table className="t">
          <thead><tr><th>Date</th><th>Target</th><th>View</th><th>Horizon</th><th>Conf.</th><th>Source</th><th>Outcome</th></tr></thead>
          <tbody>
            {claims.data?.map((c) => (
              <tr key={c.id}>
                <td className="small">{c.asof}</td>
                <td className="mono small">{c.target}</td>
                <td><DirPill d={c.direction} /></td>
                <td className="small">{c.horizon}</td>
                <td className="small">{c.confidence}</td>
                <td className="small">{c.object_key ? <a href="#" onClick={(e) => { e.preventDefault(); go(`object/${c.object_key}/${c.object_version}`); }}>{c.object_key} v{c.object_version}</a> : c.source}</td>
                <td className="small">{c.outcome ? <span className={`pill ${c.outcome.hit ? "pos" : c.outcome.hit === false ? "neg" : ""}`}>{c.outcome.abnormal_pct}% · {c.outcome.hit === null ? "n/a" : c.outcome.hit ? "hit" : "miss"}</span> : <span className="faint">pending</span>}</td>
              </tr>
            ))}
            {claims.data && claims.data.length === 0 && <tr><td colSpan={7} className="empty">No claims yet.</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
}
