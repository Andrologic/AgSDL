# Preparing AgSDL 0.2

Status: **design and contract preparation; not a released or implementable
edition.** This is the maintained entry point for the next model. Publication
status remains in the [root README](../../README.md#release-status-and-history).
The normative specification is still `agsdl-0.1.0`; the 0017 experiment is a
separate frozen static-reader candidate.

## Read the current model

1. [Agents and Messages](../../proposals/0019-agent-prompt-and-resources.md):
   persistent participation, optional initial prompt, information, media and
   configured access.
2. [Flow](../../proposals/0020-blueprint-flow-0.2.md): completion, result transfer,
   deterministic conditions and Agent decisions, loops, parallel connections,
   explicit joins, recovery and message handling.
3. [Logic blocks](../../proposals/0021-logic-block-contract-0.2.md): proposed common
   contract for Condition, Join, Prepare, Call and reusable/custom behavior.
   Includes small graphs and cases to exercise before implementation.

The Agent and flow directions are accepted under [Decision 0011](../decisions/0011-message-based-agent-model.md)
and [Decision 0012](../decisions/0012-blueprint-flow-directions.md). Their concrete
serialization remains proposed. Proposal 0021 develops a reviewable contract;
preparing it does not adopt its new block rules.

## How the pieces fit

An Agent keeps its context across Messages. It may be prepared without an initial
prompt and wait for its first Message. Humans and software use that same Agent
concept. Its selected Engine, Tools and access determine how it can work; the
language supplies no default provider or promise of compatibility by name.

Messages distinguish instructions from supporting information and can contain
multiple media items. A source can be inline or referenced. Media delivery,
actual access and optional output constraints must agree with the selected
configuration. A resource URI alone proves neither permission nor availability.

A single Agent needs no flow graph. When flow is declared, steps describe work
and connections describe what follows. Completing a step does not end an Agent's
lifetime. By default, an Agent transfers all user-visible text produced for that
work, including progress Messages and the final reply, without reasoning or raw
Tool exchanges. Explicit result selection remains possible.

An Agent's routing decision is final when it completes the work. The integration
identifies it explicitly. Routing preserves the visible text, including a
decision written there; it does not insert a Tool-only decision into that text.
When explicit data can determine the authored rule, the graph can evaluate it
directly without asking for another Agent judgment.

Several connections from one selected output activate all their destinations.
Several direct inputs to an Agent remain separate Messages. A Join explicitly
groups required results into one input. A return connection can form a loop
through the same Agents, with no implicit iteration cap. Queueing is the default;
steering and first-satisfactory joins are explicit alternatives.

Configuration alternatives can be selected before Agent initialization. Once
initialized, an Agent retains its configuration and context. Editing the authored
blueprint follows stop, edit and start. Ordinary Messages and authorized
workspace edits are activity within that configuration, not hot reconfiguration.

## Proposed block vocabulary

The block contract in 0021 is the source for these proposals, not this summary.

| Function | Purpose | Status |
| --- | --- | --- |
| Condition | Apply an explicit deterministic rule to available data. | Direction accepted; predicates and contract proposed. |
| Join | Wait for required results and group them, or select a first satisfactory result when configured. | Direction accepted; activation and data contract proposed. |
| Prepare | Select and assemble content for the next step while preserving its roles. | Configurable transfer accepted; block form proposed. |
| Call | Invoke a function, Tool or service through a declared implementation. | New flow contract proposed. |
| Composition | Reuse a local graph of existing steps without changing their meaning or Agent identities. | Proposed. |
| Custom implementation | Supply a versioned behavior through Call and its declared requirements. | Proposed; no interpreter supplied by current readers. |
| Approval control | Admit an explicitly protected action only under its required authorization. | Existing control retained in principle; new-flow binding still proposed. |

Parallel launch, loops and error paths do not need separate mandatory block
families. Queueing belongs to message handling. A favorable opinion does not
replace an approval control. A requested branch stop does not prove it stopped
or undo its effects.

## Source hierarchy and earlier material

| Material | Meaning |
| --- | --- |
| [Official specification](../../spec/README.md) | Normative 0.1.0 contract; current schemas and official readers derive from it. |
| [0017 experiment](../../experimental/kiss-0.2/README.md) | Frozen candidate `agsdl-exp-0017-c1`, with its own examples and 42-case static comparison. Its grammar does not implement the model described above. |
| [0014 sketches](../research/0.2-design-examples.md) and [0015 reports](../../proposals/0015-validation-reports-0.2.md) | Earlier proposed inputs, not the current Agent/Message contract or adopted 0.2 syntax. |
| [0019](../../proposals/0019-agent-prompt-and-resources.md) and [0020](../../proposals/0020-blueprint-flow-0.2.md) | Current accepted design directions, with remaining grammar and integration work identified. |
| [0021](../../proposals/0021-logic-block-contract-0.2.md) | Proposed shared block contract and semantic review scenarios. |

Historical files retain their vocabulary and evidence. This preparation does not
rewrite frozen snapshots, migrate old documents or relabel static comparison as
evidence of context continuity, media delivery or execution.

## Before a 0.2 release

| Requirement | Current state and next evidence |
| --- | --- |
| Consistent Agent/content/flow directions | Recorded in 0019/0020 and their decisions. |
| Reviewed common block contract | Proposed in 0021; resolve its remaining semantic choices before freezing a candidate. |
| Concrete new edition | Not allocated here. Define Message and block serialization, references, conditions, selectors and configuration bindings. |
| Lifecycle and correlation rules | Define queue/steering boundaries, result grouping by current work, no-visible-text cases, duplicate/late data, first-satisfactory ties and pending stops. |
| Examples, schema and static readers | Derive them from the selected candidate and compare independent readers on its own cases. Existing 0.1/0017 checks do not cover it. |
| Integration evidence | Exercise actual Agent continuity, Tool calls, effects, media, approvals and stop behavior in consuming software before claiming support for them. |
| Migration and publication | Review changes from 0.1 and 0017, pin the final scope, obtain adoption/publication decisions and prepare release artifacts. No publication is part of this preparation. |

The scope remains generalist. It adds no product-specific runtime, default Engine,
context-reset operation, arbitrary Agent spawning, hot configuration changes,
universal event transport or package marketplace. Future capabilities must carry
explicit semantics and support requirements rather than hiding in opaque fields.
