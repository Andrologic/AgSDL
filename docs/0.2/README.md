# AgSDL 0.2.0 guide

Status: **published bounded draft under `agsdl-0.2.0`.**
[Decision 0013](../decisions/0013-adopt-0.2.0-contract.md) records the bounded
selection. Publication status remains in the [root README](../../README.md#release-status-and-history).
The separate 0.1.0 specification and frozen 0017 experiment retain their meaning.

## Read the current model

Start with the [normative specification](../../spec/0.2/README.md). Its chapters
cover content and configuration, flow and lifecycle, and static and supplied-record
checks. Then read the [worked scenarios](worked-scenarios.md),
[serialized examples and tools](../../tooling/0.2/README.md), and
[migration guide](migration.md). Scenarios and examples are illustrative;
implementations and proposals do not override the normative requirements.

The independent Python and JavaScript declaration readers use a
[112-case corpus](../../tooling/0.2/conformance/README.md). It includes the reviewed
candidate cases promoted to 0.2.0 and rejection of the old candidate marker.
Agreement covers those declarations and reports, not runtime support.

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
Tool exchanges. Explicit result selection remains possible. A direct transfer
to another Agent delivers information; the recipient's instructions or explicit
Message preparation define the task.

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

Configuration alternatives are selected before Agent initialization. Once
selected, the configuration is retained; an initialized Agent keeps its context. Editing the authored
blueprint follows stop, edit and start. Ordinary Messages and authorized
workspace edits are activity within that configuration, not hot reconfiguration.

## Block vocabulary

The [flow chapter](../../spec/0.2/flow.md) defines the rules. This table is a summary.

| Function | Purpose and bound |
| --- | --- |
| Condition | Apply an explicit deterministic predicate to current input. |
| Join | Group required results or select a first satisfactory result within the direct-fork structure. |
| Prepare | Select and assemble content while preserving instruction and information roles. |
| Call | Invoke a declared external contract through its selected implementation. |
| Composition | Expand a non-nested serial/conditional body, preserving existing Agent identities. |
| Custom implementation | Supply versioned behavior through Call; static readers do not execute it. |
| Approval control | Capture and admit a protected Agent or Call invocation through an ordered gate chain. |

Parallel launch, loops and error paths do not need separate mandatory block
families. A favorable opinion does not replace an approval control. A requested
branch stop does not prove it stopped or undo its effects.

## Source hierarchy and earlier material

| Material | Meaning |
| --- | --- |
| [0.2.0 specification](../../spec/0.2/README.md) | Normative bounded contract published as `v0.2.0`. |
| [0.1.0 specification](../../spec/README.md) | Separate normative contract retained by the published 0.1.1 release. |
| [0019](../../proposals/0019-agent-prompt-and-resources.md), [0020](../../proposals/0020-blueprint-flow-0.2.md), [0021](../../proposals/0021-logic-block-contract-0.2.md) | Proposal basis for the selected concrete 0.2.0 rules. Broader alternatives are not adopted implicitly. |
| Persistent-Agent candidate | Historical `agsdl-exp-flow-0.2-c1` at `bc441c0a894d286c4585eee261b07f8f03f9d6a7`; retained reports keep that identity. |
| [0017 experiment](../../experimental/kiss-0.2/README.md) | Frozen `agsdl-exp-0017-c1`, with its own 42-case comparison, predating persistent Agents. |
| [0014 sketches](../research/0.2-design-examples.md), [0015 reports](../../proposals/0015-validation-reports-0.2.md) | Earlier proposed inputs, not additional normative 0.2.0 requirements. |

## Release scope

The bounded contract and migration guide are published, with adoption recorded
in Decision 0013. The [release notes](../releases/0.2.0.md) record edition-specific
verification. Consuming implementations must demonstrate continuity,
Tool effects, media delivery, authority enforcement and stopping before claiming
support for those behaviors. Static agreement and record consistency do not
supply that evidence.

This edition adds no product-specific runtime, default Engine, context reset,
arbitrary Agent spawning, hot configuration changes, universal transport or
package marketplace.
