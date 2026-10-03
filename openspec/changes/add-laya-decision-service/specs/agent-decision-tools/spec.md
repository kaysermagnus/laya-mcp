# Spec Delta

## Purpose

Agent-facing MCP server (streamable HTTP) exposing domain decision tools that translate to typed questions answered by the decision service.

## ADDED Requirements

### Requirement: MCP streamable-HTTP endpoint
The server SHALL expose its tools over MCP streamable-HTTP on a published port (default :8091) so multiple agents can connect concurrently.

#### Scenario: Agent discovers tools
- **WHEN** an MCP client connects and lists tools
- **THEN** it sees `rerank`, `route_model`, and `decide` with input schemas

### Requirement: rerank tool
`rerank` SHALL accept a question and a list of candidate items `{id, text}`, evaluate each candidate with a `score` (relevance) plus `noul` decision in a shared batch; a candidate survives when its score reaches the relevance floor or its noul keep probability clears the keep threshold, and return surviving items sorted by relevance with their scores, plus a `dropped` list of gated-out ids. Empty survivors SHALL be a normal result, not an error.

#### Scenario: Relevant candidates ranked, irrelevant dropped
- **WHEN** called with a question and mixed-relevance candidates
- **THEN** survivors are sorted best-first and gated-out ids appear in `dropped`

#### Scenario: Nothing relevant
- **WHEN** no candidate passes the keep-gate
- **THEN** the tool returns an empty result list with all ids in `dropped`

### Requirement: route_model tool
`route_model` SHALL accept a request description (context and/or user question), evaluate a `choice` decision over the model registry, and return the chosen label, confidence, and whether the decision abstained to the registry default.

#### Scenario: Confident routing
- **WHEN** a request clearly matches one registry entry's criteria
- **THEN** the tool returns that label with `abstained: false`

### Requirement: decide tool
`decide` SHALL accept a state and arbitrary typed questions and return the decision service's answers verbatim — a passthrough for uses not covered by the domain tools.

#### Scenario: Passthrough
- **WHEN** called with valid typed questions
- **THEN** the response contains the same `answers` structure the decision service returns

### Requirement: Actionable backend errors
When the decision service is unreachable or rejects a request, tools SHALL return an error message naming the cause and the corrective action (e.g., service name to check), not a bare stack trace.

#### Scenario: Backend down
- **WHEN** the decision service is unreachable
- **THEN** the tool error states the endpoint it tried and suggests checking the `laya-serve` service
