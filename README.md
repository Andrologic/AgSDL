# AgSDL

AgSDL is the working identifier for the Agentic Systems Definition Language.
It is an open, implementation-independent specification for describing complete
agentic systems in a form that people and software can read, validate, exchange,
and version.

The project is at the pre-draft stage. No syntax or compatibility promise exists
yet.

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
- `examples/` will contain conforming examples and counterexamples.
- `proposals/` records proposed normative changes before they enter the spec.
- `docs/` contains scope, rationale, and architecture decisions.

## Current work

The first milestone is a terminology and requirements draft. Syntax comes only
after the system model and conformance boundaries are clear. See
[`ROADMAP.md`](ROADMAP.md) and [`docs/scope.md`](docs/scope.md).

## Contributing

Read [`CONTRIBUTING.md`](CONTRIBUTING.md) before proposing normative changes.
Run `./scripts/check.sh` before committing.

## License

No license has been selected yet. Choosing licenses for the specification,
schemas, examples, and future reference implementations is an explicit project
decision before public release.
