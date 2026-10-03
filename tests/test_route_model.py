"""route_model + registry: choice over models.yaml, abstain -> default."""

from __future__ import annotations

import pytest

import laya_mcp.server as srv
from laya_mcp.registry import Registry


@pytest.fixture(autouse=True)
def _client(stub):
    srv.configure(stub)
    yield
    srv.configure(None)


def _registry(tmp_path, entries: str) -> Registry:
    p = tmp_path / "models.yaml"
    p.write_text(f"models:\n{entries}", encoding="utf-8")
    return Registry.load(p)


TWO = (
    "  - label: fast-cheap\n    criteria: quick simple factual tasks\n"
    "  - label: slow-strong\n    criteria: complex reasoning, code, high stakes\n"
    "    default: true\n"
)


def test_route_model_offers_registry_labels(stub, tmp_path):
    srv.configure(stub, registry=_registry(tmp_path, TWO))
    stub.answer(model={"choice": "fast-cheap", "confidence": 0.9})
    out = srv.route_model(request="what is 2+2?")
    assert out["label"] == "fast-cheap"
    assert out["abstained"] is False
    options = stub.calls[0]["questions"]["model"]["criteria"]
    assert set(options) == {"fast-cheap", "slow-strong"}


def test_route_model_abstains_to_default(stub, tmp_path):
    srv.configure(stub, registry=_registry(tmp_path, TWO))
    stub.answer(model={"choice": "fast-cheap", "confidence": 0.2, "low_confidence": True})
    out = srv.route_model(request="???")
    assert out["label"] == "slow-strong"  # the marked default
    assert out["abstained"] is True


def test_route_model_first_entry_is_default_when_none_marked(stub, tmp_path):
    entries = "  - label: alpha\n    criteria: first\n  - label: beta\n    criteria: second\n"
    srv.configure(stub, registry=_registry(tmp_path, entries))
    stub.answer(model={"choice": "beta", "confidence": 0.1, "low_confidence": True})
    out = srv.route_model(request="???")
    assert out["label"] == "alpha"
    assert out["abstained"] is True


def test_route_model_too_few_entries_is_actionable(stub, tmp_path):
    srv.configure(stub, registry=_registry(tmp_path, "  - label: only\n    criteria: x\n"))
    with pytest.raises(Exception, match="models.yaml|registry"):
        srv.route_model(request="hi")
    # other tools keep working
    stub.answer(q={"noul": 0.7})
    assert srv.decide(state="s", questions={"q": {"type": "noul", "instructions": "i"}})
