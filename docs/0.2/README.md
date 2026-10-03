# Preparing AgSDL 0.2

Status: **concrete candidate requirements pending final review and maintainer
adoption; unreleased.** This is the maintained entry point for the next model. Publication
status remains in the [root README](../../README.md#release-status-and-history).
The normative specification is still `agsdl-0.1.0`; the 0017 experiment is a
separate frozen static-reader candidate.

## Read the current model

Start with the [candidate specification](../../spec/0.2/README.md) for concrete
requirements under `agsdl-exp-flow-0.2-c1`. Its chapters cover content and
configuration, flow and lifecycle, and the scope of static and record checks.
The following documents explain the accepted directions and their use:

1. [Agents and Messages](../../proposals/0019-agent-prompt-and-resources.md):
   persistent participation, optional initial prompt, information, media and
   configured access.
2. [Flow](../../proposals/0020-blueprint-flow-0.2.md): completion, result transfer,
   deterministic conditions and Agent decisions, loops, parallel connections,
   explicit joins, recovery and message handling.
3. [Logic blocks](../../proposals/0021-logic-block-contract-0.2.md): proposed common
   contract for Condition, Join, Prepare, Call and reusable/custom behavior.
   Includes small graphs and cases to exercise before implementation.
4. [Worked scenarios](worked-scenarios.md): follow a basic conversation, a
   deterministic test loop and two grouped reviews, then inspect a custom Call.
   These semantic walkthroughs are illustrative, not executable fixtures.
5. [Migration guide](migration.md): carry intent forward from official 0.1 or
   the frozen 0017 experiment without relabelling either edition.

The [tooling guide](../../experimental/agent-flow-0.2/README.md) supplies JSON
examples, a schema and independent Python/JavaScript declaration readers. The
[107-case comparison](../../experimental/agent-flow-0.2/conformance/README.md)
covers static semantics and complete reports. The [candidate boundaries](../../spec/0.2/README.md#remaining-release-scope)
remain explicit; passing checks does not adopt the candidate or establish
execution support.

The Agent and flow directions are accepted under [Decision 0011](../decisions/0011-message-based-agent-model.md)
and [Decision 0012](../decisions/0012-blueprint-flow-directions.md). Their concrete
serialization is specified in the candidate and remains proposed. Proposal 0021
develops the common block contract; neither preparation nor static verification
adopts its new rules.

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

## Proposed block vocabulary

The [flow chapter](../../spec/0.2/flow.md) defines the concrete candidate rules;
0021 records the proposed common block contract. This table is a summary.

| Function | Purpose | Status |
| --- | --- | --- |
| Condition | Apply an explicit deterministic rule to available data. | Direction accepted; predicates and contract proposed. |
| Join | Wait for required results and group them, or select a first satisfactory result when configured. | Direction accepted; activation and data contract proposed. |
| Prepare | Select and assemble content for the next step while preserving its roles. | Configurable transfer accepted; block form proposed. |
| Call | Invoke a function, Tool or service through a declared implementation. | New flow contract proposed. |
| Composition | Reuse a local graph of existing steps without changing their meaning or Agent identities. | Non-nested serial/conditional candidate form specified; adoption pending. |
| Custom implementation | Supply a versioned behavior through Call and its declared requirements. | Proposed; no interpreter supplied by current readers. |
| Approval control | Admit an explicitly protected action only under its required authorization. | Gate chains, capture and admission freshness specified in the candidate; adoption pending. |

Parallel launch, loops and error paths do not need separate mandatory block
families. Queueing belongs to message handling. A favorable opinion does not
replace an approval control. A requested branch stop does not prove it stopped
or undo its effects.

## Source hierarchy and earlier material

| Material | Meaning |
| --- | --- |
| [Official specification](../../spec/README.md) | Normative 0.1.0 contract; official schemas and readers derive from it. |
| [Candidate specification](../../spec/0.2/README.md) | Canonical concrete requirements under `agsdl-exp-flow-0.2-c1`, pending final review and maintainer adoption. |
| [0017 experiment](../../experimental/kiss-0.2/README.md) | Frozen candidate `agsdl-exp-0017-c1`, with its own examples and 42-case static comparison. Its grammar does not implement the model described above. |
| [0014 sketches](../research/0.2-design-examples.md) and [0015 reports](../../proposals/0015-validation-reports-0.2.md) | Earlier proposed inputs, not the current Agent/Message contract or adopted 0.2 syntax. |
| [0019](../../proposals/0019-agent-prompt-and-resources.md) and [0020](../../proposals/0020-blueprint-flow-0.2.md) | Current accepted design directions; concrete rules are specified separately in the candidate, with integration evidence still scoped. |
| [0021](../../proposals/0021-logic-block-contract-0.2.md) | Proposed shared block contract and semantic review scenarios. |

Historical files retain their vocabulary and evidence. This preparation does not
rewrite frozen snapshots, migrate old documents or relabel static comparison as
evidence of context continuity, media delivery or execution.

## Before a 0.2 release

This is the maintained completion index. Decisions 0011/0012 establish the
accepted directions; 0021 proposes their block forms and local composition.
The candidate now specifies their bounded concrete forms. Final review must
assess that scope explicitly; preparation does not adopt it or silently remove
accepted directions.
Execution evidence is required for claims about a consuming implementation,
not for every possible Engine or Tool before publishing a language draft.

| Requirement | Current state and next evidence |
| --- | --- |
| Consistent Agent/content/flow directions | Recorded in 0019/0020 and their decisions. |
| Reviewed common block contract | Concrete bounded rules are in the candidate specification; final review and explicit adoption remain. |
| Concrete new edition | Candidate requirements retain `agsdl-exp-flow-0.2-c1`; final edition allocation and adoption remain pending. |
| Lifecycle and correlation rules | c1 now proposes FIFO admission, explicit steering ownership and acknowledgement, unchanged-origin delivery, exact text assembly, Source selection and closed recovery inputs. Recorded checks cover delivery/configuration and output assembly; independent review and consuming integration evidence remain distinct requirements. |
| Modular contract and declarations | c1 proposes non-nested serial/conditional composition, protected Agent/Call admission, bounded structured results, explicit URI origins and exact scoped support claims. Examples and adverse static/record checks cover this bounded form; the independent declaration comparison covers 107 cases; final review and adoption remain. |
| Examples, schema and static readers | Examples, schema and independent Python/JavaScript declaration readers are available, with a 107-case comparison. Final coverage review remains pending. Existing 0.1/0017 evidence does not transfer. |
| Integration evidence | Exercise actual Agent continuity, Tool calls, effects, media, approvals and stop behavior in consuming software before claiming support for them. |
| Migration and publication | The [migration guide](migration.md) addresses the concrete candidate; [release notes](../releases/0.2.0.md) are an unreleased draft. Final review, edition allocation and explicit adoption/publication decisions remain. No publication is part of this preparation. |

The scope remains generalist. It adds no product-specific runtime, default Engine,
context-reset operation, arbitrary Agent spawning, hot configuration changes,
universal event transport or package marketplace. Future capabilities must carry
explicit semantics and support requirements rather than hiding in opaque fields.
