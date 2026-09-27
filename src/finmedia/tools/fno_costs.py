"""F&O round-trip cost calculator (education use).

Shows what a trade really costs after statutory charges, and how the same
trade's cost changed across rule regimes (the "why your 2023 strategy fails
now" story). Rates come from config/fno_charges.yaml and must be verified
against current circulars before any number is published.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date
from typing import Any, Literal

Instrument = Literal["futures", "options"]


def _rate_on(schedule: list[dict[str, Any]], on: date, allow_earliest: bool = False) -> tuple[float, bool]:
    """Rate in force on a date. Returns (rate, approximated).

    With allow_earliest, dates before the first entry use the earliest known
    rate and are flagged as approximated.
    """
    applicable = [e for e in schedule if date.fromisoformat(str(e["from"])) <= on]
    if applicable:
        return float(max(applicable, key=lambda e: str(e["from"]))["rate"]), False
    if allow_earliest and schedule:
        return float(min(schedule, key=lambda e: str(e["from"]))["rate"]), True
    raise ValueError(f"No rate in force on {on.isoformat()}")


@dataclass
class CostBreakdown:
    trade_date: str
    instrument: str
    buy_value: float
    sell_value: float
    gross_pnl: float
    brokerage: float
    stt: float
    exchange_txn: float
    sebi_fee: float
    stamp_duty: float
    gst: float
    total_charges: float
    net_pnl: float
    breakeven_move_per_unit: float
    stt_rate: float
    notes: list[str]

    def as_dict(self) -> dict[str, Any]:
        return {k: (round(v, 2) if isinstance(v, float) and k != "stt_rate" else v)
                for k, v in asdict(self).items()}


def round_trip_cost(charges: dict[str, Any], *, instrument: Instrument, buy_price: float,
                    sell_price: float, quantity: int, trade_date: date, exchange: str = "NSE",
                    orders: int = 2) -> CostBreakdown:
    """Charges for buying and selling `quantity` units (price is premium for options)."""
    buy_value = buy_price * quantity
    sell_value = sell_price * quantity
    turnover = buy_value + sell_value

    notes: list[str] = []
    stt_rate, _ = _rate_on(charges["stt"][instrument], trade_date)
    stt = stt_rate * sell_value
    exch_rate, approximated = _rate_on(charges["exchange_txn"][exchange][instrument], trade_date,
                                       allow_earliest=True)
    if approximated:
        notes.append("exchange charges held at the earliest modelled rate (historical slabs not modelled)")
    exchange_txn = exch_rate * turnover
    sebi_fee = float(charges["sebi_fee"]["rate"]) * turnover
    stamp_duty = float(charges["stamp_duty"][instrument]) * buy_value
    brokerage = float(charges["brokerage"]["per_order_inr"]) * orders
    gst = float(charges["gst_rate"]) * (brokerage + exchange_txn + sebi_fee)

    total = brokerage + stt + exchange_txn + sebi_fee + stamp_duty + gst
    gross = sell_value - buy_value
    return CostBreakdown(
        trade_date=trade_date.isoformat(),
        instrument=instrument,
        buy_value=buy_value,
        sell_value=sell_value,
        gross_pnl=gross,
        brokerage=brokerage,
        stt=stt,
        exchange_txn=exchange_txn,
        sebi_fee=sebi_fee,
        stamp_duty=stamp_duty,
        gst=gst,
        total_charges=total,
        net_pnl=gross - total,
        breakeven_move_per_unit=total / quantity,
        stt_rate=stt_rate,
        notes=notes,
    )


def compare_regimes(charges: dict[str, Any], dates: list[date], **trade: Any) -> list[CostBreakdown]:
    """Cost of the same trade under the rules in force on each date."""
    return [round_trip_cost(charges, trade_date=d, **trade) for d in dates]
