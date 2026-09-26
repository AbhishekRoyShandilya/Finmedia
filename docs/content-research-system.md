# Finmedia — Content Catalog & Research System

*What we make, what research each format needs, and how the system makes sure every number and historical claim is accurate. Research date: 26 Sep 2026. Companions: [`strategy-research-2026-09.md`](strategy-research-2026-09.md), [`next-gen-finance-pillar.md`](next-gen-finance-pillar.md), [`voice-and-style-guide.md`](voice-and-style-guide.md).*

---

## 0. The principle

> **The LLM is never the source of a fact. It is the librarian and the writer.**
> Every number, date, quote and historical reaction comes from a stored, cited, timestamped record in our own knowledge base. The model retrieves, compares and drafts; it does not "remember."

That one rule separates us from creators whose videos *sound* deep but can't be traced back to evidence.

**Compliance tiers used below**
- **E**: education/research. Legal now, with no SEBI Research Analyst (RA) registration needed.
- **M**: media/news reporting. Legal now; no recommendations.
- **RA**: needs our SEBI Research Analyst registration (company-specific views, calls, the paid tier).

---

## 1. The complete content catalog

### A. Event-driven (real time, speed matters)

| # | Format | Platform & length | Turnaround | Research it needs | Historical layer it needs | Tier |
|---|---|---|---|---|---|---|
| A1 | **Pre-Market Desk**: what the evening's regulation or event means for tomorrow's open | YouTube 6–10 min + WhatsApp/newsletter card | ≤ 3 hrs after the event | The primary document (circular, consultation paper, filing); a map of which companies are exposed and through which revenue lines; whether it's a proposal or final; the implementation timeline | Past events from the same regulator or of the same type → price reaction at T+1, T+5, T+20, T+60, and whether the final rule was diluted | M → RA for company views |
| A2 | **Market Autopsy**: why X moved 8% today | Reel + YouTube 8–12 min | Same day | A timestamped timeline: exchange announcement, first media report, price and volume by minute, sector and peer moves, broker notes | Prior moves of similar size in the same stock or sector, and what followed | M / RA |
| A3 | **Before the Move**: reconstructing the information timeline | YouTube 10–15 min | 1–3 days | Intraday price, volume and open interest; the disclosure time from the exchange feed; bulk/block deals; option-chain changes; the peer-company timeline | Frequency of "pre-announcement drift" for this event type | M. **Never allege insider trading.** Describe the observable data only |
| A4 | **Policy Day specials**: RBI MPC, Union Budget, GST Council, SEBI board meeting | Live stream + recap + Reels | Live / same day | The official statement, minutes, budget documents, board-meeting press release; line-by-line comparison with the previous version | Market reaction on every past Budget / MPC day; how sectors behaved after similar policy moves | M / E |
| A5 | **Earnings Decoded**: what the results say about the business, not just the EPS | YouTube 8–12 min, Reels | 24–48 hrs | The results filing, investor presentation, earnings-call transcript, segment data; guidance vs. actual | The company's own post-earnings reactions; guidance-accuracy history | RA (company view) / M (facts only) |
| A6 | **Global Spillover**: Fed, crude, rupee, China, US tariffs → Indian sectors | Reel + YouTube | Same day | Official releases (Fed statement, EIA data); FPI flow data; the rupee reference rate | Indian sector sensitivity to past shocks of the same kind | E / M |
| A7 | **Were We Right?**: a 1-day and 30-day post-mortem | YouTube 6–10 min | T+1, T+30 | Our original published claims (timestamped) vs. what happened | Our running scorecard | RA (for calls) / M |

### B. Deep research and documentary (the "Hidden Economy" style, but more rigorous)

