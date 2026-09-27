import pytest

from finmedia.costs import BudgetExceeded, BudgetGuard, Usage, month_key
from finmedia.llm import LLM, FALLBACK_BETA, LLMRefusal
from finmedia.models import TriageResult

from .conftest import FakeMessages


def test_usd_math(store, cfg):
    guard = BudgetGuard(store, cfg)
    # Opus 5: $5 in / $25 out per 1M tokens.
    usd = guard.usd_for("claude-opus-5", Usage(input_tokens=1_000_000, output_tokens=100_000))
    assert usd == pytest.approx(5.0 + 2.5)
    cached = guard.usd_for("claude-opus-5", Usage(cache_read_tokens=1_000_000, cache_write_tokens=1_000_000))
    assert cached == pytest.approx(0.5 + 6.25)


def test_unknown_model_priced_at_most_expensive(store, cfg):
    guard = BudgetGuard(store, cfg)
    assert guard.usd_for("mystery-model", Usage(output_tokens=1_000_000)) == pytest.approx(25.0)


def test_budget_blocks_when_exhausted(store, cfg):
    guard = BudgetGuard(store, cfg)
    store.add_cost(month=month_key(), kind="subscription", item="HeyGen", inr=cfg["budget"]["monthly_cap_inr"])
    with pytest.raises(BudgetExceeded):
        guard.check("claude-opus-5", prompt_chars=1000, max_output_tokens=1000)


def test_llm_call_uses_caching_fallbacks_and_records_cost(llm, store, fake_client):
    result = llm.structured("triage", "system prompt", "document", TriageResult)
    assert result.playbook_id == "market_structure_flows"
    call = fake_client.beta.messages.calls[0]
    assert call["model"] == "claude-opus-5"
    assert call["system"][0]["cache_control"] == {"type": "ephemeral"}
    assert call["fallbacks"] == "default" and call["betas"] == [FALLBACK_BETA]
    assert call["output_config"] == {"effort": "low"}
    assert call["thinking"] == {"type": "adaptive"}
    assert store.month_spend(month_key(), "llm") > 0


def test_llm_refusal_raises(store, cfg):
    client = type("C", (), {})()
    client.beta = type("B", (), {"messages": FakeMessages(stop_reason="refusal")})()
    llm = LLM(BudgetGuard(store, cfg), cfg, client=client)
    with pytest.raises(LLMRefusal):
        llm.structured("triage", "s", "u", TriageResult)
