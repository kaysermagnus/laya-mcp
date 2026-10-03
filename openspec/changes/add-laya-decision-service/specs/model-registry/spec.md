# Spec Delta

## Purpose

Declarative registry of candidate models that `route_model` chooses among, with a defined default for low-confidence decisions.

## ADDED Requirements

### Requirement: YAML-defined entries
The registry SHALL be a YAML file (default `models.yaml`) listing candidate entries, each with a unique `label`, free-text `criteria` describing what it handles best, and at most one `default: true` entry.

#### Scenario: Registry loads at startup
- **WHEN** the MCP server starts with a valid `models.yaml`
- **THEN** `route_model` offers the listed labels as choice options

### Requirement: Minimum viable registry
The registry SHALL contain at least 2 entries for `route_model` to operate; a registry failing this SHALL cause `route_model` to return an actionable configuration error while other tools remain usable.

#### Scenario: Too few entries
- **WHEN** `models.yaml` has fewer than 2 entries
- **THEN** `route_model` responds with a configuration error naming the file and the missing requirement

### Requirement: Abstain to default
When the routing decision's confidence falls below the abstention threshold, the tool SHALL return the registry's default entry flagged `abstained: true`. If no entry is marked default, the first entry acts as default.

#### Scenario: Low confidence falls back
- **WHEN** the decision abstains
- **THEN** the tool returns the default label with `abstained: true`
