# Decision 0011: messages, optional output constraints and configured access

- Status: accepted 0.2 design directions; no normative adoption or publication.
- Date: 2026-09-29.
- Starting revision: `af9ee182a6d4bdbdb3cbc138930645c38f993465`.

The maintainer chose Messages as the basic interaction, accepted optional but
explicit output constraints, and placed workspace/resource behavior in AgSDL
Engine and Tool configuration. Record these directions in
[Proposal 0019](../../proposals/0019-agent-prompt-and-resources.md).

## Accepted directions

1. An Agent is an initialized participant that continues across Messages with
   its context. Fresh context requires another Agent; there is no reset switch.
   Human and software participation use the same Agent concept. Messages are
   the interaction baseline; a basic exchange needs no named Operation catalog.
2. Keep prompt instructions distinct from accessible information, with content
   supplied directly or by reference. Messages and results may contain multiple
   media types. Input and output support depend on the selected Model, when
   applicable, and Engine/harness/Tool path, not their names alone.
3. Output constraints are optional. Declared constraints distinguish permitted
   formats, required results and optional results, including structure when
   needed. An unconstrained reply needs no fabricated schema. A configuration's
   format capabilities are not themselves a requirement to emit every format.
4. AgSDL configuration describes workspace exposure, access rules and Tools.
   The implementation enforces those choices. The resource collection is not a
   required inventory of every accessible file. Ordinary authorized workspace
   edits and later Messages do not require reconfiguration or a new Agent.
   The core adds no universal frozen/live resource choice, snapshotting rule or
   refresh mechanism. Such behavior belongs to the configured integration.

For the next 0.2 model, direction 1 supersedes the reusable-task-definition
framing in [Decision 0010](0010-human-and-software-agents.md). Its common Agent
concept, external account handling and separate approval controls remain.
Changing the declared system configuration still requires stop, edit and start;
this rule does not classify ordinary workspace edits as configuration changes.

## Limits

These directions do not adopt every proposed shape or detail of 0019. Message
serialization, Interface constraints and Engine/Tool binding details still need
a precise candidate and review. There is no new transport, scheduler, runtime,
Goal-loop contract, hot reload, automatic migration or publication in this step.

The frozen 0017 candidate, its acyclic graphs, readers and corpus keep their
current meaning. The official specification is unchanged. Static comparison
cannot establish context continuity, actual media support or access enforcement.
Those require execution evidence from consuming implementations.
