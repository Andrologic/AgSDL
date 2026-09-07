# Proposal 0002: core conceptual model

- Status: proposed
- Date: 2026-09-02
- Revised: 2026-09-05 under [Decision 0004](../docs/decisions/0004-approved-design-directions.md)

Decision 0004 approves the directions for imported-Agent composition, direct
authorization accounting, and validation by phase. The relations and detailed
rules below remain proposed; they are not adopted normative semantics.

## 0.1.0 disposition, 2026-09-07

This conceptual proposal remains proposed. [Decision 0007](../docs/decisions/0007-adopt-0.1.0-contract.md)
adopts only the bounded concrete contract selected through 0012/0013 and applied
in [spec](../spec/README.md). Its [traceability record](../docs/reviews/0007-0.1.0-contract-traceability.md)
identifies the adopted subset and exclusions. Earlier pending-adoption wording
below describes the conceptual preparation stage, not the status of that
applied 0.1.0 contract. No whole-proposal acceptance follows.

## Problem

Agent frameworks expose different units of composition. One may treat a prompt
and a model as an agent, another may require an executable class, and a third may
make an agent a node in a workflow. These representations hide or combine facts
that a portable description needs to state separately.

AgSDL needs a minimal conceptual model before it can define syntax. The model
must describe a complete agentic system without making a framework, provider,
transport, runtime, or deployment platform part of its portable meaning. It must
also distinguish a reusable definition from the changing data produced when a
system runs.

## Scope

This proposal defines the entities needed to describe:

- a system and its externally visible boundary;
- the agents and reusable components inside that boundary;
- communication, coordination, and control;
- identity, policy, authorization, and human approval;
- execution, deployment, observation, and evaluation; and
- packaging, configuration profiles, references, and extensions.

The proposal assigns responsibilities, directed relationships, cardinalities,
and invariants to those entities. It does not define a serialization format,
execution engine, transport, provider API, or conformance level.

## Modeling conventions

### Definitions, runtime instances, execution occurrences, and immutable artifacts

A **definition** is a versioned description of intended structure or behavior.
Definitions are static for the purpose of one resolution and validation
operation. They may be edited between versions, but an edit produces a distinct
definition version rather than changing the meaning of an already resolved
version.

The model classifies each identified subject as a **definition**, **runtime
instance**, **execution occurrence**, or **immutable artifact**. These categories
are disjoint for one subject identity, even when records in different categories
describe the same component or execution.

An **execution occurrence** is data created or observed during an execution.
Occurrences include messages, state snapshots, approval decisions, trace
records, and evaluation results. An occurrence identifies the definition
versions under which it arose when those versions are known.

A **runtime instance** is an addressable realization of a definition in a
deployment. Runtime instances include deployed runtime processes and other
deployed components that need lifecycle, placement, or principal identity. They
exist before, during, or after any one execution and are not execution
occurrences. A runtime instance identifies the deployment definition and
realized definition versions that established it.

An **immutable artifact** is fixed content preserved for distribution or later
evidence. Package versions, package files, and sealed trace exports are
artifacts. An artifact has content identity or an integrity reference and, when
derived from another category, records the source identity and applicable
definition versions. Creating an artifact during an execution does not make the
artifact an execution occurrence after it has been sealed. The creation event
remains an occurrence and refers to the artifact.

Definitions can constrain runtime instances, execution occurrences, and
artifacts. None of those subjects can alter the meaning of the definitions that
constrain them. A runtime may use an occurrence to select new behavior, but that
selection is itself behavior described or permitted by a definition.

Some concerns therefore have two or more named forms:

- a **state definition** constrains a **state occurrence**;
- an **authorization requirement** constrains an **authorization decision**;
- an **approval requirement** constrains an **approval request** and an
  **approval decision**;
- an **evaluation definition** produces an **evaluation result**; and
- a **trace requirement** constrains an **execution trace**, which contains
  **trace records**.

A **message occurrence** has no corresponding message definition in this model.
Interfaces and protocols define its contract. The relationship model names
occurrence forms explicitly so that an execution result is never treated as a
reusable definition. A trace or evaluation may also emit an immutable report
artifact. That artifact refers to the trace or evaluation result rather than
replacing its occurrence identity.

### Portable requirements and resolved bindings

A portable definition may declare a **binding requirement**. A binding
requirement states capabilities and constraints that an implementation must
satisfy, but does not identify that implementation. A **resolved binding** is a
deployment-specific record that selects a runtime or environment element and
shows which binding requirement it satisfies.

Conceptual resolution validates definitions, references, and binding
requirements without requiring resolved bindings. Deployment resolution
compares those requirements with candidate implementations and records each as
satisfied, unsatisfied, or indeterminate. A deployment that claims readiness
must resolve every required binding. Replacing a resolved binding does not
change portable meaning unless the replacement also changes a portable
definition or requirement.

### Applicability by validation phase

