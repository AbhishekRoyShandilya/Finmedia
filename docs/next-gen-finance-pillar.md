# Finmedia — The "Next-Gen Finance" Pillar

*How we lead young investors and traders from the way they invest today to the way money will work next. Research date: 26 Sep 2026. Companion to [`strategy-research-2026-09.md`](strategy-research-2026-09.md).*

---

## 0. The approach in one paragraph

**We don't teach finance. We map where money is moving next, prove it with data, and show people how to position themselves before it becomes mainstream**, through skills, systems and capital. Every piece of content answers four questions:

1. **What is shifting?** (evidence, not opinion)
2. **Who is winning from it today, and why?** (the mechanism)
3. **Where is the window?** (why it's open now, and what will close it)
4. **What should you do this week?** (a skill to learn, a system to build, a change to how capital is positioned; never a stock tip)

We aren't an exam teacher ("what is an option"), a tip seller ("buy this"), or a hype channel ("crypto will 100x"). We're the people who read the SEBI studies, the RBI annual report and the regulator circulars, then turn them into *"here's what this means for your money and career."*

---

## 1. The core thesis: why today's retail approach won't survive

This is the anchor story for the whole pillar, and SEBI's own data backs it.

### 1a. The transfer is real, and in FY24 it was nearly rupee-for-rupee

| Metric | Figure | Source period |
|---|---|---|
| Individual traders' F&O losses (before costs) | **₹61,000+ crore** | FY24 |
| Proprietary traders' gross trading profit | ₹33,000 crore | FY24 |
| FPIs' gross trading profit | ₹28,000 crore | FY24 |
| **Prop + FPI combined** | **≈ ₹61,000 crore** | FY24 |
| Share of FPI / prop profits made by algo trading | 97% / 96% | FY24 |
| Individuals who lost money | 87.7% | FY26 |
| Individuals' aggregate net loss | ₹91,685 crore | FY26 |
| Prop / FPI gross profit | ~₹44,000 cr / ~₹14,000 cr | FY26 |
| **Share of prop + FPI profits made by algo entities** | **99%** | FY26 |
| Transaction costs paid by individuals | ~₹25,000 cr (FY26); ~₹1 lakh cr (FY22–FY26) | FY22–FY26 |
| Index options turnover in same-day-expiry (0DTE) contracts | ~59% | FY26 |
| Algo share of NSE turnover | 54% cash, 69% derivatives | Q1 FY26 |
| Traders who lost two years in a row, kept trading, and lost again | ~90% | FY26 study |

**Your intuition is right, and it's the most powerful hook we have.** In FY24, what individuals lost in F&O (before costs) almost exactly equals what prop firms and foreign investors made. Almost all of that institutional profit came from machines. In FY26 retail lost less, but the institutional profit was still 99% algorithmic.

### 1b. The mechanism: why the money flows one way

Explain this properly and the audience never forgets it:

1. **Speed.** Algos react in microseconds. Retail reacts to the headline, to the Telegram forward, or to a price that has already moved.
2. **Pricing.** Institutions price volatility with models, while retail buys options as lottery tickets. With 59% of index options turnover in 0DTE contracts, retail is often buying expensive, fast-decaying premium from people who priced it better.
3. **Costs.** ₹1 lakh crore in five years goes to brokers, exchanges and taxes. Most retail strategies can't overcome that drag.
4. **Behavior.** No position sizing and no written rules. Revenge trading after losses. Stopping after one big win. Machines don't have these leaks.
5. **Information processing.** Institutions read every filing and circular systematically. Retail reads summaries of summaries.
6. **Capital and diversification.** Institutions run hundreds of small, uncorrelated bets. Retail runs a few big, correlated ones.

### 1c. The honest counter-thesis: where retail *does* have an edge

This is what makes us different from the "90% lose, so give up" channels. The message is **stop fighting where you're structurally weak, and compete where the structure favors you:**

| Retail advantage | Why institutions can't copy it |
|---|---|
| **Time horizon** | Funds are judged quarterly. You can hold for 5 years through a drawdown. |
| **Small size** | You can buy a ₹500-crore small-cap position that a ₹50,000-crore fund can't use. |
| **No benchmark or career risk** | You can hold cash, stay out of the market, or look "wrong" for a year. |
| **Retail-only structures** | Small-shareholder quotas in buybacks, retail IPO quotas. These are reserved for you by regulation. |
| **Domain knowledge** | A nurse understands hospitals; an engineer understands the capex cycle. That's an information edge in *your* sector. |
| **Doing nothing** | The cheapest strategy, and one most traders and institutions don't use. |
| **Using the same tools cheaply** | Free broker APIs, and LLMs that read filings for ₹2–5k/month. The tooling gap is closing faster than people realize. |

The pillar is built around this: **the future isn't "retail vs. machines." It's retail *with* machines, used where the retail structure wins.**

---

## 2. The eight shifts (the thesis map)

Each shift is a recurring content theme. For each one: what is happening, where the window is, how to position, and what closes the window.

### Shift 1: Algo trading goes retail (and becomes legal and structured)

- **What's happening:** SEBI's retail algo framework (circular of 4 Feb 2025) has been mandatory for all brokers since **1 Apr 2026**.
  - DIY algos via a broker API need **no exchange registration below 10 orders per second**, but do need a static IP and daily authentication.
  - Your own algo may be used by your immediate family.
  - Zerodha made its trading API **free for personal use** (Feb–Mar 2025).
  - Selling "black-box" strategies requires RA registration plus exchange empanelment as an algo provider.
- **The window:** the rails are now legal and cheap, but most retail can't code, and most coders don't understand markets. People who learn both *now* get:
  - a systematic, rule-based personal process (the real edge is **discipline**, not speed);
  - a career skill institutions pay for;
  - a business option (empanelled algo provider, tools).
- **How to position:** Python + a broker API + honest backtesting (with costs and slippage) + rules that sit well below 10 orders per second. Target the medium-frequency, small-capacity strategies institutions ignore. **Never try to beat HFT on speed.**
- **What closes it:** brokers shipping no-code AI strategy builders to everyone (1–3 years). After that the edge moves to *which* rules you run, not *whether* you can automate them.

### Shift 2: AI becomes the retail analyst

- **What's happening:** institutions already use machines to read filings, circulars and transcripts. LLMs now do this for a retail budget. Our IRDAI example: the consultation paper came out on the evening of 23 Sep 2026, PB Fintech fell up to 36% the next day, and the whole evening was available to analyze it.
- **The window:** retail doesn't yet use AI *systematically*: as a watcher of every regulator and filing feed, or as a mapper of which companies are exposed to which events. Most people use ChatGPT to ask "should I buy X?", which is the worst possible use.
- **How to position:** build a personal "research desk":
  - a feed watcher (SEBI, RBI, IRDAI, NSE/BSE announcements);
  - an LLM summarizer and exposure mapper;
  - a watchlist trigger;
  - a journal.
  - We teach the exact build.
- **What closes it:** brokers embedding AI research in their apps. That's already starting, but it will be generic. A *personal* system tuned to your holdings stays an edge.

### Shift 3: The personal "wealth OS"

- **What's happening:** India's data rails are ahead of its consumer tools.
  - The Account Aggregator network has ~294–310M linked accounts and 450–500M fulfilled consents.
  - RBI recognized Sahamati as the network's self-regulatory organization in Jun 2026.
  - Consolidated account statements (CAS) cover all demat and mutual fund holdings.
  - Broker APIs are free.
- **The window:** almost nobody under 30 has one dashboard with their actual net worth, allocation, risk, costs paid and tax position. People who do make better decisions and stop trading out of boredom.
- **How to position:** build your own tracker (CAS parser + broker API + spreadsheet or Python + a monthly AI review). Content: "Build your wealth OS in a weekend."
- **Business link:** this is PTIS's consumer entry point.

### Shift 4: Tokenization, the rails of the next financial system

- **What's happening globally:**
  - Tokenized real-world assets reached **~$33.7B** by May 2026, up from $5.4B at the start of 2025.
  - Tokenized US Treasuries are **~$13.5B**.
  - BlackRock's tokenized money-market fund **BUIDL** passed **$2.8B** (Jul 2026).
- **What's happening in India:**
  - RBI's **Unified Markets Interface** is piloting tokenized certificates of deposit, settled in wholesale CBDC: ~248 transactions worth **₹17,000 crore**. Gold tokenization is being explored.
  - SEBI approved a **DLT pilot for corporate-bond trading and settlement**.
  - **SM REITs** (min. ₹10–15k investment) already give regulated fractional ownership of real estate.
- **The honest take (this is what makes us credible):** retail India has **no direct tokenized product worth chasing today**. What's exploitable now is:
  1. **Knowledge and career.** Tokenization, DLT settlement and compliance engineers are scarce. This is the biggest window for young viewers.
  2. **Regulated proxies for fractional ownership.** SM REITs, REITs/InvITs, and GIFT City products.
  3. **Understanding the infrastructure layer.** Which *types* of businesses (depositories, exchanges, registrars, bank tech) are building the rails. We cover this at the sector level; company-specific views need our RA license.
  4. **Being ready for access.** When UMI or a SEBI framework opens to retail, the people who already understand it move first.
- **What closes it:** retail access and mainstream products (roughly 2028–2032). At that point the knowledge edge becomes common.
- **Trap to warn about:** offshore "tokenized asset" or "fractional real estate" apps that are outside SM REIT rules. They are unregulated, and there's no recourse.

### Shift 5: Decentralized finance: learn the ideas, respect the tax and legal walls

- **Reality in India (2026):**
  - a flat **30% tax** on crypto (virtual digital asset) gains, **1% TDS**, and **no loss set-off** (confirmed again in Budget 2026-27);
  - stablecoins are a legal grey zone (the ED has alleged ₹2,500 cr of unauthorized cross-border stablecoin transfers under FEMA);
  - a comprehensive digital-asset bill is still in committee.
- **Our angle:** the *ideas* from DeFi (24×7 markets, instant settlement, programmable money, self-custody) are **moving into regulated rails**: UMI, wholesale CBDC, T+0 settlement. Understanding DeFi is how you understand the future of TradFi, whether or not you own any tokens.
- **How to position:** learn the mechanics (wallets, smart contracts, stablecoins, how on-chain lending works). At most a small, tax-aware allocation. Compliance first.
- **Rule for us:** any crypto-related promotion must carry ASCI's mandatory disclaimer (*"Crypto products and NFTs are unregulated and can be highly risky. There may be no regulatory recourse for any loss from such transactions."*). Never promote offshore exchanges or derivatives platforms that aren't authorized in India.

### Shift 6: Borderless portfolios (GIFT City and LRS)

- **What's happening:** residents can invest abroad up to **$250,000 a year** under RBI's Liberalised Remittance Scheme (LRS). **NSE IX (in GIFT City) lists receipts for US stocks** (unsponsored depository receipts, "UDRs"), and GIFT City has retail outbound funds. UDRs held over 2 years pay 12.5% long-term capital gains tax.
- **The window:** the product shelf is expanding but awareness is low. Most young investors are 100% India, and heavily concentrated in small caps and F&O.
- **How to position:** research on concentration risk, the cost of different routes (GIFT City vs. overseas broker vs. international mutual fund), and currency diversification. Education, not product pushing.

### Shift 7: Retail-only structural edges ("special situations")

- **Example: the buyback reset.**
  - From 1 Oct 2024, buyback proceeds were taxed as deemed dividend, and buybacks collapsed ~84% (₹49,836 cr in FY24 → ₹7,897 cr in FY25).
  - **Budget 2026 reversed this:** from **1 Apr 2026** buybacks are taxed as capital gains again, on actual gains only. Expect buybacks to revive.
  - SEBI's buyback rules reserve part of every tender offer for **small shareholders**. This is a structural retail-only edge. *(Verify the current reservation % and small-shareholder threshold in SEBI's Buy-back Regulations before publishing.)*
