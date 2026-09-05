# Cumulative conceptual qualification for AgSDL 0.0.2

- Date: 2026-09-05
- Status: non-normative local review; no publication or adoption decision
- Baseline: `v0.0.1`, peeled commit `53d9880c80c9434d9a287dea677c94880393460e`
- Examined commit: `b1c22aa4bcd880136dc3bd3c46ef9db19237a716`
- Review branch: `feature/review-0.0.2`, created from that verified local `develop`

## Verdict and boundary

Favorable for the cumulative work as a non-normative conceptual milestone,
with two non-blocking wording findings at the examined commit, corrected in the
separate follow-up recorded below. No reproducible defect found
in this review blocks that limited qualification. This does not establish an
implementable language, compatibility, conformance, execution, or interoperability.

The subject is the entire 44-file diff from the peeled baseline to the examined
commit, not only the latest reconciliation. New files were read as additions;
modified files were compared with the baseline and relevant surrounding text.
The scope and contribution rules, Decisions 0001 through 0004, and relevant
core definitions and conformance rules supplied the interpretation boundary.

Task A owns the forthcoming release documents. No candidate from A was part of
this review, so this report does not certify those documents or a final release
tree. Publication, tagging, and normative adoption are separate decisions.

## Coverage inventory

The following families cover every changed path exactly once. Paths are relative
to the repository root; a family review is not an executable semantic test.

| Family | Changed paths | Review focus |
| --- | --- | --- |
| Repository authority, 6 | `AGENTS.md`, `CONTRIBUTING.md`, `GOVERNANCE.md`, `README.md`, `ROADMAP.md`, `docs/scope.md` | Source hierarchy, published versus proposed status, repository and runtime boundaries, maintenance-check scope |
| Decisions, 3 | `docs/decisions/0001-specification-before-syntax.md`, `docs/decisions/0003-repository-boundary.md`, `docs/decisions/0004-approved-design-directions.md` | Recorded amendment and accepted directions versus detailed proposal rules |
| Plans, 2 | `docs/plans/2026-09-04-local-work.md`, `docs/plans/2026-09-05-conceptual-reconciliation.md` | Completed local work, dependencies, remaining adoption gates |
| Historical reviews, 2 | `docs/reviews/0003-implementation-readiness.md`, `docs/reviews/0004-closure-record.md` | Historical base and closure scope; earlier findings are not silently applied to the new base |
| Research and source evidence, 8 | `docs/research/prior-art.md`, `docs/research/mcp-2026-07-28.md`, `docs/research/a2a-1.0.1.md`, `docs/research/a2a-v1.0.1.sha256`, `docs/research/agent-user-interaction-protocol.md`, `docs/research/a2ui.md`, `docs/research/ap2-v0.2.0.md`, `docs/research/open-agent-specification.md` | Recorded editions, source facts versus assessments, upstream conflicts, evidence limits and comparative claims |
| Proposals and index, 12 | `proposals/README.md`, `proposals/0001-requirements-and-use-cases.md`, `proposals/0002-core-conceptual-model.md`, `proposals/0003-conformance-and-versioning.md`, `proposals/0004-trust-security-and-control.md`, `proposals/0005-mcp-binding-profile.md`, `proposals/0006-a2a-1.0-external-binding.md`, `proposals/0007-agent-user-interaction-protocol-binding.md`, `proposals/0008-a2ui-format-binding.md`, `proposals/0009-agent-payments-protocol-binding.md`, `proposals/0010-open-agent-specification-binding.md`, `proposals/0011-first-exchange-contract.md` | Core reconciliation, mapping boundaries, conditional evidence, version separation, scope and loss reporting |
| Examples, 4 | `examples/README.md`, `examples/a2a-1.0-external-binding.md`, `examples/a2ui-declarative-interface.md`, `examples/conceptual/composition-and-authorization.md` | Updated original witnesses, external mappings, refusal and missing evidence, hypothetical versus tested behavior |
| Future normative artifacts, 2 | `spec/README.md`, `schemas/README.md` | No adopted language or schema; schema expressiveness does not override normative meaning |
| Verification, 5 | `scripts/check.sh`, `scripts/check-markdown-links.py`, `scripts/test-check-markdown-links.py`, `scripts/verify-a2a-1.0.1-sources.sh`, `scripts/test-verify-a2a-1.0.1-sources.sh` | Local execution, failure paths, synthetic fixtures, link-check exclusions and hash-check limits |

## Facts and deductions

**Facts.** The baseline is an ancestor of the examined commit. The diff contains
44 additions or modifications, with no deletion. All eleven proposals retain
proposed status. `spec/` and `schemas/` each contain only their README.
Decision 0004 accepts directions while reserving exact contract choices.
README, ROADMAP, and the example index distinguish the tagged 0.0.1 contents
from subsequent work. Historical reviews identify their own examined states.

**Deduction.** The cumulative changes preserve the conceptual status of the
repository. Acceptance of a design direction has not been presented as adoption
of the detailed language or as implementation evidence.

**Facts.** Proposal 0002 permits zero locally owned Agents and definitions but
requires at least one participating Agent. Its authorization associations retain
several decisions, evaluated requirements, originating points, and bounded reuse.
The composition example includes no-participant rejection, denial,
indeterminate and missing evidence, and an observed Effect without inferred
permission. Proposal 0007 retains its pre-attempt refusal boundary; proposal
0009 retains separate payment Actions and constrained decision reuse.

