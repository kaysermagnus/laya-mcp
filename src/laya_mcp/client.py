"""HTTP client for laya-serve (Jev wire protocol, /v1/systemone)."""

from __future__ import annotations

import os
from typing import Any, Protocol

import httpx

DEFAULT_URL = "http://localhost:8090"


class DecisionClient(Protocol):
    """The seam the tools depend on: single and batch typed decisions."""

    def predict(self, state: Any, questions: dict, **kwargs) -> dict:
        """POST /v1/systemone — one state, a map of typed questions."""
        ...

    def predict_batch(self, states: list, questions: dict, **kwargs) -> list[dict]:
        """POST /v1/systemone/batch — shared questions over many states."""
        ...


class BackendError(RuntimeError):
    """laya-serve unreachable or rejecting — message names the fix."""


class LayaServeClient:
    """Sync httpx client; the MCP server runs sync tools in a threadpool."""

    def __init__(
        self,
        base_url: str,
        *,
        model: str | None = "typed-decisions",
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ):
        self._base = base_url.rstrip("/")
        self._model = model
        self._http = httpx.Client(base_url=self._base, timeout=timeout, transport=transport)

    @classmethod
    def from_env(cls) -> LayaServeClient:
        return cls(
            os.environ.get("LAYA_SERVE_URL", DEFAULT_URL),
            model=os.environ.get("LAYA_MODEL", "typed-decisions"),
        )

    def _post(self, path: str, body: dict) -> dict:
        if self._model:
            body.setdefault("model", self._model)
        try:
            r = self._http.post(path, json=body)
            r.raise_for_status()
        except httpx.ConnectError as e:
            raise BackendError(
                f"laya-serve unreachable at {self._base} — is the laya-serve service running?"
            ) from e
        except httpx.HTTPStatusError as e:
            detail = e.response.text[:300]
            raise BackendError(
                f"laya-serve rejected the request ({e.response.status_code}): {detail}"
            ) from e
        except httpx.HTTPError as e:
            raise BackendError(f"laya-serve request failed: {e}") from e
        return r.json()

    def predict(self, state: Any, questions: dict, **kwargs) -> dict:
        return self._post("/v1/systemone", {"state": state, "questions": questions, **kwargs})

    def predict_batch(self, states: list, questions: dict, **kwargs) -> list[dict]:
        out = self._post(
            "/v1/systemone/batch", {"states": list(states), "questions": questions, **kwargs}
        )
        return out["results"]
