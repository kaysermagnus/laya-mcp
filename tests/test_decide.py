"""decide tool: typed-question passthrough to laya-serve."""

from __future__ import annotations

import httpx
import pytest

import laya_mcp.server as srv
from laya_mcp.client import BackendError, LayaServeClient


@pytest.fixture(autouse=True)
def _client(stub):
    srv.configure(stub)
    yield
    srv.configure(None)


def test_decide_returns_answers_verbatim(stub):
    stub.answer(urgency={"choice": "billing", "confidence": 0.91})
    out = srv.decide(
        state="I was billed twice. Please refund the duplicate.",
        questions={
            "urgency": {
                "type": "choice",
                "instructions": "Which department?",
                "criteria": {"billing": "refunds", "technical": "bugs"},
            }
        },
    )
    assert out["answers"]["urgency"]["choice"] == "billing"
    assert stub.calls[0]["questions"]["urgency"]["type"] == "choice"


def test_decide_backend_down_is_actionable(stub):
    stub.error = BackendError(
        "laya-serve unreachable at http://x — is the laya-serve service running?"
    )
    with pytest.raises(Exception, match="laya-serve"):
        srv.decide(
            state="x",
            questions={"q": {"type": "noul", "instructions": "y?"}},
        )


def test_client_translates_connect_error():
    """The real adapter turns raw httpx failures into named BackendErrors."""

    def _boom(request):
        raise httpx.ConnectError("refused", request=request)

    client = LayaServeClient("http://laya-serve:8090", transport=httpx.MockTransport(_boom))
    with pytest.raises(BackendError, match="laya-serve"):
        client.predict("s", {"q": {"type": "noul", "instructions": "y?"}})
