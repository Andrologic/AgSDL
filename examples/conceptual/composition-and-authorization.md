# Imported-Agent composition and authorization evidence

- Status: non-normative conceptual example of proposed rules
- Date: 2026-09-05

This example exercises [proposal 0002](../../proposals/0002-core-conceptual-model.md)
after the directions approved in
[Decision 0004](../../docs/decisions/0004-approved-design-directions.md).
It describes conceptual definitions and hypothetical execution evidence. It
supplies no AgSDL syntax, runtime, adapter, or executable conformance test.
The names below are labels, not identifiers in an adopted language.

## A System with two imported Agents

A Report system composes a Draft agent and a Review agent. Draft package version
1 owns and exports the Draft agent definition; Review package version 2 owns
and exports the Review agent definition. Each source package also owns the
Agent's required dependencies. Those packages supply explicit Interface,
behavioral-direction, and Principal relations rather than inferring them from
an external service advertisement.

Each Agent exposes one Interface containing its input operation. Its source
Instructions define its bounded task. Both Interfaces declare their input and
output contracts, their available Action, permitted acting Principals, and
target Resource kinds. The resolved source definitions and their dependencies
retain their source identities and versions. The distinct Agent definition
identities and Principal identities are recorded separately. The meaning of
`Agent represented by Identity` remains the open contract question in proposal
0002; this example makes no full conformance claim that depends on resolving it.

Report system owns a local Report flow and its steps. It also owns the local
export Action, Effect, Resource descriptions, Principal definition, Policies,
authorization requirements, and Trace requirement described below. Every local
definition is reachable through the System's declared relations. Each imported
definition keeps its package lifecycle owner.

| Relation | Witness |
| --- | --- |
| Report system `uses` Agent | Draft agent and Review agent, two imported definitions |
| Report system `owns` Agent | Zero |
| Report system `owns` Definition | Report flow and the other local definitions |
| Draft package version 1 `owns` Draft agent | One source lifecycle owner |
| Review package version 2 `owns` Review agent | One source lifecycle owner |
| Report system `exposes` Interface | Draft agent's intake Interface, one system Interface |
| Report system `uses` Control flow | Report flow, which invokes both Agents in sequence |

Report flow invokes Draft agent, then Review agent with the draft, and requests
one Export report Action if review accepts. Rejected review terminates without
export. An export refusal, unavailable evidence, or failed export has an
explicit failure terminal. Successful export reaches the completion terminal.
The flow has one entry, successors for every nonterminal step, and no cycle.
It schedules invocations through the declared Interfaces without asserting a
separate static participant graph. No Topology is claimed.

The package Agents remain reusable definitions. Using them in another System
does not clone them or share their runtime state by implication. Report flow
is a local definition; invoking it or realizing either Agent produces separate
runtime or occurrence subjects with their applicable definition versions.

Two composition boundary cases matter:

- If a permitted source also supplies Report flow and every other needed
  definition, Report system can own zero local definitions. The generic
  `System owns Definition` minimum is zero, so it does not indirectly require
  a local wrapper. The System still declares its participation and exposed
  Interface relations and satisfies its other obligations.
- Removing both participating Agents leaves no valid complete System under
  the proposed model, even if the System owns a flow and exposes an Interface.
  The `System uses Agent` minimum remains one.

## One export occurrence, two different checks

Export report targets a Report Resource and an External destination Resource.
Each has an identified governing authority. The Action declares its input,
permitted export Principal, failure behavior, and possible Report disclosed
Effect. The declared outward crossing from the system trust domain to the
destination trust domain identifies the Resources and both controls below.
An external destination is an environment endpoint, not an imported Agent.

The hypothetical export executor has one acting Principal identity belonging
to a runtime Principal under the declared Export principal definition. The
executor's identity is distinct from the imported Agent definition identities.
The selected runtime and deployment identify the definition versions they
realize. Neither importing an Agent nor accepting its review grants the
executor authority to disclose the report.

Export report is mediated by two Policy application points:

| Point | Evaluated requirement | Policy and required evidence |
| --- | --- | --- |
| Content gate | Content release requirement | Release policy requires authentication evidence for the export Principal and evidence that the fixed report version satisfies its release conditions. |
| Destination gate | Destination access requirement | Destination policy requires authentication evidence and a valid Authority grant for that Principal to disclose this report to this destination. |

Each point requires exactly one requirement and applies its stated Policy.
The requirements are distinct even if they share some evidence. Both define
denial, indeterminate-result, unavailable-mechanism, and control-failure
behavior that stops disclosure. Neither requires human approval in this
witness; adding such a requirement would require its matching evidence.