The obligations below, including relation minima, use the two phases in
[proposal 0003, Validation by phase](0003-conformance-and-versioning.md#validation-by-phase-and-declared-missing-obligations).
An incomplete fragment may pass unresolved-document validation only when its
missing obligations are explicitly declared and permitted to be deferred at
that phase under the applicable contract. A declaration alone grants no
permission to defer an invariant. At resolved-graph validation, a required
obligation still missing prevents a positive verdict for the graph in scope.
This proposal defines no general inventory of deferrable minima.

### Ownership, use, and containment

This proposal uses three distinct relation kinds:

- **owns** gives one definition lifecycle responsibility for another. An owned
  entity has at most one owner within a resolved system.
- **contains** places an entity inside a boundary or aggregate. Containment does
  not imply that the contained entity cannot be reused elsewhere.
- **uses** states a dependency without transferring ownership or containment.

An entity can be contained by one system, defined in a package owned elsewhere,
and used by several agents. Keeping these relations separate prevents reuse from
being mistaken for duplication.

Every local definition has exactly one lifecycle owner. The owner controls its
creation, revision, deprecation, and retirement. A lifecycle owner is a System
for definitions local to a complete system, a Fragment for definitions local to
an unpackaged reusable fragment, or a Package version for definitions local to
a reusable package. A definition imported by reference keeps its original
lifecycle owner. Use, containment, configuration, packaging, and deployment do
not transfer that ownership.

System participation is expressed by `System uses Agent`. A participating Agent
may be locally owned or imported from a Fragment, Package version, or another
permitted source. Several Systems may use the same Agent definition. This
relation identifies a definition participating in an application boundary; it
does not create a runtime instance, transfer lifecycle ownership, or grant
authority. A System may own no local definitions and use exclusively imported
Agents, provided its other complete-System obligations are satisfied.

### Document roots

An AgSDL document has one of two root forms. A **complete system document** has
exactly one System root and describes one complete agentic application boundary.
A **reusable fragment document** has exactly one Fragment or Package version
root and exports definitions for composition without claiming to describe a
complete system.

A **fragment** is a reusable definition aggregate. It declares the definitions
it exports, its internal definitions, dependencies, and unresolved requirements
that a consuming System, Fragment, or Package version must satisfy. A Package
version may contain one or more Fragments and may also export definitions
directly. Neither root creates a runtime boundary, exposes a system interface,
or establishes system-level policy by itself. A processor must not invent a
synthetic System to validate or package either root.

Invariants:

- A document has exactly one root form: complete system or reusable fragment.
- A System root owns every definition local to that complete system document,
  including definitions used by its contained Agents.
- A Fragment or Package version root owns every definition local to that
  reusable fragment document.
- Composition incorporates exported definitions and checks unresolved
  requirements. It does not change the root form or lifecycle ownership of the
  source document.

### Identity and references

Every definition that another entity can target has an identity that is unique
within its declared resolution scope. A **reference** is a directed edge from
one definition or occurrence to an identified target. It records target
identity, expected target kind, and any version constraint needed for resolution.

A reference resolves to exactly one target for a given resolution operation.
Zero matches, multiple matches, and a target of the wrong kind are resolution
errors. Resolution does not copy the target into the source and does not change
the target's owner.

An occurrence may hold a reference to another occurrence, such as a reply to a
message. The runtime assigns occurrence identity. Such identity need only be
unique within the trace or execution scope declared for it.

### Principals, identities, and authentication evidence

A **principal** is a human, agent, runtime instance, external system, or other
actor that can request, authorize, perform, or be held accountable for an
action. A Principal definition describes a stable actor or actor class. A
runtime Principal is the addressable actor for an execution and is a runtime
instance. A Principal has one or more identities valid in declared scopes.

An **identity** is a stable identifier for a principal, definition, runtime
instance, or occurrence within a declared scope. Identity names a subject. It
does not establish that a claimant controls or represents that subject.

**Authentication evidence** is an occurrence or external evidence reference
used to establish that a claimant controls or represents a principal identity
under a stated authentication mechanism, context, and validity interval. It is
an input to an authorization decision, not an identity, principal, authority
grant, or authorization decision.

Invariants:

- Every action occurrence has exactly one acting Principal identity. It may also
  identify an initiating Principal identity when Delegation or Handoff
  separates initiation from execution.
- Definition identity and Principal identity remain distinct even when they
  share a label.
- Authentication evidence identifies the claimed principal identity,
  authentication mechanism, issuer or verifier, validity interval, and
  verification result when one has been produced.
- Authentication proves no authority beyond the identity binding it supports.
- Authorization does not retroactively make missing or invalid authentication
  evidence valid when the applicable authorization requirement demands it.

The `Agent represented by Identity` relation below remains a broader conceptual
question. For the adopted 0.1.0 contract, Decision 0007 resolves its bounded
interpretation: the Agent Key identifies its Definition, exactly one actsAs
reference names its declared Principal, and invoke.principal equals that target.
Configuration does not rebind the Principal; authentication remains external.
The conceptual row cannot add Identity records or Principal cardinality checks
to that specification.

### Cardinality notation

`A --relation--> B [x..y]` means that one `A` has from `x` through `y` outgoing
relations of that kind to `B`. `*` means no fixed upper bound. Each relation
table also states the inverse cardinality from one target back to its sources.

## Core entities

### System

A **system** is the definition of one agentic application boundary. It declares
the system's purpose, participating Agents, owned components, exposed
interfaces, governing policies, optional topology, control flow, and execution
requirements. It is the root used to resolve and validate a complete description.

The system owns definitions that are local to it and uses local or imported
Agent definitions as participants. Imported definitions retain their source
lifecycle owners. It does not own runtime instances or execution occurrences.

Invariants:

- A resolved complete system document has exactly one root System.
- A System uses at least one Agent as a participant, even when it owns no Agent
  locally. Ownership alone does not declare participation.
- Every locally owned definition is reachable from that root by containment,
  ownership, or use relations.
- Every interaction crossing the system boundary uses an interface declared by
  the system or by a contained agent that the system exposes.
- A system with one agent does not require a topology. Its agent and exposed
  interfaces are sufficient when no participant graph or permitted
  inter-participant path needs to be declared.
- The system boundary identifies what AgSDL governs. External systems remain
  environment elements unless they have their own system definitions.

### Agent

An **agent** is a definition of an autonomous decision-making participant. It
accepts inputs through interfaces, applies instructions and roles, may use a
model, tools, skills, memory, knowledge, and state, and produces actions or
messages. Autonomy means the participant can select among permitted next actions
from current inputs and state. It does not imply unrestricted authority.

An agent may be composite. A composite agent contains other agents and presents
an agent boundary of its own. Composition does not erase the contained agents'
identities or policies.

Invariants:

- An agent has at least one interface through which the system or another agent
  can address it.
- An agent has at least one source of behavioral direction, through instructions,
  a role, a skill, or a control flow.
- Each action attributable to an agent is subject to the effective policies and
  authorization context at the action point.
- Containing an agent does not grant the containing agent the contained agent's
  permissions.

### Role

A **role** is a reusable definition of responsibilities, behavioral expectations,
and constraints assigned to an agent. A role describes what the agent is
responsible for, not who the agent is and not which permissions it receives.

Invariants:

- An agent may have several roles, and role order has no meaning unless a control
  flow or extension defines one.
- A role cannot grant authorization. Policies may map a role to permissions, but
  the authorization decision remains separate.
- Conflicting role constraints are a validation error unless an explicit
  precedence rule resolves them.

### Model

A **model** is a definition of a computational inference capability used to
derive outputs from inputs. It states portable capability requirements and may
state provider-neutral limits. Provider identifiers and request options are
runtime bindings or extensions unless the specification later standardizes
  their meaning.

Invariants:

- Using a model does not make the model an agent. The agent owns decision
  responsibility for actions attributed to it.
- A model binding must satisfy every capability required by its use site.
- A model definition does not contain credentials.

### Instructions

**Instructions** are an ordered definition of directives supplied to an agent,
model invocation, skill, or control-flow step. They state intended behavior and
constraints in a form consumed by an implementation.

Invariants:

- Instruction order is significant.
- Every instruction set declares its target kind and intended application point.
- Instructions cannot grant authorization or override policy.
- If several instruction sets apply at one point, the description states their
  composition order. An implementation cannot infer portable precedence from a
  framework's defaults.

### Tool

A **tool** is a definition of an invocable operation with declared inputs,
outputs, effects, failures, and authorization needs. A tool is the operation
contract. The service, process, function, or device that performs it belongs to
the runtime or environment. The tool may declare binding requirements without
naming or resolving an implementation.

Invariants:

- Every tool declares whether it can produce effects outside the current
  execution state.
- Every Effect produced through a Tool is attributable to its Action
  occurrence.
- Tool availability does not imply authorization to invoke it.
- A tool result is an occurrence and cannot silently redefine the tool contract.

A tool contract is distinct from four adjacent concerns. A **packaged skill**
is a skill definition distributed in a package. An **externally advertised
service** is a claim at a system boundary that others may discover and request a
bounded service. An **authority grant** permits an identified principal to take
specified actions. An **implementation feature** is behavior that a processor,
runtime, or adapter claims to support. Availability or support in any one of
these concerns does not imply the others. The final name and contract for an
externally advertised service remain open.

### Skill

A **skill** is a reusable behavioral capability composed from instructions,
tools, knowledge, control flow, or other skills. It defines how an agent performs
a bounded kind of work. A skill is not an authorization unit, though policy may
refer to it.

Invariants:

- A skill declares its inputs, outputs, preconditions, and completion condition.
- A skill's dependencies resolve before the skill can be assigned.
- Recursive skill composition has an explicit termination condition or finite
  expansion bound.
- Assigning a skill does not transfer ownership of its dependencies to the agent.
- Packaging a skill does not expose it as an external service, grant authority
  to use it, or prove that a runtime supports its requirements.

### Memory

**Memory** is a definition of retained information that an agent or system may
read or update across control-flow steps or executions. It states retention,
scope, access, update rules, and any storage binding requirements. Memory
content is runtime state. A memory definition does not require a resolved
storage binding during conceptual resolution.

Invariants:

- Every memory definition declares its lifetime and visibility scope.
- Memory updates require authorization when the effective policy protects the
  target memory.
- A trace records memory access when policy or evaluation requirements demand it.
- Memory does not imply factual correctness. Knowledge claims require their own
  provenance or validation rules.

### Knowledge

**Knowledge** is a definition of information sources an agent may consult as
evidence. It states source identity, subject, provenance expectations, freshness
expectations, and access method. Retrieved or embedded content is an occurrence
or immutable package artifact, depending on whether it is acquired at runtime
or shipped with a package.

Invariants:

- A knowledge definition distinguishes authoritative sources from supporting
  sources when that distinction matters.
- Knowledge access is subject to policy and authorization.
- Declaring knowledge does not assert that every contained claim is true or
  current.
- Runtime retrieval records enough source identity to support required trace and
  evaluation claims.

### State

A **state definition** describes execution data that can affect later behavior
within a declared scope. It states allowed fields, ownership, lifetime,
transitions, and any state-management binding requirements. A **state
occurrence** holds values at a point in an execution.

Invariants:

- Each state occurrence conforms to one identified state definition version.
- A state transition identifies its initiating agent, control-flow step, tool,
  runtime, or external event.
- State has one declared authority for resolving concurrent writes.
- State history is distinct from a trace. A runtime may derive either from the
  other only when the declared retention and fidelity are sufficient.

### Environment

An **environment** is a definition of external conditions and resources visible
to a system at runtime. It includes external services, devices, networks,
variables, secret references, and operating constraints. An environment element
is outside the system's ownership boundary even when the deployment provisions
it.

Invariants:

- Environment definitions refer to secrets by identity or binding requirement,
  not by embedding secret values.
- Each required environment capability has a testable binding condition.
- An external resource used by the system appears through an environment,
  runtime, deployment, interface, or tool relation.

### Resource and trust boundary

A **resource** is an identified asset, capability, data set, state, memory,
knowledge source, interface operation, tool operation, environment element, or
other target whose access or change can be governed. A resource may be local to
a system or external. Resource ownership, lifecycle ownership of its definition,
and authority over actions on it are separate facts.

A **trust boundary** is a definition of a boundary across which principals,
data, instructions, messages, authentication evidence, or effects move between
different trust domains. It identifies each side, the crossing operations and
resources, the assumptions that cease to hold at the crossing, and the policy
application points and controls that govern it. A trust boundary may coincide
with a System, Agent, Runtime, Deployment, or Environment boundary, but
containment alone does not create or remove one.

Invariants:

- Every protected action targets at least one Resource.
- Every Resource has an identified owning or governing principal, or is marked
  external with the authority source that governs it.
- Every declared trust-boundary crossing identifies its direction, subject,
  source trust domain, destination trust domain, and applicable controls.
- Crossing a trust boundary never transfers resource ownership or principal
  authority by implication.

### Interface

An **interface** is a definition of operations or message exchanges available at
an agent or system boundary. It declares direction, input and output contracts,
interaction mode, and failure behavior without prescribing a transport.

An **interface operation** is one addressable request, response, notification,
or message contract within an interface. A single-message interaction can use
an interface operation directly. A Protocol is required only when portable
meaning depends on a sequence of two or more related operations or messages.

Invariants:

- Every interface operation has a declared inbound, outbound, or bidirectional
  direction relative to its owner.
- Messages crossing a boundary conform to an operation declared by that
  boundary's interface.
- An interface operation declares whether it is a complete single-message
  interaction or participates in a Protocol.
- Transport bindings cannot change the portable operation contract.
- Exposing an interface does not grant callers authorization to use it.

### Message occurrence

A **message occurrence** is information sent from one identified endpoint
to one or more identified endpoints through an interface operation. Its
envelope records sender, intended recipient, operation identity, and correlation
identity when correlation applies. Its content conforms to the selected
interface operation. A message records protocol position only when it
participates in a Protocol.

Invariants:

- A message occurrence has exactly one declared sender. Broadcast infrastructure
  may relay it without becoming that sender.
- A message occurrence has at least one intended recipient or one declared
  broadcast scope.
- Replies and correlated messages reference earlier message occurrences without
  changing them.
- Delivery, processing, and acceptance are separate facts. A trace must not
  collapse them into one event.

### Protocol

A **protocol** is a definition of allowed message or operation sequences between
roles at interfaces. It defines interaction states, valid transitions, and
completion or failure conditions. It does not define the transport carrying an
interaction.

Invariants:

- Every protocol transition identifies its source state, trigger, permitted
  sender role, permitted receiver role, and resulting state.
- A protocol has at least one initial state and one completion or failure state.
- Every reachable nonterminal state has at least one outgoing transition or an
  explicit wait condition.
- Protocol recursion has a declared return point and termination condition.

### Topology

A **topology** is the static directed graph of addressable participants and
permitted interaction paths in a system. Nodes refer to agents, systems, human
participants, or environment endpoints. Edges refer to interfaces and may be
constrained by protocols and policies.

Invariants:

- Every topology node resolves to one addressable definition or external
  endpoint definition.
- Every topology edge has a direction. A bidirectional path consists of two
  directed permissions unless an interface defines one bidirectional operation.
- A topology edge permits a path but does not schedule an interaction or grant
  authorization.
- A cyclic topology is valid only when the participating protocols or control
  flows define progress, termination, or an intentional long-lived loop.
- Omitting a topology declares no static participant graph. It does not require
  a synthetic one-node graph and does not prevent a single agent from being a
  complete system.

### Control flow

A **control flow** is a definition of how control can move among steps based on
events, outcomes, state, and policy decisions. Steps may invoke agents, tools,
skills, protocol transitions, evaluation definitions, or approval requirements.

Invariants:

- A control flow has at least one entry step.
- Every nonterminal step declares at least one possible successor or an explicit
  wait condition.
- Each branch condition has portable meaning or is marked as an extension.
- Parallel branches declare their join, cancellation, and state-conflict rules.
- Every cycle has a termination condition, a finite bound, or an explicit
  declaration that it is a long-lived loop.

### Model-selected transition

A **model-selected transition definition** permits a model-assisted choice from
a closed set of successor steps. It names the selection authority responsible
for accepting the choice, the observation evidence required, and the policy to
apply when the model returns no allowed successor, several successors, or an
unusable result. It does not define a deterministic branch predicate or promise
that repeated executions choose the same successor.

A **transition selection observation** is an execution occurrence that records
the candidate produced by the model, the allowed set in force, the accepted or
rejected outcome, the selection authority, and the successor selected when one
is accepted. Protected model content may be referenced or redacted under the
applicable trace requirement, but the observation must still prove that the
accepted successor belonged to the declared closed set.

Invariants:

- The allowed successor set is finite, non-empty, and fixed by the resolved
  definition before the model returns a candidate.
- The model proposes a candidate. The declared selection authority accepts or
  rejects it and remains accountable for the transition.
- The failure policy identifies the fallback, retry, wait, escalation, or
  terminal failure behavior for every unusable selection outcome.
- A model-selected transition cannot target a step outside its allowed set,
  even when instructions or runtime defaults suggest that step.

### Action and effect

An **Action** is a definition of an operation that a principal may request or
perform. It declares its target Resource kinds, inputs, possible Effects,
failure behavior, and the policy application points that govern it when the
action is protected. An **action occurrence** records one attempted or performed
action, its initiating and acting principals, target Resources, applicable
definition version, associated authorization decisions, and outcome. Missing
required decision evidence remains explicit rather than becoming a permission.

A Tool invocation and an Interface operation each reference the Action they
make available. A control-flow step may reference an Action directly. These use
sites do not create separate authority for the same Action.

An **Effect** is a definition of an externally relevant change that an Action
can produce in system state, a Resource, an external environment, or an
information flow. An **effect occurrence** records a change that actually
happened or was observed. Absence of an effect occurrence does not prove that no
effect happened unless the declared observation boundary can establish that
fact.

Invariants:

- Every Action identifies the permitted acting Principal kinds or identities
  and at least one target Resource kind. Every Action occurrence identifies one
  acting Principal and at least one target Resource.
- Every Effect is attributable to one Action occurrence or to an identified
  external event.
- A protected Action identifies one or more policy application points that run
  before the governed Effect can occur.
- A permitted authorization decision supports permission only for its evaluated
  requirement and stated scope. It does not satisfy a different required check,
  assert that the Action ran, or prove that an Effect occurred.
- One Action occurrence may retain several decisions through the neutral
  `has authorization decision` relation. Each association identifies the Policy
  application point or points for which that decision is accounted, under the
  authorization rules below. The relation records evidence, not permission.
- An Action occurrence and its Effect occurrences preserve distinct identities
  and outcomes.

### Delegation and handoff

A **Delegation** is a definition that permits a delegating principal to
authorize a delegate principal to perform a bounded set of Actions on specified
Resources under stated conditions, lifetime, redelegation limits, and revocation
rules. A **delegation occurrence** records one establishment, use, revocation,
expiry, or rejection of that delegated authority. Delegation changes the
authority context. It does not transfer control-flow responsibility, ownership,
identity, or runtime capability.

A **Handoff** is a definition that permits one principal or control-flow step to
transfer responsibility for a bounded work item to another principal or step.
It declares the transferred context, acceptance condition, completion or return
condition, failure behavior, and whether separate delegation is required for
protected Actions. A **handoff occurrence** records the offer, acceptance or
rejection, and resulting responsibility. Handoff changes who is responsible for
continuing the work. It grants no authority by itself.

Invariants:

- Delegation identifies delegator, delegate, Actions, Resources, scope,
  validity, revocation behavior, and whether redelegation is allowed.
- Delegated authority cannot exceed the delegator's delegable authority and
  cannot outlive its authority source.
- Handoff identifies the initiating and receiving principals or steps, the work
  item, transferred context, acceptance outcome, and failure behavior.
- A receiving principal must obtain authorization independently for every
  protected Action. A Handoff can reference a Delegation but cannot replace it.
- Traces preserve the initiator, delegator when applicable, acting principal,
  and handoff chain without collapsing them into one identity.

### Policy

A **policy** is a definition of rules that permit, deny, require, or constrain an
action or information flow under stated conditions. Policy evaluation produces
a decision occurrence. A policy can require authorization evidence or
satisfaction of an approval requirement, but it is distinct from both.

A **policy application point** is a defined mediation point for a protected
Action. It identifies the Action and Resources it can mediate, the applicable
Policy and Authorization requirement, the evidence it supplies for a decision,
and the behavior for denial, indeterminate results, unavailable decision
mechanisms, and control failure.

Invariants:

- Every policy states its scope, target actions, conditions, and possible
  decisions.
- Every protected Action is mediated by at least one policy application point
  before any governed Effect.
- Deny and conflict behavior is explicit for every set of policies that can
  apply together.
- Policy application points precede the effects they govern.
- Instructions, roles, tools, and skills cannot bypass an applicable policy.

### Authorization requirement and decision

An **authorization requirement** is a definition of the evidence and decision
mechanism required at an application point. An **authorization decision** is an
occurrence stating whether an identified principal may perform a specified
action on a specified resource under the effective policy and context.

A decision is `evaluated against` exactly one Authorization requirement and is
`made at` exactly one Policy application point. That point requires the evaluated
requirement. The neutral `evaluated against` and `has authorization decision`
relations replace `satisfies` and `authorized by` for decision accounting so that
denial does not read as permission. A decision may exist before any Action
attempt; its existence does not create an Action occurrence. When an occurrence
exists, its `has authorization decision` associations retain every decision
used for its required checks, including
denied or indeterminate outcomes when the attempt boundary permits them.

For each required check, the evidence distinguishes:

- a permitted decision with the required evidence and matching scope;
- a denied decision, preserving the evaluated context and result;
- an indeterminate decision, including recorded incomplete evidence; and
- missing decision evidence, where no decision record is available for the
  check. Missing evidence proves neither permission nor denial. A record whose
  required contents are absent is incomplete evidence, not a valid permission.

These are distinctions for each check, not a new aggregate decision or a result
vocabulary for an authorization engine. A refusal or indeterminate result
retains the Action, Resource, Principal, Policy version, context, and time of
the evaluation even when it prevents an attempt.

An occurrence association identifies the relevant point or points, each of
which must require the decision's evaluated requirement. It preserves the
original decision and its originating point. Accounting for a decision at
another point or occurrence is allowed only when its scope and context remain
valid and the applicable binding or authorization contract permits that reuse.
Sharing an Authorization requirement is necessary but does not by itself
authorize reuse. This rule preserves bounded evidence reuse without treating
decisions as reusable definitions.

An **authority grant** is a definition of the bounded authority considered by
that mechanism. It identifies the principal, permitted actions, protected
resources, scope, lifetime, and delegation limits. It is neither a tool or skill
assignment nor an implementation feature claim.

Invariants:

- An authorization decision binds principal, action, resource, context, policy
  version, result, decision time, evaluated requirement, and originating Policy
  application point. Every occurrence association matches that scope and
  identifies the point or points where it accounts for a required check.
- Every required check needs a matching permitted decision and its required
  evidence before the governed Effect may proceed. A denied or indeterminate
  decision, incomplete evidence, or missing decision evidence cannot stand in
  for that permission. An observed Effect without those facts remains
  reportable as an occurrence; observation does not establish authorization.
- An authorization requirement identifies the authentication evidence,
  authority grants, Policy decisions, and Approval decisions required for the
  protected Action at its policy application point.
- A permission is not transferable unless policy defines delegation.
- Delegated authorization cannot exceed the delegating principal's delegable
  authority.
- An authorization decision occurs close enough to the effect to account for
  relevant state and policy changes.

### Approval requirement, request, and decision

An **approval requirement** is a definition of required approver qualifications,
presented information, allowed decisions, expiry, and the effect of no response.
An **approval request** is an occurrence that presents one bounded proposed
action for decision. An **approval decision** is an occurrence supplied by an
identified human principal in response to that request and may contribute to an
authorization decision.

Invariants:

- An approval request identifies the exact proposed action, relevant resource,
  requesting principal, and material context.
- An approval decision is valid only for its declared scope and lifetime.
- An approval decision for one action cannot be inferred as approval of later
  or broader actions.
- When an Authorization requirement requires human approval, no permitted
  Authorization decision is valid without a matching, unexpired Approval
  decision for the same Action, Resources, principal scope, and material
  context.
- The execution trace preserves the request and decision when the applicable
  trace requirement requires them, without requiring disclosure of protected
  rationale or credentials.

### Evaluation definition and result

An **evaluation definition** is a method that assesses a definition, runtime
instance, execution occurrence, immutable artifact, execution trace, or system
outcome against stated criteria. An **evaluation result** is an execution
occurrence containing observations, scores or judgments, and the identity and
category of the evaluated subject.

Invariants:

- An evaluation definition states its subject type, inputs, procedure, criteria,
  and result contract.
- An evaluation result identifies the evaluation definition version and the
  subject's definition version, runtime-instance identity, occurrence identity,
  or artifact integrity reference, as applicable.
- An evaluator's model, tools, data, or human judgment are declared when they
  affect reproducibility or interpretation.
- An evaluation result does not alter the evaluated subject.

### Trace requirement, execution trace, trace record, and trace artifact

A **trace requirement** is a definition of required event kinds, correlation,
retention, redaction, and access rules. An **execution trace** is an execution
occurrence aggregate containing an ordered or causally linked collection of
immutable **trace records** about one execution.

A trace record is immutable within the occurrence history. It becomes an
immutable artifact only when a sealing operation preserves it as fixed content.

A **trace artifact** is an immutable artifact that seals some or all of an
execution trace for exchange or retention. It identifies the source execution
trace and preserves its record identities. Exporting or filtering a trace does
not change the source occurrence.

Invariants:

- Each trace record has an identity, event kind, time or causal position, and
  attribution to a runtime principal or runtime component when known.
- Trace records preserve causal links across delegation, tool calls, message
  occurrences, approval decisions, state transitions, and policy decisions.
- Required authorization evidence preserves the Action occurrence association
  when an occurrence exists, the evaluated requirement, the originating point,
  and every point where the decision is accounted for. A trace distinguishes
  denied or indeterminate decisions from missing or withheld decision evidence.
  Pre-attempt decisions remain traceable without inventing an Action occurrence.
- Redaction is represented so a consumer can distinguish absent data from
  withheld data.
- Execution-trace immutability prevents silent alteration. Corrections append
  records or produce a new execution-trace version.

### Runtime

A **runtime** is a definition of execution capabilities that realize a system.
At deployment, a resolved binding may select it to realize portable definitions.
It schedules work, manages occurrences, and enforces declared application
points. A runtime instance is an execution participant with its own principal
identity.

Invariants:

- A runtime binding identifies each portable definition version it realizes.
- A runtime reports unsupported required capabilities before claiming it can
  execute the system.
- Runtime defaults cannot change portable meaning. Any added behavior is a
  declared configuration profile choice or extension.
- A runtime cannot claim policy enforcement for an application point it cannot
  mediate or verify.

### Deployment

A **deployment** is a definition that places a system and its runtime bindings
into one or more target environments. It states placement, scaling, lifecycle,
connectivity, and binding requirements without requiring a particular platform.
A **deployed instance** is a runtime instance established under the deployment,
not data created or observed during one execution.

Invariants:

- Every deployment resolves one system version, one or more runtime bindings,
  and at least one target environment.
- Each resolved binding identifies the portable binding requirement it
  satisfies and the selected runtime or environment element.
- Each required interface, secret reference, data resource, and external service
  has a deployment binding or an explicit unsatisfied requirement.
- Scaling preserves identity, state authority, and message-delivery semantics
  declared by the system.
- Deployment changes do not rewrite the referenced system definition.
- Every deployed instance identifies the deployment definition and the system,
  runtime, or component definition versions it realizes.

### Package

A **package version** is an immutable artifact containing definitions, other
artifacts, and dependency declarations. It provides a resolution boundary and a
reusable namespace. Its package metadata identifies the package identity and
artifact version. Packaging changes location and distribution, not entity
semantics.

Invariants:

- Package-version content does not change. A content change creates a new
  package version.
- Every exported definition has identity unique within the package version.
- Package dependencies declare compatible target versions and resolve without
  ambiguity.
- A package does not gain authority over a system merely because the system uses
  its definitions.

### Configuration profile

A **configuration profile** is a named set of constrained choices applied to a
base definition for a stated operational context. It can select among declared
options, supply bindings, or tighten constraints. It cannot remove base
requirements or change the kind of an entity.

A **conformance profile** is a separate concept defined by the conformance model.
It groups named conformance contracts and does not customize a base definition.
Neither profile kind can be used where the other is required. Whether a
configuration profile may require a conformance profile remains open.

Invariants:

- A configuration profile names exactly one base definition or configuration
  profile as its direct base.
- Configuration profile application order is explicit when several
  configuration profiles compose.
- The resolved result satisfies every constraint inherited from its base chain.
- A configuration profile cycle is invalid.

### Extension

An **extension** is a named, versioned addition whose semantics are outside the
current AgSDL core. It declares its owner, scope, target entity kinds, validation
rules, and effect on portability.

Invariants:

- Every extension is identifiable as non-core without understanding its payload.
- A consumer either understands an extension version or reports it as
  unsupported. It cannot silently ignore an extension marked as required.
- An extension cannot redefine a core term or weaken a core invariant.
- Extension data remains associated with its declared target through package,
  configuration profile, and deployment resolution.

## Relationship model

The first table defines relations among portable definitions. A target inverse
of `0..*` means that any number of sources may reuse the same target. Ownership
and containment impose tighter inverses where stated. These relations can be
resolved and validated without selecting a runtime or target environment.
Rows for a specific definition kind refine the generic lifecycle-ownership row;
they do not add a second owner.

| Source definition | Relation | Target definition or requirement | Targets per source | Sources per target |
| --- | --- | --- | --- | --- |
| System | owns | Definition | 0..* | 0..1 |
| System | owns | Agent | 0..* | 0..1 |
| System | uses | Agent | 1..* | 0..* |
| System | exposes | Interface | 1..* | 0..* |
| System | uses | Topology | 0..1 | 0..* |
| System | uses | Control flow | 0..* | 0..* |
| System | governed by | Policy | 0..* | 0..* |
| System | evaluated by | Evaluation definition | 0..* | 0..* |
| System | declares | Runtime binding requirement | 0..* | 1 |
| Fragment | owns | Definition | 0..* | 0..1 |
| Fragment | exports | Definition | 1..* | 0..* |
| Fragment | declares | Unresolved requirement | 0..* | 1 |
| Package version | contains | Fragment | 0..* | 0..1 |
| Agent | contains | Agent | 0..* | 0..1 |
| Agent | assigned | Role | 0..* | 0..* |
| Agent | uses | Model | 0..* | 0..* |
| Agent | directed by | Instructions | 0..* | 0..* |
| Agent | uses | Tool | 0..* | 0..* |
| Agent | assigned | Skill | 0..* | 0..* |
| Agent | uses | Memory | 0..* | 0..* |
| Agent | consults | Knowledge | 0..* | 0..* |
| Agent | uses | State definition | 0..* | 0..* |
| Agent | exposes | Interface | 1..* | 0..* |
| Agent | represented by | Identity | 1 | 1 |
| Agent | acts as | Principal definition | 1 | 0..* |
| Agent | governed by | Policy | 0..* | 0..* |
| Model | constrained by | Policy | 0..* | 0..* |
| Instructions | target | Agent, Model invocation, Skill, or Control-flow step | 1 | 0..* |
| Tool | requires | Tool binding requirement | 1..* | 1 |
| Tool | makes available | Action | 1..* | 0..* |
| Tool | governed by | Policy | 0..* | 0..* |
| Skill | composed from | Instructions, Tool, Knowledge, Control flow, or Skill | 1..* | 0..* |
| Memory | requires | Storage binding requirement | 1..* | 1 |
| Memory | governed by | Policy | 0..* | 0..* |
| Knowledge | accessed through | Tool or Interface | 1..* | 0..* |
| Knowledge | governed by | Policy | 0..* | 0..* |
| State definition | requires | State-management binding requirement | 1..* | 1 |
| Environment | contains | Environment element | 0..* | 0..1 |
| Principal definition | identified by | Identity | 1..* | 0..1 |
| Resource | governed or owned by | Principal definition or external authority source | 1 | 0..* |
| Trust boundary | separates | Trust domain | 2 | 0..* |
| Trust boundary | governs crossing through | Interface operation, Tool, or Action | 1..* | 0..* |
| Interface | contains | Interface operation | 1..* | 1 |
| Interface | governed by | Policy | 0..* | 0..* |
| Interface operation | participates in | Protocol | 0..1 | 0..* |
| Interface operation | makes available | Action | 1 | 0..* |
| Protocol | assigns participant | Role | 2..* | 0..* |
| Protocol | carried by | Interface | 1..* | 0..* |
| Topology | contains node for | Agent, System, Human participant, or Environment endpoint | 1..* | 0..* |
| Topology | contains directed edge through | Interface | 0..* | 0..* |
| Control flow | contains | Control-flow step | 1..* | 1 |
| Control-flow step | invokes | Agent, Tool, Skill, Evaluation definition, or Approval requirement | 0..1 | 0..* |
| Control-flow step | transitions to | Control-flow step | 0..* | 0..* |
| Control-flow step | may request | Action | 0..1 | 0..* |
| Control-flow step | may select through | Model-selected transition definition | 0..1 | 1 |
| Model-selected transition definition | allows | Control-flow step | 1..* | 0..* |
| Action | targets | Resource kind | 1..* | 0..* |
| Action | may produce | Effect | 0..* | 0..* |
| Protected Action | mediated by | Policy application point | 1..* | 1..* |
| Policy application point | applies | Policy | 1..* | 0..* |
| Policy application point | requires | Authorization requirement | 1 | 0..* |
| Delegation | permits | Action on Resource | 1..* | 0..* |
| Handoff | transfers responsibility for | Work item | 1 | 0..* |
| Handoff | may require | Delegation | 0..* | 0..* |
| Policy | applies to | Definition, binding requirement, message occurrence kind, or application point | 1..* | 0..* |
| Authorization requirement | applies | Policy | 1..* | 0..* |
| Authorization requirement | considers | Authority grant | 0..* | 0..* |
| Authorization requirement | may require | Approval requirement | 0..* | 0..* |
| Evaluation definition | evaluates | Definition, runtime instance kind, execution occurrence kind, immutable artifact kind, execution trace, or system outcome | 1..* | 0..* |
| Trace requirement | describes observation of | System | 1 | 0..* |
| Package version | owns | Definition | 0..* | 0..1 |
| Package version | exports | Definition | 1..* | 0..* |
| Package version | contains | Definition or immutable artifact | 1..* | 0..1 |
| Package version | depends on | Package version | 0..* | 0..* |
| Configuration profile | based on | Definition or Configuration profile | 1 | 0..* |
| Extension | targets | Core entity definition | 1..* | 0..* |

Deployment relations select implementations but remain separate from portable
meaning:

| Source | Relation | Target | Targets per source | Sources per target |
| --- | --- | --- | --- | --- |
| System | deployed by | Deployment | 0..* | 1 |
| Deployment | deploys | System | 1 | 0..* |
| Deployment | binds | Runtime | 1..* | 0..* |
| Deployment | targets | Environment | 1..* | 0..* |
| Deployment | supplies | Resolved binding | 1..* | 1 |
| Resolved binding | satisfies | Binding requirement | 1 | 0..* |
| Resolved binding | selects | Runtime or Environment element | 1 | 0..* |
| Runtime | realizes | System or component definition | 1..* | 0..* |
| Runtime | operates in | Environment | 1..* | 0..* |
| Deployment | establishes | Runtime instance | 1..* | 1 |
| Runtime instance | realizes | Runtime, System, or component definition | 1..* | 0..* |

Execution and evidence relations describe runtime subjects and preserved
evidence. They do not make their sources reusable definitions:

| Source subject | Relation | Target | Targets per source | Sources per target |
| --- | --- | --- | --- | --- |
| Message occurrence | sent by | Principal identity | 1 | 0..* |
| Message occurrence | addressed to | Principal identity or broadcast scope | 1..* | 0..* |
| Message occurrence | conforms to | Interface operation | 1 | 0..* |
| Message occurrence | follows | Protocol | 0..1 | 0..* |
| Message occurrence | replies to or correlates with | Message occurrence | 0..* | 0..* |
| State occurrence | conforms to | State definition | 1 | 0..* |
| Authentication evidence | supports identity claim for | Principal identity | 1 | 0..* |
| Action occurrence | instantiates | Action | 1 | 0..* |
| Action occurrence | performed by | Acting Principal identity | 1 | 0..* |
| Action occurrence | initiated by | Principal identity | 0..1 | 0..* |
| Action occurrence | targets | Resource | 1..* | 0..* |
| Action occurrence | has authorization decision | Authorization decision | 0..* | 0..* |
| Effect occurrence | caused by | Action occurrence or external event | 1 | 0..* |
| Effect occurrence | instantiates | Effect | 0..1 | 0..* |
| Delegation occurrence | governed by | Delegation | 1 | 0..* |
| Delegation occurrence | delegates from and to | Principal identity | 2 | 0..* |
| Handoff occurrence | governed by | Handoff | 1 | 0..* |
| Handoff occurrence | transfers from and to | Principal identity or Control-flow step | 2 | 0..* |
| Authorization decision | evaluates for | Principal identity | 1 | 0..* |
| Authorization decision | applies | Policy | 1..* | 0..* |
| Authorization decision | evaluated against | Authorization requirement | 1 | 0..* |
| Authorization decision | made at | Policy application point | 1 | 0..* |
| Authorization decision | considers | Authentication evidence | 0..* | 0..* |
| Approval request | satisfies | Approval requirement | 1 | 0..* |
| Approval request | requested by | Principal identity | 1 | 0..* |
| Approval decision | responds to | Approval request | 1 | 0..1 |
| Approval decision | supplied by | Human principal identity | 1 | 0..* |
| Approval decision | contributes to | Authorization decision | 0..1 | 0..* |
| Evaluation result | produced under | Evaluation definition | 1 | 0..* |
| Evaluation result | evaluates | Definition, runtime instance, execution occurrence, immutable artifact, execution trace, or system outcome | 1..* | 0..* |
| Transition selection observation | produced under | Model-selected transition definition | 1 | 0..* |
| Transition selection observation | selects | Control-flow step | 0..1 | 0..* |
| Execution trace | satisfies | Trace requirement | 0..* | 0..* |
| Execution trace | records | Trace record | 0..* | 1 |
| Execution trace | describes execution of | System | 1 | 0..* |
| Trace artifact | seals | Execution trace | 1 | 0..* |

The `has authorization decision` associations carry the relevant application
point or points described in the authorization section. Their `0..*` minimum
allows unprotected occurrences and honest records of missing evidence. It does
not waive required checks for protected Effects. The `0..*` inverse permits
bounded reuse; it does not make a decision globally valid.

An `Environment element`, `Human participant`, `Control-flow step`, `Interface
operation`, `Policy application point`, `Trust domain`, `Resource kind`, `Work
item`, `Model invocation`, `System outcome`, binding requirement, unresolved
requirement, and resolved binding are subordinate records rather than additional
top-level entity kinds. Each subordinate record has identity within its owning
definition, runtime instance, execution occurrence, or immutable artifact.

## Recursion, reuse, references, and cycles

### Recursive composition

Two forms of recursion are part of the model:

- An agent may contain agents. The result is a hierarchy of responsibility and
  addressing.
- A skill may compose skills, and a protocol may invoke a nested protocol. The
  result is reusable behavior.

Recursive definitions must resolve to a finite graph. Runtime recursion within
that graph is valid only when its control definition declares how it returns,
terminates, or remains intentionally active. No recursion grants permissions
across a boundary.

### Reuse

Agents, roles, models, instructions, tools, skills, memory, knowledge, protocols,
policies, evaluation definitions, runtime definitions, and extensions are
reusable definitions. Reuse creates another directed `uses`, `assigned`, or
equivalent relation to the same identified definition. It does not clone the
definition.

State occurrences, message occurrences, authentication evidence, Action and
Effect occurrences, Delegation and Handoff occurrences, approval requests,
approval decisions, authorization decisions, execution traces, trace records,
and evaluation results are not reusable definitions. A later occurrence may
reference them as evidence or history, but it cannot treat them as mutable
shared templates.

### Reference resolution

Resolution starts at the declared System, Fragment, or Package version root,
applies configuration profiles in their declared order, loads package
dependencies, and resolves every required reference to one target. Resolution
of a Fragment or Package version checks its exports, dependencies, and
unresolved requirements without constructing a synthetic System.
The resolved graph records the exact definition versions selected. Runtime
bindings happen after conceptual resolution and cannot repair an ambiguous or
kind-invalid reference.

References can be local to a system or package, imported from a dependency, or
supplied by a deployment binding. A deployment binding may satisfy a declared
external requirement. It cannot replace a locally resolved definition with a
different kind or incompatible version.

### Cycle rules

Cycles are classified rather than rejected as one category:

| Cycle kind | Rule |
| --- | --- |
| Ownership or containment | Invalid. An entity cannot own or contain itself, directly or indirectly. |
| Package dependency | Invalid for the initial model. Resolution order must be acyclic. |
| Configuration profile base | Invalid. Configuration profile constraints require a finite ordered base chain. |
| Static use or reference | Valid if every reference resolves and no entity's definition depends on infinite expansion. |
| Topology | Valid when policy permits the edges and the associated behavior defines progress or an intentional long-lived loop. |
| Control flow or protocol | Valid only with a termination condition, finite bound, or explicit long-lived-loop declaration. |
| Delegation authority | Invalid when authority depends on a cycle. Every delegated grant traces to a non-delegated authority source. |
| Handoff responsibility | Valid only when the associated control flow defines return, termination, or an intentional long-lived loop. |
| Message correlation | Valid only for non-causal grouping. Reply and causal relations must remain acyclic. |
| Trace causality | Invalid. Causal order must form a directed acyclic graph even if recorded interactions loop. |

## Cross-cutting invariants

The resolved model obeys these invariants in addition to each entity's local
invariants:

1. Every required reference resolves to exactly one target of the expected kind.
2. Every definition, runtime instance, execution occurrence, and artifact
   identity is unique within its declared scope.
3. Ownership and containment graphs are acyclic. Each local definition has
   exactly one lifecycle owner, and each imported definition keeps the owner
   declared by its source. A complete System has at least one participating
   Agent through `uses`, independently of how many definitions it owns locally.
4. Every boundary-crossing interaction uses a declared interface and direction.
5. Every Action identifies its permitted acting Principal kinds or identities
   and target Resource kinds. Every Action occurrence identifies its acting
   Principal identity and target Resources. Every Effect is attributable to an
   Action occurrence or identified external event.
6. Every protected Action passes through its policy application points before
   any governed Effect is permitted. Each point applies its declared Policy.
   Each required check obtains a matching
   permitted Authorization decision and the authentication evidence and human
   Approval decision required for that Action and context. When an Action
   occurrence exists, direct decision associations preserve every evaluated
   requirement and relevant point. Denial, indeterminate results, incomplete
   evidence, and missing evidence remain distinct; none supplies permission.
   A decision for one requirement cannot satisfy another requirement. Reuse
   follows the scope, context, and binding limits in the authorization section.
7. Reuse preserves definition identity. Customization uses a configuration
   profile, a new definition, or an extension rather than mutating an imported
   definition.
8. Runtime instances, execution occurrences, and immutable artifacts identify
   the applicable definition versions when needed to interpret, audit, or
   reproduce them.
9. Core validation is independent of provider, framework, transport, runtime,
   deployment platform, and extension payload semantics.
10. A required extension that a consumer does not understand prevents a claim of
    full portable interpretation.
11. A complete system document and a reusable fragment document are distinct
    root forms. Validation never supplies a synthetic System for a Fragment or
    Package version root.
12. Delegation changes bounded authority and Handoff changes bounded work
    responsibility. Neither relation implies the other.

## Requirements traceability

This proposal covers the requirements that shape the conceptual model as
follows. Coverage here means that the model has a responsible entity, relation,
or invariant. It does not claim that later syntax, processing, or conformance
work is complete.

| Requirements | Conceptual coverage |
| --- | --- |
| REQ-001, REQ-002 | System, Fragment, Package version, Principal, Identity, references, lifecycle ownership, interfaces, and governing-control relations expose the principal facts for inspection and stable addressing. |
| REQ-003 | System, Agent, Interface, runtime binding requirements, Trace requirement, and Evaluation definition can describe a complete single-agent system. Topology is optional. |
| REQ-004 | Topology, Protocol, Control flow, Delegation, Handoff, shared reusable definitions, ownership, and Policy relations cover the core multi-agent structure. Explicit routing remains to be defined. |
| REQ-010, REQ-011, REQ-016, REQ-017 | System and Fragment or Package version roots, Configuration profile, Reference, identity scopes, dependency relations, unresolved requirements, and deterministic reference-resolution invariants cover composition and controlled resolution without a synthetic System. System participation is independent of source lifecycle ownership and permits exclusively imported Agents. Missing obligations follow proposal 0003's phase rules and require explicit permission to defer. |
| REQ-018 through REQ-020 | Extension identity, required-extension failure behavior, and preservation through package, configuration profile, and deployment resolution cover extension boundaries. Portable fallback still needs precise processing rules. |
| REQ-021 through REQ-026 | Principal, Identity, authentication evidence, Resource, Trust boundary, Action, Effect, Policy application point, Policy, Authorization requirement and decision, Approval requirement, request, and decision, Delegation, Handoff, Environment, Tool, and Interface represent protected actions, secret references, supervision, and trust crossings. Multiple decisions for one occurrence retain each evaluated requirement, relevant point, context, and result without implying that denial or missing evidence grants permission. Review, override, interruption, and escalation vocabularies remain to be defined. |
| REQ-027 through REQ-031 | Trace requirement, execution trace, trace record, Evaluation definition, and Evaluation result preserve observable identity and definition-result separation. Metric definitions, probabilistic targets, and conformance claims remain to be defined. |
| REQ-032 through REQ-035 | Binding requirements, resolved bindings, Runtime, Deployment, Environment, and the binding-separation rules distinguish portable needs from selected implementations and visible capability gaps. Target-assessment report behavior remains to be defined. |

REQ-005 through REQ-009, REQ-012 through REQ-015, and REQ-036 through REQ-038
mainly govern syntax, processor reports, version compatibility, exchange, and
framework adapters. Their detailed rules are outside this core entity model and
remain open for later proposals or normative text.

## Consequences

This model gives later specification work a stable separation between behavior,
authority, execution, and observation. It supports simple single-agent systems
without requiring every optional entity. It also scales to composite agents,
multi-agent protocols, human gates, and deployment-specific bindings.

The model has more named entities than framework configurations usually expose.
That cost is intentional. Combining role with authorization, memory with state,
or topology with control flow would make important portable differences
implicit. A future serialization may offer concise forms, but those forms must
expand to the same conceptual relations.

The relationship table is a conceptual constraint set, not a schema. Later work
must decide which relations are written directly, inferred from containment, or
represented through intermediate records.

### Syntax-free boundary examples

Consider a travel-planning system with a planner agent and a booking agent. The
planner's `request booking` operation is an interface fact. A request, tentative
offer, acceptance, and final confirmation form a protocol fact. A directed path
from the planner to the booking agent through that interface is a topology fact.
A control-flow step that invokes the planner, then permits a booking invocation
after approval, is a control-flow fact. None of these facts implies the other
three.

A one-agent summarization system may expose one `submit document` interface
operation and use a control flow that invokes its sole agent and then returns
the result. It needs no participant protocol when the interaction is a single
operation, and no topology when there is no static inter-participant path to
declare.

The [composition and authorization example](../examples/conceptual/composition-and-authorization.md)
uses two imported Agents in one System and retains two distinct authorization
checks for one export Action occurrence, including refusal and missing-evidence
variants. It also identifies the remaining identity and phase-contract limits.

## Alternatives considered

### Treat every component as a generic resource

A single resource entity with typed properties would make the core smaller. It
would also move responsibilities and invariants into type-specific conventions,
which recreates the ambiguity this proposal is meant to remove.

### Treat agents as workflow nodes

This fits graph-oriented frameworks but loses the distinction between a
decision-making participant and a scheduled invocation of that participant. The
proposal keeps agents in the topology and puts invocations in control-flow
steps.

### Combine memory, knowledge, and state

All three hold information, but their responsibilities differ. State affects
later execution, memory retains information under update and retention rules,
and knowledge identifies evidence sources. One storage system may implement all
three without collapsing their portable meaning.

### Combine policy, authorization, and approval

A policy is a rule definition, an authorization requirement defines a decision
point, and an authorization decision records its outcome. An approval
requirement defines a human gate; its request and decision are occurrences.
Separating them preserves who decided what, under which rule, and for how long.

### Model only static definitions

Static definitions alone cannot express deployed identity, correlation,
traceability, state transitions, approval scope, durable artifacts, or
evaluation subjects. This proposal separates definitions, runtime instances,
execution occurrences, and immutable artifacts while leaving event syntax and
storage to later work.

## Security considerations

The model separates availability from authority. A visible tool, interface,
skill, memory, or knowledge source does not become usable until policy and an
authorization decision permit the action. An approval decision is bounded to an
action and context. Delegation preserves both initiator and actor identity.

Secrets remain external values referenced through environment and deployment
bindings. Trace requirements include attribution, causal links, redaction, and
correction behavior so audit data does not silently omit or rewrite security
events. A runtime can claim enforcement only for application points it mediates
or verifies.

Composite agents and recursive skills create no implicit trust inheritance.
Each boundary and effect retains its own applicable policies. Required
extensions fail closed when a consumer cannot interpret their semantics.

## Compatibility impact

AgSDL has no published syntax or compatibility promise, so this proposal breaks
no existing conforming document. If accepted, later terminology, schemas, and
conformance rules should use these entity names and preserve the four subject
categories.

Framework adapters may map several conceptual entities to one framework object,
or one conceptual entity to several implementation objects. Such a mapping is
compatible when it preserves the declared relationships, invariants, and
observable behavior. A framework default has no portable meaning unless an
adapter represents it as a definition, configuration profile choice, or
extension.

## Reconciled directions

[Decision 0004](../docs/decisions/0004-approved-design-directions.md) resolves
the direction of these earlier design questions:

- A complete System may use exclusively imported Agents as participants. The
  proposed `System uses Agent` minimum preserves the need for an Agent while
  both generic and Agent-specific ownership minima allow zero local ownership.
- One Action occurrence may directly retain several Authorization decisions.
  The proposed neutral relation names and point accounting keep each required
  check visible, without an aggregate decision or implied permission on denial.
- Incomplete fragments use proposal 0003's two validation phases. Only an
  explicitly permitted and declared deferral can postpone an obligation.

The approved directions do not adopt these detailed relations or determine
the remaining contract choices below.

## Open questions

1. Must a System declare a governing Principal in addition to the lifecycle
   ownership of its local definitions, or can system governance ownership remain
   project metadata in the first draft?
2. Does the first draft need a first-class goal entity, or are system purpose,
   control-flow completion conditions, and evaluation criteria sufficient?
3. Should credentials references become a named core entity, or remain
   subordinate environment and deployment records?
4. Which relations can a serialization infer without reducing agreement between
   independent implementations?
5. Should package dependency cycles remain forbidden if a later resolver can
   prove finite symbol resolution?
6. What minimum trace event set is required for a portable conformance claim?
7. Which additional runtime instance, execution occurrence, and immutable
   artifact kinds belong in the core specification rather than a later
   observability proposal?
8. How should a definition express capability compatibility without importing
   provider-specific model and tool taxonomies?
9. Which extension effects must always be marked required because ignoring them
    could change security, control flow, or externally visible behavior?
10. What core term, if any, should name an externally advertised service, and
    how should it relate to an interface operation or packaged skill without
    equating discovery, assignment, authority, and implementation support?
11. May a configuration profile require a conformance profile, and if so, does
    that reference constrain deployment resolution without changing the base
    definition's portable meaning?
12. Which entities may act as the selection authority for a model-selected
    transition, and what minimum observation evidence supports audit without
    requiring disclosure of protected model inputs or reasoning?
13. Which authentication mechanisms and evidence formats belong in optional
    profiles rather than the core, while preserving the core distinction among
    Principal, Identity, and authentication evidence?
14. Which Effect categories need standardized names for portable risk analysis?
15. What does `Agent represented by Identity` identify, and what cardinalities
    should that relation have in the first external contract? Its interpretation
    is resolved for 0.1.0 by Decision 0007 as recorded above. Broader conceptual
    identity design remains open; definition and Principal identity stay distinct.
16. Which exact obligations may a future contract defer during unresolved-document
    validation, and which declarations prove that permission? Proposal 0003
    governs the phases; this proposal adds no general deferral inventory.
17. How should the first contract represent and preserve the proposed neutral
    decision associations and their application-point context? This proposal
    defines conceptual accounting only, without syntax or result aggregation.
