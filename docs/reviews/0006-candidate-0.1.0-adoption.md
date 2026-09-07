# Candidate 0.1.0 adoption review dossier

- Date: 2026-09-06.
- Status: adoption recorded by Decision 0007; normative application prepared,
  official-edition evidence and final delivery review pending.
- Preparation base: `b5c97f692d3f9446988f0a79c07412c0b558e585`.
- Integrated evidence base: `90997464428ce7c3072179e1053cf2934fb80fef`.
- Current experimental edition: `proposal-0013-candidate-1`.

## Current disposition, 2026-09-07

[Decision 0007](../decisions/0007-adopt-0.1.0-contract.md) records the maintainer's
readiness delegation following the explicit adoption/unchanged-actor question.
It adopts the selected 0013 contract and unreplaced 0012 inheritance, retaining
Agent Key, unique actsAs and invoke.principal equality. The
[specification](../../spec/README.md) now applies that contract independently of
historical proposals. [Traceability and reader adaptations](0007-0.1.0-contract-traceability.md)
record its official identity and mechanical consequences.

The final experimental integration is `0aa44c14825b03e52cbd5d588921929995ebc6fc`.
The local closure record at
`~/.codex/chantier-archives/agsdl-010-mvp-2026-09-07/cloture.md`
records 190 passing reader tests and comparisons of 121 historical and 26 modular
cases without difference or blockage. Retained reports are in its `preuves/`
directory. These are experimental results, not official-edition conformance.
This application does not rerun or relabel them.

Reader/corpus adaptation and new official-edition evidence remain pending, as
do final delivery review and publication authorization. Root README and release
notes belong to the final integration lot. This dossier records no publication.

## Historical dossier, 2026-09-06

The remainder preserves the facts, recommendations and pending choices at that
date. Its pending-adoption and Principal-choice language is historical; the
current disposition above supersedes it for the adopted bounded scope.

This dossier separates recorded facts, deductions, recommendations and pending
choices. [Decision 0001](../decisions/0001-specification-before-syntax.md),
[Decision 0004](../decisions/0004-approved-design-directions.md),
[CONTRIBUTING](../../CONTRIBUTING.md) and the [repository boundary](../scope.md)
govern any later adoption. Proposal 0013 remains experimental. Preparing this
dossier does not change normative text or authorize publication.

## Current facts and evidence, 2026-09-06

The maintainer's directions recorded in [proposal 0013](../../proposals/0013-modular-mvp-contract.md)
establish reusable Agent and graph definitions, several configurations for one
graph, per-Agent engine choices, explicit Tool implementations and reusable
Instructions/Skills where compatible. Multiple addressable Interface operations
and sequential approvals for one call are required for the modular MVP.
These needs are settled for this work. Their exact record shapes and rules
still require adoption.

A configuration stays fixed for an execution. Changes require stopping, editing
and starting a new execution. Required capabilities cannot be silently removed
or replaced; unknown support is not readiness. No required product integration,
hot reload, state migration or real-engine demonstration is a delivery gate.

### Historical pre-comparison handoff

The following table preserves the handoff before the JavaScript reader and
cross-reader run completed. It is historical evidence, not the current status.

| Evidence at the preparation snapshot | Status and limit |
| --- | --- |
| Lot A, `280347eec4e2e051d296f9271bfccc86c98d4d40` | Modular proposal and derived experimental schemas integrated; proposed semantics only. |
| Lot B corpus and comparator, including `1c796de9c457a4166064c7f5555a052b09f893ff` | Integrated at the preparation base. The manifest has 26 cases, including four direct-annex resolveG cases. |
| Python, `512056a8e5e324651ab40d5f4e29541098ea5129` | Integrated and independently audited. The orchestration handoff reports that the original 22 observations and four added resolveG cases pass with Python. This dossier does not rerun or extend that reader audit. |
| Modular JavaScript | Still active at this dated handoff; no completion claimed here. |
| Modular cross-reader comparison | Not yet performed at this snapshot. No agreement, zero-mismatch result or completed evidence gate is claimed. |

