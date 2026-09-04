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

## Proposed work after 0.0.1

Proposals 0005 through 0010 investigate versioned bindings to MCP, A2A, AG-UI,
A2UI, AP2, and Open Agent Specification. They remain non-normative and do not
establish implementation support or interoperability.

The relation between the conformance levels named in Decision 0001 and the
implementation features and profiles proposed in proposal 0003 remains an open
design decision. The roadmap does not select one model.

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
- Resolve the conformance model and define compatibility rules.
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
