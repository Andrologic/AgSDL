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
