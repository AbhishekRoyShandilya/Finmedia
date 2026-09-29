import { useCallback, useEffect, useRef, useState } from "react";
import type { Direction } from "./types";

export function useAsync<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const fnRef = useRef(fn);
  fnRef.current = fn;
  const reload = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fnRef.current());
      setError("");
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  }, []);
  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  return { data, error, loading, reload, setData };
}

export function useHash(): string[] {
  const read = () => (window.location.hash || "#/research").replace(/^#\/?/, "").split("/");
  const [parts, setParts] = useState<string[]>(read());
  useEffect(() => {
    const on = () => setParts(read());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return parts;
}

export function go(path: string): void {
  window.location.hash = "#/" + path.replace(/^\//, "");
}

export function DirPill({ d }: { d: Direction | string }) {
  const cls = d === "positive" ? "pos" : d === "negative" ? "neg" : "";
  return <span className={`pill ${cls}`}>{d}</span>;
}

export function StatusDot({ status }: { status?: string | null }) {
  const cls = status === "running" || status === "queued" ? "run" : status === "done" || status === "final" ? "ok"
    : status === "failed" || status === "flagged" ? "bad" : "";
  return <span className={`dot ${cls}`} title={status || ""} />;
}

export function Err({ msg }: { msg: string }) {
  return msg ? <div className="banner bad">{msg}</div> : null;
}

export function fmtTime(s?: string | null): string {
  if (!s) return "";
  const d = new Date(s);
  if (isNaN(d.getTime())) return s;
  return d.toLocaleString(undefined, { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

export function inr(n?: number | null): string {
  if (n === undefined || n === null) return "";
  return "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: n < 10 ? 2 : 0 });
}

export const VERDICT: Record<string, string> = {
  works: "Works",
  does_not_work: "Doesn't work",
  works_only_when: "Works only when",
  not_applicable: "",
};

export function Busy({ label }: { label: string }) {
  return (
    <span className="row small muted">
      <span className="dot run" /> {label}
    </span>
  );
}
