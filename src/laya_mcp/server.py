"""laya-mcp: agent-facing decision tools backed by laya-serve.

    uv run laya-mcp                                  # stdio (default)
    uv run laya-mcp --transport http --host 0.0.0.0 --port 8091   # streamable-http

The backend is laya-serve (Jev HTTP). Point at it with LAYA_SERVE_URL
(default http://localhost:8090). Tools: decide, rerank, route_model.
"""

from __future__ import annotations

import argparse
from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import DecisionClient, LayaServeClient
from .registry import Registry

_client: DecisionClient | None = None
_registry: Registry | None = None


def configure(client: DecisionClient | None, registry: Registry | None = None) -> None:
    """Inject the decision backend / registry (tests; defaults from env/files)."""
    global _client, _registry
    _client = client
    _registry = registry


def _get_client() -> DecisionClient:
    global _client
    if _client is None:
        _client = LayaServeClient.from_env()
    return _client


def _get_registry() -> Registry:
    global _registry
    if _registry is None:
        _registry = Registry.load()
    return _registry


mcp = FastMCP(
    "laya-mcp",
    instructions=(
        "Cheap, deterministic System 1 decisions: rerank candidates by "
        "relevance, route_model picks a registry model, decide answers "
        "arbitrary typed questions. No text is generated."
    ),
)

#: Conservative character budget for a candidate's text: ~750 tokens of the
#: 1024-token checkpoint context, leaving headroom for the question prefix.
#: Longer texts are truncated, not refused.
MAX_STATE_CHARS = 3000

#: Relevance-score floor: the ordinal scale's "partially relevant" level.
#: A calibrated noul sits mid-range for borderline text — the score floor
#: keeps it (recall), while KEEP_THRESHOLD below catches confident keeps.
SCORE_FLOOR = 2.0

#: noul keep-gate probability at or above which a candidate survives even
#: when its score falls below the floor.
KEEP_THRESHOLD = 0.5

_RERANK_QUESTIONS = {
    "relevance": {
        "type": "score",
        "instructions": "How relevant is this text for answering the question?",
        "criteria": [
            "completely irrelevant",
            "tangential",
            "partially relevant",
            "relevant",
            "directly answers the question",
        ],
    },
    "keep": {
        "type": "noul",
        "instructions": "Is this text relevant enough to help answer the question?",
    },
}


@mcp.tool()
def decide(
    state: Any,
    questions: dict[str, Any],
    min_confidence: float | None = None,
) -> dict:
    """Answer typed questions about a state via laya-serve (passthrough).

    questions: {qid: {type: "choice"|"score"|"noul", instructions, criteria}}.
    Returns the service's answers verbatim.
    """
    kwargs = {"min_confidence": min_confidence} if min_confidence is not None else {}
    return _get_client().predict(state, questions, **kwargs)


@mcp.tool()
def rerank(
    question: str,
    candidates: list[dict[str, Any]],
    min_confidence: float | None = None,
) -> dict:
    """Score and gate retrieval candidates; return survivors best-first.

    Each candidate is {"id": ..., "text": ...}. Every candidate gets a
    relevance score plus a keep/drop gate in one batch; survivors are
    sorted by relevance descending, gated-out ids land in `dropped`.
    An empty `results` list means nothing was relevant — not an error.
    """
    states = [str(c["text"]) for c in candidates]
    prefixed = [f"Question: {question}\n\n{s}"[:MAX_STATE_CHARS] for s in states]
    kwargs = {"min_confidence": min_confidence} if min_confidence is not None else {}
    results = _get_client().predict_batch(prefixed, _RERANK_QUESTIONS, **kwargs)

    kept, dropped = [], []
    for cand, res in zip(candidates, results, strict=True):
        answers = res.get("answers", {})
        score = float(answers.get("relevance", {}).get("score", 0.0))
        keep = float(answers.get("keep", {}).get("noul", 0.0))
        if score >= SCORE_FLOOR or keep >= KEEP_THRESHOLD:
            kept.append({"id": cand["id"], "relevance": score})
        else:
            dropped.append(cand["id"])
    kept.sort(key=lambda r: -r["relevance"])
    return {"results": kept, "dropped": dropped}


#: Confidence below which route_model escalates to the registry default.
ROUTE_MIN_CONFIDENCE = 0.5


@mcp.tool()
def route_model(
    request: str,
    min_confidence: float | None = None,
) -> dict:
    """Pick the best registry model for a request (choice decision).

    request: the context and/or user question to route. Returns
    {"label", "confidence", "abstained"} — on low confidence the answer
    escalates to the registry's default entry with abstained: true.
    """
    registry = _get_registry()
    registry.check_routable()
    threshold = ROUTE_MIN_CONFIDENCE if min_confidence is None else min_confidence
    questions = {
        "model": {
            "type": "choice",
            "instructions": "Which model should handle this request?",
            "criteria": {e.label: e.criteria for e in registry.entries},
        }
    }
    out = _get_client().predict(request, questions, min_confidence=threshold)
    answer = out.get("answers", {}).get("model", {})
    confidence = float(answer.get("confidence", 0.0))
    abstained = bool(answer.get("low_confidence")) or confidence < threshold
    label = registry.default.label if abstained else answer.get("choice")
    return {"label": label, "confidence": confidence, "abstained": abstained}


def main() -> None:
    parser = argparse.ArgumentParser(description="laya-mcp decision tools server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "http"],
        default="stdio",
        help="stdio for in-process agents; http serves streamable-http (default: stdio)",
    )
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8091)
    args = parser.parse_args()

    if args.transport == "http":
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
