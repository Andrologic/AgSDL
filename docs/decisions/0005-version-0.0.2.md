# Decision 0005: prepare version 0.0.2 as a conceptual candidate

- Status: accepted for local preparation; not published
- Date: 2026-09-05

## Context

Version `0.0.1` is the latest published AgSDL release. The local `develop`
history now contains reviewed conceptual work, external-binding research,
proposal reconciliation, a candidate first exchange contract, and repository
verification tools. None of that work has produced an accepted syntax or
normative specification.

The maintainer authorized preparation of a local `0.0.2` candidate so the
cumulative work can be reviewed as one conceptual pre-release. Publication,
tagging, pushing, and creating a remote release remain outside this decision.

## Decision

Prepare version `0.0.2` locally as a non-normative conceptual candidate. The
planned release tag is `v0.0.2`, but this preparation does not create it and
does not state that the version has been published.

The candidate describes the cumulative repository change since `v0.0.1`:

- all eleven proposals remain proposed and non-normative;
- proposals 0005 through 0010 document bindings to MCP, A2A, AG-UI, A2UI, AP2,
  and Open Agent Specification without claiming implemented support;
- Decision 0004 records five accepted design directions, and the proposed model
  and examples reconcile composition, authorization accounting, conformance
  claims, validation phases, and first-contract preparation with them;
- proposal 0011 is a bounded candidate for reading, inspection, structural
  validation, and exchange, pending maintainer review and possible adoption;
- repository-boundary documentation, research records, review evidence,
  Markdown-link checking, and pinned A2A source verification are included as
  maintenance and review support.

The accepted status of this decision applies only to candidate preparation and
the scope listed above. It does not accept any proposal, external binding,
serialization, schema, diagnostic contract, feature identity, or conformance
profile as normative AgSDL.

## Consequences

The README, roadmap, and candidate release notes distinguish published version
`0.0.1` from the locally prepared `0.0.2` candidate. A later publication action
may create `v0.0.2` only after the maintainer reviews the candidate and
authorizes publication.

No compatibility, software support, execution, interoperability, or adoption
claim follows from this preparation. In particular, proposal 0011 remains a
candidate. The preparation also fixes no content, date, or acceptance criterion
for version `0.1.0`.