The [modular corpus and comparison contract](../../experimental/modular-candidate-1/README.md)
and [manifest](../../experimental/modular-candidate-1/fixtures/manifest.json)
identify the current inputs, oracles and pinned source bytes. A later evidence
lot will record both reader SHAs, the exact corpus revision, commands, retained
raw reports, failures and exclusions after comparison. It must update this dated
status rather than anticipate success. Repository checks verify documentation
and corpus bookkeeping; they do not replace that comparison.

### Current integrated modular evidence from B46/B48

The later evidence lot completed both independent reader paths and ran them on
the same 26-case corpus. The pinned inputs are:

| Source | Revision or SHA-256 |
| --- | --- |
| Integrated checkout and comparison base | `90997464428ce7c3072179e1053cf2934fb80fef` |
| Python modular reader | `512056a8e5e324651ab40d5f4e29541098ea5129` |
| JavaScript modular reader | `ef4ac52ef6efcf9af50f49e488fa008dc0932d80` |
| Corpus with 26 cases, including direct annexes | `1c796de9c457a4166064c7f5555a052b09f893ff` |
| Proposal 0013 source revision | `280347eec4e2e051d296f9271bfccc86c98d4d40` |
| Proposal 0013 file SHA-256 | `7c9e2aa8e5c6d7c8c0b419aaf3afb666f9ad3510057c98dc7f0f3ac3e904773b` |

The retained integrated summary at
`/private/tmp/agsdl-010-mvp-orchestration/comparison-root-integrated-9099746/summary.json`
records 26 cases, no blocked case and no failure. The independent audit at
`/private/tmp/agsdl-010-mvp-orchestration/audit-D-comparison-corrected.md`
records the same modular result, a successful 121-case candidate-2 comparison
and 96 passing JavaScript tests across both editions.

The initial modular comparison remains at
`/private/tmp/agsdl-010-mvp-orchestration/comparison-1/`. It failed with 21
component differences across 14 cases: 14 opaque Slice sets, three State sets,
two Check sets and two Finding sets. `comparison-2/` is a separate retained
result. Neither directory was replaced by the integrated evidence. This history
matters because the final zero-difference summary followed reader corrections;
it was not the first observed result.

The comparison checks the report contract, corpus assertions, exact Slice
boundaries and exchange bytes. It does not supply a second semantic oracle.
Shared mistakes and untested combinations remain possible. No reader executed
an Agent, engine, Tool, content adapter or approval service.

## What supersedes candidate-2

The 121-case comparison retained below remains evidence for its own edition.
The following limits no longer describe the requested MVP scope.

| Historical candidate-2 limit | Established need and proposed 0013 response |
| --- | --- |
| One action and port pair per selected Interface | One messaging Interface can expose `draft` and `send`. Invoke explicitly selects an operation id within that Interface; Action and Ports follow that operation. Splitting the Interface is no longer the recommended workaround. |
| At most one immediate approval gate | Legal then financial approval can protect the same send call. Each gate names that call; refusal cannot reach it or a later gate. Batch approval, reuse, parallel approval and quorum remain outside this candidate. |
| One subjectless Selection | One configuration can bind writer to engine A and researcher to engine B. Another configuration can change those assignments while retaining Agent and graph definitions. Repeated calls of one Agent share one binding within a configuration. |

These examples explain the delta; they are not new normative rules. A G pass
checks declared paths and data availability, not human authentication or timely
approval. An R assessment records declarations, including unknown and
not-provided states. Even declared-supported proves no actual compatibility,
evidence authenticity or permission to launch.

## Remaining Principal decision

Facts: [proposal 0002](../../proposals/0002-core-conceptual-model.md), open
question 15, and Decision 0004 reserve the precise Agent-to-Identity meaning.
Proposal 0013 retains the candidate-2 constraint: an Agent has exactly one
`actsAs` Principal reference, and `invoke.principal` equals that target.
An Agent Key identifies a definition. The Principal definition declares an
accountable actor or actor class. Configuration selects an engine, tools and
content; it has no Principal selection field. Authenticated occurrence identity
remains external evidence.

