# AgSDL

AgSDL is the Agentic Systems Definition Language, an open,
implementation-independent specification for describing agentic systems in a
form that people and software can read, validate, exchange and version.

AgSDL 0.2.0 is published as a bounded language draft under
[`v0.2.0`](https://github.com/Andrologic/AgSDL/releases/tag/v0.2.0). Start with the
[0.2.0 specification](spec/0.2/README.md), [tools and examples](tooling/0.2/README.md)
and [migration guide](docs/0.2/migration.md). It describes persistent Agents,
Messages, explicit configuration and optional flow under `agsdl-0.2.0`.
[Decision 0013](docs/decisions/0013-adopt-0.2.0-contract.md) records the bounded
adoption; [release notes](docs/releases/0.2.0.md) record its limits and verification.
Static readers do not execute Agents, Calls or graphs and do not prove runtime
interoperability.

AgSDL 0.1.1 remains available under `v0.1.1`, with unchanged
contract `agsdl-0.1.0`. Its [specification](spec/README.md),
[progressive examples](examples/0.1.0/README.md),
[implementation walkthrough](docs/implementation-guide.md) and
[reader guide](tooling/README.md) retain that edition. It is a bounded first draft,
not a stable or universal language release. The
[0.1.1 diagnostic dossier](docs/reviews/0009-0.1.1-diagnostic-expectations.md)
records its additional evidence limits.

## AgSDL 0.2.0

The [0.2 guide](docs/0.2/README.md) explains the model and source hierarchy.
The normative chapters define content and configuration, flow and lifecycle,
composition and protected admission, and scoped static and supplied-record
checks. Independent Python and JavaScript declaration readers use a 112-case
corpus. Agreement is bounded to those inputs; record consistency and schema
validation do not establish execution support.

The previous persistent-Agent candidate is preserved in Git at
`bc441c0a894d286c4585eee261b07f8f03f9d6a7` with marker
`agsdl-exp-flow-0.2-c1`. The [KISS experiment](experimental/kiss-0.2/README.md)
remains a separate frozen candidate under [0017](proposals/0017-agent-only-kiss-0.2.md).
Its [42-case assessment](experimental/kiss-0.2/ASSESSMENT.md) retains its own scope.
Neither candidate's retained reports are relabelled as 0.2.0 results.

## What 0.1.0 describes

The contract separates three declaration layers:

- **Document (D)** records the document boundary, definitions, typed
  relations, dependencies, deferrals and extensions.
- **Graph (G)** records a closed control flow of invocations, conditions,
  approval gates and terminal outcomes.
- **Runtime declaration (R)** records explicit configurations, per-Agent
  engines, Tool implementations and reusable content applications. It declares
  compatibility evidence; it does not verify readiness or execute anything.

Configurations never inherit defaults. A document may declare several
configurations for the same graph, and selection is explicit or absent. Engine
and adapter identities are open Edition values, so custom names receive no
special trust.

## 0.1.0 reader operations

The adopted 0.1.0 contract names seven independent operation contracts:

| Operation | Purpose |
| --- | --- |
| `inspect` | Inventory readable structure without semantic validation. |
| `validateD` | Validate the Document declarations. |
| `validateG` | Validate graph structure using local declarations. |
| `resolveG` | Validate graph structure with directly supplied dependency annexes. |
| `validateR` | Validate runtime declarations and declared compatibility. |
| `exchange` | Preserve supplied bytes exactly when lossless exchange is available. |
| `lossyExchange` | Refuse output unconditionally and inventory prospective declared losses. |

Each operation emits a scoped report. A successful process exit only means that
a response was produced. It is not a whole-document conformance, execution or
readiness claim.

## Repository boundary

This repository maintains the specification, its supporting artifacts and the
material needed to govern, publish and verify them. It may publish non-normative
reference tooling for reading, transforming and analyzing AgSDL documents.
Reference tooling does not execute the systems described by those documents.
See the [project scope](docs/scope.md) and
[Decision 0003](docs/decisions/0003-repository-boundary.md).

## Repository structure

- `spec/` contains the adopted normative 0.1.0 text; `spec/0.2/` contains the adopted 0.2.0 contract.
- `schemas/` contains derived JSON Schema shapes; the specification controls.
- `examples/0.1.0/` contains official but non-normative examples of that text.
- `tooling/readers/` contains non-normative 0.1.0 readers.
- `tooling/0.2/` contains the 0.2.0 derived schema, examples, declaration readers
  and supplied-record checks.
- `experimental/` preserves candidate editions and their bounded evidence.
- `proposals/` records proposed material changes and the adoption history.
- `docs/` contains scope, decisions, research, review evidence and release notes.
  The [0.2 index](docs/0.2/README.md) describes the current edition; dated records
  describe their historical revisions.
- `scripts/` contains repository and source-verification checks.

For background, the [proposal register](proposals/README.md) distinguishes
adopted, proposed and frozen material. [Prior-art research](docs/research/prior-art.md)
compares external concepts at the recorded source editions. The
[examples index](examples/README.md) separates published examples from earlier
conceptual illustrations. Neither research nor historical examples overrides
the specification or the accepted 0.2 directions.

## Release status and history

This section is the current publication-status reference. AgSDL 0.2.0 is the
latest published release, tagged
[`v0.2.0`](https://github.com/Andrologic/AgSDL/releases/tag/v0.2.0), with contract
marker `agsdl-0.2.0`. It is a regular GitHub release of a bounded language
draft. The contract remains under development, without a stable compatibility
guarantee. See its [release notes](docs/releases/0.2.0.md) for scope and evidence.

Version 0.1.1 was published as [`v0.1.1`](https://github.com/Andrologic/AgSDL/releases/tag/v0.1.1)
for documentation, corpus and reader maintenance, as described in the
[release notes](docs/releases/0.1.1.md). The contract marker remains `agsdl-0.1.0`. No new
language syntax or execution feature is introduced by that maintenance scope.
Historical decisions and reviews retain their status at the time of writing.

The published `v0.0.1` and `v0.0.2` tags remain conceptual pre-drafts. Their
proposals and examples keep the status recorded at those releases. The current
normative 0.1.0 subset was adopted separately by
[Decision 0007](docs/decisions/0007-adopt-0.1.0-contract.md); material outside its selection retains its recorded status unless adopted
separately. Decision 0013 records the later bounded 0.2.0 adoption.

- [0.2.0 release notes](docs/releases/0.2.0.md)
- [0.1.1 maintenance release notes](docs/releases/0.1.1.md)
- [0.1.0 release notes](docs/releases/0.1.0.md)
- [Delivery-readiness review](docs/reviews/0008-0.1.0-release-readiness.md)
- [Roadmap](ROADMAP.md)
- [0.0.2 release](https://github.com/Andrologic/AgSDL/releases/tag/v0.0.2)
- [0.0.2 release notes](docs/releases/0.0.2.md)
- [0.0.1 decision](docs/decisions/0002-version-0.0.1.md)

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing normative behavior or
terminology. [Governance](GOVERNANCE.md) defines proposal review and adoption. Run `./scripts/check.sh` before committing.

## License

The entire repository is licensed under the [Apache License 2.0](LICENSE).
