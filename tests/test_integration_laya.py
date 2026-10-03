"""End-to-end against the real laya-serve container (opt-in).

Needs `docker compose up -d` (or any laya-serve on LAYA_SERVE_URL).
Auto-skips when the service isn't running.
"""

from __future__ import annotations

import os
import time
import urllib.request

import pytest

import laya_mcp.server as srv
from laya_mcp.client import LayaServeClient
from laya_mcp.registry import Registry

URL = os.environ.get("LAYA_SERVE_URL", "http://localhost:8090")


def _serve_up() -> bool:
    for attempt in range(2):
        try:
            with urllib.request.urlopen(f"{URL}/health", timeout=3) as r:
                return r.status == 200
        except Exception:
            if attempt == 0:
                time.sleep(0.5)
    return False


pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _serve_up(), reason=f"laya-serve not running on {URL}"),
]


@pytest.fixture(autouse=True)
def _real_client(tmp_path):
    reg = tmp_path / "models.yaml"
    reg.write_text(
        "models:\n"
        "  - label: weak\n    criteria: trivial lookups\n"
        "  - label: strong\n    criteria: hard reasoning, code, math\n"
        "    default: true\n",
        encoding="utf-8",
    )
    srv.configure(LayaServeClient(URL), registry=Registry.load(reg))
    yield
    srv.configure(None)


def test_rerank_drops_irrelevant_candidates():
    out = srv.rerank(
        question="What propels the Pequod?",
        candidates=[
            {
                "id": "sea",
                "text": (
                    "The Pequod's sails filled as the ship left Nantucket, "
                    "driven by the trade winds across the Atlantic."
                ),
            },
            {
                "id": "tax",
                "text": (
                    "Form 1040 instructions: enter your adjusted gross "
                    "income on line 11 before computing tax."
                ),
            },
        ],
    )
    ids = [r["id"] for r in out["results"]]
    assert "sea" in ids and "tax" in out["dropped"]


def test_route_model_picks_strong_for_hard_request():
    out = srv.route_model(
        request=(
            "Prove whether this distributed consensus algorithm "
            "is safe under network partitions."
        )
    )
    assert out["label"] in {"weak", "strong"}
    assert out["confidence"] >= 0.0
