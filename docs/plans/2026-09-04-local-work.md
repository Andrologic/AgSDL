# Local implementation-preparation work plan

- Status: bounded maintenance completed; continuation awaits maintainer decisions
- Date: 2026-09-04
- Starting integration commit: `3fac313`
- Coordinator: Codex task `01a06e19-35e4-70f0-a295-1e7a26c5ed6a`

## Objective and authority

Prepare AgSDL for an implementable specification through reviewed, bounded
local changes. This plan follows the [repository scope](../scope.md) and does
not accept proposed semantics. The maintainer authorized local worktrees,
commits, iterative review, and integration into `develop`.

The immediate outcome is corrected project documentation, independently
verified conceptual findings, useful repository checks, and a short decision
queue. Syntax, a normative first subset, and runtime behavior need decisions
that this maintenance plan does not make.

## Execution rules

- Keep the primary checkout on `develop`. Make changes on `feature/*` branches
  in separate local worktrees.
- Run at most two production tasks concurrently. Permit one bounded independent
  review agent only when a production task has stopped work for review, keeping
  no more than two delegated workers active in total.
- Assign non-overlapping files. The coordinator owns integration and this plan.
- Use `gpt-5.6-sol` with high reasoning for bounded editorial and checking work;
  use `gpt-6-astra` with medium reasoning for conceptual analysis. Escalate to
  Astra high only for a concrete unresolved review issue within authorized scope.
- Keep all changes, task execution, and Git integration on this computer. Do not
  push, publish, deploy, open remote pull requests, or modify another project.
- Read-only primary-source verification is permitted. Browser verification is
  useful only when the subject needs it; Markdown and shell checks do not need
  a browser.
- At a substantive uncertainty, leave the affected semantics unchanged, record
  the question, and continue only work independent of its answer. A review
  objection requires correction or an explicit unresolved status, not a forced
  merge.

## Lots and dependencies

| Lot | Ownership | Work | Dependency and exit criterion |
| --- | --- | --- | --- |
| 0 | Coordinator | Integrate `feature/repository-boundary` | Reviewed diff and passing repository checks; merged locally as `3fac313` |
| A | Documentation task | `README.md`, `ROADMAP.md`, `docs/research/prior-art.md` | After 0; published versus proposed status is accurate, comparative summaries match their source notes, and no new semantic decision is made |
| B | Conceptual review task | `docs/reviews/0003-implementation-readiness.md` | After 0, parallel with A; findings distinguish contradictions, missing rules, intentional restrictions, and false positives; unresolved decisions have minimal alternatives and dependencies |
| C | Verification task | Repository checking scripts and focused tests | After a worker slot is free; improve checks for real repository defects without creating an AgSDL validator or changing language semantics |
| D | Bounded follow-up task | Only files assigned after B | After B review; apply only corrections that restore an already explicit meaning; stop if choosing among substantive alternatives is necessary |
| E | Coordinator and independent reviewer | Integrated diff and completion record | After A through D where authorized; checks pass, each merged step is reviewed, and unresolved semantic decisions remain visible |

The coordinator reads task progress and responds to blockers. Each returned lot
is reviewed before dependent work is launched. Tasks can be reused for later
lots once their prior work is integrated; this avoids multiplying active
worktrees and contexts.

## Review and merge gate

1. The author reviews the entire diff and runs `./scripts/check.sh`.
2. The author commits one coherent step and returns the worktree, branch, SHA,
   scope, checks, and open questions.
3. The coordinator reviews the actual diff and its source context. For a lot
   needing a second review, a separate reviewer receives the objective, base,
   and diff without an instruction to confirm the author's conclusion.
4. Fix actionable findings and rerun the checks affected by the correction.
   Record uncertainty that cannot be resolved within the authorized scope.
5. The coordinator integrates the reviewed SHA into local `develop`, runs the
   repository checks on the combined result, and verifies the working tree.

