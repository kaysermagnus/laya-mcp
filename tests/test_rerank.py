"""rerank tool: score + keep-gate over retrieval candidates."""

from __future__ import annotations

import pytest

import laya_mcp.server as srv
from laya_mcp.server import MAX_STATE_CHARS


@pytest.fixture(autouse=True)
def _client(stub):
    srv.configure(stub)
    yield
    srv.configure(None)


def _cands(*texts):
    return [{"id": f"c{i}", "text": t} for i, t in enumerate(texts)]


def test_rerank_orders_survivors_and_drops_gated(stub):
    stub.batch(
        {"relevance": {"score": 3.0}, "keep": {"noul": 0.9}},
        {"relevance": {"score": 1.2}, "keep": {"noul": 0.1}},
        {"relevance": {"score": 4.5}, "keep": {"noul": 0.8}},
    )
    out = srv.rerank(question="who is Ahab?", candidates=_cands("a", "b", "c"))
    assert [r["id"] for r in out["results"]] == ["c2", "c0"]
    assert out["results"][0]["relevance"] == 4.5
    assert out["dropped"] == ["c1"]


def test_rerank_uses_score_and_gate_questions(stub):
    stub.batch({"relevance": {"score": 4.0}, "keep": {"noul": 0.9}})
    srv.rerank(question="q", candidates=_cands("a"))
    questions = stub.calls[0]["questions"]
    assert questions["relevance"]["type"] == "score"
    assert questions["keep"]["type"] == "noul"
    # the question reaches the model inside the candidate's state text
    assert "q" in stub.calls[0]["states"][0] and "a" in stub.calls[0]["states"][0]


def test_rerank_confident_noul_overrides_low_score(stub):
    """Score below the floor survives when the gate is confident anyway."""
    stub.batch(
        {"relevance": {"score": 1.8}, "keep": {"noul": 0.92}},
        {"relevance": {"score": 1.5}, "keep": {"noul": 0.1}},
    )
    out = srv.rerank(question="q", candidates=_cands("a", "b"))
    assert [r["id"] for r in out["results"]] == ["c0"]
    assert out["dropped"] == ["c1"]


def test_rerank_nothing_relevant_is_not_an_error(stub):
    stub.batch(
        {"relevance": {"score": 1.0}, "keep": {"noul": 0.2}},
        {"relevance": {"score": 1.9}, "keep": {"noul": 0.3}},
    )
    out = srv.rerank(question="q", candidates=_cands("x", "y"))
    assert out["results"] == []
    assert out["dropped"] == ["c0", "c1"]


def test_rerank_truncates_oversized_candidates(stub):
    stub.batch({"relevance": {"score": 4.0}, "keep": {"noul": 0.9}})
    srv.rerank(question="q", candidates=_cands("x" * (MAX_STATE_CHARS + 5000)))
    sent = stub.calls[0]["states"][0]
    assert len(sent) <= MAX_STATE_CHARS