- **Other retail-only structures:** retail and shareholder quotas in IPOs, open offers, delisting offers, rights issues.
- **Our angle:** show the historical base rates (acceptance ratios, returns, the risks) and a checklist. **Pre-RA we publish statistics and mechanics only, not "tender in company X."**
- **What closes it:** crowding. When everyone chases the same structure, the returns compress. That's why monthly "windows" content has a shelf life, which keeps the audience coming back.

### Shift 8: The income side of wealth (skills as an asset class)

- For a 22-year-old, the biggest "investment return" is **career capital**. Quant, data, AI, tokenization and fintech-compliance skills are exactly what the institutions that capture the money are hiring for.
- **Content:** "The jobs capturing the ₹58,000 crore": what prop desks, FPIs, exchanges and fintechs actually hire, and a 12-month learning path.
- **Positioning:** "If you can't beat them yet, get paid by them while you build your own system."

---

## 3. How we define "exploitable before mainstream"

Use a consistent framework so the audience learns how to think, not just what to think.

### The window model

```
Stage 1: Rails appear       → regulation/infra quietly published (circulars, pilots)
                               Edge: KNOWLEDGE (read what others don't)
Stage 2: Builders arrive    → specialists, early tools, niche communities
                               Edge: SKILL (can build/use what others can't)
Stage 3: Products launch    → apps, funds, broker features
                               Edge: ACCESS/POSITIONING (early users, early capital)
Stage 4: Mainstream         → ads, influencers, everyone's cousin
                               Edge: GONE (costs, crowding, hype)
```

