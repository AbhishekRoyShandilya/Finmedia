"""Finmedia business viability - Monte Carlo of monthly revenue, cost and cash over 36 months.

PRE-DECLARED RULE (written before the first run, 2026-09-27):
  PROCEED-WORTHY in a scenario if BOTH:
    (a) P(monthly revenue >= monthly cost by month 24) >= 50%, and
    (b) P(month-36 monthly revenue >= Rs 2,00,000) >= 40%   (a lean team's income + costs)
  Reported for every scenario, pass or fail, with P10 / P50 / P90 - never the best path.

Every parameter below is an ASSUMPTION with its source or reasoning. Founder time is NOT costed (opportunity
cost stated separately). Revenue = recognised monthly (annual plans spread over 12 months).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field, replace

import numpy as np

MONTHS, PATHS = 36, 20_000


@dataclass
class Scenario:
    name: str
    # audience: latent success tier (fail, modest, good, breakout) - dedicated weekly long-form + daily Reels.
    # Base rate: only ~1.3% of all channels reach 100k (vidIQ 2026), but that base includes hobby channels.
    tier_p: tuple = (0.40, 0.35, 0.18, 0.07)
    tier_K: tuple = ((2e3, 8e3), (15e3, 60e3), (80e3, 250e3), (400e3, 1.2e6))   # subscriber ceiling ranges
    tier_t50: tuple = (12, 18, 20, 18)                                           # month of half-ceiling
    views_per_sub: float = 0.8        # long-form monthly views per subscriber (4 videos/month)
    rpm_med: float = 60.0             # Rs per 1000 views; Hindi finance Rs25-100, English 80-250 (upGrowth 2026)
    demonetize_hazard_yr: float = 0.04
    list_join_rate: float = 0.005     # share of monthly long-form views that join WhatsApp/newsletter
    list_churn: float = 0.025
    ra_license: bool = True
    license_month: tuple = (4, 9)     # NISM XV + registration; 10% of paths delayed to month 12
    conv_med: float = 0.0035          # monthly free->paid of the list (median paid stock ~0.6%, top 2-5%: beehiiv 2026)
    churn_range: tuple = (0.03, 0.06) # paid newsletter churn clusters 3-5%/month (industry benchmarks)
    price_med: float = 5000.0         # Rs/yr; tools: MC Pro 999, Trendlyne 2,090, Tijori 3,500, Screener 4,999
    sponsor_rate_med: float = 0.8     # Rs per view of a sponsored video (assumption); needs RA for broker money
    b2b: bool = True
    b2b_p: tuple = (0.01, 0.04, 0.08, 0.12)   # monthly chance of a new B2B client, by tier (assumption)
    b2b_start: int = 9                # first month a B2B client can sign
    b2b_fee_med: float = 50_000.0     # Rs/month white-label desk (assumption; no public price data)
    b2b_churn: float = 0.029          # ~30%/yr
    # --- evidence-lab pivot (added 2026-09-27, declared before its first run) ---
    # skill course (education only: method, no calls, lagged data -> legal pre-RA). Launches every 6 months.
    edu: bool = False
    edu_start: int = 4
    edu_price_med: float = 4999.0     # assumption; course market 1-3% sales-page conversion (acceleroi 2026)
    edu_launch_conv: float = 0.015    # share of the list buying per launch; email-list course launches 1-2% (benchmarks)
    edu_evergreen: float = 0.001      # monthly evergreen sales as a share of the list
    edu_refund: float = 0.10
    # research tool (backtest-honesty / event-impact tracker); needs a data licence -> extra cost
    tool: bool = False
    tool_start: int = 9
    tool_price_med: float = 2500.0    # Trendlyne 2,090-5,900, Tijori 3,500 a year
    tool_conv: float = 0.001          # monthly, share of the list
    tool_churn: float = 0.035
    tool_cost: float = 15_000.0       # NSE-authorised vendor data licence, per month (strategy doc 7: Rs2k-15k+)
    base_cost: float = 24_000.0       # Rs12k tools cap + Rs12k research LLM (budget-lean-launch.md sec 10)
    one_time: float = 120_000.0       # RA + NISM + lawyer review + deposit lien (strategy doc 3b / 7)


def lognorm(rng, med, sigma, size):
    return med * np.exp(rng.normal(0, sigma, size))


def simulate(sc: Scenario, seed: int = 7, paths: bool = False) -> dict:
    rng = np.random.default_rng(seed)
    n = PATHS
    tier = rng.choice(4, size=n, p=np.array(sc.tier_p) / sum(sc.tier_p))
    lo = np.array([k[0] for k in sc.tier_K])[tier]; hi = np.array([k[1] for k in sc.tier_K])[tier]
    K = np.exp(rng.uniform(np.log(lo), np.log(hi)))
    t50 = np.array(sc.tier_t50)[tier] + rng.normal(0, 3, n)
    w = rng.uniform(4, 6, n)
    vps = lognorm(rng, sc.views_per_sub, 0.35, n)
    rpm = lognorm(rng, sc.rpm_med, 0.35, n)
    join = lognorm(rng, sc.list_join_rate, 0.5, n)
    conv = lognorm(rng, sc.conv_med, 0.5, n)
    churn = rng.uniform(*sc.churn_range, n)
    price = lognorm(rng, sc.price_med, 0.3, n)
    spon_rate = lognorm(rng, sc.sponsor_rate_med, 0.5, n)
    lic = rng.integers(sc.license_month[0], sc.license_month[1] + 1, n).astype(float)
    lic[rng.random(n) < 0.10] = 12
    if not sc.ra_license:
        lic[:] = np.inf
    b2b_p = np.array(sc.b2b_p)[tier]
    b2b_fee = lognorm(rng, sc.b2b_fee_med, 0.5, n)

    subs0 = K / (1 + np.exp(t50 / w))
    R = {k: np.zeros((n, MONTHS)) for k in ("ads", "research_subs", "sponsor", "b2b", "course", "tool")}
    edu_price = lognorm(rng, sc.edu_price_med, 0.3, n); edu_conv = lognorm(rng, sc.edu_launch_conv, 0.5, n)
    tool_price = lognorm(rng, sc.tool_price_med, 0.3, n); tool_conv = lognorm(rng, sc.tool_conv, 0.5, n); tsub = np.zeros(n)
    cost = np.zeros((n, MONTHS)); subsY = np.zeros((n, MONTHS)); paid = np.zeros((n, MONTHS)); lstY = np.zeros((n, MONTHS)); cliY = np.zeros((n, MONTHS))
    lst = np.zeros(n); psub = np.zeros(n); clients = np.zeros(n); demon = np.zeros(n)
    for m in range(MONTHS):
        t = m + 1
        subs = np.maximum(K / (1 + np.exp(-(t - t50) / w)) - subs0, 0) + 50 * t
        subsY[:, m] = subs
        views = subs * vps
        # YouTube ads: after YPP (1k subs) and month 3; demonetisation shock kills ads for 3 months
        hit = rng.random(n) < sc.demonetize_hazard_yr / 12
        demon = np.where(hit, 3, np.maximum(demon - 1, 0))
        ypp = (subs >= 1000) & (t >= 3) & (demon == 0)
        R["ads"][:, m] = np.where(ypp, views * rpm / 1000, 0)
        # owned list
        lst = lst * (1 - sc.list_churn) + views * join
        lstY[:, m] = lst
        # paid research: after the RA licence; trust ramps 0.5 -> 1.0 over 12 months of public track record
        live = t >= lic
        trust = np.clip(0.5 + 0.5 * (t - lic) / 12, 0.5, 1.0)
        psub = psub * (1 - churn) + np.where(live, lst * conv * trust, 0)
        paid[:, m] = psub
        R["research_subs"][:, m] = psub * price / 12 * 0.97            # 3% payment fees
        # sponsorship: registered-to-registered only (brokers cannot pay unregistered creators)
        per_video = views / 4
        n_spon = np.where(per_video >= 15_000, 1 + (per_video >= 60_000), 0)
        R["sponsor"][:, m] = np.where(live, n_spon * per_video * spon_rate, 0)
        # B2B white-label desk: after licence + month 9
        if sc.b2b:
            can = live & (t >= sc.b2b_start) & (clients < 10)
            clients = clients + (can & (rng.random(n) < b2b_p * trust))
            clients = clients - rng.binomial(clients.astype(int), sc.b2b_churn)
            R["b2b"][:, m] = clients * b2b_fee
            cliY[:, m] = clients
        if sc.edu and t >= sc.edu_start:
            launch = (t - sc.edu_start) % 6 == 0
            buyers = lst * ((edu_conv if launch else 0) + sc.edu_evergreen)
            R["course"][:, m] = buyers * edu_price * (1 - sc.edu_refund) * 0.97
        if sc.tool and t >= sc.tool_start:
            tsub = tsub * (1 - sc.tool_churn) + lst * tool_conv
            R["tool"][:, m] = tsub * tool_price / 12 * 0.97
        rev = sum(v[:, m] for v in R.values())
        cost[:, m] = (sc.tool_cost if sc.tool and t >= sc.tool_start else 0) + sc.base_cost + np.where(rev > 150_000, 45_000, 0) + np.where(rev > 400_000, 80_000, 0) \
            + (sc.one_time if m == 0 else 0)
    rev = sum(R.values())
    run_cost = cost.copy(); run_cost[:, 0] -= sc.one_time
    cover = rev >= run_cost
    # breakeven = first month from which revenue covers running cost for 3 consecutive months
    ok3 = cover[:, :-2] & cover[:, 1:-1] & cover[:, 2:]
    be = np.where(ok3.any(1), ok3.argmax(1) + 1, np.inf)
    cash = np.cumsum(rev - cost, 1)
    pct = lambda x: [round(float(np.percentile(x, q))) for q in (10, 50, 90)]
    last12 = rev[:, 24:]
    cv = np.std(last12, 1) / np.maximum(np.mean(last12, 1), 1)
    mix = {k: round(float(v[:, 24:].sum() / max(last12.sum(), 1) * 100), 1) for k, v in R.items()}
    out = {
        "scenario": sc.name,
        "P_breakeven_by_m12": round(float((be <= 12).mean() * 100), 1),
        "P_breakeven_by_m24": round(float((be <= 24).mean() * 100), 1),
        "P_breakeven_by_m36": round(float((be <= 36).mean() * 100), 1),
        "median_breakeven_month_if_any": float(np.median(be[np.isfinite(be)])) if np.isfinite(be).any() else None,
        "rev_m12_P10_P50_P90": pct(rev[:, 11]), "rev_m24_P10_P50_P90": pct(rev[:, 23]),
        "rev_m36_P10_P50_P90": pct(rev[:, 35]),
        "P_rev_m36_ge_2L": round(float((rev[:, 35] >= 200_000).mean() * 100), 1),
        "P_rev_m36_ge_5L": round(float((rev[:, 35] >= 500_000).mean() * 100), 1),
        "cash_m36_P10_P50_P90": pct(cash[:, 35]), "max_cash_hole_P50": round(float(np.median(cash.min(1)))),
        "max_cash_hole_P10": round(float(np.percentile(cash.min(1), 10))),
        "subs_m36_P10_P50_P90": pct(subsY[:, 35]), "paid_m36_P10_P50_P90": pct(paid[:, 35]),
        "mix_last12_pct": mix, "cv_monthly_rev_last12_median": round(float(np.median(cv)), 2),
        "recurring_share_last12_pct": round(mix["research_subs"] + mix["b2b"] + mix["tool"], 1),
    }
    # lumpy streams (course launches) are invisible in single-month snapshots -> also report trailing averages
    t12 = rev[:, 24:36].mean(1)
    out["rev_trailing12_avg_m36_P10_P50_P90"] = pct(t12)
    out["P_trailing12_avg_m36_ge_2L"] = round(float((t12 >= 200_000).mean() * 100), 1)
    r6 = np.array([rev[:, max(0, m - 5):m + 1].sum(1) >= run_cost[:, max(0, m - 5):m + 1].sum(1) for m in range(MONTHS)]).T
    r6[:, :5] = False
    be6 = np.where(r6.any(1), r6.argmax(1) + 1, np.inf)
    out["P_trailing6_covers_cost_by_m24"] = round(float((be6 <= 24).mean() * 100), 1)
    out["P_trailing6_covers_cost_by_m12"] = round(float((be6 <= 12).mean() * 100), 1)
    out["PASS_a"] = out["P_breakeven_by_m24"] >= 50
    out["PASS_b"] = out["P_rev_m36_ge_2L"] >= 40
    out["PROCEED_WORTHY"] = bool(out["PASS_a"] and out["PASS_b"])
    # median path by tier
    out["rev_m36_median_by_tier"] = {nm: round(float(np.median(rev[tier == i, 35]))) for i, nm in
                                     enumerate(["fail", "modest", "good", "breakout"])}
    out["P_tier"] = {nm: round(float((tier == i).mean() * 100), 1) for i, nm in
                     enumerate(["fail", "modest", "good", "breakout"])}
    if paths:
        out["_paths"] = dict(subs=subsY, lst=lstY, paid=paid, clients=cliY, rev=rev, tier=tier)
    return out


BASE = Scenario("BASE")
SCENARIOS = [
    BASE,
    replace(BASE, name="PESSIMISTIC audience", tier_p=(0.60, 0.28, 0.10, 0.02)),
    replace(BASE, name="OPTIMISTIC audience", tier_p=(0.25, 0.40, 0.25, 0.10)),
    replace(BASE, name="NO RA licence (ads only)", ra_license=False),
    replace(BASE, name="RA but NO B2B", b2b=False),
    replace(BASE, name="Half conversion + high churn", conv_med=0.00175, churn_range=(0.05, 0.08)),
    replace(BASE, name="Premium price Rs12k/yr, half conversion", price_med=12_000, conv_med=0.00175),
    replace(BASE, name="English track (RPM x2)", rpm_med=120),
    # Instagram-first: Reels reach feeds the owned list (not modelled in BASE) -> list joins x3
    replace(BASE, name="Instagram funnel (list joins x3)", list_join_rate=0.015),
    # B2B sold on the research desk itself (demo + track record), not on audience size
    replace(BASE, name="B2B-first (5%/mo any tier, from m6)", b2b_p=(0.05, 0.05, 0.06, 0.08), b2b_start=6),
    replace(BASE, name="IG funnel + B2B-first", list_join_rate=0.015, b2b_p=(0.05, 0.05, 0.06, 0.08), b2b_start=6),
    replace(BASE, name="IG funnel + B2B-first, PESSIMISTIC audience", list_join_rate=0.015,
            b2b_p=(0.05, 0.05, 0.06, 0.08), b2b_start=6, tier_p=(0.60, 0.28, 0.10, 0.02)),
]
# ---- evidence-lab pivot, declared 2026-09-27 before the first run. Same pass rule. ----
LAB = replace(BASE, edu=True, tool=True)
PIVOT = [
    replace(LAB, name="P1 Lab: course + tool, audience odds UNCHANGED"),
    replace(BASE, name="P1a course only", edu=True),
    replace(BASE, name="P1b tool only", tool=True),
    # assumption, shown separately: high-intent 'does X work in India?' topics + a gap in Hindi -> modestly better odds
    replace(LAB, name="P2 Lab + modestly better audience odds", tier_p=(0.35, 0.37, 0.20, 0.08)),
    replace(LAB, name="P3 Lab + IG funnel + B2B-first", list_join_rate=0.015, b2b_p=(0.05, 0.05, 0.06, 0.08), b2b_start=6),
    replace(LAB, name="P3b same + better audience odds", list_join_rate=0.015, b2b_p=(0.05, 0.05, 0.06, 0.08),
            b2b_start=6, tier_p=(0.35, 0.37, 0.20, 0.08)),
    replace(LAB, name="P4 P3 with PESSIMISTIC audience", list_join_rate=0.015, b2b_p=(0.05, 0.05, 0.06, 0.08),
            b2b_start=6, tier_p=(0.60, 0.28, 0.10, 0.02)),
    replace(LAB, name="P5 P3 but course converts half", list_join_rate=0.015, b2b_p=(0.05, 0.05, 0.06, 0.08),
            b2b_start=6, edu_launch_conv=0.0075),
]

if __name__ == "__main__":
    res = [simulate(s) for s in SCENARIOS + PIVOT]
    json.dump(res, sys.stdout if len(sys.argv) < 2 else open(sys.argv[1], "w"), indent=1)