**Deduction.** Those binding paths do not require reversal of the reconciled
composition or authorization directions. One successful check cannot supply a
different required decision, and an observation does not create permission.

**Facts.** Proposals 0001 and 0003 make REQ-009 a capability to express bounded
feature/profile claims, without imposing a duty to publish one. Proposal 0003
requires explicit permission and declarations for phase deferral. Proposal 0010
separates preservation of incomplete imports from a positive validation verdict.
Proposal 0011 fixes a candidate primary-document scope, excludes annex internals,
proposes only the Fragment Interface-minimum deferral, and separates preservation
of invalid artifacts from producer conformance.

**Deduction.** Missing relations, valid unretrieved references, invalid local
references, and missing occurrence evidence remain different cases. Syntax,
identity comparison, the exact 0011 adoption choices, and a future normative
draft remain open work rather than defects merely because this milestone is
conceptual.

**Facts.** The binding research records MCP 2026-07-28; A2A specification 1.0.1
and protocol 1.0; separate AG-UI published packages and a pinned 1.0 draft;
A2UI 0.9.1 and candidate 1.0 at a pinned commit; AP2 0.2.0; and Agent Spec
26.1.2. The related proposals require separate identities and evidence for
external contracts, adapters, and runtimes. A2A source conflicts, AG-UI draft
and package differences, A2UI schema/transport conflicts, AP2 dependency and SDK
gaps, and Agent Spec runtime limits are recorded rather than silently repaired.

**Deduction.** Their presence supports conceptual mapping review only. No binding
implementation or behavioral equivalence follows from these documents, upstream
SDK tests, discovery metadata, or repository checks.

## Non-blocking findings and recommendations

Locations below refer to the examined commit. Both findings were sent to the
coordinator, who confirmed them and authorized this task to correct only the
identified passages without changing the model.

1. **Human approval is overgeneralized in A2UI research.** In
   `docs/research/a2ui.md:299-302`, the trust-limit bullet says protected Actions
   require a matching human decision and an Authorization decision. The core
   makes human approval conditional at `proposals/0002-core-conceptual-model.md:771-774`
   and permits zero Approval requirements at line 1001. A protected Action whose
   authorization requirement has no human-approval gate is the counterexample;
   the composition example expressly includes that case. Recommend qualifying
   the human decision by the applicable Approval requirement. This is an
   overbroad research summary, not an adopted extra requirement or implemented
   authorization defect.
2. **The A2UI example conflates selection and realization.**
   `examples/a2ui-declarative-interface.md:23-26` says its resolved binding selects
   a renderer runtime instance. The core defines Runtime as a definition at
   `proposals/0002-core-conceptual-model.md:832-835` and makes it a selection target
   at line 1022. An instance is separately defined at lines 59-64. A Runtime
   definition with two deployed instances exposes the ambiguity. Recommend naming
   the selected Runtime definition and identifying its instance through deployment
   evidence separately. The example already disclaims implementation, so this
   wording does not establish a false deployed capability.

These limited inconsistencies do not change the status or principal outcomes of
the conceptual work.

### Authorized correction follow-up

Commit `356decb96e50190e258a2f8c618f50548539255d`, directly after the examined
commit, changes only the two passages. The research now conditions human approval
on the Authorization requirement while retaining Authorization decisions at
applicable Policy application points. The example selects the renderer Runtime
definition and separately attributes its instance to the Deployment.

The author compared this targeted diff with proposal 0002 and ran
`./scripts/check.sh` successfully before committing it. This is author
verification, not independent approval of the correction. The coordinator is
organizing independent review. The cumulative inventory above still describes
the fixed examined commit; it is not a claim to have reviewed later integration.

## Local checks and limits

The five verification scripts were inspected before execution. `./scripts/check.sh`
passed on the examined tree and again after adding this report. It ran the A2A
verifier's synthetic success, digest-mismatch, and missing-declaration cases;
seven Markdown-link tests; the repository link scan; shell syntax checks for the
A2A scripts; required-file checks; whitespace checks; and `git diff --check`.
The tests exercise useful maintenance failures, not AgSDL semantics.
An ad hoc local comparison against `git diff --name-only` also confirmed that
the coverage inventory lists all 44 changed paths exactly once.

The link checker is deliberately limited as documented in CONTRIBUTING. It does
not establish heading-anchor validity, remote-link availability, or full Markdown
parsing. The whitespace scan depends on `rg`; it was available in this run.
The A2A test substitutes a synthetic manifest. Passing it does not verify the
real upstream files, release provenance, an Agent Card, or an A2A server.

No upstream source checkout was read or executed. No network, fetch, remote
version search, browser, external runtime, or interoperability suite was used.
External assertions were compared with the recorded research and source
identities, not independently reverified against remote publishers. Historical
cleanup and audit records were read as records, not reenacted or certified here.

This report is the only added project file; the two existing-file edits belong
to the separate correction commit above. Future release documentation and the
final integrated tree need their own review. A passing maintenance check and
this favorable conceptual verdict cannot certify a
conforming AgSDL document, processor, adapter, or runtime.
