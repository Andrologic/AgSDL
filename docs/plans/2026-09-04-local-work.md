# Local implementation-preparation work plan

- Status: active, non-normative maintenance plan
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

## Execution record

| Lot | State | Evidence |
| --- | --- | --- |
| 0 | Integrated | `3fac313`; `./scripts/check.sh` passed before and after integration |
| A | Dispatched | Sol high, isolated worktree |
| B | Dispatched | Astra medium, isolated worktree |
| C | Queued | Wait for capacity and confirm the smallest useful checking scope |
| D | Conditional | Depends on verified findings from B |
| E | Pending | Coordinator records integrated commits and remaining decisions here |
