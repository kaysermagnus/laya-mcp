# Spec Delta

## Purpose

Internal HTTP service that answers typed questions (`choice`, `score`, `noul`) about a state in a single forward pass, backing all agent-facing decision tools.

## ADDED Requirements

### Requirement: Typed decisions over HTTP
The service SHALL expose an HTTP endpoint that accepts a `state` (text or JSON document) plus a map of typed questions and returns an answer per question: `choice` → selected label, `score` → ordinal level, `noul` → P(true); each with a confidence value.

#### Scenario: Single decision request
- **WHEN** a caller POSTs a state and questions `{"urgency": {"type": "choice", ...}}`
- **THEN** the response contains `answers.urgency.choice` and a confidence

#### Scenario: Invalid request rejected
- **WHEN** a caller POSTs a null state, an unknown question type, or a malformed questions map
- **THEN** the service returns a 4xx error naming the offending field

### Requirement: Batch decisions
The service SHALL accept a batch of independent requests in one call and return results in request order.

#### Scenario: Batch preserves order
- **WHEN** a caller submits N requests in one batch
- **THEN** it receives N results aligned to the original request order

### Requirement: Abstention threshold
The service SHALL accept a `min_confidence` parameter; answers below threshold SHALL be flagged (`low_confidence` / abstention status) rather than silently returned as normal.

#### Scenario: Below-threshold answer flagged
- **WHEN** a request sets `min_confidence` and an answer's confidence is below it
- **THEN** that answer reports its abstention status to the caller

### Requirement: Self-contained inference
The service SHALL run its decision checkpoint (`laya-typed-decisions` checkpoint (PyTorch, CPU)) inside the container image and require no model download, GPU, or external model service at runtime.

#### Scenario: Cold start offline
- **WHEN** the container starts with no network access
- **THEN** it serves decisions from the baked-in checkpoint

### Requirement: Internal-only exposure
The decision endpoint SHALL be reachable on the container network and SHALL NOT require a published host port; a `/health` endpoint SHALL report liveness.

#### Scenario: Compose-internal reachability
- **WHEN** a sibling service on the same compose network requests `http://laya-serve:8090/health`
- **THEN** it receives a healthy response without any host port mapping