| # | Format | Length | Research it needs | Historical layer | Tier |
|---|---|---|---|---|---|
| B1 | **Market Investigations**: how an industry actually makes money and what is changing it | 15–25 min | Business-model graph (value chain, take rates, customer acquisition cost, margins by segment); regulations; company filings across the sector; expert interviews | 10–20 years of the sector's regulation and valuation cycles | E / RA |
| B2 | **India's Financial History documentaries**: scams, crises, turning points | 20–35 min | **Primary record only**: SEBI/RBI orders, JPC reports, court judgments, annual reports, contemporaneous newspapers; a precise timeline | The full market reaction then, and what changed in regulation afterwards | E |
| B3 | **Hidden Systems explainers**: how money really moves (FPI flows, SIP flows, market makers, clearing, IPO grey market, operator mechanics) | 12–20 min | Regulations, exchange rulebooks, AMFI/NSDL data, SEBI studies | Flow data over time; past episodes where the system broke | E |
| B4 | **Forensic patterns**: red flags that preceded past collapses | 15–20 min | **Only adjudicated or officially documented cases** (SEBI orders, court findings, auditor resignations on record) | A pattern library across cases | E. Named living cases only on the public record; legal review before publishing |
| B5 | **Macro India**: inflation, rates, debt, rupee, jobs, and what they mean for your money | 12–20 min | MOSPI, RBI (DBIE database, Bulletin, annual report, Financial Stability Report), Budget, Economic Survey | Long time series of these indicators and how asset classes behaved in each regime | E |

### C. Quant and historical (the PTIS moat)

| # | Format | Research it needs | Historical layer | Tier |
|---|---|---|---|---|
| C1 | **Market Replay**: "we've seen this setup N times, here's what followed" | A precise definition of the setup; point-in-time data | Event study with sample size, median, spread and hit rate | E (index/sector) / RA (single stock) |
| C2 | **Data Stories**: SEBI studies, flows, participation | The official study or dataset | The same metric's history | E |
| C3 | **Seasonality & base rates**: Budget day, expiry day, results season, Diwali (Muhurat) sessions | Official calendars | 15–25 years of the same calendar events | E |
| C4 | **Myth vs Data**: testing popular trading claims | The claim's exact wording; clean data | A backtest including costs and slippage | E |

### D. Next-Gen Finance pillar

| # | Format | Research it needs | Historical layer | Tier |
|---|---|---|---|---|
| D1 | **The Transfer**: why retail money flows to institutions | SEBI F&O studies (FY22–FY26), exchange participant data, algo turnover shares | Year-by-year losses, costs, participation | E |
| D2 | **Build Your Own Edge**: build-alongs | Broker API docs, SEBI retail algo framework, data-licensing terms | Honest backtests | E (open code, no strategy sales) |
| D3 | **The Experiment**: can AI do X? Includes the failures | Our own experiment logs, data and code | Our experiment archive | E |
| D4 | **The Rails**: tokenization and market infrastructure | RBI Unified Markets Interface (UMI) and CBDC reports, SEBI pilots, BIS/IMF papers, RWA.xyz data | Adoption curve of past infrastructure shifts (demat, UPI, T+1) | E |
| D5 | **Decentralized, Decoded** | Official tax rules, RBI/SEBI statements, the draft bill; on-chain data | Crypto regulatory history in India (2018 RBI ban, 2020 Supreme Court reversal, 2022 tax) | E (ASCI disclaimer) |
| D6 | **Open Windows**: monthly special situations (buybacks, open offers, IPO quotas) | SEBI buyback / takeover / ICDR regulations; tax rules; offer letters | Acceptance ratios and returns by past offer | E (stats) / RA (specific offers) |
| D7 | **Borderless Portfolios**: GIFT City, LRS | RBI LRS rules, IFSCA circulars, tax treatment | Currency and diversification history | E |
| D8 | **Investor 2030 / Future Trader** | Regulatory roadmaps, global precedents | Past structural shifts and who won them | E |
| D9 | **Skills & Careers** | Hiring data, role requirements | — | E |

### E. Personal wealth systems

| # | Format | Research it needs | Tier |
|---|---|---|---|
| E1 | **Wealth OS** builds (dashboards, CAS parsing, Account Aggregator) | Sahamati/AA specs, CAS formats | E |
| E2 | **Cost & tax audits**: what your trading or funds really cost | Brokerage and tax rules, the MF expense-ratio (TER) framework | E |

### F. Short-form and distribution

