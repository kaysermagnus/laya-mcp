# laya-mcp

MCP server exposing [laya](https://github.com/NandhaKishorM/laya) typed decisions — cheap, deterministic "System 1" judgments in one forward pass, no text generated — for agents that need to rerank candidates, gate relevance, or route between models.

```
agent ──MCP──> laya-mcp ──HTTP──> laya-serve ──> typed-decisions (CPU, baked in)
 :8091 streamable-http           :8090 internal
```

One Docker image runs both services; `laya-serve` stays on the compose network (no host port).

## Tools

| tool | input | output |
|---|---|---|
| `rerank` | `question`, `candidates: [{id, text}]` | `results: [{id, relevance}]` best-first + `dropped: [ids]` — empty results means "nothing relevant", not an error |
| `route_model` | `request` | `{label, confidence, abstained}` — low confidence escalates to the registry default |
| `decide` | `state`, `questions` | raw laya-serve answers (choice/score/noul passthrough) |

## Build & run

```bash
docker build -t laya-mcp:latest .
docker compose up -d        # dev stack: laya-serve (internal) + laya-mcp on :8091
```

From a sibling project (e.g. book-to-rag), reference the same image in its compose:

```yaml
  laya-serve:
    build: ../laya-mcp       # or `image: laya-mcp:latest` once built
  laya-mcp:
    image: laya-mcp:latest
    command: ["laya-mcp", "--transport", "http", "--host", "0.0.0.0", "--port", "8091"]
    ports: ["8091:8091"]
    depends_on: [laya-serve]
```

Connect an MCP client to `http://localhost:8091/mcp` (streamable-http). For stdio agents outside Docker: `uv run laya-mcp` with `LAYA_SERVE_URL` pointing at a reachable laya-serve.

## Configuration

| env | default | purpose |
|---|---|---|
| `LAYA_SERVE_URL` | `http://localhost:8090` | decision backend for the MCP server |
| `LAYA_MODEL` | `typed-decisions` | checkpoint pinned on every request |
| `LAYA_REGISTRY` | `models.yaml` | routing registry path for `route_model` |
| `LAYA_SERVE_URL` (compose) | `http://laya-serve:8090` | service-to-service address |

`models.yaml` ships **placeholder** entries (`fast-cheap`, `slow-strong`) — replace with the models your harness actually uses. Mount a real one over `/app/models.yaml` or set `LAYA_REGISTRY`.

## Notes

- Inference is PyTorch CPU inside the container (MLX/ANE can't run in Docker on macOS). Expect ~50–300 ms per decision.
- The `laya-typed-decisions` checkpoint (English, 1024-token context) is baked into the image — cold start works offline (`HF_HUB_OFFLINE=1`).
- The host MLX copy at `~/.lmstudio/models/sjoerdbodbijl/laya-mlx` is the *base* checkpoint (512 ctx) and is unrelated to this service; `pip install laya-mlx` can drive it on the host for experiments.

## Tests

```bash
uv sync
uv run pytest          # unit tests — stubbed decision client
uv run pytest -m integration   # needs `docker compose up` running
```

See `CONTEXT.md` for domain language and `openspec/changes/add-laya-decision-service/` for the design.