For example, Agent `reviewer` actsAs Principal `review-service`. Configuration
`local` chooses engine A and configuration `remote` chooses engine B. Both
invocations still name `review-service`. Neither engine choice authenticates a
person or grants authority. Two different Agent definitions may also share that
Principal without becoming the same Agent definition.

Deduction: configuration `customer-a` cannot change this same Agent's Principal
to `customer-a-actor`, nor can `customer-b` change it to `customer-b-actor`.
Changing only invoke.principal breaks the retained agreement. Separate Agent
definitions with their own actsAs relations can describe separate roles, but
that changes the described Agent identities; it is not configuration-only
rebinding or an established lossless conversion.

| Actual pending choice | Consequence |
| --- | --- |
| Retain the proposed Principal constraint for adoption | Record the definition-key meaning and reconcile 0002. Engine portability leaves the declared Principal unchanged. Runtime authentication remains external. |
| Amend the candidate to permit configuration-level Principal rebinding | First specify the actor relation, cardinality, invoke agreement and approval scope, then update contract and evidence. No binding field or runtime identity model is assumed by this dossier. |
| Defer this adoption choice | Preserve experimental status for the affected scope and record its consequence for the release decision. |

Recommendation: retain the current constraint unless the maintainer requires
configuration-only actor changes. It is implementable and keeps engine selection
separate from actor declaration. This recommendation neither decides the open
choice nor requires a redesign. It does not reopen per-Agent engine selection.

## Adoption record and application sequence

The remaining decision is whether to accept, amend or defer the precise modular
contract and release units, with their prerequisites and limits. A reduced
release scope would need an explicit disposition of the established MVP needs;
the historical single-operation, single-gate and subjectless-selection options
are not equivalent ways to meet them. Implementation agreement alone adopts
neither C1-C10 nor official feature identities.

Recommendation: use the attached modular comparison when preparing the decision
text, then record the Principal choice, selected units, exact proposal edition
and any amendments. Reconcile proposals
0002, 0003 and 0011 with the inherited 0012 rules and 0013 replacements.
Direct supplied dependency resolution and unsupported transitive resolution,
required extension interpretation and unknown classification retain their
explicit limits. Approval expiry declarations do not establish timing feasibility.

The [delivery plan](../plans/2026-09-05-0.1.0-delivery.md) defines completion gates
for application and release review. After an adoption decision, place only the
adopted semantics in spec, derive schemas and official report/feature identities,
then update fixtures and both readers for that exact edition. Replay both
implementations and retain new evidence. Experimental reports cannot be relabelled
as normative results. Close independent delivery review against the adopted scope
before seeking separate publication authorization.

## Historical candidate-2 evidence

This section preserves the completed experiment at
`4a43c5ee645b271b5640bd780b109c16ea380b08`, edition
`proposal-0012-candidate-2`. Its results and reproduction commands apply to that
checkout only. They do not close the modular comparison or adoption gates.

The source revision integrates the candidate contract, three experimental
schemas, a 121-case corpus and separately implemented Python and JavaScript
readers. Their READMEs record independent implementation provenance; this
documentary review does not independently audit that development history.

The evidence is pinned to these sources:

| Source | Revision or SHA-256 |
| --- | --- |
| Complete checkout, including both readers and comparator | `4a43c5ee645b271b5640bd780b109c16ea380b08` |
| Proposal 0012 file SHA-256 | `9f0ead2cbe9a5e158e3017f1ba692cbd3cba69e9240048130dc49c19c1222e07` |
| Corpus manifest file SHA-256 | `be9af6c2bd6c90ec6e3693eb7e203f2470ffd2eb4aca201a5a4c472d6f037946` |
| Report-boundary clarification and assertions | `62b6b2a0f1cd8667f6ec36b0ff83194078b77c01` |
| Final Python correction | `5c1ee146347a0ab97028930688459230d386a8ff` |
| Final JavaScript correction | `4cdca6db9ee371291029386d74858cee6d3719bb` |

