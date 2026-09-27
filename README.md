# Finmedia

Research-to-Reel pipeline for an evidence-based Indian market research brand: official documents in, fact-checked Hindi Reel scripts out, under a hard monthly budget.

**Status (27 Sep 2026): milestone 1, research → script.** The video layer (voice clone, avatar, Remotion assembly, publishing) is the next milestone. Strategy and plans are in [`docs/`](docs/).

## What it does

```
official sources ──► ingest ──► rule pre-filter ──► AI triage ──► research brief ──► Hindi Reel scene plan
 (RSS, inbox PDFs)      (free)        (free)          (playbooks)   (every fact quoted,   (+ automatic checks
                                                                      numbers verified)     + review sheet)
```

- **Ingest:** regulator RSS feeds (SEBI, RBI), GDELT news signals (optional), and `data/inbox/`, a folder for official PDFs or text files you save by hand.
- **Pre-filter** (`config/prefilter.yaml`): keyword rules drop routine filings before any paid AI call.
- **Triage:** classifies each document into one of the playbooks in [`system/event_playbooks.yaml`](system/event_playbooks.yaml) and scores materiality.
- **Research brief:** facts with exact quotes from the document, mechanism, who is exposed, questions for historical research, skeptic points. **Code checks that every quote and number really appears in the source.**
- **Reel scene plan:** 35–60 s Hindi script in our expert (not news-anchor) voice, scene by scene with visuals, three title variants, caption, disclosure, sources.
- **Lint:** blocks news-anchor phrases, advice/promise language, missing AI disclosure, low visual effort, and any number that isn't in the brief.
- **Review sheet:** a Markdown file for your approval (Gate G2 facts, Gate G3 script).
- **Budget guard:** every AI call is checked against the monthly cap *before* it runs and recorded after.

Audience tools (no AI, free to run):
- **5-Minute Strategy Test:** scores any strategy's claims on 10 questions.
- **F&O cost calculator:** true round-trip cost of a trade, and how the same trade's cost changed across rule regimes (2023 → 2025 → 2026).

## Setup

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
export ANTHROPIC_API_KEY=...        # needed only for triage / brief / reel
pytest                               # 24 tests, no API calls
```

Run the fetchers from your own machine or server. Some official Indian sites block cloud IP ranges.

## Daily workflow

```bash
finmedia ingest                      # fetch feeds + inbox, run the free pre-filter
finmedia list --status kept          # what survived the pre-filter
finmedia triage --limit 10           # AI classification (paid, budget-guarded)
finmedia brief 42                    # research brief for document 42 (paid)
finmedia reel 42 --series event      # Hindi Reel plan + review sheet in output/reels/ (paid)
finmedia daily --reels 1             # all of the above for the top item
finmedia costs                       # month-to-date spend vs the ₹12,000 cap
finmedia costs add --item "HeyGen Creator" --inr 2550   # record subscriptions
```

Tools:

```bash
finmedia strategy-test config/strategy_test_example.yaml
finmedia fno-cost --instrument futures --buy 25000 --sell 25020 --qty 75 \
    --compare 2023-06-01,2025-06-01,2026-06-01
finmedia lint output/reels/<file>.plan.json
```

Example from the cost calculator: the same 20-point Nifty futures trade (1 lot of 75) keeps **₹1,095** after costs under 2023 rules but **₹392** under 2026 rules, mainly because STT on futures rose from 0.0125% to 0.05%. (Exchange charges before Oct 2024 are approximated and flagged in the output. Verify rates before publishing.)

## Configuration

| File | What it controls |
|---|---|
| `config/settings.yaml` | Budget cap (₹12,000/month, ₹2,600 for AI), model and effort per step, token prices, volume limits |
| `config/sources.yaml` | Feeds and the inbox folder |
| `config/prefilter.yaml` | Keyword weights and routine-filing drops |
| `config/lint_rules.yaml` | Banned anchor phrases, advice language, number and effort rules |
| `config/fno_charges.yaml` | STT (dated schedule), exchange charges, stamp duty, GST, brokerage |
| `prompts/*.md` | System prompts for triage, brief and Reel script (kept stable so they're cached) |
| `system/event_playbooks.yaml` | The playbooks the router chooses between |

AI calls use Claude Opus 5 by default, with adaptive thinking, prompt caching, validated structured outputs, and server-side refusal fallbacks (set `llm.refusal_fallbacks: false` to turn them off). You can switch the triage model to a cheaper one in `settings.yaml` after checking quality.

## Project layout

```
src/finmedia/
  sources/        rss.py, gdelt.py, inbox.py
  agents/         triage.py, brief.py, reel.py, prompts.py
  tools/          strategy_test.py, fno_costs.py
  prefilter.py    playbooks.py   store.py (SQLite)   costs.py (budget guard)
  llm.py          verify.py      lint.py             review.py   pipeline.py   cli.py
config/  prompts/  system/  tests/  docs/
```

## Next milestones

1. **Video layer:** voice (ElevenLabs), avatar clips (HeyGen), Remotion templates that render the scene plan into a 9:16 Reel with charts and document "receipts".
2. **Publishing:** Instagram Graph API (with AI label) and a WhatsApp/newsletter post.
3. **Historian:** licensed price data + event-study engine to answer the brief's history questions.
4. **Strategy Test web page:** the checklist as a free public tool (lead magnet).

## Docs

Strategy and research: [`docs/strategy-research-2026-09.md`](docs/strategy-research-2026-09.md) · [`docs/instagram-first-launch.md`](docs/instagram-first-launch.md) · [`docs/intelligence-system-architecture.md`](docs/intelligence-system-architecture.md) · [`docs/automated-video-pipeline.md`](docs/automated-video-pipeline.md) · [`docs/hindi-script-guide.md`](docs/hindi-script-guide.md) · [`docs/budget-lean-launch.md`](docs/budget-lean-launch.md) · and more in `docs/`.

*Education and research only. Nothing produced by this project is investment advice.*
