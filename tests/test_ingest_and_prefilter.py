from finmedia.config import load_yaml
from finmedia.models import Document
from finmedia.playbooks import catalog_text, playbook_ids
from finmedia.prefilter import score_document
from finmedia.sources.inbox import read_inbox
from finmedia.sources.rss import parse_feed

from .conftest import FIXTURES

SOURCE = {"id": "test_feed", "category": "regulator", "regulator": "TEST"}


def test_parse_feed_reads_all_entries():
    docs = parse_feed((FIXTURES / "sample_feed.xml").read_bytes(), SOURCE)
    assert [d.title for d in docs][0].startswith("Consultation Paper")
    assert len(docs) == 3
    assert docs[0].published_at is not None
    assert docs[0].regulator == "TEST"


def test_prefilter_keeps_policy_and_drops_routine():
    rules = load_yaml("config/prefilter.yaml")
    docs = parse_feed((FIXTURES / "sample_feed.xml").read_bytes(), SOURCE)
    results = [score_document(d, rules, min_score=3) for d in docs]
    assert results[0].keep and results[0].score >= 3
    assert not results[1].keep and "routine filing" in results[1].reasons[0]
    assert not results[2].keep


def test_inbox_reads_text_with_title_and_url(tmp_path):
    (tmp_path / "circular.txt").write_text((FIXTURES / "sample_circular.txt").read_text(encoding="utf-8"),
                                            encoding="utf-8")
    (tmp_path / "ignore.csv").write_text("a,b", encoding="utf-8")
    docs = read_inbox(tmp_path, {"id": "inbox"})
    assert len(docs) == 1
    assert docs[0].title.startswith("Consultation Paper")
    assert docs[0].url == "https://example.org/cp-derivatives-expiry"


def test_store_deduplicates(store):
    doc = Document(source_id="x", title="Same", text="body")
    assert store.add_document(doc) is not None
    assert store.add_document(doc) is None


def test_playbooks_loaded():
    ids = playbook_ids()
    assert "regulatory_change" in ids and "rumour_unverified" in ids
    assert "market_structure_flows" in catalog_text()
