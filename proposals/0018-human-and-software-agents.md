# Proposal 0018: human and software participation through Agent

Status: accepted 0.2 design direction under
[Decision 0010](../docs/decisions/0010-human-and-software-agents.md).
This is a conceptual proposal with static feasibility examples, not a new
candidate edition, normative adoption, runtime contract or published release.
The common participation direction remains. For the next 0.2 model,
[Decision 0011](../docs/decisions/0011-message-based-agent-model.md) supersedes
the reusable-definition framing below with persistent Agents and Messages in
[0019](0019-agent-prompt-and-resources.md).
The complete static rule source remains [0017](0017-agent-only-kiss-0.2.md),
marker `agsdl-exp-0017-c1`. Its bytes and reader behavior are unchanged.

## Problem and definition

A system may assign the same review task to software in one configuration and
to a person in another. Separate Human and Agent models would repeat instructions,
interfaces, graph calls and result bindings.

For the next 0.2 model, an **Agent describes a participant in the system through
its instructions and interface. Its work may be performed by software or by a
human.** This is a reusable definition, not a person's account or a running session.

An Engine remains software. For human participation, that software presents the
Agent's instructions and input to a person, receives a response and supplies the
declared output or failure. The existing Configuration selects this Engine and
its content adapter. Concrete people, accounts, assignment, authentication and
permissions remain the consuming application's responsibility.

This direction introduces no Human catalog, Agent subtype, participant field,
standard engine name, default engine or mandatory provider. An opaque name such
as `example/human-task-broker` in an example confers no portable human guarantee.
The Agent definition is shared; changing a selection still changes the exact
artifact/execution pin and requires a new execution under the existing rules.

## Task completion and authorization

A review operation receives text and returns corrected text. A human or software
implementation may satisfy that interface. Instructions must be presented in
the declared order; returned values must satisfy the declared ports. Provider
behavior and actual human participation require evidence outside a static file.
Request/response here specifies the result contract, not an immediate response
or a UI protocol. This proposal adds no queue, assignment lifecycle, human-task
API, polling, durable resumption or generic invocation timeout.

An approval remains a control on admission of a particular call. A normal Agent
output, including a Boolean labelled approved, does not satisfy an approval gate.
Keep the existing ordered chain, input availability, denial, failure, expiry and
call-admission rules. A human review does not itself authorize publication.

The consuming application can ask the same person to review and approve, or
choose different people. The document makes neither an identity-equality nor a
separation-of-duties claim. There is no approval-to-Agent reference in the current
grammar. Wiring an Agent's ordinary result directly into a gate is outside this
proposal's examples and would require an explicit contract.

## Two examples and proof limits

The [static feasibility examples](../experimental/kiss-0.2/human-participation/README.md)
use the unchanged 0017 grammar and readers:

1. One reviewer and graph with automated and human-assisted configurations.
   Selecting either leaves Agent and graph declarations unchanged. The external
   implementation choice changes; no person is represented as a second actor.
2. A human-assisted review followed by a separate human approval gate and a
   publication call. The reviewed text is available at the gate. Denial and
   failure cannot reach publication; a failure-bypass mutation is rejected.

These are complete static artifacts, not executable human-service integrations.
Engine and adapter names are fictional, their parameters empty and claims absent.
Both selections must therefore remain compatibility-inconclusive. That outcome
is expected, not a claim that either runtime works. The check also rejects a
review-result type incompatible with publication, regardless of its performer.

The examples show that no extra syntax is needed to describe these scenarios.
They do not amend the frozen candidate's meanings, prove execution equivalence,
verify human identity or establish interoperability. Any later change to frozen
candidate rules needs a new marker and its own review and comparison evidence.

## Alternatives and consequences

| Option | Consequence |
| --- | --- |
| Separate Human and Agent types | Repeats task interfaces and graph integration, and needs rules for changing performer type. |
| Agent subtype or reserved human Engine name | Adds a declaration that a static reader cannot authenticate; open custom engines remain necessary. |
| Treat a human only as an approval recipient | Cannot describe ordinary human work such as editing, assessment or collecting information. |
| Replace approval by an Agent returning a Boolean | Loses the existing admission, refusal and expiry semantics unless they are rebuilt elsewhere. |

Use the common Agent definition and existing bindings. Preserve approval as a
separate control. No current official artifact is automatically migrated; 0.1.1
and its `agsdl-0.1.0` contract remain unchanged.

## Security and remaining boundary

Agent text and provider names are untrusted data. A name, annotation or claim
cannot establish that a person participated or had permission. Presenting data
to a human also requires the consuming application to enforce its access rules.
A static pass cannot authorize execution.

A portable requirement that a particular task must be performed by a human,
provider assignment contracts, and any explicit link between approval and an
Agent remain separate future design questions. This step accepts the common
concept and tests its shape without inventing those mechanisms.
