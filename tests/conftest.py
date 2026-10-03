"""Test seam: a stub decision client standing in for laya-serve HTTP.

Tools are exercised as plain functions (the FastMCP surface), with the
decision backend faked — mirroring book-to-rag's embedder-DI tests.
"""

from __future__ import annotations

import pytest


class StubDecisions:
    """Records calls; returns canned laya-serve-shaped answers."""

    def __init__(self):
        self.calls: list[dict] = []
        self._answers: dict[str, dict] = {}
        self._batch: list[dict] = []
        self.error: Exception | None = None

    # --- canned-response setup -------------------------------------------------
    def answer(self, **answers) -> StubDecisions:
        """Queue a single predict() response: answer(qid=..., ...)."""
        self._answers = dict(answers)
        return self

    def batch(self, *results: dict) -> StubDecisions:
        """Queue predict_batch() responses, one answer-map per state."""
        self._batch = list(results)
        return self

    # --- client protocol -------------------------------------------------------
    def predict(self, state, questions, **kwargs) -> dict:
        self.calls.append({"states": [state], "questions": questions, **kwargs})
        if self.error:
            raise self.error
        return {"model": "typed-decisions", "answers": dict(self._answers)}

    def predict_batch(self, states, questions, **kwargs) -> list[dict]:
        self.calls.append({"states": list(states), "questions": questions, **kwargs})
        if self.error:
            raise self.error
        return [{"model": "typed-decisions", "answers": dict(a)} for a in self._batch][
            : len(states)
        ]


@pytest.fixture
def stub():
    return StubDecisions()
