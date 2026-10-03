# Conceptual reconciliation review record

- Date: 2026-09-05.
- Status: historical review of proposed changes; no normative adoption.
- Integrated revision: `6334bf305add5bebd9c8ba1f960a8e1b733fbd5c`.

[Decision 0004](../decisions/0004-approved-design-directions.md) establishes the
five directions examined here. The [original work plan](https://github.com/Andrologic/AgSDL/blob/ebe403905ad626fe9a63ff4e8d9fb87f8f2ece07/docs/plans/2026-09-05-conceptual-reconciliation.md)
remains in the published historical snapshot. This record retains the technical
review; task dispatch and workstation cleanup are not project requirements.

## Reviewed changes

| Work | Base | Reviewed candidate | Integration |
| --- | --- | --- | --- |
| A: participation and authorization | `a367a1b361ed6cd1688b44b6b69932e0c4760d0c` | `504b1c8dafd51b0433f9dcf5e375180eecdea1cc` | `4355ad5` |
| B: conformance and phases | `a367a1b361ed6cd1688b44b6b69932e0c4760d0c` | `48704235f8e1d50867bc7f1d3f8cfa09b87c47f8` | `14b4037` |
| C: bounded exchange contract | `3d755a8c1f6f23f6bff2531f91f950dd8778f299` | `48cb4a4593a063e0ecd283f4a6ff9a2c682a05dc` | `4f7f89e` |

A separate reviewer found no blocking defect in A or B/C at the integrated
revision. The review verified candidate ancestry and identity of the delivered
files. A, B's proposals and final 0011 matched their reviewed candidates; the
later roadmap edit changed the work record and candidate link only.

## Findings and evidence limits

A's ownership minima permit zero local definitions while participation still
requires an Agent. Multiple authorization decisions preserve evaluated
requirements, originating points, and context. Refusal, indeterminate results,
and absent evidence grant no permission. The examples cover imported Agents,
the no-participant counterexample, multiple checks, pre-attempt decisions under
0007, and bounded reuse under 0009. The auditor found no conflict with those
bindings.

B preserves optional publication of feature/profile claims. Its phase rules
distinguish absent relations, unretrieved external references, contradictions,
and express deferral permission. A required obligation still missing prevents
a positive resolved-graph verdict.

C fixes the document and local-Agent scope, keeps annex boundaries separate,
and proposes only the Fragment Interface-minimum deferral. Invalid references
are not covered by that exception. The final producer clarification resolves
the earlier review finding: exact preservation of an invalid artifact does not
satisfy the producer's conforming-output obligation, and future producer
conformance remains a decision before adoption. Existing examples and 0010's
phase clarification agree with the integrated changes.

Audit limits: conceptual and Git review, no network, edits, or execution of an
agentic system. The auditor did not repeat `check.sh` or perform cleanup. The repository checks were run separately, as recorded below.
Identity, representation, and adoption choices remain open as required by the
mission; they are not unfinished implementation work in this closure.

## Verification

`./scripts/check.sh` passed on the integrated revision, including source
verification and seven Markdown-link tests. The integration review confirmed
the candidate diffs and the independent findings. These maintenance checks and
conceptual review do not establish conformance or execution support. Publication
and later adoption are recorded in their separate decisions and release notes.
