# Decision 0012: declared flow between persistent Agents

- Status: accepted 0.2 design directions; no normative adoption or publication.
- Date: 2026-09-29.
- Starting revision: `88cb5c2863a1669f4d98ccb8e001b2266564044d`.

The maintainer confirmed the flow choices after the Message and Agent decisions
in [0011](0011-message-based-agent-model.md), then authorized recording them for
0.2. The accepted directions are specified in
[Proposal 0020](../../proposals/0020-blueprint-flow-0.2.md#accepted-flow-directions).
They cover completion, configurable result transfer, configuration selection
before initialization, recovery, parallel branches, loops, queueing or steering,
and joins with scoped stop requests.

These directions extend the next model beyond the bounded acyclic experiment.
The exclusions in [Decision 0008](0008-0.2-experiment-directions.md) still apply
to that experiment; they do not veto the parallel and looping flow now selected
for the next 0.2 model. Decision 0011's Agent continuity, content roles, output
constraints and configured access remain in force.

The concrete grammar, validation rules and integration acknowledgements listed
as remaining work in 0020 are not adopted by this decision. No scheduler,
transport, runtime, hot reconfiguration, context reset or automatic migration is
introduced. The official specification, frozen 0017 candidate and reader evidence
remain unchanged. Publication and claims of execution support require separate
work and evidence.

## Refinement on 2026-10-02: default result transfer

The maintainer replaced the last-Message default with all user-visible response
text produced for the completed step, including intermediate Messages and the
final reply, in response order. For a single input Message, collect the response
from that input through completion. Exclude reasoning, Tool invocations and raw
Tool results, and do not carry earlier conversation history forward implicitly.
Explicit result selection remains available, including for non-text content.

This refines the accepted transfer direction in
[0020](../../proposals/0020-blueprint-flow-0.2.md#completion-and-result-transfer).
The maintainer also confirmed that using an explicitly identified routing
decision does not alter the default transferred text. A decision present in the
user-visible response stays in that text. A decision supplied only through a
Tool exchange remains excluded, without automatic insertion into the text.

Text assembly, attribution with queueing or steering, and the case with no
user-visible text still need candidate rules. This refinement settles text
preservation when routing uses a decision; it does not adopt the withdrawn named
outcome design or its transmission mechanisms. The official contract, frozen
candidate and readers remain unchanged.

## Refinement on 2026-10-02: terminal routing decisions

The maintainer clarified that an Agent announces its routing decision only when
it has finished the work. That decision closes the current step; the Agent then
waits for later Messages while retaining its context. There is no provisional
choice, revision within that completed step or "last decision wins" rule.
[0020](../../proposals/0020-blueprint-flow-0.2.md#completion-and-result-transfer)
records this direction. The concrete integration rules for associating the
decision with step completion remain candidate work.

## Refinement on 2026-10-02: parallel output connections

The maintainer confirmed that several connections from the same selected output
of a step activate all their destinations as parallel branches. One routing
decision can therefore start several steps without a separate parallel-launch
step. Connections from other outputs are not activated by that selection.
[0020](../../proposals/0020-blueprint-flow-0.2.md#parallel-branches-and-loops)
records the rule and a small scenario. This does not change Agent message-handling
modes or define how parallel results are joined. Concrete serialization and
validation remain candidate work; no runtime support is established.

## Refinement on 2026-10-02: explicit result joins

The maintainer confirmed an explicit join step for waiting for required results
and passing one input containing them to the next step. Direct connections to
an Agent instead deliver separate Messages under its queueing or steering mode.
[0020](../../proposals/0020-blueprint-flow-0.2.md#joining-parallel-results)
records this distinction and an illustrative graph. This does not settle result
serialization, correlation across iterations or acceptance conditions, and does
not establish execution support.

## Refinement on 2026-10-02: deterministic branch conditions

The maintainer chose deterministic evaluation when explicit data can decide the
authored rule. A flow need not request a second Agent verdict for such a rule.
Judgment can still be assigned to an Agent. The blueprint selects the mechanism;
it does not delegate that choice implicitly to the consuming software.
[0020](../../proposals/0020-blueprint-flow-0.2.md#deterministic-conditions-and-agent-decisions)
records this direction. The predicates and integration contract proposed in
[0021](../../proposals/0021-logic-block-contract-0.2.md) remain subject to review.

## Refinement on 2026-10-03: default delivery as information

The maintainer confirmed that a direct connection delivers the source result
as information. The destination's instructions or explicit Message preparation
define the task to perform. An Agent already configured for that task needs no
additional preparation step. Record this direction in
[0020](../../proposals/0020-blueprint-flow-0.2.md#completion-and-result-transfer).
This accepts the content-role default, not a concrete JSON shape, the withdrawn
0022 notation or its reference and grouping rules. The normative specification
and existing reader contracts remain unchanged.
