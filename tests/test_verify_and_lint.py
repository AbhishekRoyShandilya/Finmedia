from finmedia.lint import lint_reel
from finmedia.verify import numbers_in, spoken_numbers, verify_brief

from .conftest import FIXTURES, sample_brief, sample_reel

DOC = (FIXTURES / "sample_circular.txt").read_text(encoding="utf-8")


def test_numbers_normalized():
    assert numbers_in("₹61,000 crore and 2.50% and ५९") == {"61000", "2.5", "59"}


def test_spoken_scale_words():
    [(raw, candidates)] = spoken_numbers("61 हज़ार करोड़ रुपये")
    assert raw == "61" and "61000" in candidates


def test_brief_verification_passes_for_grounded_brief():
    result = verify_brief(sample_brief().model_dump(mode="json"), DOC)
    assert result["ok"], result


def test_brief_verification_catches_invented_numbers_and_quotes():
    brief = sample_brief().model_dump(mode="json")
    brief["mechanism"] = "Costs could rise 37% for sellers."
    brief["facts"][0]["source_quote"] = "text that is not in the document"
    result = verify_brief(brief, DOC)
    assert not result["ok"]
    assert "37" in result["unsupported_numbers"]
    assert result["missing_quotes"]


def test_good_reel_passes(lint_rules):
    report = lint_reel(sample_reel().model_dump(mode="json"), lint_rules,
                       brief=sample_brief().model_dump(mode="json"))
    assert report.passed, report.as_dict()


def test_anchor_phrase_and_advice_are_errors(lint_rules):
    plan = sample_reel().model_dump(mode="json")
    plan["scenes"][0]["narration"] = "जी हाँ, आपने सही सुना! अभी खरीद लो।"
    report = lint_reel(plan, lint_rules)
    joined = " ".join(report.errors)
    assert "News-anchor phrase" in joined and "Recommendation" in joined


def test_missing_disclosure_and_low_effort_are_errors(lint_rules):
    plan = sample_reel().model_dump(mode="json")
    plan["disclosure"] = "Not investment advice."
    for scene in plan["scenes"]:
        scene["visual"] = "AVATAR"
    report = lint_reel(plan, lint_rules)
    joined = " ".join(report.errors)
    assert "Disclosure" in joined and "non-avatar visual" in joined


def test_number_not_in_brief_is_error(lint_rules):
    plan = sample_reel().model_dump(mode="json")
    plan["scenes"][1]["narration"] = "Index options का 83 percent कारोबार expiry पर होता है।"
    report = lint_reel(plan, lint_rules, brief=sample_brief().model_dump(mode="json"))
    assert any("'83'" in e for e in report.errors)
