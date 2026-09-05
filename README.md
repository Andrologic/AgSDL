# AgSDL

AgSDL is the working identifier for the Agentic Systems Definition Language.
It is an open, implementation-independent specification for describing complete
agentic systems in a form that people and software can read, validate, exchange,
and version.

The project is at the pre-draft stage. Version `0.0.2` is a non-normative
conceptual release under the tag `v0.0.2`. It makes no promise of syntax,
compatibility, conformance, execution, or interoperability. All eleven proposals
remain non-normative, including the first exchange-contract candidate.

See the [0.0.2 release](https://github.com/Andrologic/AgSDL/releases/tag/v0.0.2),
[release notes](docs/releases/0.0.2.md), and
[publication decision](docs/decisions/0006-publish-version-0.0.2.md).
The earlier `v0.0.1` release retains the status recorded in
[Decision 0002](docs/decisions/0002-version-0.0.1.md).

## Intended scope

An AgSDL document should eventually be able to describe:

- the system boundary, purpose, inputs, outputs, and ownership;
- agents, roles, models, instructions, tools, skills, memory, and knowledge;
- topology, delegation, handoffs, messages, and interaction protocols;
- permissions, secrets, trust boundaries, human approvals, and failure policies;
- runtime requirements, deployment targets, lifecycle, and portability;
- traces, metrics, evaluations, conformance claims, and extension points.

AgSDL will define a portable system model. It will not require a particular
agent framework, model provider, transport, or execution engine.

## Repository boundary

This repository maintains the specification, its supporting artifacts, and the
material needed to govern, publish, and verify them. It may also publish
non-normative reference tooling for reading, transforming, and analyzing AgSDL
documents. Planned operations include parsing, validation, normalization,
reference resolution, and static inspection.

Reference tooling may produce transformed artifacts, diagnostics, and reports.
It does not execute the systems described by AgSDL documents. See the
[`project scope`](docs/scope.md) and
[`Decision 0003`](docs/decisions/0003-repository-boundary.md) for the complete
boundary.

## Repository structure

- `spec/` will contain normative specification text.
- `schemas/` will contain machine-readable validation artifacts.
- `examples/` contains non-normative conceptual examples during the pre-draft
  stage.
- `scripts/` contains repository and source-verification checks.
- `proposals/` records proposed normative changes before they enter the spec.
- `docs/` contains scope, rationale, and architecture decisions.

## Current work

The repository now contains eleven non-normative proposals. Proposals 0001 through
0004 were the conceptual inputs included in `v0.0.1`; proposals 0005 through
0010 were added later to investigate external bindings. Proposal 0011 prepares
a bounded reading, inspection, structural-validation, and exchange contract
for maintainer review. None has been accepted into the normative specification.
Syntax comes only after the system model and conformance boundaries are clear.

- [`Roadmap`](ROADMAP.md)
- [`Conceptual reconciliation and first-contract preparation`](docs/plans/2026-09-05-conceptual-reconciliation.md)
- [`Approved design directions`](docs/decisions/0004-approved-design-directions.md)
- [`First exchange contract candidate`](proposals/0011-first-exchange-contract.md)
- [`Version 0.0.2 preparation decision`](docs/decisions/0005-version-0.0.2.md)
- [`Version 0.0.2 release notes`](docs/releases/0.0.2.md)
- [`Local implementation-preparation work plan`](docs/plans/2026-09-04-local-work.md)
- [`Project scope`](docs/scope.md)
- [`Prior-art research`](docs/research/prior-art.md)
- [`MCP 2026-07-28 binding research`](docs/research/mcp-2026-07-28.md)
- [`A2A 1.0.1 binding research`](docs/research/a2a-1.0.1.md)
- [`AG-UI research`](docs/research/agent-user-interaction-protocol.md)
- [`A2UI research`](docs/research/a2ui.md)
- [`AP2 v0.2.0 binding research`](docs/research/ap2-v0.2.0.md)
- [`Open Agent Specification research`](docs/research/open-agent-specification.md)
- [`Cross-proposal review`](docs/reviews/0001-cross-proposal-review.md)
- [`Post-correction review`](docs/reviews/0002-post-correction-review.md)
- [`Proposals`](proposals/README.md)
- [`Version 0.0.1 decision`](docs/decisions/0002-version-0.0.1.md)
- [`Repository boundary decision`](docs/decisions/0003-repository-boundary.md)

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before proposing normative changes.
Run `./scripts/check.sh` before committing.

## License

The entire repository is licensed under the
[Apache License 2.0](LICENSE).
