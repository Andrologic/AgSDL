# Conceptual reconciliation and first-contract preparation

- Status: active, non-normative work plan
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
| C | First-contract task: proposal 0011 | After A and B review; specify a bounded candidate operation scope, inputs, outputs, preservation obligations, acceptance witnesses, and remaining decisions for maintainer review |
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
| 0 | Prepared | Decision 0004 records the five explicit approvals |
| A | Queued | Core relations and conceptual witnesses |
| B | Queued | Conformance requirements and validation phases |
| C | Waiting for A and B | Candidate contract only |
| D | Pending | Integrated review and maintainer handoff |