| Shift | Stage today (Sep 2026) | Primary edge to exploit now |
|---|---|---|
| Retail algo trading | Stage 2 → 3 | Skill |
| AI research desk | Stage 2 | Skill + knowledge |
| Personal wealth OS | Stage 2 | Skill |
| Tokenization (India) | Stage 1 | Knowledge + career |
| DeFi ideas → TradFi rails | Stage 1–2 | Knowledge |
| GIFT City / global portfolios | Stage 2 → 3 | Access |
| Buyback revival / special situations | Stage 3 (reopened by tax change) | Access (retail quotas) |
| Skills-as-asset | Stage 2 | Skill |

### What counts as a legitimate edge vs. a trap

| Legitimate asymmetry (we teach it) | Trap disguised as an "edge" (we expose it) |
|---|---|
| **Information:** public but under-read sources (circulars, filings, SEBI studies) | "Inside" tips, paid Telegram calls, "operator" stocks |
| **Skill:** coding, data, AI, honest backtesting | Buying someone's "95% accuracy" algo or bot |
| **Access:** regulated but under-used routes (GIFT City, SM REITs, retail quotas) | Offshore forex and crypto-derivative apps. RBI keeps an *Alert List* of unauthorized forex platforms, and trading on them is illegal |
| **Structure:** time horizon, small size, no benchmark | "Loopholes" that are actually tax evasion or FEMA violations |