| # | Format | Source | Tier |
|---|---|---|---|
| F1 | **60-Second Intelligence** Reel | Cut from A/B/C/D, one verified number each | Inherits the source's tier |
| F2 | **AI Demo** Reel | D2/D3 screen recordings | E |
| F3 | **Carousel / data card** | Knowledge-base charts | Inherits |
| F4 | **Daily brief** (WhatsApp Channel / newsletter) | A1 + A6 + calendar | M → RA |
| F5 | **Live streams** (Budget, RBI day, Q&A) | A4 | M |

### G. Premium (after RA registration)

| # | Format | Needs |
|---|---|---|
| G1 | Event notes with views and scenarios | RA disclosures, trading-window log, rationale archive |
| G2 | Public scorecard | Every call timestamped, outcomes auto-computed |
| G3 | B2B white-label pre-market desk | Everything above plus SLA and licensing |

---

## 2. The knowledge base the system must hold

Six layers. Build them in this order.

### L1: Official source registry (Tier-1 truth)

The system should watch and archive these, keeping the original document, its publication timestamp (IST, down to the minute where possible) and a content hash:

| Domain | Sources |
|---|---|
| Securities | SEBI (circulars, master circulars, consultation papers, board meeting outcomes, orders and adjudications, studies, bulletins, press releases); **SAT and Supreme Court** orders |
| Banking & money | RBI (monetary policy statements and minutes, notifications, DBIE database, Bulletin, annual report, Financial Stability Report, press releases, Alert List of unauthorized forex platforms) |
| Insurance & pension | IRDAI (regulations, circulars, consultation papers, annual report); PFRDA |
| Fiscal & tax | Union Budget documents, Economic Survey, CBDT notifications, GST Council press releases, Finance Acts |
| Statistics | MOSPI (GDP, CPI, IIP, PLFS), Labour Bureau, commerce ministry trade data |
| Exchanges | NSE/BSE corporate announcements, bulk/block deals, shareholding patterns, F&O bhavcopy, participant-wise open interest, FII/DII provisional data, circulars, index methodology and constituent changes |
| Flows | NSDL FPI daily data, AMFI monthly data (incl. SIP flows), CCIL bond data |
| Companies | Annual reports, quarterly results, investor presentations, earnings-call transcripts, credit-rating actions, MCA filings |
| Competition & sector regulators | CCI, TRAI, CERC, DGCA, and others as needed |
| Global | Federal Reserve (statements, FRED), ECB, BIS, IMF (WEO, GFSR), World Bank, EIA/OPEC (crude), US Treasury |
| Government | PIB, Gazette notifications, Lok Sabha / Rajya Sabha questions and answers |

**Stored status field:** `proposal | draft | final | notified | effective | diluted | withdrawn | stayed_by_court`. Most bad takes come from treating a consultation paper as a final rule.

### L2: Market data (licensed, point-in-time)

- Prices and volumes from an **NSE/BSE-authorized vendor**: EOD first, then intraday. Adjusted for corporate actions, with the unadjusted series also kept.
- **Index constituents as they were on each date.** Without this, every "historical" backtest suffers survivorship bias.
- F&O: open interest, option chains, implied volatility, expiry calendars (including rule changes such as the Nov 2024 weekly-expiry rationalization).
- Delivery %, bulk/block deals, FII/DII flows, MF holdings by month.

### L3: Event database (the moat)

Every event we detect or cover becomes a row. This is what lets us say *"we found 23 comparable events"* truthfully.

```
event_id, event_type (taxonomy below), regulator/source, doc_url, doc_hash,
published_at_ist, market_status_at_publish (pre/during/post-market, holiday),
status (proposal/final/...), status_history[],
affected_sectors[], affected_companies[] with exposure_score + exposure_reason
  (e.g. "insurance distribution = 58% of revenue, FY26 AR p.112"),
reaction: for each company/sector → return T-5, T-1, T0, T+1, T+5, T+20, T+60,
  abnormal return vs sector index and vs Nifty, volume multiple, OI change,
follow_ups: final rule date & dilution %, earnings impact next 4 quarters,
  analyst rating changes, management commentary,
our_coverage: content ids, published_at, claims[], outcome
```

