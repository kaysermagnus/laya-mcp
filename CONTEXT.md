# laya-mcp

An MCP server that gives agents cheap, deterministic "System 1" judgments — reranking candidates, gating relevance, and routing between models — backed by a laya decision model over HTTP.

## Language

**Decision**:
The atomic unit laya produces: a typed answer to a question about a state — `choice` (pick a label), `score` (ordinal level), or `noul` (P(true) for a statement) — with a confidence. Produced in one forward pass, never generated text.
_Avoid_: prediction, inference, generation

**State**:
The input a Decision is made about — text, or a JSON document. For `rerank`, each candidate's text becomes a State.
_Avoid_: context, document, prompt

**Rerank**:
Scoring retrieval candidates for true relevance and returning survivors in best-first order. Reorders and removes — never alters text.
_Avoid_: re-rank (hyphenated), filter — a Gate drops; a Rerank also orders

**Gate**:
The keep/drop `noul` applied per candidate during a Rerank. Absolute: a candidate passes or not on its own merits, not relative to the pool.
_Avoid_: threshold, filter

**Route**:
Choosing one entry from the Registry for a request — a `choice` Decision whose options are registry labels.
_Avoid_: dispatch, selection

**Escalate**:
What a Route does when its confidence is below threshold: return the Registry's default entry flagged `abstained`. Stands in for "ask the strongest model" when the decision model isn't sure.
_Avoid_: fallback (fallback implies something failed; escalation is a deliberate decision)

**Registry**:
The `models.yaml` file listing candidate models — each a `label` plus free-text `criteria` describing what it handles best — that `route_model` chooses among.
_Avoid_: catalog, config

**laya-serve**:
The internal HTTP service (Jev wire protocol, `/v1/systemone`) the MCP tools call. Infrastructure, not a domain concept — tools expose Decisions, not HTTP.