Passing repository checks establishes their stated maintenance coverage only.
It does not establish semantic completeness or implementation conformance.

## Decisions reserved for the maintainer

The independent review may narrow or reject these candidate questions:

- whether a complete System may contain only imported Agent definitions;
- how one Action occurrence relates to several authorization decisions;
- how the accepted mention of conformance levels relates to the proposed
  implementation-feature model;
- which first subset and processing rules become normative;
- serialization, type compatibility, data routing, concurrency, and verdict
  aggregation where more than one substantive interpretation remains possible.

Documenting alternatives does not select or accept them. Work on schemas,
parsers, adapters, or another product starts only after the applicable decisions
and scope have been explicitly authorized.

## Conditional continuation after maintainer decisions

The [implementation-readiness review](../reviews/0003-implementation-readiness.md#five-decisions-for-maintainer-review)
records five decision gates and small witnesses for checking the answers. A
general redesign is not an exit criterion. Preserve the existing distinctions
unless a reviewed decision changes them.

| Next phase | Prerequisite | Work and reviewable result |
| --- | --- | --- |
| Reconcile proposed core rules | Explicit answers to the relevant D1 through D4 questions | Update the affected proposals and traceability together. Reuse the witnesses to check both accepted and rejected cases. Serialize edits to the same proposal; parallelize only independent files. |
| Bound the first external contract | D5 scope, plus D3, D4, and the Identity-row interpretation where applicable | Name the intended third-party operation, required inputs, preserved information, diagnostics, and verdict rules. Include D1 and D2 only if their constructs enter that scope. |
| Adopt a normative subset | Review and acceptance of that bounded contract | Put adopted semantics in `spec/`, then derive syntax, schemas, and positive and negative conformance cases. Keep unresolved features explicitly outside the claim. |
| Demonstrate independent interoperability | Stable adopted input and result contracts, plus separate authorization for any other repository | Compare independent readers on the same corpus. Verify preservation and loss reporting before claiming compatibility with a third-party product such as Agent Graph Studio. |

Keep the two-task capacity limit in these phases. Each phase ends with a
reviewed result and a passing integrated check; the next phase is dispatched
only when its prerequisite is actually satisfied. These phases are a proposed
sequence, not authorization to settle the reserved questions or start work in
another repository.

## Execution record

| Lot | State | Evidence |
| --- | --- | --- |
| 0 | Integrated | `3fac313`; `./scripts/check.sh` passed before and after integration |
| A | Integrated | `95b1720`, merged as `d8e9e07`; coordinator reviewed source summaries and requested corrections before integration |
| B | Integrated | `8c2a2ff` and correction `47ece89`, merged as `bf4aa27`; separate Astra review identified the REQ-009 wording nuance, corrected before integration |
| C | Integrated | `4f55e45`, merged as `4409d1d`; coordinator and separate Astra reviewer verified the limited checker. Two false positives were corrected before approval; seven focused tests and the integrated repository check passed |
| D | Integrated | `83d381c`, merged as `3cf8e27`; coordinator verified the definition against proposal 0002; relation meanings and cardinalities are unchanged |
| E | Completed | Coordinator reviewed the integrated scope and reran repository checks. Remaining conceptual work stops at D1 through D5; no proposed language semantics were adopted |

The two production tasks were reused rather than multiplied:

- `01a06e2f-cee5-7db0-97fa-1c3a4d6bf6c9`: lots A and C, Sol high.
- `01a06e30-24a9-7692-a2c6-f97e5920e8d8`: lots B and D, Astra medium.

Both tasks completed their assigned work and await further instructions. The
independent review agent completed its checks. The primary checkout remains on
`develop`; integration commits are local. No push, publication, deployment, or
change in another project was performed.

The readiness review describes its recorded base commit. Lot D subsequently
corrected the Principal wording it identified; the separate Agent Identity-row
question remains open. The Markdown checker verifies repository links only and
does not establish AgSDL conformance or third-party interoperability.