**Event taxonomy (v1):** regulatory (by regulator, and by type: pricing cap, commission cap, disclosure, ban, licensing), monetary policy, fiscal/tax, court ruling, enforcement order, corporate (earnings, guidance, M&A, buyback, open offer, delisting, fund-raise, promoter pledge, auditor resignation, rating action), index change, global macro shock, commodity shock, geopolitical, market-structure change (lot sizes, expiries, margins, settlement cycle).

### L4: Company business-model graph

- Revenue by segment and geography; key revenue drivers and unit economics; the regulators each segment answers to.
- Promoter holding and pledges; related-party intensity; auditor history.
- **Exposure tags** linking companies to regulations and macro variables. For example, `PB Fintech ← IRDAI commission caps (high)`, `OMCs ← crude, fuel-pricing policy`. This powers the automatic exposure map in format A1.

### L5: Historical case files (for documentaries and analogues)

A curated folder per case: a precise timeline, primary documents, key numbers with sources, the market reaction, and the regulatory aftermath. Seed library (India first; **verify every date against the primary record before publishing**):

| Case | Anchor date | Primary record to collect |
|---|---|---|
| 1991 balance-of-payments crisis, gold pledge & liberalisation | 1991 | RBI history volumes, Budget 1991 speech |
| Harshad Mehta securities scam | exposed Apr 1992 | Janakiraman Committee, JPC report |
| Ketan Parekh scam & UTI US-64 crisis | 2001 | JPC report 2002, SEBI orders |
| Global financial crisis (India impact) | Jan & Oct 2008 | RBI annual report 2008-09, market data |
| Satyam fraud | 7 Jan 2009 | Ramalinga Raju letter, SEBI order, court judgment |
| Taper tantrum & rupee crash | May–Aug 2013 | RBI measures, FPI outflow data |
| Demonetisation | 8 Nov 2016 | RBI annual report 2016-17/2017-18, government notification |
| GST rollout | 1 Jul 2017 | GST Council records |
| LTCG reintroduced | Budget, 1 Feb 2018 | Finance Act 2018 |
| RBI crypto banking ban → Supreme Court quashes it | 6 Apr 2018 → 4 Mar 2020 | RBI circular, SC judgment |
| IL&FS default & NBFC crisis | Sep 2018 | MCA/NCLT filings, RBI Financial Stability Reports |
| Corporate tax cut rally | 20 Sep 2019 | Taxation Laws (Amendment) Ordinance 2019 |
| Yes Bank moratorium | 5 Mar 2020 | RBI press releases, reconstruction scheme |
| COVID crash | Mar 2020 | Market-wide circuit data, RBI measures |
| Franklin Templeton debt scheme wind-up | 23 Apr 2020 | SEBI orders, SC proceedings |
| Adani–Hindenburg | 24 Jan 2023 | Hindenburg report, SC expert committee report, SEBI filings |
| RBI action on Paytm Payments Bank | 31 Jan 2024 | RBI press release |
| Budget: F&O STT hike, LTCG to 12.5% | 23 Jul 2024 | Finance (No. 2) Act 2024 |
| Buyback taxed as dividend → reversed | 1 Oct 2024 → 1 Apr 2026 | Finance Acts 2024 & 2026 |
| SEBI F&O curbs (weekly expiries, lot sizes) | Nov 2024 onward | SEBI circular of 1 Oct 2024 |
| SEBI interim order vs Jane Street (index manipulation) | Jul 2025 | SEBI interim order |
| SEBI order vs Avadhut Sathe Trading Academy | 4 Dec 2025 | SEBI order, SAT order of 22 Jan 2026 |
| IRDAI distribution-economics consultation → PB Fintech falls up to 36% | 23–24 Sep 2026 | IRDAI consultation paper, exchange data |

### L6: Our own track record

Every published claim is stored with its timestamp, the exact wording, the evidence cited, the confidence level, and the outcome (computed automatically). This powers "Were We Right?", the public scorecard, and the audit trail SEBI requires from an RA.

---

## 3. Accuracy protocol (how the system avoids being wrong)

### 3a. Source hierarchy

