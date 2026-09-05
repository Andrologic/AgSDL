# Decision 0001: define the system model before syntax

- Status: accepted
- Date: 2026-09-02

## Context

Choosing YAML, JSON, or another notation first would make field names look like
settled concepts. The project does not yet have a reviewed system model or
conformance boundary.

## Decision

AgSDL will define terminology, entities, relationships, requirements, and
conformance contracts before selecting a canonical serialization.

The original decision referred to conformance levels. [Decision
0004](0004-approved-design-directions.md) amends that direction to implementation
features and conformance profiles; it preserves the requirement to define the
model before syntax.

Examples created during this phase are exploratory. They do not establish
normative syntax.

## Consequences

The first project work is documentation and prior-art research. Schema and parser
work begins after the conceptual model has been reviewed.
