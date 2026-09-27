# Finmedia — Instagram-First Launch Plan

*Decided 27 Sep 2026: we build the research and video pipelines for **Instagram Reels first**, and start YouTube once Reels gain reach. This doc covers the launch plan, the "visible effort" rules both platforms reward, and the new **Strategy Reality Check** content pillar. Companions: [`automated-video-pipeline.md`](automated-video-pipeline.md), [`budget-lean-launch.md`](budget-lean-launch.md), [`next-gen-finance-pillar.md`](next-gen-finance-pillar.md).*

---

## 1. Why Instagram first works

| Reason | Detail |
|---|---|
| **Cheaper to run** | Only ~25 min of finished video a month (30 Reels) instead of 120–175 min. Voice and avatar costs drop a lot (§6) |
| **Faster feedback** | **Trial Reels** show a Reel to non-followers first. We can test hooks and topics without affecting our main followers, and Instagram can auto-share winners to followers after 72 hours |
| **Buys time on YouTube policy** | YouTube's AI-persona rules for finance are uncertain (see [`automated-video-pipeline.md`](automated-video-pipeline.md) §9). Building an audience and proof on Instagram first reduces that risk |
| **Builds the funnel early** | Reels → WhatsApp Channel / newsletter → later paid research. The funnel matters more than any single platform |

**What Instagram doesn't do:** it doesn't pay steady ad revenue for Reels the way YouTube does. On Instagram, the business value is **audience, trust and sign-ups**, not ad income.

---

## 2. Instagram rules that shape our Reels (checked Sep 2026)

| Rule | What it means for us |
|---|---|
| **Original content only.** Since 30 Apr 2026, accounts that mostly repost others' content lose recommendations to non-followers (the penalty now covers photos and carousels too, not just Reels) | Every Reel is our own research, visuals and narration. Never re-upload others' clips, and never screen-record other creators' videos |
| **AI disclosure required.** Meta requires its AI label for photorealistic AI video or realistic AI audio, and may penalize missing labels. A correct label isn't reported to reduce reach | Turn on the AI label on every Reel with the twin or cloned voice, plus our on-screen label (India IT Rules 2026) |
| **Length:** Reels can be up to 3 minutes, but longer Reels are shown mostly to existing followers | Discovery Reels: 30–60 s. Deeper "mini-explainers": 60–90 s |
| **Publishing API** needs a Professional (Creator/Business) account; capped at roughly 25–50 API posts per 24 h, and most accounts can publish Reels up to 90 s via the API | Plenty for 1 Reel/day; Reels over 90 s get uploaded manually |

---

## 3. Visible effort: what both platforms reward (and YouTube will review later)

YouTube's Partner Program review is done by a **human reviewer** who checks whether the channel is original, not reused or template-made, and Instagram's ranking now pushes original content. Our automated pipeline must therefore produce **visibly crafted** videos, not template filler.

**Minimum "effort signals" in every Reel and video:**

| Signal | Rule |
|---|---|
| **Original research** | At least one number or finding we computed or sourced ourselves, cited on screen |
| **Custom visuals** | At least 2 visual types per Reel (chart, highlighted document, animation, map, text card), plus the avatar. Never avatar-only |
| **Motion and design** | Animated charts, highlights and transitions made for this topic. No static slideshow |
| **Sound design** | A music bed that drops out at the key reveal; clean, levelled voice |
| **Captions** | Hand-checked Hindi captions (not raw auto-captions) |
| **Variety** | Rotate 6–8 layouts and 2 avatar looks; the scene plan must not produce the same structure every day |
| **Perspective** | Every Reel makes a point or an argument, never just "news read aloud" |
| **Series identity** | Named series with a consistent intro card, so the channel looks like a publication, not a content farm |

**Keep the proof:** archive each video's scene plan, sources and project files. If a platform ever questions originality, we can show the work behind every video.

---

## 4. New content pillar: Strategy Reality Check

Two recurring series aimed squarely at active traders, who are some of the most engaged viewers in Indian finance content.

