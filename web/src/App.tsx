import { useEffect, useState } from "react";
import { api } from "./api";
import type { Status } from "./types";
import { useHash } from "./ui";
import Research from "./pages/Research";
import Library from "./pages/Library";
import ObjectPage from "./pages/ObjectPage";
import Content from "./pages/Content";
import Memory from "./pages/Memory";
import Sources from "./pages/Sources";
import Scoreboard from "./pages/Scoreboard";
import Settings from "./pages/Settings";

const NAV: [string, string][] = [
  ["research", "Research"],
  ["library", "Library"],
  ["content", "Content studio"],
  ["memory", "Memory"],
  ["sources", "Sources"],
  ["scoreboard", "Scoreboard"],
  ["settings", "Settings"],
];

export default function App() {
  const parts = useHash();
  const page = parts[0] || "research";
  const [status, setStatus] = useState<Status | null>(null);
  const [statusErr, setStatusErr] = useState("");
  const [open, setOpen] = useState(false);

  useEffect(() => {
    let alive = true;
    const load = () =>
      api.get<Status>("/api/status").then(
        (s) => alive && (setStatus(s), setStatusErr("")),
        (e) => alive && setStatusErr(e.message),
      );
    load();
    const t = setInterval(load, 30000);
    return () => {
      alive = false;
      clearInterval(t);
    };
  }, []);
  useEffect(() => setOpen(false), [page, parts[1]]);

  const navKey = page === "object" ? "library" : page;
  let body;
  switch (page) {
    case "library": body = <Library />; break;
    case "object": body = <ObjectPage objKey={parts[1]} version={parts[2]} status={status} />; break;
    case "content": body = <Content id={parts[1]} />; break;
    case "memory": body = <Memory />; break;
    case "sources": body = <Sources />; break;
    case "scoreboard": body = <Scoreboard />; break;
    case "settings": body = <Settings status={status} />; break;
    default: body = <Research threadId={parts[1]} status={status} />;
  }

  return (
    <div className="app">
      <div className="topbar">
        <button className="btn sm menu-btn" onClick={() => setOpen(!open)} aria-label="Menu">☰</button>
        <b>Finmedia</b>
      </div>
      <nav className={`nav ${open ? "open" : ""}`}>
        <div className="brand">
          <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true">
            <rect width="32" height="32" rx="7" fill="var(--accent)" />
            <path d="M8 22 L13 14 L18 18 L24 9" stroke="var(--accent-ink)" strokeWidth="3" fill="none" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
          <div><b>Finmedia</b><small>Research Desk</small></div>
        </div>
        {NAV.map(([k, label]) => (
          <a key={k} href={`#/${k}`} className={navKey === k ? "on" : ""}>
            <span>{label}</span>
          </a>
        ))}
        <div className="foot">
          {statusErr && <span style={{ color: "var(--neg)" }}>API: {statusErr}</span>}
          {status && (
            <>
              <span className="row"><span className={`dot ${status.ai.ready ? "ok" : "bad"}`} /> LLM: {status.ai.provider}{status.ai.ready ? "" : " (no key)"}</span>
              <span className="row"><span className={`dot ${status.bridge.reachable ? "ok" : ""}`} /> PTIS quant: {status.bridge.reachable ? "online" : "offline"}</span>
              <span className="row"><span className={`dot ${status.collectors.running ? "ok" : ""}`} /> Collectors: {status.collectors.running ? "on" : "off"}</span>
              <span>Research budget left: ₹{Number(status.budget.research_left_inr).toLocaleString("en-IN", { maximumFractionDigits: 0 })}</span>
            </>
          )}
        </div>
      </nav>
      <div className="main">{body}</div>
    </div>
  );
}
