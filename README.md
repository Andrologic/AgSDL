# AgSDL

AgSDL is the Agentic Systems Definition Language, an open,
implementation-independent specification for describing agentic systems in a
form that people and software can read, validate, exchange and version.

AgSDL 0.1.0 is published as a bounded first-draft MVP under `v0.1.0`. It is
not a stable or universal language release.
It defines a deterministic Document/Graph/Runtime declaration model and seven
static reader operations. It does not define Agent execution, engine launch,
hot reload, deployment or runtime interoperability.

Start with the [0.1.0 specification](spec/README.md), then read the
[progressive examples](examples/0.1.0/README.md),
[implementation walkthrough](docs/implementation-guide.md) and the
[reader guide](tooling/README.md). The Python and JavaScript readers can inspect
the full example and validate its D, G and R units without installation. Their
0.1.0 delivery comparison covered 137 cases without blocked cases, failures or
mismatches. The [0.1.1 diagnostic dossier](docs/reviews/0009-0.1.1-diagnostic-expectations.md)
records additional limits; this evidence does not establish universal agreement.

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

## Reader operations

The adopted contract names seven independent operation contracts:

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

- `spec/` contains the adopted normative 0.1.0 text.
- `schemas/` contains derived JSON Schema shapes; the specification controls.
- `examples/0.1.0/` contains official but non-normative examples of that text.
- `tooling/readers/` contains non-normative official-edition readers.
- `experimental/` preserves candidate editions and their bounded evidence.
- `proposals/` records proposed material changes and the adoption history.
- `docs/` contains scope, decisions, plans, reviews, research and release notes.
- `scripts/` contains repository and source-verification checks.

## Release status and history

This section is the current publication-status reference. Version 0.1.0 is
published as `v0.1.0`; 0.1.1 is prepared locally for documentation, corpus
and reader maintenance, as described in the [local release notes](docs/releases/0.1.1.md). The contract marker remains `agsdl-0.1.0`. No new
language syntax or execution feature is introduced by that maintenance scope.
Historical decisions and reviews retain their status at the time of writing.

The published `v0.0.1` and `v0.0.2` tags remain conceptual pre-drafts. Their
proposals and examples keep the status recorded at those releases. The current
normative 0.1.0 subset was adopted separately by
[Decision 0007](docs/decisions/0007-adopt-0.1.0-contract.md); material not adopted
by that decision remains proposed or experimental.

- [0.1.1 local maintenance notes](docs/releases/0.1.1.md)
- [0.1.0 release notes](docs/releases/0.1.0.md)
- [Delivery-readiness review](docs/reviews/0008-0.1.0-release-readiness.md)
- [Roadmap](ROADMAP.md)
- [0.0.2 release](https://github.com/Andrologic/AgSDL/releases/tag/v0.0.2)
- [0.0.2 release notes](docs/releases/0.0.2.md)
- [0.0.1 decision](docs/decisions/0002-version-0.0.1.md)

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md) before changing normative behavior or
terminology. Run `./scripts/check.sh` before committing.

## License

The entire repository is licensed under the [Apache License 2.0](LICENSE).