### 4a. "पुरानी Strategy, नया Market": why your 2022–23 strategy is failing now

The core insight: **many strategies from 2022–23 aren't just performing worse; the market rules they relied on no longer exist.** Each change below is a Reel (and later a YouTube episode):

| Date | What changed | Why old strategies break |
|---|---|---|
| **1 Oct 2024** | STT on F&O raised: futures 0.0125% → 0.02%, options 0.0625% → 0.10% | Every trade costs more. High-frequency scalping edges that were thin before can now be negative |
| **20 Nov 2024** | Weekly expiry limited to **one index per exchange** (Nifty on NSE, Sensex on BSE). BankNifty, FinNifty and Midcap Nifty weekly expiries ended | **"BankNifty expiry-day strategies" can't be run any more.** The contract is gone |
| **20 Nov 2024** | Minimum index-derivative contract value raised to **₹15 lakh** (from ₹5–10 lakh); extra 2% margin (ELM) on short options on expiry day | Bigger lots mean more capital per trade and bigger losses per mistake. Option-selling on expiry day costs more margin |
| **1 Feb 2025** | **Upfront premium collection** from option buyers; **no calendar-spread margin benefit on expiry day** | Leverage tricks and cheap expiry-day spreads stopped working |
| **1 Apr 2025** | **Intraday monitoring** of position limits | Positions that were only checked at day-end are now checked during the day |
| **1 Sep 2025** | Expiry days moved: **NSE to Tuesday, BSE to Thursday** | 25 years of "Thursday expiry" habits, backtests and weekly rhythms no longer match reality |
| **1 Apr 2026** | **STT raised again (Budget 2026):** futures 0.02% → **0.05%**, options premium 0.10% → **0.15%**, exercised options 0.125% → 0.15% | A 20-point Nifty futures trade (1 lot of 75) that kept ~₹1,095 after costs under 2023 rules keeps only ~₹392 now (our cost calculator; verify before publishing). Scalping and small-target strategies are hit hardest |
| **1 Apr 2026** | Retail algo framework fully in force (APIs, static IP, orders-per-second limits) | Old API bots and "shared algos" need rework or registration |
| **3 Aug 2026** | **Closing Auction Session (CAS)** for F&O stocks: continuous trading stops at 3:15 pm; the closing price comes from a 3:15–3:35 pm auction. SEBI opened a consultation on 12 Sep 2026 to review it | Strategies built on the last-30-minute VWAP close, or on closing-price behaviour, now face a different mechanism. **Still changing:** cover it as "proposal/consultation," not final |
| **Ongoing** | Algos are now ~69% of derivatives turnover; retail premium turnover and active retail traders fell ~20% after the new rules | Crowding and faster competitors wipe out simple, widely shared edges |

Also cover the **non-rule reasons** strategies decay:
- **Market regime:** trending vs range-bound, volatility high vs low.
- **Crowding:** once a strategy is on YouTube, everyone trades it.
- **Survivorship:** you only hear about the strategies that happened to work.

> Before production, confirm each date and number from the primary circular (SEBI/NSE/BSE/Finance Act). Cover pending items (like the CAS consultation) as proposals, not final rules.

### 4b. "5-Minute Strategy Test": how to check any strategy you saw online

A repeatable checklist the audience can apply to any strategy an influencer shows. It works as a series, a free downloadable checklist, and later a free web tool.

**The 10 questions (each: 🟢 / 🟡 / 🔴):**

| # | Question | Red flag |
|---|---|---|
| 1 | **Is there a verifiable record, or only screenshots?** | P&L screenshots only. SEBI's Avadhut Sathe order was about selectively publicised winning trades while participants were in net losses |
| 2 | **How many trades is it based on?** | Fewer than ~50 trades: that can easily be luck |
| 3 | **Are all costs included?** (brokerage, STT, exchange fees, stamp duty, slippage) | "Gross profit" only. STT alone went up in Oct 2024 |
| 4 | **Which period was it tested on?** | Only before Nov 2024, so it used expiries, lot sizes and rules that no longer exist (4a) |
| 5 | **What happens when it loses?** Win rate vs size of losses | "90% win rate" with rare huge losses (typical of naked option selling) |
| 6 | **Worst drawdown and worst month?** | Not disclosed |
| 7 | **How many settings were tuned?** | Many parameters, one index, one timeframe: likely curve-fitted to the past |
| 8 | **Any hidden bias?** | Uses today's stock list for old dates, or decides using a price you couldn't have known at the time |
| 9 | **Does it fit your capital?** | Needs lot sizes or margin you don't have (₹15 lakh minimum contract value) |
| 10 | **Who profits if you believe it?** | Course, paid Telegram group, broker referral link |

