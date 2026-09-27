import json

from finmedia import pipeline
from finmedia.models import Document

from .conftest import FIXTURES


def test_end_to_end_with_fake_llm(store, llm, tmp_path, monkeypatch):
    real_path_setting = pipeline.path_setting
    monkeypatch.setattr(pipeline, "path_setting",
                        lambda key: tmp_path / "out" if key == "output_dir" else real_path_setting(key))

    text = (FIXTURES / "sample_circular.txt").read_text(encoding="utf-8")
    pipeline.add_documents(store, [
        Document(source_id="inbox", title="Consultation Paper on review of framework for equity derivatives expiry",
                 text=text, category="regulator"),
        Document(source_id="inbox", title="Closure of Trading Window", text="routine"),
    ])
    assert pipeline.run_prefilter(store) == {"kept": 1, "dropped": 1}

    triage = pipeline.run_triage(store, llm)
    assert len(triage["triaged"]) == 1 and triage["stopped"] is None
    doc_id = triage["triaged"][0]["id"]

    brief = pipeline.run_brief(store, llm, doc_id)
    assert brief["verification"]["ok"], brief["verification"]

    paths = pipeline.run_reel(store, llm, doc_id)
    saved = json.loads(paths["plan"].read_text(encoding="utf-8"))
    assert saved["lint"]["passed"], saved["lint"]
    review = paths["review"].read_text(encoding="utf-8")
    assert "Gate G2" in review and "Approved by" in review
