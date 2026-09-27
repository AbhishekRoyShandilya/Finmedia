"""Command-line interface: `finmedia <command>`."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

import yaml

from . import pipeline
from .config import load_yaml, settings
from .costs import BudgetGuard, month_key
from .lint import lint_reel
from .tools.fno_costs import compare_regimes, round_trip_cost
from .tools.strategy_test import run_test


def _print(obj) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_ingest(args) -> None:
    store = pipeline.open_store()
    _print(pipeline.ingest(store, only=args.source))
    _print(pipeline.run_prefilter(store))


def cmd_triage(args) -> None:
    store = pipeline.open_store()
    _print(pipeline.run_triage(store, pipeline.make_llm(store), limit=args.limit))


def cmd_list(args) -> None:
    store = pipeline.open_store()
    for row in store.documents(status=args.status, limit=args.limit):
        print(f"{row['id']:>5}  {row['status']:<8} score={row['prefilter_score']!s:<4} {row['title'][:90]}")


def cmd_brief(args) -> None:
    store = pipeline.open_store()
    _print(pipeline.run_brief(store, pipeline.make_llm(store), args.doc_id))


def cmd_reel(args) -> None:
    store = pipeline.open_store()
    paths = pipeline.run_reel(store, pipeline.make_llm(store), args.doc_id, series=args.series, notes=args.notes)
    _print({k: str(v) for k, v in paths.items()})


def cmd_daily(args) -> None:
    store = pipeline.open_store()
    _print(pipeline.run_daily(store, pipeline.make_llm(store), reels=args.reels))


def cmd_lint(args) -> None:
    data = json.loads(Path(args.plan).read_text(encoding="utf-8"))
    plan = data.get("plan", data)
    brief = json.loads(Path(args.brief).read_text(encoding="utf-8")) if args.brief else None
    report = lint_reel(plan, load_yaml("config/lint_rules.yaml"), brief=brief, ra_approved=args.ra_approved)
    _print(report.as_dict())
    sys.exit(0 if report.passed else 1)


def cmd_strategy_test(args) -> None:
    facts = yaml.safe_load(Path(args.file).read_text(encoding="utf-8"))
    result = run_test(facts)
    print(f"\n{result['verdict']}  ({result['verdict_hi']})\n")
    for line in result["lines"]:
        print(line)
    print(f"\n{result['note']}")


def cmd_fno_cost(args) -> None:
    charges = load_yaml("config/fno_charges.yaml")
    trade = dict(instrument=args.instrument, buy_price=args.buy, sell_price=args.sell, quantity=args.qty)
    if args.compare:
        dates = [date.fromisoformat(d) for d in args.compare.split(",")]
        _print([b.as_dict() for b in compare_regimes(charges, dates, **trade)])
    else:
        _print(round_trip_cost(charges, trade_date=date.fromisoformat(args.date), **trade).as_dict())


def cmd_costs(args) -> None:
    store = pipeline.open_store()
    month = args.month or month_key()
    if args.action == "add":
        store.add_cost(month=month, kind="subscription", item=args.item, inr=args.inr)
    guard = BudgetGuard(store, settings())
    budget = settings()["budget"]
    total = store.month_spend(month)
    print(f"Month {month}: spent ₹{total:,.0f} of ₹{budget['monthly_cap_inr']:,} cap "
          f"(LLM ₹{store.month_spend(month, 'llm'):,.2f} of ₹{budget['llm_cap_inr']:,}); "
          f"LLM budget left ₹{max(guard.remaining_llm_inr(month), 0):,.2f}")
    for row in store.month_breakdown(month):
        print(f"  {row['kind']:<12} {row['item']:<40} calls={row['calls']:<4} ₹{row['inr']:,.2f}")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="finmedia", description="Research-to-Reel pipeline")
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("ingest", help="fetch documents and run the pre-filter")
    s.add_argument("--source", help="only this source id from config/sources.yaml")
    s.set_defaults(func=cmd_ingest)

    s = sub.add_parser("list", help="list stored documents")
    s.add_argument("--status", choices=["new", "kept", "dropped", "triaged", "briefed"])
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(func=cmd_list)

    s = sub.add_parser("triage", help="LLM triage of kept documents (paid)")
    s.add_argument("--limit", type=int)
    s.set_defaults(func=cmd_triage)

    s = sub.add_parser("brief", help="write a research brief for a document (paid)")
    s.add_argument("doc_id", type=int)
    s.set_defaults(func=cmd_brief)

    s = sub.add_parser("reel", help="draft a Reel scene plan from a brief (paid)")
    s.add_argument("doc_id", type=int)
    s.add_argument("--series", default="event", choices=["event", "strategy_decay", "strategy_test", "transfer"])
    s.add_argument("--notes", default="", help="editor notes for the scriptwriter")
    s.set_defaults(func=cmd_reel)

    s = sub.add_parser("daily", help="ingest, triage and draft Reels for top items (paid)")
    s.add_argument("--reels", type=int, default=1)
    s.set_defaults(func=cmd_daily)

    s = sub.add_parser("lint", help="check a Reel plan JSON against the rules")
    s.add_argument("plan")
    s.add_argument("--brief", help="brief JSON to cross-check numbers")
    s.add_argument("--ra-approved", action="store_true")
    s.set_defaults(func=cmd_lint)

    s = sub.add_parser("strategy-test", help="run the 5-Minute Strategy Test on a YAML file")
    s.add_argument("file")
    s.set_defaults(func=cmd_strategy_test)

    s = sub.add_parser("fno-cost", help="F&O round-trip cost calculator")
    s.add_argument("--instrument", choices=["futures", "options"], required=True)
    s.add_argument("--buy", type=float, required=True)
    s.add_argument("--sell", type=float, required=True)
    s.add_argument("--qty", type=int, required=True)
    s.add_argument("--date", default=date.today().isoformat())
    s.add_argument("--compare", help="comma-separated dates, e.g. 2023-06-01,2025-06-01,2026-06-01")
    s.set_defaults(func=cmd_fno_cost)

    s = sub.add_parser("costs", help="show this month's spend, or record a subscription")
    s.add_argument("action", nargs="?", choices=["show", "add"], default="show")
    s.add_argument("--item", help="subscription name, e.g. HeyGen Creator")
    s.add_argument("--inr", type=float, help="amount in rupees")
    s.add_argument("--month", help="YYYY-MM (default: current month)")
    s.set_defaults(func=cmd_costs)
    return p


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