**Scoring:** any 🔴 on questions 1, 3 or 4 = "don't trust it yet"; 3+ 🟡 = "test it yourself before using real money."

**Format ideas:**
- Reel: "एक strategy देखी? 5 minute में test करो." Walk through 3 questions per Reel, a series of 4.
- Reel: "90% win rate वाली strategy क्यों डुबो देती है". Show the math of win rate vs loss size with a simple animation.
- Lead magnet: **"Comment TEST to get the full checklist"**. Deliver it via an Instagram DM automation (within API limits) or a WhatsApp Channel link.
- Later: a free web tool where you enter a strategy's claimed numbers and get the checklist score. This connects to PTIS backtesting.

**Guardrails:**
- **Never name, show or mock specific influencers.** Use generic, anonymized claim types ("a viral '₹5,000 daily' strategy"). This avoids defamation and copyright problems, and reposting others' clips would also trigger Instagram's originality penalty.
- Education only: we teach **how to test**, never "this strategy will make money."
- No performance claims of our own.

---

## 5. 60-day Instagram launch plan

| Weeks | Focus | Output |
|---|---|---|
| **1–2** | Twin + voice recorded and tested; Reel templates (6–8 layouts) built; research playbooks run by hand | 5 test Reels posted as **Trial Reels** only |
| **3–4** | 1 Reel/day across 4 series: **पुरानी Strategy नया Market**, **5-Minute Strategy Test**, **The Transfer** (SEBI data), **Event explainers** | 14 Reels; checklist lead magnet live; WhatsApp Channel open |
| **5–8** | Double down on the 2 series with the best share and save rates; start semi-automatic pipeline | 28 Reels; weekly cost + performance review |

**Metrics that matter on Instagram:** shares per 1,000 views, saves per 1,000 views, % who watch past 3 seconds, completion rate, follows per 1,000 accounts reached, and lead-magnet sign-ups.

### Gate to start YouTube (any one of these)
- 10,000 Instagram followers, **or**
- 3 Reels above 100,000 views, **or**
- 1,000 WhatsApp Channel / newsletter subscribers.

*(Proposed targets. Adjust after the first 30 days of data.)*

When the gate is met, the best-performing Reel topics become the first YouTube long videos. The research is already done.

---

## 6. Cost during the Instagram-only phase

Volume: 30 Reels × ~50 s ≈ **25 min of narration**, with the avatar on screen ~40% ≈ **10 avatar-minutes ≈ 200 HeyGen credits** a month.

| Item | Plan | ₹/month (approx.) |
|---|---|---|
| Claude | Pro subscription | ~1,800 |
| Voice clone | ElevenLabs Creator (the Starter plan at $6 may cover ~25 min, but leaves no room for retakes or the professional clone) | ~1,950 |
| Avatar | HeyGen Creator (600 credits; ~200 used, the rest roll over one month) | ~2,550 |
| Server | Laptop rendering | 0 |
| Canva | Free | 0 |
| Data, news, reports | Free sources | 0 |
| **Total** | | **≈ ₹6,300**, well under the ₹10–12k cap |

The spare budget can go to Canva Pro (₹333) or be saved for the YouTube launch.

---

## Sources

