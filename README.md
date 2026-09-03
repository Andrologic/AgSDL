# AgSDL

AgSDL is the working identifier for the Agentic Systems Definition Language.
It is an open, implementation-independent specification for describing complete
agentic systems in a form that people and software can read, validate, exchange,
and version.

The project is at the pre-draft stage. The planned version `0.0.1` is a
non-normative conceptual release. It makes no promise of syntax, compatibility,
conformance, execution, or interoperability. See
[`Decision 0002`](docs/decisions/0002-version-0.0.1.md) for its exact status.

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

## Repository structure

- `spec/` will contain normative specification text.
- `schemas/` will contain machine-readable validation artifacts.
- `examples/` contains non-normative conceptual examples during the pre-draft
  stage.
- `proposals/` records proposed normative changes before they enter the spec.
- `docs/` contains scope, rationale, and architecture decisions.

## Current work

The first milestone is a terminology and requirements draft. Syntax comes only
after the system model and conformance boundaries are clear.

- [`Roadmap`](ROADMAP.md)
- [`Project scope`](docs/scope.md)
- [`Prior-art research`](docs/research/prior-art.md)
- [`MCP 2026-07-28 binding research`](docs/research/mcp-2026-07-28.md)
- [`AG-UI research`](docs/research/agent-user-interaction-protocol.md)
- [`AG-UI binding proposal`](proposals/0007-agent-user-interaction-protocol-binding.md)
- [`A2UI research`](docs/research/a2ui.md)
- [`Cross-proposal review`](docs/reviews/0001-cross-proposal-review.md)
- [`Post-correction review`](docs/reviews/0002-post-correction-review.md)
- [`Proposals`](proposals/README.md)
- [`Version 0.0.1 decision`](docs/decisions/0002-version-0.0.1.md)

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before proposing normative changes.
Run `./scripts/check.sh` before committing.

## License

The entire repository is licensed under the
[Apache License 2.0](LICENSE).