| Tier | Source | Allowed use |
|---|---|---|
| 1 | Official document (regulator, government, exchange, court) or company filing | Can stand alone |
| 2 | Licensed market data; official statistical series | Can stand alone for numbers |
| 3 | Reputable media, broker research, rating agencies | Needs a second independent source, **or** attribution on screen ("according to HSBC…") |
| 4 | Social media, Telegram, forums, unnamed "sources" | Never the basis of a claim. Only as "this is what people are saying" |

### 3b. Rules that are hard-coded into the pipeline

1. **Every number has a citation**: source, document, page/table, retrieval date. A script without citations can't move to production.
2. **Point-in-time discipline.** Historical analysis uses only what was knowable then: as-of constituents, the announcement time vs. market hours, no look-ahead.
3. **Timestamps in IST, with market status.** "Released at 6:10 pm after the close" is the difference between insight and hindsight.
4. **Proposal ≠ rule.** Status is always stated on screen.
5. **Base rates come with their spread.** Never "stocks rise 12% after X." Say "in 23 cases the median was +4%, the range was −18% to +31%, and 15 of 23 were positive." Always show N.
6. **Similarity criteria are published.** State what counted as a "comparable event" and what didn't.
7. **Costs are included** in every backtest (brokerage, STT, slippage, impact).
8. **Automated fact-check pass.** A second model cross-checks every numeric claim in the script against L1–L3 and flags anything unsupported.
9. **Human sign-off.** A named person approves every script. For company-specific views, the RA signs off with disclosures.
10. **Public corrections log.** Mistakes are corrected on screen and logged. That builds credibility over time.

### 3c. Methods for "historical impact" (standard, defensible)

- **Event study:** abnormal return = stock return − expected return (market model, or sector index as the benchmark), over windows T−5…T+60. Report cumulative abnormal returns with confidence intervals when N is large enough.
- **Analogue matching:** events with the same type, the same regulator and similar exposure. Rank by similarity; show the top matches with their differences.
- **Regime tagging:** bull, bear or sideways; high or low volatility; rate cycle. A reaction in 2013 may not transfer to 2026.
- **Confounders:** flag same-day results, index rebalances and global shocks that contaminate the reaction.

---

## 4. The pipeline, format by format

```
L1 watchers (circulars/filings/data)  ─┐
L2 licensed market data               ─┼─→ Event detection & classification (L3 row created)
Calendar (MPC, Budget, results)       ─┘            │
                                                    ├─→ Exposure map (L4)
                                                    ├─→ Analogue search + event study (L3/L2)
                                                    ├─→ Case-file lookup (L5) for narrative depth
                                                    ▼
                                        Research brief (all claims cited)
                                                    ▼
                                  Script draft in house voice (see style guide)
                                                    ▼
                         Fact-check model → compliance gate → human/RA sign-off
                                                    ▼
                       Production (VO/twin/mascot + charts from L2) → distribution
                                                    ▼
                                    Claims logged to L6 → outcomes computed
```

**Build order (MVP → moat)**
1. L1 watchers for SEBI, RBI, IRDAI and NSE/BSE announcements, plus an archive with hashes.
2. L2 EOD licensed data and as-of index constituents.
3. L3 schema, backfilled with the ~25 seed cases above plus the last 3 years of major regulatory events.
4. L4 exposure tags for the Nifty 500 (start with regulation-sensitive sectors: insurance, NBFCs, OMCs, telecom, power, pharma, gaming, capital-markets companies).
5. The event-study engine and analogue matcher.
6. L6 track record, plus the scorecard page.

---

## 5. Sources used in this document

- Earlier research docs in this folder (SEBI F&O studies, IRDAI case, regulatory framework) and their source lists.
- [SEBI](https://www.sebi.gov.in) · [RBI](https://www.rbi.org.in) · [IRDAI](https://irdai.gov.in) · [NSE](https://www.nseindia.com) · [MOSPI](https://www.mospi.gov.in) · [AMFI](https://www.amfiindia.com) · [NSDL FPI](https://www.fpi.nsdl.co.in): the official sources the L1 registry should monitor.
