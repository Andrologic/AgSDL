# Roadmap

Every phase follows the repository boundary established by
[Decision 0003](docs/decisions/0003-repository-boundary.md) and maintained in
[the project scope](docs/scope.md).

## Published history: 0.0.1 and 0.0.2

Version `0.0.1` was published under `v0.0.1` as reviewed conceptual work. It did
not define syntax, compatibility, conformance, execution or interoperability.
Its four proposals remained proposed inputs.

Version `0.0.2` was published under `v0.0.2` with eleven proposed documents,
external-binding research and the first exchange-contract candidate. Decision
0006 authorized that publication without adopting a syntax or claiming software
support. See the [0.0.2 notes](docs/releases/0.0.2.md).

Those tags are historical snapshots. Their status is not changed by the
0.1.0 adoption.

## Published: bounded 0.1.0 first draft

[Decision 0007](docs/decisions/0007-adopt-0.1.0-contract.md) adopts the selected
0013 contract and unreplaced 0012 rules as a bounded normative first draft. The
text now lives in `spec/`, its derived shapes live in `schemas/`, and independent
Python and JavaScript readers are integrated under `tooling/readers/`.

This first-draft MVP is published under `v0.1.0`. It does not make AgSDL stable,
universal or executable. Both readers agree on the pinned 137-case official
corpus with no blocked case or failure, and the delivery review records the
limits of that evidence. The maintainer authorized publication on 2026-09-07.

## Published maintenance: 0.1.1

Version 0.1.1 is published under `v0.1.1` with documentation, examples, corpus
provenance and reader diagnostic maintenance. The `agsdl-0.1.0` contract marker
is unchanged. The
[diagnostic dossier](docs/reviews/0009-0.1.1-diagnostic-expectations.md) distinguishes
determined corrections from unresolved diagnostic and Unicode-order questions.
This work does not establish universal reader agreement or runtime support.
See [release status](README.md#release-status-and-history) for publication status.

See the [0.1.1 release notes](docs/releases/0.1.1.md) for the bounded
verification scope, retained evidence and publication record.

## Proposed preparation: 0.2

The [preparation guide, in French](docs/0.2-preparation.md) brings together the
concepts, reading path, evidence and scope decisions for the next version.

[Proposal 0014](proposals/0014-minimal-core-0.2.md) explores a smaller composable
core through [candidate examples](docs/research/0.2-design-examples.md).
[Proposal 0015](proposals/0015-validation-reports-0.2.md) explores lightweight
validation reports and diagnostic agreement. Both are proposed, not adopted or
implemented.
[Proposal 0016](proposals/0016-kiss-experiment-0.2.md) and its
[experimental examples](experimental/kiss-0.2/README.md) make the authorized
prototype directions precise. Two independent static readers now agree on the
[38-case c2 corpus](experimental/kiss-0.2/ASSESSMENT.md); this experimental
evidence does not establish normative adoption or execution support.

| Work | Status and completion condition |
| --- | --- |
| Test the bounded KISS candidate | Complete for c2: two readers, 38-case comparison and assessment. Evidence remains experimental. |
| Make the direction reviewable | Preparation guide and progressive examples available. |
| Decide the first 0.2 scope | Pending maintainer decision, including differences from 0.1 and deferred capabilities. |
| Adopt and document the chosen contract | After the scope decision: record adoption and apply the agreed rules in spec, with derived schemas and a migration guide. Preserve frozen candidate evidence. |
| Align readers and conformance evidence | After adoption: target the agreed edition, cover adopted behavior and obtain independent review. Experimental reports cannot be relabelled as official results. |
| Prepare publication | After integrated checks and review: release notes, exact source revision and explicit publication authorization. No 0.2 release is ready or published. |

## Completed 0.1.0 delivery sequence

| Work | Status |
| --- | --- |
| Adopt and apply the bounded D/G/R contract | Done. |
| Derive official schemas and reader/report identities | Done. |
| Integrate an official JavaScript reader | Done. |
| Integrate the independent Python reader | Done. |
| Integrate the official corpus and comparison tooling | Done. |
| Prepare public documentation and one official example | Done. |
| Run and retain the official cross-reader comparison | Done: 137 cases, no blocked case or failure. |
| Complete independent whole-delivery review | Done for the bounded 0.1.0 delivery. |
| Authorize and publish 0.1.0 | Published as the `v0.1.0` MVP pre-release. |

## Phase 0: foundation

Status: the repository boundary, initial research and versioned decision process
are established. Broader governance and terminology beyond the bounded 0.1.0
contract remain future work.

- Maintain the scope and non-goals.
- Extend terminology through reviewed proposals when needed.
- Keep research about external systems separate from implementation claims.
- Define broader governance before a stable release.

## Phase 1: conceptual model

Status: a bounded subset is normative for 0.1.0. Broader conceptual proposals,
external bindings and examples remain non-normative unless a later decision
adopts them.

- Preserve Definition, Configuration and Execution as distinct concepts.
- Propose material semantic additions before changing the specification.
- Keep historical conceptual examples and proposals labelled by their status.

## Phase 2: bounded language draft

Status: the 0.1.0 D/G/R contract, schemas, two readers, official corpus and
bounded delivery evidence are complete. The bounded MVP is published under `v0.1.0`.

- Maintain both readers against the same pinned official inputs and assertions.
- Preserve nonzero comparison results and resolve founded defects before release.
- Keep the evidence limits visible in every implementation claim.

## Phase 3: later interoperability work

Status: research and binding proposals exist; adopted mappings, execution
evidence and interoperability claims remain future work.

- Map AgSDL concepts to selected frameworks and protocols through proposals.
- Define any future execution or conformance contract separately.
- Add round-trip and portability evidence appropriate to an adopted contract.
- Publish versioned binding fixtures only with explicit scope and evidence.
