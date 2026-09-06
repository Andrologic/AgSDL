# Candidate 0.1.0 adoption review dossier

- Date: 2026-09-06.
- Status: preparation for maintainer review; no adoption decision.
- Evidence source revision: `4a43c5ee645b271b5640bd780b109c16ea380b08`.
- Experimental edition: `proposal-0012-candidate-2`.

This dossier separates observed facts, deductions, open recommendations and
pending decisions. It does not amend a proposal, establish a redesign, or make
product integration a prerequisite. [Decision 0001](../decisions/0001-specification-before-syntax.md),
[Decision 0004](../decisions/0004-approved-design-directions.md) and the
[repository boundary](../scope.md) remain in force. The maintainer can select D
alone or a scope including G and/or R, subject to their D prerequisites.

## Evidence and status

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

The experimental evidence step can now close for the pinned candidate. The
three conceptual choices below remain open. Agreement does not select release
scope or turn experimental identifiers into official feature identities.

## Choice 1: Agent definition identity and Principal identity

**Facts.** Decision 0004, “Consequences and limits”, reserves the exact meaning
of the Agent-to-Identity relation. [Proposal 0002](../../proposals/0002-core-conceptual-model.md),
open question 15, still leaves it open. Proposal 0012, “Concepts and invariants before
representation”, recommends that the Agent's key is its unique definition identity,
with exactly one `actsAs` reference to a Principal definition. It infers no
acting identity, authentication, authority or runtime instance.

**Example.** Distinct Agent definitions `writer` and `reviewer` can both act as
Principal `editorial-team`. That Principal can describe two scoped identities.
This does not create four Agent definitions, identify an authenticated account
for a call, or establish that either identity has permission. D leaves the
Principal payload opaque; it does not validate a general identity registry.

| Pending option | Effect for an integrator |
| --- | --- |
| Accept the proposed definition-key interpretation and reconcile 0002 | Deduplicate descriptions by Agent key; follow `actsAs` separately to the actor. Authentication and runtime instance identity need separate evidence. |
| Amend the interpretation/cardinality before adoption | Specify what the additional identity relation identifies and how it differs from Principal identity; revise text, fixtures and readers before claiming agreement on it. |
| Defer the identity choice | Keep the candidate experimental; do not present its interpretation as the adopted Agent identity model. |

**Open recommendation.** The definition-key interpretation is reasonable and
keeps distinct concepts separate. No supplied need establishes a separate
Identity registry as necessary. This is a recommendation, not an acceptance
of C1 or a closure of question 15.

## Choice 2: bounded G, Interface operations and approval

**Facts.** Proposal 0002, “Interface” and its relationship table, allows one
Interface to contain multiple Interface operations; each operation makes an
Action available. Proposal 0012, “G: closed simple-graph grammar”, gives a selected
Interface payload exactly one `action` and one pair of input/output maps.
An invocation must match that Action and those maps. G checks selected payloads,
not full Interface validity under 0002.

**Deduction and example.** A messaging Interface with `draft` and `send`
operations cannot retain both operations as a single selected G Interface.
The two operations have different Actions and inputs. Splitting it into two
Interface definitions changes the described boundary identities; it is not an
identity-preserving conversion already authorized by this candidate.

| Pending option | Effect for an integrator |
| --- | --- |
| Adopt G only for Interfaces with one operation, with an explicit conceptual correspondence | A selected Interface's action/maps describe its sole operation. Multioperation Interfaces remain outside G coverage; the correspondence itself must be adopted in reviewed text. |
| Require multioperation Interface coverage in 0.1.0 | Amend operation selection and identity/mapping rules before adoption, then update schemas, fixtures and both readers. |
| Defer G | Keep D inspection/exchange of opaque payloads without a claim of graph validation for those Interfaces. |

**Open recommendation.** A bounded G is viable if the single-operation
correspondence and exclusions are explicit. The evidence does not establish a
need to redesign the complete Interface model, nor does it establish that
multioperation coverage can be omitted from the maintainer's chosen scope.

**Facts about approval.** The same G section permits at most one approval gate
for an immediate invocation. Its approved edge is that invocation's only
incoming edge. A decision is by one declared human Principal; validation does
not authenticate that human. The interval starts on entering the gate and is
`min(timeoutMs, validForMs)`. There is no graph-level timeout, approval reuse,
or executable decision intake API. Cycles and parallelism are also outside G.
Decision 0004's general accounting for several Authorization decisions on one
Action occurrence does not automatically adopt this narrower gate contract.

**Example and pending decision.** Sequential legal and financial approvals for
one call, or one approval covering a batch of calls, are outside this G
contract. If G is retained, either accept that limit explicitly as simple graph
coverage, or amend the candidate and rerun evidence if those scenarios are
required. Integrators must not interpret a G pass as general authorization,
permission enforcement or a successful human approval run.

## Choice 3: scope of R selection

**Facts.** Proposal 0012, “R: closed runtime-declaration grammar”, gives each
Requirement a local definition `subject`. The document has at most one
Selection with one engine and one interface, optional model/provider/hosting,
and evidence claims. Selection has no subject or Deployment reference. D knows
Runtime and Deployment kinds, but their existence creates no R assignment.
Open engine identifiers, no inferred default, and unassessed evidence do not
settle the selection's scope or cardinality.

**Deduction and example.** Requirements can name Agent `writer` and Agent
`researcher`, but R cannot assign a local engine to the first and a remote
engine to the second. Naming both engines elsewhere in opaque definitions
would not make those assignments R-validated. A common document-wide choice
is one possible interpretation, not an established meaning of the current
subjectless Selection.

| Pending option | Coverage, cost and integrator consequence |
| --- | --- |
| Define R as one common selection for the document | Requires an explicit scope rule and corresponding evidence. Keeps one selection and the smaller grammar, but cannot express heterogeneous per-Agent assignments. Splitting documents is not an established lossless substitute for one System. |
| Support heterogeneous assignments in R | Requires a reviewed subject/assignment model and cardinality, including applicability, conflicts, requirement evidence and any relationship to Deployment. Costs text, schema, fixture and reader changes; enables explicit assignments without implying execution support. |
| Defer R | Preserve runtime metadata as opaque where allowed, without claiming validated engine assignments. |

**Open recommendation.** Decide from the configurations 0.1.0 must describe.
Both common selection and heterogeneous assignment are coherent directions;
this dossier gives neither priority. Neither can be inferred from the demand
for open engine identities. An R pass would still cover declarations, not
compatibility, readiness, evidence authenticity or runtime behavior.

## Adoption record still required

**Pending decisions.** Record the selected units; the Agent identity meaning;
the Interface correspondence and approval limits if G is retained; and the
selection scope if R is retained. Accept, amend or defer each explicitly.
Then reconcile proposals 0002, 0003 and 0011 with 0012 and Decisions 0001/0004.
C3-C7 and C10 remain candidate choices for that review, not individually
approved decisions merely because two readers implement them.

Two other limits belong in any adopted scope statement. Resolution uses only
direct supplied dependencies: a selected imported Agent needing a third-party
Interface can yield unsupported. Semantic extension interpretation is not
implemented in this edition; required interpretation is unsupported and
unknown classification is inconclusive. A third-party implementation's added
support cannot be silently reported as this candidate's positive semantics.
Vendor independence does not establish arbitrary composition or extension
support.

**Recommended sequence.** Obtain the separate scope decision; apply adopted text and official identities;
replay against that edition; complete release review. The
[delivery plan](../plans/2026-09-05-0.1.0-delivery.md) keeps adoption, normative
application and publication pending. No product dependency or external runtime
run is required to prepare this dossier.
