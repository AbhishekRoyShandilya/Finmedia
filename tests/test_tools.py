from datetime import date

import pytest
import yaml

from finmedia.config import load_yaml, project_root
from finmedia.tools.fno_costs import compare_regimes, round_trip_cost
from finmedia.tools.strategy_test import run_test

CHARGES = load_yaml("config/fno_charges.yaml")


def test_viral_claim_fails_strategy_test():
    facts = yaml.safe_load((project_root() / "config" / "strategy_test_example.yaml").read_text(encoding="utf-8"))
    result = run_test(facts)
    assert result["verdict"].startswith("DON'T TRUST")
    assert set(result["critical_reds"]) == {"q1_record", "q3_costs", "q4_period"}


def test_well_documented_strategy_passes():
    result = run_test({
        "instrument": "fno", "record": "broker_statement", "trades": 240, "costs_included": "all",
        "test_end_date": "2026-08-31", "win_rate": 0.45, "avg_win": 3000, "avg_loss": 1500,
        "max_drawdown_pct": 18, "tuned_parameters": 2, "works_on_multiple_markets": True,
        "capital_required_inr": 200000, "your_capital_inr": 500000, "seller_incentive": "none",
    })
    assert result["verdict"].startswith("PASSES")


def test_futures_round_trip_2026_hand_checked():
    b = round_trip_cost(CHARGES, instrument="futures", buy_price=25000, sell_price=25020,
                        quantity=75, trade_date=date(2026, 6, 1))
    # STT 0.05% of sell value 18,76,500 = 938.25
    assert b.stt == pytest.approx(938.25)
    assert b.stamp_duty == pytest.approx(37.5)          # 0.002% of 18,75,000
    assert b.brokerage == 40
    assert b.gross_pnl == pytest.approx(1500)
    assert b.total_charges == pytest.approx(1108.39, abs=0.02)


def test_same_trade_costs_more_under_newer_rules():
    old, mid, new = compare_regimes(CHARGES, [date(2023, 6, 1), date(2025, 6, 1), date(2026, 6, 1)],
                                    instrument="futures", buy_price=25000, sell_price=25020, quantity=75)
    assert old.stt < mid.stt < new.stt
    assert new.net_pnl < old.net_pnl
    assert old.notes and not new.notes     # historical exchange slabs are flagged


def test_options_stt_on_sell_premium():
    b = round_trip_cost(CHARGES, instrument="options", buy_price=100, sell_price=110,
                        quantity=75, trade_date=date(2026, 6, 1))
    assert b.stt == pytest.approx(0.0015 * 110 * 75)
