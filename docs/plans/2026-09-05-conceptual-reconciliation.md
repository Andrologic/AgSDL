# Conceptual reconciliation and first-contract preparation

- Status: approved reconciliation completed; candidate contract awaits maintainer review
- Date: 2026-09-05
- Starting integration commit: `aed7cf2`

## Authority and outcome

[Decision 0004](../decisions/0004-approved-design-directions.md) records the
maintainer's five approved directions. This work reconciles proposed rules and
prepares a reviewable first external contract. It does not adopt that contract
in `spec/` or select syntax, implement a parser, or modify another project.

The [previous work plan](2026-09-04-local-work.md) remains the completed record
of the first chantier. Its decision gates now have approved directions, not
approved detailed language semantics.

## Execution and ownership

Keep the primary checkout on `develop` and all edits in `feature/*` worktrees.
Run at most two production tasks at once. A stopped author may be replaced by
one independent reviewer within that same active-worker limit. Authors return
a reviewed commit and passing `./scripts/check.sh`; the coordinator reviews the
diff, resolves review findings, merges locally, and checks the combined result.
No push, publication, deployment, installation, or other-project work is needed.

| Lot | Owner and files | Dependency and completion criterion |
| --- | --- | --- |
| 0 | Coordinator: decisions and this plan | Record maintainer directions accurately without adopting detailed semantics |
| A | Core task: proposal 0002 and a new conceptual example | D1 and D2 are represented consistently in prose, relations, invariants, and witnesses; core phase applicability points to the conformance rules |
| B | Conformance task: proposals 0001 and 0003, ROADMAP.md | D3 is reconciled through requirements and traceability; D4 distinguishes permitted deferral from missing or invalid facts without inventing an implicit allowance |
| C | First-contract task: proposal 0011 | Preparation may start after B review; final review and commit depend on integrated A and B. Specify a bounded candidate operation scope, inputs, outputs, preservation obligations, acceptance witnesses, and remaining decisions for maintainer review |
| D | Coordinator: indexes, follow-up review record, and plan | After the other lots; check cross-document consistency and dependent bindings, preserve historical status, record integration evidence and the next review gate |

Use Astra high for the core relation changes and Astra medium for conformance
and first-contract preparation. Shared files are assigned to one author at a
time. Independent review should test concrete witnesses and seek unintended
semantic changes, rather than confirm the author's conclusion.

## Review gates

The first review checks whether D1 through D4 are faithfully reflected in the
proposals, including refusal and incomplete-evidence cases. Passing repository
checks establishes maintenance coverage only; conceptual witnesses are not an
executable AgSDL conformance suite.

The second review checks that the candidate contract names what a third-party
processor would receive, inspect, preserve, and report, while separating
proposed rules from open choices. The exact normative subset, permitted
deferral inventory, identity-row interpretation, representation and result
contracts, and any further substantive choices return to the maintainer before
adoption. Continue independent approved work if one such choice remains open.

## Execution record

| Lot | State | Evidence |
| --- | --- | --- |
| 0 | Integrated | `dc5b79a`, merged as `a367a1b`; Decision 0004 records the five explicit approvals and amends Decision 0001's conformance-level direction |
| A | Integrated | `504b1c8`, merged as `4355ad5`; coordinator and independent reviewer checked the relations and imported-Agent, refusal, and missing-evidence witnesses |
| B | Integrated | `4870423`, merged as `14b4037`; coordinator and independent reviewer verified REQ-009, phase distinctions, and absence of implicit deferral permission |
| C | Integrated as a proposal | `c29d2b0`, `cfd0df7`, and `48cb4a4`, merged as `4f7f89e`; document boundaries and local materialized imports were clarified, then the producer-conformance issue found in review was explicitly reserved for adoption |
| D | Completed | `a7fc92c`, merged as `3d755a8`, aligns existing examples and 0010; indexes and this record complete the handoff. Repository checks passed after each integration |

## Review record and next gate

Two isolated production tasks were used:

- `01a07041-028f-7023-8eac-b75d6c5b86bb`, Astra high, completed lot A.
- `01a07041-0bfe-7640-b07e-b8643eeecab6`, Astra medium, completed B and was
  reused for C. Preparation overlapped A's review; final C depended on the
  integrated A and B changes.

Both authors stopped for independent review. The reviewer tested the conceptual
witnesses against the source proposals and Decision 0004. The coordinator
checked the proposed changes, the dependent example and import passages, and
the returned corrections. The final producer-conformance clarification was
checked against the review's requested condition before merge. Repository
checks passed on the integrated result, including the existing source-verifier
tests and seven Markdown-link tests. These are maintenance tests, not an AgSDL
semantic conformance suite. No executable language test or implementation claim
was added.

The [candidate contract](../../proposals/0011-first-exchange-contract.md)
now presents concrete choices for review: a fixed declaration-and-Agent scope,
one primary document per verdict, an Interface-only deferral for Fragment
roots, the Agent definition-Identity interpretation, preservation and loss
rules, and bounded verdict aggregation. Its exact scope and these choices are
not adopted by the maintainer's earlier approval of D5.

Exact preservation of an invalid input remains separate from producing a
conforming output. Whether that preservation operation can support a future
producer conformance claim is an explicit adoption question; proposal 0003's
existing producer obligation was preserved.

The next step is maintainer review of proposal 0011's candidate choices. The
shared representation, exact equality rules, normative check inventory, and
executable corpus still need definition before independent software can claim
implementation support. No syntax, schema, parser, runtime, or other-project
work has started. All integration remains local on `develop`; both production
tasks and the reviewer have finished their assigned work.

The [closure record](../reviews/0004-closure-record.md) records the subsequent
independent audit of the final revisions, coordinator validation, verified
worktree removals, and archival of both production tasks.