The [manifest](../../experimental/candidate-2/fixtures/manifest.json) also pins
each input's exact bytes and the proposal digest. Its `contractBase` records
the clarification's integration base, `dbec97e64f37b6161eb69c6475e19ee7190e3618`;
the complete checkout above identifies the implementations used in this run.

### Final experimental comparison

Comparison-3 records 121 cases, `blocked:[]` and `failures:[]`. A fresh local
run on the clean source revision independently reproduced that result on
2026-09-06, with exit status 0, using Python 3.14.7 and Node.js 26.8.1. The 242 reader responses satisfy the report
contract and targeted corpus assertions, and their complete normalized
comparison has no mismatch. Repository checks and the separate reader tests
also pass: 54 Python tests and 37 JavaScript tests at this revision.

The local evidence is retained outside the repository at
`/private/tmp/agsdl-010-orchestration/comparison-3/` and the fresh run at
`/private/tmp/agsdl-010-orchestration/comparison-final-evidence/`. Each directory
contains `summary.json` and the raw stdout/stderr for each case and reader.
The reader-test log is
`/private/tmp/agsdl-010-orchestration/final-evidence-reader-tests.log`.
These are local evidence locations, not distributed fixtures or stable URLs.

The comparison checks separate unit/phase verdicts, rule/location/outcome
findings, Check sets, deferrals and inventory State sets. It checks opaque
Slice boundaries against original bytes and compares those bytes. Exchange
cases require exact supplied-input boundaries, byte-identical output artifacts
and matching hashes; lossy exchange remains refused. The
[comparison contract](../../experimental/candidate-2/README.md) defines the
assertions and normalization. Diagnostic prose is not compared, except for
specified Requirement identity in missing-claim details.

This is agreement on the experimental corpus and reports. It does not prove
exhaustive semantic correctness, official conformance, runtime equivalence,
engine support, evidence authenticity or interoperability. Shared mistakes and
uncovered combinations remain possible. No described system was executed.

To reproduce, use a checkout of the complete source revision above and run
from its root with Python 3.9 or newer and Node.js. Create a fresh output
directory to preserve the raw evidence:

```sh
git rev-parse HEAD
git status --short
python3 - <<'PYHASH'
import hashlib
from pathlib import Path
for name in ('proposals/0012-minimal-0.1.0-contract.md',
             'experimental/candidate-2/fixtures/manifest.json'):
    print(name, hashlib.sha256(Path(name).read_bytes()).hexdigest())
PYHASH
agsdl_evidence_dir=$(mktemp -d)
python3 experimental/candidate-2/compare-readers.py \
  --reader '["python","python3","experimental/readers/python/cli.py"]' \
  --reader '["javascript","node","experimental/readers/javascript/cli.mjs"]' \
  --reports "$agsdl_evidence_dir"
./scripts/check.sh
./scripts/check-readers.sh
```

`./scripts/check-readers.sh --compare` also runs the full comparison, but removes
its temporary reports after printing the result. Use the command above when
retaining evidence. Reader tests and repository checks are separate from the
full comparison.

### Historical comparison-2

At `dbec97e64f37b6161eb69c6475e19ee7190e3618`, comparison-2 and its documentary
replay had 121 cases, no blocked fixture and three mismatches: Check/State sets
for `external-transitive-selected`, and Check sets for `selected-key-collision`.
Exit status was 1, while the then-current individual assertions passed. Its
proposal digest was
`c2247e8b821544a34eeb93c9c2d75f42777f5a5ac2c9cb62bd6eebcfd4748c9a`.
The original reports remain in
`/private/tmp/agsdl-010-orchestration/comparison-2/`. They describe that earlier
contract and implementations, not the final snapshot. The clarification and
reader corrections listed above supersede its unresolved report differences.
