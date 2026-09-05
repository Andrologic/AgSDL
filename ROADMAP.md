# Roadmap

Every phase follows the repository boundary established by
`docs/decisions/0003-repository-boundary.md` and maintained in `docs/scope.md`.

## Published: version 0.0.1 conceptual pre-draft

Version `0.0.1` was published under the tag `v0.0.1`. It packages reviewed
conceptual work without making it normative.

The tagged release contains:

- the corrected conceptual core;
- exactly two non-normative conceptual examples;
- the repository license and release documentation; and
- proposals 0001 through 0004 as proposed conceptual inputs.

Version `0.0.1` does not define syntax, compatibility, conformance, execution,
or interoperability. Its four proposals remain proposed inputs to later work.
This list describes the tagged release, not the current `develop` branch.

## Published: version 0.0.2 conceptual pre-draft

Version `0.0.2` packages the cumulative conceptual work since `v0.0.1` under tag
`v0.0.2`. [Decision 0006](docs/decisions/0006-publish-version-0.0.2.md) authorizes
publication of the [prepared scope](docs/decisions/0005-version-0.0.2.md).
The [release notes](docs/releases/0.0.2.md) describe its contents and limits.

The release contains eleven proposed documents. It keeps proposals 0001 through
0004 non-normative, adds six proposed external bindings, and includes proposal
0011 as a first exchange-contract candidate for maintainer review. It also
records the accepted directions from Decision 0004, their reconciliation across
proposed material and examples, the repository boundary, research, and local
verification tools.

Publication does not claim software support for any binding. It does not adopt
proposal 0011, define syntax or compatibility, or establish conformance,
execution, or interoperability.

The next intended milestone is `0.1.0`, an implementable draft for software
including Macro and Agent Graph Studio. Its exact contract, graph behavior,
serialization, implementation scope, and acceptance criteria remain to be
agreed. The `0.0.2` publication does not resolve those choices.

## Conceptual work included in 0.0.2

Proposals 0005 through 0010 investigate versioned bindings to MCP, A2A, AG-UI,
A2UI, AP2, and Open Agent Specification. They remain non-normative and do not
establish implementation support or interoperability.

[Decision 0004](docs/decisions/0004-approved-design-directions.md) records five
accepted design directions:

- allow a complete System to use exclusively imported Agent definitions while
  preserving their lifecycle ownership;
- associate one Action occurrence directly with several Authorization decisions,
  each tied to its evaluated requirement and Policy application point;
- use implementation features and conformance profiles for claims, amending
  Decision 0001's reference to general conformance levels;
- permit validation by phase, with explicit declarations and applicable rules
  for each permitted deferral in an incomplete Fragment;
- prepare a bounded contract for reading, inspection, structural validation,
  and exchange, including missing information, preservation, and loss reporting.

The [reconciliation work plan](docs/plans/2026-09-05-conceptual-reconciliation.md)
records the reviewed proposal changes and preparation of the
[first contract candidate](proposals/0011-first-exchange-contract.md).
The exact first contract, including its normative subset, permitted deferral
inventory, identity-relation interpretation, and input and result rules, still
requires maintainer review. Neither the directions nor the reconciled proposals
adopt a language, stable feature identities, syntax, or implementation support.

## Phase 0: foundation

Status: the repository boundary and initial research are established;
requirements, terminology, and versioning semantics remain proposed.

- Fix the project scope and non-goals.
- Establish terminology and a requirements inventory.
- Inventory existing standards and agent frameworks.
- Establish governance and versioning rules.

## Phase 1: conceptual model

Status: proposals and conceptual examples exist, but no conceptual proposal is
normative.

- Define the system, agent, resource, protocol, policy, and runtime entities.
- Define identity, references, composition, inheritance, and extension rules.
- Define security, observability, evaluation, and human-control concepts.
- Publish representative system examples without committing to syntax.

## Phase 2: language draft

Status: future work, pending accepted conceptual semantics.

- Choose canonical and authoring serializations.
- Publish schemas and validation rules.
- Define precise feature and conformance-profile contracts, validation-phase
  rules, and compatibility rules within the accepted design directions.
- Build non-normative reference tooling after the relevant behavior is accepted.
- Candidate operations include parsing, validation, normalization, reference
  resolution, and static inspection.

## Phase 3: interoperability

Status: research and binding proposals exist; accepted mappings, executable
evidence, and interoperability claims remain future work.

- Map AgSDL concepts to selected frameworks and protocols.
- Add round-trip and portability tests.
- Publish a conformance test suite.
- Publish versioned binding fixtures and evidence requirements.
- Produce the first public draft.