This table is itself a flagship video: **"Real edges vs. fake edges: what's actually exploitable in 2026."**

---

## 4. Audience and journey

| Segment | Where they are | What they need | Our path |
|---|---|---|---|
| **Youth (18–25)** | First salary, F&O curious, influencer-fed | A reality check + career skills | "The Transfer" series → skills path → wealth OS |
| **Losing trader** | Active in F&O, down money | Permission to stop + a better process | Data on 0DTE/costs → rules-based systems → "retail edges" |
| **Investor (25–40)** | SIPs, some stocks, no system | Structure, global diversification, tax awareness | Wealth OS → GIFT City → special situations |
| **Builder** | Can code, wants to trade or build a product | Market understanding + compliance map | Algo build-alongs → AI research desk → algo empanelment / career |

**Product ladder** (every step builds trust for the next):
1. Free content (YouTube, Reels, newsletter).
2. Free open-source templates: "Wealth OS starter," "AI circular watcher," "Honest backtester."
3. Paid cohort: *"Build your AI market analyst in 4 weeks."* Strictly education, with no returns claimed.
4. Paid RA research: the pre-market desk and event notes (once registered).
5. PTIS tools (subscription).
6. B2B: licensing to brokers and media.

---

## 5. Content architecture: the flagship series

Quality bar for every episode (publish only if it passes at least 3 of 4):
- ✅ **Original data or analysis** (not a summary of someone else's video)
- ✅ **A counter-intuitive finding** (the "wait, what?" moment)
- ✅ **A time window** (why this matters *now*)
- ✅ **A concrete action** (skill, system or positioning step to take this week)

### Series 1: "The Transfer" (why retail money flows to institutions)
1. *₹61,000 crore: the year retail losses matched institutional profits almost to the rupee*
2. *99% of the winners were machines: inside SEBI's FY26 derivatives study*
3. *The 0DTE casino: why 59% of index options trading happens on expiry day*
4. *₹1 lakh crore in fees: the silent partner in every trade*
5. *Where retail actually wins: 7 structural edges institutions can't copy*
6. *The 90% who keep losing: what SEBI's data says about people who don't stop*

### Series 2: "Build Your Own Edge" (build-alongs with real code)
1. *Your first rules-based strategy on a free broker API: legal, under 10 orders/sec*
2. *An AI that reads every SEBI, RBI and IRDAI circular before you wake up*
3. *Build your wealth OS in a weekend (CAS + broker API + AI monthly review)*
4. *We backtested it honestly: costs, slippage and the edge that disappeared*
5. *Our AI strategy failed. Here's exactly why.* (failure episodes build trust)
6. *From retail trader to algo provider: what empanelment actually requires*

### Series 3: "The Rails" (tokenization and financial infrastructure)
1. *RBI already moved ₹17,000 crore on tokenized rails. Almost nobody noticed.*
2. *BlackRock tokenized a money-market fund. What that means for your FD.*
3. *UMI explained: what a T+0, programmable financial system looks like*
4. *The businesses building the rails* (sector-level research; company views only as an RA)
5. *Fractional real estate: SM REITs vs. the unregulated apps*
6. *Tokenization careers: the skills that will be scarce in 2028*

### Series 4: "Decentralized, Decoded"
1. *DeFi in 12 minutes, for people who hate crypto hype*
2. *Why India taxes crypto at 30%, and what the new digital-asset bill could change*
3. *Stablecoins: the grey zone that could reshape remittances*
4. *What TradFi is quietly copying from DeFi*

### Series 5: "Open Windows" (monthly)
*"3 windows open, 1 closing."* For example: the buyback revival after the Budget 2026 tax change, GIFT City's expanding shelf, a new SEBI pilot. Built from our event pipeline, with mechanics and base rates only (no stock calls before registration).

### Series 6: "Investor 2030" (big-picture market structure)
- *AI agents will trade for you. Who's liable when they're wrong?*
- *What happens to brokers when trading is free and AI is the advisor?*
- *T+0, 24×7, tokenized: what Indian markets look like in 2030*

### Reels translation (per episode)
- **Hook:** the single most surprising number ("₹61,000 crore lost, ₹61,000 crore made").
- **Visual:** money flowing from a crowd of phones to a server rack.
- **Payoff:** one retail edge or one action.
- **CTA:** full research on YouTube, plus the free template.

---

## 6. Compliance fit

Most of this pillar is **education and research, which is legal without RA registration** as long as we follow these rules:
- **No security-specific recommendations.** "Businesses building the rails" stays at sector level until we have the RA license.
- **No return or performance claims** for strategies, cohorts or students (the Avadhut Sathe case turned on exactly this).
- **Price data in education content** follows SEBI's 30-day lag (from 1 Jul 2026) if we want broker or registered-entity partnerships.
- **Selling algos:** a black-box strategy needs RA registration plus exchange empanelment. Open-source educational code is fine.
- **Crypto:** ASCI's disclaimer on any promotion. Never promote unauthorized platforms (RBI Alert List).
- **AI avatar delivery:** disclosed, with a real named human owning the analysis (see the main strategy doc).

---

## 7. First 12 weeks for this pillar

| Week | YouTube flagship | Reels (per week) | Free asset / tool |
|---|---|---|---|
| 1 | The Transfer #1 (₹61,000 cr) | 4 × transfer stats | "Your F&O reality check" calculator |
| 2 | The Rails #1 (RBI tokenized ₹17,000 cr) | 3 × tokenization myths | — |
| 3 | Build #2 (AI circular reader) | 3 × "AI read this so you don't have to" | Open-source circular watcher |
| 4 | The Transfer #3 (0DTE casino) | 4 | — |
| 5 | Build #3 (wealth OS) | 3 | Wealth OS starter template |
| 6 | Open Windows #1 (buyback revival) | 3 | Buyback base-rate sheet |
| 7 | Decoded #1 (DeFi in 12 min) | 3 | — |
| 8 | The Transfer #5 (retail edges) | 4 | — |
| 9 | Build #1 (first rules-based algo) | 3 | Honest backtester template |
| 10 | The Rails #2 (BUIDL vs your FD) | 3 | — |
| 11 | Build #5 (our AI strategy failed) | 3 | — |
| 12 | Investor 2030 #1 | 3 | Cohort waitlist opens |

**Metrics to watch:** 50% view-duration on flagships, template downloads per 1,000 views, newsletter sign-ups, and cohort waitlist size. The **template → newsletter → cohort** conversion is the signal that this pillar is building a business, not just views.

---

## Sources

**SEBI derivatives studies and market structure**
- [Open Magazine — SEBI FY26 F&O loss study explained](https://openthemagazine.com/business/sebi-fo-loss-study-explained-why-9-in-10-retail-traders-lost-91685-crore-in-fy26)
- [CorpLawUpdates — SEBI equity derivatives study FY26](https://www.corplawupdates.in/updates/sebi-equity-derivatives-retail-trader-study-fy26)
- [AIBI — SEBI study: 93% of individual traders lost money FY22–FY24 (PDF)](https://aibi.org.in/Sebipr/Updated_SEBI_Study_Reveals_93_percentage_of_Individual_Traders_Incurred_Losses_in_Equity_F&O_between_FY22_and_FY24.pdf)
- [Wright Research — ₹1.8 lakh crore losses over 3 years](https://www.wrightresearch.in/blog/sebi-futures-and-option-report-individual-traders-in-fandos-incur-rs-18-lakh-crore-loss-over-3-years/)
- [Business Standard — Net losses widened in FY25](https://www.business-standard.com/amp/markets/news/net-losses-of-traders-in-fo-widens-in-fy25-sebi-study-125070701221_1.html)
- [Multibagg — Algo trading 69% of NSE derivatives turnover](https://www.multibagg.ai/market-pulse/articles/ipo/nse-algorithmic-trading-derivatives-turnover-rhp-cmufcpv210014bznvcom3hnfk)
- [Investing.com — Colocation 35.7%, algo trading 53% on NSE](https://in.investing.com/news/colocation-hits-357-algo-trading-surges-to-53-the-techdriven-shift-in-nse-4655643)

**Retail algo framework and tools**
- [HDFC Sky — SEBI algo trading rules 2026](https://hdfcsky.com/sky-learn/algo-trading/sebi-algo-trading-rules)
- [Tradejini — SEBI's new algo rules from April 2026](https://www.tradejini.com/blogs/what-sebis-new-algo-trading-rules-mean-for-you)
- [QuantInsti — Algorithmic trading in India 2026](https://www.quantinsti.com/articles/algorithmic-trading-india/)
- [Zerodha — Free personal APIs from Kite Connect](https://zerodha.com/z-connect/updates/free-personal-apis-from-kite-connect)
- [Sahamati — Account Aggregator ecosystem](https://sahamati.org.in/)
- [CASParser — State of Account Aggregator in 2026](https://casparser.in/blog/state-of-account-aggregator-2026/)

**Tokenization and infrastructure**
- [Vajiram & Ravi — RBI Unified Markets Interface](https://vajiramandravi.com/current-affairs/rbi-unified-markets-interface/)
- [Social News XYZ — RBI expands e-rupee pilots, tokenised CD trial (May 2026)](https://www.socialnews.xyz/2026/05/29/rbi-expands-e-rupee-pilots-starts-tokenised-credit-deposit-trial)
- [Univest — RBI explores tokenising gold](https://univest.in/blogs/rbi-gold-tokenisation-unified-markets-interface)
- [Outlook Money — SEBI blockchain framework for corporate bonds](https://www.outlookmoney.com/invest/sebi-mulls-formation-of-working-group-to-build-blockchain-based-corporate-bond-framework)
- [Finextra — Tokenized RWAs: reading the 2026 numbers](https://www.finextra.com/blogposting/31625/tokenized-real-world-assets-reading-the-2026-numbers-behind-the-headline-growth)
- [Altrady — BlackRock BUIDL guide 2026](https://www.altrady.com/blog/cryptocurrency/blackrock-buidl-tokenized-treasury-2026)
- [RMLNLU Law Review — India's tokenisation challenge](https://rmlnlulawreview.com/2026/07/25/indias-tokenisation-challenge-from-grey-zones-to-clarity/)
- [Maheshwari & Co — Real estate tokenization legal guide (SM REITs)](https://www.maheshwariandco.com/blog/real-estate-tokenization/)

**Crypto, global investing, tax**
- [KuCoin — India maintains 30% crypto tax and 1% TDS for 2026-27](https://www.kucoin.com/news/flash/india-maintains-30-crypto-tax-and-1-tds-for-2026-2027)
- [Coinpedia — Crypto regulations India 2026](https://coinpedia.org/cryptocurrency-regulation/crypto-regulations-india/)
- [Khaitan & Co — ASCI crypto/NFT advertising guidelines](https://www.khaitanco.com/thought-leaderships/ASCI-releases-crypto-and-NFT-advertising-guidelines-effective-1-April-22-onward)
- [Vested — GIFT City explained (2026)](https://vestedfinance.com/blog/gift-city/what-is-gift-city/)
- [Upstox — Tax on US stocks via GIFT City](https://upstox.com/news/personal-finance/tax/buying-us-stocks-via-gift-city-know-the-tax-implications/article-195582/)
- [TaxGuru — Buyback tax from 1 Oct 2024](https://taxguru.in/income-tax/buyback-tax-shifted-shareholders-deemed-dividend-october-2024.html)
- [Vinod Kothari — How new taxation rules impact buybacks](https://vinodkothari.com/2026/02/from-bye-backs-to-buy-backs-how-new-taxation-rules-impact-equity-extraction/)
- [CAalley — Budget 2026: buybacks taxed as capital gains](https://www.caalley.com/news-updates/budget-2026/budget-2026-buy-back-proceeds-will-be-taxed-as-capital-gains-for-shareholders-but-promoters-pay-an-extra-price)
