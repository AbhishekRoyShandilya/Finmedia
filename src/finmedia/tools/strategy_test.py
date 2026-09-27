"""The 5-Minute Strategy Test (docs/instagram-first-launch.md §4b).

Scores the claims made about a trading strategy against ten questions. Each
question is green / amber / red. Answers can be given directly, or computed
from the facts you know about the strategy. Education only: it tells you
how much to trust a claim, never whether to trade.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

GREEN, AMBER, RED = "green", "amber", "red"
_SYMBOL = {GREEN: "🟢", AMBER: "🟡", RED: "🔴"}

# Key rule-change dates for Indian equity F&O (see instagram-first-launch.md §4a).
FNO_MEASURES = date(2024, 11, 20)   # one weekly expiry per exchange, bigger lots
STT_HIKE_2026 = date(2026, 4, 1)    # futures 0.05%, options 0.15%

QUESTIONS: dict[str, dict[str, str]] = {
    "q1_record": {"en": "Is there a verifiable record, or only screenshots?",
                  "hi": "पूरा record है, या सिर्फ़ screenshots?"},
    "q2_sample": {"en": "How many trades is it based on?",
                  "hi": "कितने trades पर based है?"},
    "q3_costs": {"en": "Are all costs included (brokerage, STT, exchange fees, stamp duty, slippage)?",
                 "hi": "क्या सारे खर्च जोड़े गए हैं?"},
    "q4_period": {"en": "Was it tested under today's market rules?",
                  "hi": "क्या आज के rules पर test हुई है?"},
    "q5_payoff": {"en": "What happens when it loses? (win rate vs size of losses)",
                  "hi": "हारने पर कितना नुकसान होता है?"},
    "q6_drawdown": {"en": "Is the worst drawdown / worst month disclosed?",
                    "hi": "सबसे बुरा दौर बताया गया है?"},
    "q7_overfit": {"en": "How many settings were tuned to fit the past?",
                   "hi": "कितनी settings पुराने data पर fit की गईं?"},
    "q8_bias": {"en": "Any hindsight bias (today's stock list, prices you couldn't know then)?",
                "hi": "कहीं hindsight का फ़ायदा तो नहीं लिया?"},
    "q9_capital": {"en": "Does it fit your capital and today's lot sizes?",
                   "hi": "क्या यह आपकी capital में fit होती है?"},
    "q10_incentive": {"en": "Who earns if you believe it?",
                      "hi": "आपके भरोसा करने से किसकी कमाई होती है?"},
}
CRITICAL = ("q1_record", "q3_costs", "q4_period")


@dataclass
class QuestionResult:
    qid: str
    status: str
    reason: str

    def line(self) -> str:
        return f"{_SYMBOL[self.status]} {QUESTIONS[self.qid]['en']} — {self.reason}"


def _score_record(v: str) -> tuple[str, str]:
    v = (v or "").lower()
    if v in {"verified", "broker_statement", "audited", "parrva"}:
        return GREEN, "verifiable trade record"
    if v in {"partial", "trade_log"}:
        return AMBER, "partial log, not independently verifiable"
    return RED, "screenshots or nothing: selective winners can't be ruled out"


def _score_sample(n: int | None) -> tuple[str, str]:
    if n is None:
        return RED, "number of trades not disclosed"
    if n >= 100:
        return GREEN, f"{n} trades"
    if n >= 50:
        return AMBER, f"{n} trades: borderline"
    return RED, f"only {n} trades: easily luck"


def _score_costs(v: str) -> tuple[str, str]:
    v = (v or "").lower()
    if v == "all":
        return GREEN, "all costs included"
    if v == "partial":
        return AMBER, "some costs missing"
    return RED, "gross numbers only; costs can wipe out thin edges"


def _score_period(end: str | None, instrument: str) -> tuple[str, str]:
    if not end:
        return RED, "test period not disclosed"
    end_date = date.fromisoformat(end)
    if instrument == "fno":
        if end_date >= STT_HIKE_2026:
            return GREEN, "includes data after the Apr 2026 STT hike"
        if end_date >= FNO_MEASURES:
            return AMBER, "after Nov 2024 F&O rules, but before the Apr 2026 STT hike"
        return RED, "tested only before Nov 2024: expiries, lot sizes and costs have changed"
    years_old = (date.today() - end_date).days / 365
    if years_old <= 1:
        return GREEN, "recent test period"
    return AMBER, f"test ends {years_old:.1f} years ago"


def _score_payoff(win_rate: float | None, avg_win: float | None, avg_loss: float | None) -> tuple[str, str]:
    if win_rate is None or avg_win is None or avg_loss is None:
        return AMBER, "win rate and average win/loss not both disclosed"
    expectancy = win_rate * avg_win - (1 - win_rate) * avg_loss
    if expectancy <= 0:
        return RED, f"negative expectancy ({expectancy:.2f} per trade) even before costs"
    if win_rate >= 0.8 and avg_loss >= 3 * avg_win:
        return RED, "high win rate with rare large losses: one bad day can erase months"
    return GREEN, f"positive expectancy ({expectancy:.2f} per trade) before costs"


def _score_drawdown(max_dd_pct: float | None) -> tuple[str, str]:
    if max_dd_pct is None:
        return RED, "worst drawdown not disclosed"
    if max_dd_pct <= 30:
        return GREEN, f"max drawdown {max_dd_pct:.0f}%"
    return AMBER, f"max drawdown {max_dd_pct:.0f}%: can you sit through that?"


def _score_overfit(params: int | None, multi_market: bool | None) -> tuple[str, str]:
    if params is None:
        return AMBER, "number of tuned settings unknown"
    if params > 6:
        return RED, f"{params} tuned settings: likely curve-fitted"
    if params > 3 or multi_market is False:
        return AMBER, f"{params} settings{'; one market only' if multi_market is False else ''}"
    return GREEN, f"{params} settings{', works across markets' if multi_market else ''}"


def _score_capital(required: float | None, yours: float | None) -> tuple[str, str]:
    if required is None or yours is None:
        return AMBER, "capital needed not compared with yours"
    if required <= yours:
        return GREEN, "fits your capital"
    if required <= 1.5 * yours:
        return AMBER, "slightly above your capital: forces bigger risk per trade"
    return RED, "needs much more capital than you have"


def _score_incentive(v: str) -> tuple[str, str]:
    v = (v or "").lower()
    if v in {"none", "no"}:
        return GREEN, "no product being sold"
    if v in {"course", "referral", "telegram", "paid_group"}:
        return AMBER, f"seller earns from a {v}: judge the evidence, not the pitch"
    if v in {"tips_with_returns_claims", "guaranteed_returns"}:
        return RED, "paid tips with return claims: a regulatory red flag"
    return AMBER, "incentive unclear"


def run_test(facts: dict[str, Any]) -> dict[str, Any]:
    """Score a strategy. `facts` keys are documented in config/strategy_test_example.yaml."""
    overrides: dict[str, str] = facts.get("answers", {}) or {}
    instrument = facts.get("instrument", "fno")
    scored = {
        "q1_record": _score_record(facts.get("record")),
        "q2_sample": _score_sample(facts.get("trades")),
        "q3_costs": _score_costs(facts.get("costs_included")),
        "q4_period": _score_period(facts.get("test_end_date"), instrument),
        "q5_payoff": _score_payoff(facts.get("win_rate"), facts.get("avg_win"), facts.get("avg_loss")),
        "q6_drawdown": _score_drawdown(facts.get("max_drawdown_pct")),
        "q7_overfit": _score_overfit(facts.get("tuned_parameters"), facts.get("works_on_multiple_markets")),
        "q8_bias": (AMBER, "can't be verified from outside; ask how the test avoided hindsight"),
        "q9_capital": _score_capital(facts.get("capital_required_inr"), facts.get("your_capital_inr")),
        "q10_incentive": _score_incentive(facts.get("seller_incentive")),
    }
    results = []
    for qid, (status, reason) in scored.items():
        if qid in overrides:
            status, reason = overrides[qid], "answered manually"
        results.append(QuestionResult(qid, status, reason))

    reds_critical = [r.qid for r in results if r.qid in CRITICAL and r.status == RED]
    ambers = sum(r.status == AMBER for r in results)
    if reds_critical:
        verdict = "DON'T TRUST IT YET"
        verdict_hi = "अभी भरोसा मत कीजिए"
    elif ambers >= 3 or any(r.status == RED for r in results):
        verdict = "TEST IT YOURSELF FIRST (paper trade)"
        verdict_hi = "पहले ख़ुद paper trade करके test कीजिए"
    else:
        verdict = "PASSES THE 5-MINUTE TEST (still paper-trade before real money)"
        verdict_hi = "5-minute test पास, फिर भी पहले paper trade"

    return {
        "verdict": verdict,
        "verdict_hi": verdict_hi,
        "critical_reds": reds_critical,
        "results": [{"id": r.qid, "status": r.status, "reason": r.reason,
                     "question": QUESTIONS[r.qid]["en"], "question_hi": QUESTIONS[r.qid]["hi"]}
                    for r in results],
        "lines": [r.line() for r in results],
        "note": "Education only. Not investment advice.",
    }
