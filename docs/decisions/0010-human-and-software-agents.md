# Decision 0010: one Agent concept for human and software work

- Status: accepted 0.2 design direction; no normative adoption or publication.
- Date: 2026-09-29.
- Starting revision: `54651b8`.

The maintainer authorized the general Agent definition and two examples after
discussing human participation. Adopt the definition in
[Proposal 0018](../../proposals/0018-human-and-software-agents.md) as the direction
for the next 0.2 model. The same Agent instructions and interface can describe
work performed by software or by a person through a mediating software Engine.

This supersedes only the blanket exclusion of human participation through Agent
in [Decision 0009](0009-agent-only-experiment.md). Its removal of Principal,
external account/permission handling and retained approval rules still apply.
An Agent represents the participant's task definition, not the person's identity.
Engine, Configuration and execution remain distinct from that definition.

Use the existing open Engine/adapter bindings for the two static examples.
Add no Human type, participant registry, reserved human engine, default provider
or approval-to-Agent field. Keep task completion distinct from authorization:
an ordinary result does not discharge an approval gate.

The frozen 0017 candidate, readers and 42-case corpus remain unchanged. Its
readers can test the new examples' existing syntax and static invariants, not
prove the proposed performer model or an actual human interaction. Normative
integration, any future candidate change and execution contracts require their
own scope and evidence. No production adapter is included in this decision.