For this example, Export report defines the start of local export preparation
as the attempt boundary. The attempt creates one Action occurrence, Export
attempt 17, before either point evaluates it. Both points run before any Report
disclosed Effect. Preparation itself has no governed external Effect. This
boundary is part of the hypothetical Action contract, not a universal rule
for bindings.

| Occurrence evidence | Required association and context |
| --- | --- |
| Content decision 17 | `evaluated against` Content release requirement; `made at` Content gate; permitted for the acting Principal, report version, destination, release Policy version, material context, and decision time |
| Destination decision 17 | `evaluated against` Destination access requirement; `made at` Destination gate; permitted for the same Action scope under the destination Policy version and its decision time |
| Export attempt 17 | `has authorization decision` Content decision 17 for Content gate, and Destination decision 17 for Destination gate |

There is one Export report Action occurrence and two directly associated
decisions. The decisions are separate execution occurrences, not Agent or
Policy definitions. The two required checks have matching permitted evidence
in this path. No third aggregate decision is created. Neither decision proves
execution success. A Report disclosed Effect occurrence needs separate
observation evidence and identifies Export attempt 17 as its cause.

The local Trace requirement retains the attempt, both decisions, each evaluated
requirement, originating point, associated point, Principal and Resource
identities, context, Policy versions, times, outcome, and any observed Effect.
Redaction preserves the distinction between withheld and absent evidence.

## Refusal, incomplete evidence, and missing evidence

These are alternative histories of the same single-attempt witness. They do
not add an export attempt merely to fit the authorization relation.

| Variant | Preserved evidence | Consequence in this declared flow |
| --- | --- | --- |
| Both checks permit | Both decisions and their matching required evidence | The flow may proceed to disclosure; separate evidence must establish whether it occurs. |
| Destination check denies | Content decision permits; Destination decision denies and preserves its evaluated context, requirement, and point | Both remain directly associated with Export attempt 17. The flow stops before disclosure. The neutral association does not describe denial as authorization granted. |
| Destination evaluation is indeterminate | Content decision permits; Destination decision records an indeterminate result because grant validity cannot be established | The attempt retains both decisions. The incomplete authorization evidence cannot support disclosure. |
| Destination decision is missing | Content decision is present; no Destination decision record is available | The missing check remains identified by its point and requirement. No decision or denial is invented. The declared flow stops if it cannot obtain the decision. |
| A record lacks required context | A claimed permitted Destination decision omits the target destination or required validity evidence | The record is incomplete evidence and cannot establish a matching permitted check. It is not silently repaired. |

A partial trace is a narrower observation than execution. If a received trace
omits Destination decision 17, a reader cannot infer that the live executor
never obtained it, nor that disclosure did or did not occur. The reader reports
the missing evidence. If an Effect is independently observed without the
required authorization evidence, the reader retains that observation without
claiming the Effect was authorized.

A binding may place authorization before the attempt boundary.
[Proposal 0007](../../proposals/0007-agent-user-interaction-protocol-binding.md#interface-roles-and-operations)
uses that boundary for its mapped Actions. A denial there creates no Action
occurrence. The decision retains its evaluated Action, requirement, originating
point, Principal, Resources, and context in evidence without a fabricated
occurrence association. This example does not change that binding's boundary.

## Reuse and validation limits

Content decision 17 cannot satisfy Destination access requirement. Shared
Policies, shared authentication evidence, or one successful export result do
not erase the distinction between the two required checks.

A different witness could have two points requiring the same Authorization
requirement. Reusing one decision there would still need matching scope,
context, validity, and explicit permission from the applicable binding or
authorization contract. The occurrence association would identify both points
while the decision retained its original `made at` point. A later occurrence
could reference the same decision only under those same limits. This preserves
the bounded reuse described in
[proposal 0009](../../proposals/0009-agent-payments-protocol-binding.md#checkout-and-payment-separation),
without assuming that this example implements AP2. It also leaves MCP retry
reconsideration and correlation rules intact.

This composition witness assumes its mandatory source facts are supplied. If
an imported Fragment lacks an Interface, its missing obligation does not become
valid merely because the Fragment declares an Unresolved requirement.
[Proposal 0003](../../proposals/0003-conformance-and-versioning.md#validation-by-phase-and-declared-missing-obligations)
governs the two validation phases. Unresolved-document validation can permit
the omission only under an explicit deferral rule and declaration; a required
obligation still missing at resolved-graph validation prevents a positive
verdict for the graph in scope. The permitted deferral inventory and exact
Agent-to-Identity contract remain open. No phase deferral grants runtime
authorization or fills missing occurrence evidence.
