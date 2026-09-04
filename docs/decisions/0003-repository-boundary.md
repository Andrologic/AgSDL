# Decision 0003: define the repository boundary

- Status: accepted
- Date: 2026-09-04

## Context

AgSDL needs a clear boundary for the language artifacts and supporting material
maintained here. That boundary preserves the recorded status of proposals,
decisions, and normative text while keeping the specification independent of
any implementation.

## Decision

This repository maintains AgSDL research, decisions, proposals, specification
text, schemas, examples, fixtures, conformance material, protocol mappings, and
reference tooling. It also maintains the governance, contribution, licensing,
publication, automation, and verification material needed for the repository.

**Reference tooling** is non-normative software published with AgSDL to read,
transform, or analyze AgSDL artifacts. It may produce transformed artifacts,
diagnostics, and reports. It does not execute the systems those artifacts
describe. Its specific operations and behavior remain subject to accepted
decisions and the normative specification.

Conformance material may include tests and harnesses that exercise an
implementation against adopted requirements. It assesses observable behavior
without defining the implementation's internal design.

External systems are described through the interfaces and documented behavior
relevant to AgSDL mappings and conformance.

This decision fixes the repository boundary only. It does not accept the
semantics proposed in proposals 0001 through 0010.

## Consequences

`docs/scope.md` is the source of truth for work that belongs in this repository.
The README and contributor instructions summarize that boundary and link to the
scope instead of redefining it.

Schemas and reference tooling follow the specification. They do not create
normative meaning when the specification is silent.
