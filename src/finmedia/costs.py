"""Monthly budget guard: every paid call is checked before it runs and recorded after."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

from .store import Store

# Rough characters-per-token used only for the *pre-call* worst-case estimate.
# Devanagari text uses more tokens per character than English, so this is
# deliberately conservative.
CHARS_PER_TOKEN_ESTIMATE = 2.5
CACHE_WRITE_MULTIPLIER = 1.25
CACHE_READ_MULTIPLIER = 0.10


class BudgetExceeded(RuntimeError):
    """Raised when a call would push spending past the monthly cap."""


def month_key(day: date | None = None) -> str:
    return (day or date.today()).strftime("%Y-%m")


@dataclass
class Usage:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_write_tokens: int = 0
    cache_read_tokens: int = 0


class BudgetGuard:
    def __init__(self, store: Store, settings: dict[str, Any]):
        self.store = store
        self.budget = settings["budget"]
        self.prices: dict[str, list[float]] = settings["llm"]["prices_usd_per_mtok"]

    # ------------------------------------------------------------- pricing

    def _price(self, model: str) -> tuple[float, float]:
        if model not in self.prices:
            # Unknown model (e.g. a fallback): assume the most expensive known
            # price so the ledger never under-reports.
            worst = max(self.prices.values(), key=lambda p: p[1])
            return float(worst[0]), float(worst[1])
        price_in, price_out = self.prices[model]
        return float(price_in), float(price_out)

    def usd_for(self, model: str, usage: Usage) -> float:
        price_in, price_out = self._price(model)
        return (
            usage.input_tokens * price_in
            + usage.cache_write_tokens * price_in * CACHE_WRITE_MULTIPLIER
            + usage.cache_read_tokens * price_in * CACHE_READ_MULTIPLIER
            + usage.output_tokens * price_out
        ) / 1_000_000

    def to_inr(self, usd: float) -> float:
        return usd * float(self.budget["usd_inr"])

    # -------------------------------------------------------------- checks

    def worst_case_inr(self, model: str, prompt_chars: int, max_output_tokens: int) -> float:
        est = Usage(
            input_tokens=int(prompt_chars / CHARS_PER_TOKEN_ESTIMATE),
            output_tokens=max_output_tokens,
        )
        return self.to_inr(self.usd_for(model, est))

    @staticmethod
    def pool_for(role: str | None) -> str:
        """Research-desk roles spend from their own pool, so a deep report can never eat the media budget."""
        return "llm_research" if role and role.startswith("research_") else "llm"

    def remaining_llm_inr(self, month: str | None = None, pool: str = "llm") -> float:
        month = month or month_key()
        if pool == "llm_research":
            return float(self.budget["research_llm_cap_inr"]) - self.store.month_spend(month, "llm_research")
        llm_left = float(self.budget["llm_cap_inr"]) - self.store.month_spend(month, "llm")
        media_spend = self.store.month_spend(month) - self.store.month_spend(month, "llm_research")
        total_left = float(self.budget["monthly_cap_inr"]) - media_spend
        return min(llm_left, total_left)

    def check(self, model: str, prompt_chars: int, max_output_tokens: int, role: str | None = None) -> float:
        """Raise BudgetExceeded unless the worst case of this call fits the budget."""
        pool = self.pool_for(role)
        worst = self.worst_case_inr(model, prompt_chars, max_output_tokens)
        left = self.remaining_llm_inr(pool=pool)
        if worst > left:
            cap = (f"research cap ₹{self.budget['research_llm_cap_inr']}" if pool == "llm_research" else
                   f"LLM cap ₹{self.budget['llm_cap_inr']}, total cap ₹{self.budget['monthly_cap_inr']}")
            raise BudgetExceeded(
                f"Call could cost up to ₹{worst:.2f} but only ₹{max(left, 0):.2f} is left this month ({cap})."
            )
        return worst

    def record(self, item: str, model: str, usage: Usage) -> float:
        usd = self.usd_for(model, usage)
        inr = self.to_inr(usd)
        self.store.add_cost(
            month=month_key(), kind=self.pool_for(item), item=f"{item}:{model}", inr=inr, usd=usd,
            input_tokens=usage.input_tokens, output_tokens=usage.output_tokens,
            cache_write_tokens=usage.cache_write_tokens, cache_read_tokens=usage.cache_read_tokens,
        )
        return inr