- [Instagram for Creators: Trial Reels](https://creators.instagram.com/blog/instagram-trial-reels) · [Meta newsroom: Trial Reels](https://about.fb.com/news/2024/12/trial-reels-try-content-non-followers-first-see-what-perfoms-best/)
- [TechCrunch: Instagram restricts reach of content aggregators (Apr 2026)](https://techcrunch.com/2026/04/30/instagram-restricts-reach-of-content-aggregators-in-new-crackdown/) · [Tubefilter: Instagram's penalty for unoriginal aggregators](https://www.tubefilter.com/2026/04/30/instagram-removes-algorithm-recommendations-repost-content-aggregator/)
- [Social Media Today: Reels expanded to 3 minutes](https://www.socialmediatoday.com/news/instagram-officially-expands-reels-length-3-minutes/737766/) · [Metricool: Reels length](https://metricool.com/instagram-reels-length/)
- [Kompozy: Instagram AI detection & labeling 2026](https://kompozy.io/guides/instagram-ai-content-detection-and-labeling) · [AuditSocials: Meta AI label policy 2026](https://www.auditsocials.com/blog/meta-ai-generated-content-label-policy-2026)
- [Phyllo: Instagram Reels API guide](https://www.getphyllo.com/post/a-complete-guide-to-the-instagram-reels-api) · [InstantDM: Instagram API rate limits 2026](https://instantdm.com/blog/instagram-api-rate-limits-explained-2026-developer-guide)
- [AIR Media-Tech: YouTube Partner Program requirements 2026](https://air.io/en/monetization/youtube-partner-program-requirements-2026-the-complete-guide) · [vidIQ: YouTube Partner Program guide](https://vidiq.com/blog/post/youtube-partner-program-guide/)
- [Zerodha: brief on SEBI's F&O measures](https://zerodha.com/z-connect/kite/a-short-brief-on-the-new-sebi-measures-for-the-fo-space) · [BusinessToday: new F&O rules kick off (20 Nov 2024)](https://www.businesstoday.in/markets/story/sebis-new-fo-rules-kick-off-today-heres-what-are-these-changes-454352-2024-11-20) · [Business Standard: SEBI's six F&O measures](https://www.business-standard.com/amp/markets/news/sebi-announces-six-key-changes-to-curb-speculation-in-derivatives-trading-124100101316_1.html)
- [ICICI Direct: new STT rules from 1 Oct 2024](https://www.icicidirect.com/research/equity/finace/new-stt-rules-in-futures-and-options-trading) · [ICICI Direct: STT changes in Budget 2026](https://www.icicidirect.com/futures-and-options/articles/stt-changes-in-budget-2026-what-f-o-traders-need-to-know) · [Upstox: how the 2026 STT hike affects traders](https://upstox.com/news/personal-finance/tax/explained-how-the-stt-hike-on-equity-futures-and-options-affects-traders-and-investors/article-189260/)
- [Kotak Neo: NSE to Tuesday, BSE to Thursday from Sep 2025](https://www.kotakneo.com/news/market-news/sebi-to-end-thursday-expiry/) · [News on AIR: NSE, BSE swap expiry days](https://www.newsonair.gov.in/nse-bse-swap-derivatives-expiry-days)
- [Outlook Money: F&O rules cut retail participation ~20%](https://www.outlookmoney.com/invest/sebis-fo-regulations-lead-to-drop-in-retail-participation-small-traders-affected-says-report)
- [m.Stock: SEBI reviews CAS rules](https://www.mstock.com/articles/sebi-reviews-cas-proposed-changes-to-derivatives-settlement-ieps-and-new-market-timings) · [Multibagg: CAS closing auction and F&O timing](https://www.multibagg.ai/market-pulse/articles/sebi-cas-closing-auction-fno-cmsexkib000110zqnw0ad1op6) · [BusinessToday: CAS rollout and F&O turnover (Sep 2026)](https://www.businesstoday.in/markets/stocks/story/cas-rollout-sends-average-daily-fo-turnover-tumbling-to-multi-month-low-whats-ahead-553115-2026-09-03)
- SEBI Avadhut Sathe order and algo share of turnover: see [`strategy-research-2026-09.md`](strategy-research-2026-09.md) and [`next-gen-finance-pillar.md`](next-gen-finance-pillar.md)
