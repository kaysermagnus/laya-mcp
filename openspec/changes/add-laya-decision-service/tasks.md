# Tasks

## 1. Scaffolding

- [x] 1.1 Create `pyproject.toml` (uv layout: `src/laya_mcp/`, `tests/`) with deps `fastmcp`, `httpx`, `pydantic`, `pyyaml`; verify `uv sync` succeeds
- [x] 1.2 Write `CONTEXT.md` glossary (Decision, Rerank, Gate, Route, Escalate, Registry); verify file exists and uses the book-to-rag glossary format
- [x] 1.3 Create `models.yaml` with two clearly-marked placeholder entries (label, criteria, default on the stronger one); verify it parses as valid YAML

## 2. decide tool (TDD: red → green)

- [x] 2.1 Write failing test: MCP in-memory client calls `decide` with a stubbed decision HTTP client → verify test fails before implementation
- [x] 2.2 Implement `decide` (passthrough to laya-serve `/v1/systemone`) → verify test passes
- [x] 2.3 Write failing test: backend unreachable → tool error names endpoint + corrective action → implement → verify passes

## 3. rerank tool (TDD: red → green)

- [x] 3.1 Write failing test: mixed-relevance candidates → survivors sorted by score, gated-out ids in `dropped` (stubbed decisions) → implement `rerank` (score+noul batch per candidate) → verify passes
- [x] 3.2 Write failing test: zero survivors → empty list + all ids in `dropped`, no error → implement → verify passes
- [x] 3.3 Write failing test: candidate `text` exceeding token budget is truncated, not an error → implement → verify passes

## 4. model-registry + route_model (TDD: red → green)

- [x] 4.1 Write failing test: valid registry loads at startup, entries become choice options → implement registry loader (`models.yaml`) → verify passes
- [x] 4.2 Write failing test: confident `route_model` call → chosen label, `abstained: false` → implement tool → verify passes
- [x] 4.3 Write failing test: low-confidence decision → default label, `abstained: true`; no default marked → first entry → implement → verify passes
- [x] 4.4 Write failing test: registry with <2 entries → `route_model` returns config error, other tools unaffected → implement → verify passes

## 5. Serving + packaging

- [x] 5.1 Dockerfile: install `laya[serve]` + CPU-only torch, bake `typed-decisions` checkpoint at build time (HF_HOME in-image); verify `docker build` produces an image
- [x] 5.2 Compose/docker-run check: `laya-serve` on :8090 (no host publish) answers `/health` and a real `/v1/systemone` decision → verify via `curl` inside the network
- [x] 5.3 `laya-mcp` service on :8091 streamable-HTTP; verify an MCP client lists the three tools
- [x] 5.4 Integration smoke (real model): `rerank` and `route_model` end-to-end against baked ONNX → verify sensible answers on a fixed example; mark test as slow/opt-in

## 6. Docs

- [x] 6.1 README.md: build, run, compose-service snippet for sibling projects; verify commands run as written
