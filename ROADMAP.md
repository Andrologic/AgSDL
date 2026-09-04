# Roadmap

Every phase follows the repository boundary established by
`docs/decisions/0003-repository-boundary.md` and maintained in `docs/scope.md`.

## Version 0.0.1: conceptual pre-draft

Version `0.0.1` packages the reviewed conceptual work without making it
normative. Its release tag will be `v0.0.1`.

The version is ready only when:

- the corrected conceptual core is present;
- the repository contains exactly two non-normative conceptual examples;
- the repository license and release documentation are present; and
- `./scripts/check.sh` succeeds.

Version `0.0.1` does not define syntax, compatibility, conformance, execution,
or interoperability. The four proposals remain proposed inputs to later work.

## Phase 0: foundation

- Fix the project scope and non-goals.
- Establish terminology and a requirements inventory.
- Inventory existing standards and agent frameworks.
- Establish governance and versioning rules.

## Phase 1: conceptual model

- Define the system, agent, resource, protocol, policy, and runtime entities.
- Define identity, references, composition, inheritance, and extension rules.
- Define security, observability, evaluation, and human-control concepts.
- Publish representative system examples without committing to syntax.

## Phase 2: language draft

- Choose canonical and authoring serializations.
- Publish schemas and validation rules.
- Define conformance levels and compatibility rules.
- Build non-normative reference tooling after the relevant behavior is accepted.
- Candidate operations include parsing, validation, normalization, reference
  resolution, and static inspection.

## Phase 3: interoperability

- Map AgSDL concepts to selected frameworks and protocols.
- Add round-trip and portability tests.
- Publish a conformance test suite.
- Publish versioned binding fixtures and evidence requirements.
- Produce the first public draft.
