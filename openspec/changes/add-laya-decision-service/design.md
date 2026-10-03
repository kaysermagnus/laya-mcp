# Design

## Context

See proposal.md — Why. Constraints that shape the approach:

- Docker on macOS runs a Linux VM: **no Metal/ANE**, so MLX inference is impossible inside a container. The user's `~/.lmstudio` MLX weights (base `laya`, 512 ctx) are unusable here — both by runtime and by context size (book chunks are ~1024 tokens).
- `laya` (PyPI) already ships `laya-serve` (Jev HTTP API), `laya[mcp]`, and an ONNX export path (`scripts/export_onnx.py --quantize`) — this project wires, it does not reimplement.
- `laya-typed-decisions` is the fine-tuned English checkpoint (0.766 vs 0.362 base on the decisions benchmark) with 1024-token context — the only shipped checkpoint covering book-to-rag's chunks.
- book-to-rag's public seam is `query()` in `book_rag/__init__.py`; its rerank loop is a *separate change* in that repo. This repo only needs to offer a stable HTTP contract for it to call.

## Goals / Non-Goals

**Goals:**
- One Docker image → two services: `laya-serve` (internal HTTP :8090, compose network only) and `laya-mcp` (streamable-HTTP MCP :8091, calls laya-serve over HTTP so only one model is resident).
- Domain tools `rerank` / `route_model` / `decide` over laya's typed decisions; `rerank` batches candidates into shared forward passes.
- `models.yaml` registry; abstain → default entry.

**Non-Goals:**
- No GPU/ANE acceleration (impossible in Docker on macOS; a host `laya-mlx`/`laya-apple` backend is a future env-switchable option).
- No fine-tuning, no multilingual checkpoint baked (HF cache volume left as the lazy-pull escape hatch).
- No auth on either endpoint — compose-local deployment only.
- The book-to-rag retrieve-loop lives in the book-to-rag repo, not here.

## Decisions

- **PyTorch CPU over ONNX in the image**: `laya-serve` only serves torch `Agent`s — ONNX exists as `ONNXAgent` for evals/export, with no serve path, so ONNX would mean writing a custom HTTP wrapper (parity risk for zero spec gain). CPU torch on a 421M encoder is fast enough for rerank batches. Cost accepted: bigger image (~1 GB torch CPU wheel + ~840 MB checkpoint). Alternative rejected: ONNXAgent + custom serve wrapper — deviation from upstream wire behavior.
- **Two processes, one image**: `laya-mcp` calls `laya-serve` via HTTP rather than loading ONNX in-process. Rationale: single resident model (~210 MB RAM saved), same contract for tests, and book-to-rag hits the identical endpoint. Alternative: in-process router inside the MCP server — rejected (two containers would each hold a model).
- **FastMCP (Python) over TypeScript SDK**: the project is Python (uv) like its sibling book-to-rag; tools are thin async wrappers over httpx.
- **rerank semantics: `score` floor + `noul` override, not `choice` best-of-N**: absolute thresholds let callers detect "nothing relevant"; `choice` always crowns a winner. Live probing showed the calibrated noul sits mid-range for borderline text (relevant≈0.36 vs irrelevant≈0.13) — a fixed 0.5 noul gate would gut recall, so the keep rule is `score >= 2.0 (partially relevant) or noul >= 0.5`.
- **Registry abstain → default**: mirrors laya's own `escalate` action; the default entry stands in for "strongest general model".

## Risks / Trade-offs

- **CPU-only decision latency (~50–300 ms/call)** → acceptable for rerank batches of ~10 candidates and single route calls; if it ever hurts, a host `laya-mlx` endpoint can back the same HTTP contract via env.
- **1024-token context still truncates oversized chunks** → callers must pre-truncate; the rerank tool truncates `text` to a documented token budget rather than failing.
- **Placeholder registry ships useless routing until edited** → entries are clearly marked `placeholder: true`-style comments; `route_model` still functions (that's the point of the minimum-viable-registry rule).
- **ONNX export is a build-time step inside the Dockerfile** → pin laya + onnxruntime versions; a build arg can swap to the PyTorch checkpoint if export breaks.

## Migration Plan

New service — nothing to migrate. Rollout: `docker build` the image in laya-mcp, then book-to-rag's compose adds the two services (`build: ../laya-mcp`). Rollback: remove the services; no state persists.

## Open Questions

- Real registry contents (deferred by user — `models.yaml` ships placeholders).
- Whether a future host MLX backend is worth the env-switch — only if measured CPU latency proves painful.
