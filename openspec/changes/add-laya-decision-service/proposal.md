# Proposal

## Why

Local agents need cheap, deterministic "System 1" judgments — reranking retrieval candidates, gating relevance, and routing requests between models — without paying LLM latency/cost or trusting generative output to be parseable. Laya (non-autoregressive typed-decision encoder, ~33 ms/decision) fits exactly, but nothing exposes it as a reusable, containerized service for agents on this machine.

## What Changes

- New project `laya-mcp`: a single Docker image producing two services.
  - `laya-serve`: internal HTTP decision API (Jev wire contract) on the compose network only, serving `laya-typed-decisions` exported to ONNX INT8, baked into the image.
  - `laya-mcp`: streamable-HTTP MCP server (agent-facing) that calls `laya-serve` over HTTP and exposes domain tools: `rerank`, `route_model`, `decide`.
- `rerank` tool: batch `score` + `noul` gate over candidate items; returns survivors sorted by relevance. Absolute thresholds (not relative best-of-N) so callers can detect "nothing relevant".
- `route_model` tool: `choice` decision over a YAML-defined candidate registry; low-confidence answers abstain to the registry's default entry.
- `decide` tool: raw typed-question passthrough for unanticipated uses.
- `models.yaml` routing registry: two clearly-marked placeholder entries to be replaced with the user's real model set.
- `CONTEXT.md` glossary for the new project; Dockerfile + compose service definitions consumable by sibling projects (book-to-rag).

## Capabilities

### New Capabilities
- `decision-serving`: the internal HTTP service that answers typed questions (`choice`, `score`, `noul`) about a state via the ONNX `laya-typed-decisions` checkpoint, including batch requests and abstention thresholds.
- `agent-decision-tools`: the MCP tool surface agents call — `rerank`, `route_model`, `decide` — over streamable HTTP.
- `model-registry`: the declarative registry of candidate models (label, criteria, default flag) that `route_model` chooses among, including the abstain-to-default rule.

### Modified Capabilities
- (none — greenfield project)

## Impact

- New repo `~/Projects/personal/laya-mcp/` (uv Python package, Dockerfile, CONTEXT.md, openspec/).
- Consumed by `book-to-rag` as two compose services (`build: ../laya-mcp`); book-to-rag's `retrieve` rerank is a separate change in that repo.
- No cloud APIs, keys, or host GPU required: inference is ONNX CPU inside the container.
- The user's MLX checkpoint at `~/.lmstudio/models/sjoerdbodbijl/laya-mlx` is **not** used — it is the base `laya` checkpoint (512-token context, English) and MLX cannot run inside Docker on macOS. It remains usable on the host via `pip install laya-mlx` for experiments.
