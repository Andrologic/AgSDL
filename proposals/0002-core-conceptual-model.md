# Proposal 0002: core conceptual model

- Status: proposed
- Date: 2026-09-02

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

### Cardinality notation

`A --relation--> B [x..y]` means that one `A` has from `x` through `y` outgoing
relations of that kind to `B`. `*` means no fixed upper bound. Each relation
table also states the inverse cardinality from one target back to its sources.

## Core entities

### System

A **system** is the definition of one agentic application boundary. It declares
the system's purpose, owned components, exposed interfaces, governing policies,
optional topology, control flow, and execution requirements. It is the root used
to resolve and validate a complete description.

The system owns definitions that are local to it and uses definitions supplied
by packages. It does not own runtime instances or execution occurrences.

Invariants:

- A resolved description has exactly one root system.
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
- Every externally visible effect is attributable to a tool invocation or an
  interface operation.
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

### Identity

An **identity** is a stable identifier for a definition, runtime principal, or
occurrence within a declared scope. For a runtime principal, identity also names
the subject to which authorization decisions and trace attribution apply.

Invariants:

- Identity uniqueness is enforced within its declared scope.
- Definition identity and runtime principal identity are distinct even when they
  share a label.
- Delegation preserves the initiating and acting principal identities in the
  authorization record and trace.
- Authentication evidence binds a runtime principal to an identity but is not
  itself the identity.

### Interface

An **interface** is a definition of operations or message exchanges available at
an agent or system boundary. It declares direction, input and output contracts,
interaction mode, and failure behavior without prescribing a transport.

Invariants:

- Every interface operation has a declared inbound, outbound, or bidirectional
  direction relative to its owner.
- Messages crossing a boundary conform to an operation declared by that
  boundary's interface.
- Transport bindings cannot change the portable operation contract.
- Exposing an interface does not grant callers authorization to use it.

### Message occurrence

A **message occurrence** is information sent from one identified endpoint
to one or more identified endpoints through an interface according to a
protocol. Its envelope records sender, intended recipient, protocol position,
and correlation identity. Its content conforms to the selected interface
operation.

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

### Policy

A **policy** is a definition of rules that permit, deny, require, or constrain an
action or information flow under stated conditions. Policy evaluation produces
a decision occurrence. A policy can require authorization evidence or
satisfaction of an approval requirement, but it is distinct from both.

Invariants:

- Every policy states its scope, target actions, conditions, and possible
  decisions.
- Deny and conflict behavior is explicit for every set of policies that can
  apply together.
- Policy application points precede the effects they govern.
- Instructions, roles, tools, and skills cannot bypass an applicable policy.

### Authorization requirement and decision

An **authorization requirement** is a definition of the evidence and decision
mechanism required at an application point. An **authorization decision** is an
occurrence stating whether an identified principal may perform a specified
action on a specified resource under the effective policy and context.

An **authority grant** is a definition of the bounded authority considered by
that mechanism. It identifies the principal, permitted actions, protected
resources, scope, lifetime, and delegation limits. It is neither a tool or skill
assignment nor an implementation feature claim.

Invariants:

- An authorization decision binds principal, action, resource, context, policy
  version, result, and decision time.
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

| Source definition | Relation | Target definition or requirement | Targets per source | Sources per target |
| --- | --- | --- | --- | --- |
| System | owns | Agent | 1..* | 0..1 |
| System | exposes | Interface | 1..* | 0..* |
| System | uses | Topology | 0..1 | 0..* |
| System | uses | Control flow | 0..* | 0..* |
| System | governed by | Policy | 0..* | 0..* |
| System | evaluated by | Evaluation definition | 0..* | 0..* |
| System | declares | Runtime binding requirement | 0..* | 1 |
| Agent | contains | Agent | 0..* | 0..1 |
| Agent | assigned | Role | 0..* | 0..* |
| Agent | uses | Model | 0..* | 0..* |
| Agent | directed by | Instructions | 0..* | 0..* |
| Agent | uses | Tool | 0..* | 0..* |
| Agent | assigned | Skill | 0..* | 0..* |
| Agent | uses | Memory | 0..* | 0..* |
| Agent | consults | Knowledge | 0..* | 0..* |
| Agent | owns | State definition | 0..* | 0..1 |
| Agent | exposes | Interface | 1..* | 0..* |
| Agent | represented by | Definition identity | 1 | 1 |
| Agent | governed by | Policy | 0..* | 0..* |
| Model | constrained by | Policy | 0..* | 0..* |
| Instructions | target | Agent, Model invocation, Skill, or Control-flow step | 1 | 0..* |
| Tool | requires | Tool binding requirement | 1..* | 1 |
| Tool | governed by | Policy | 0..* | 0..* |
| Skill | composed from | Instructions, Tool, Knowledge, Control flow, or Skill | 1..* | 0..* |
| Memory | requires | Storage binding requirement | 1..* | 1 |
| Memory | governed by | Policy | 0..* | 0..* |
| Knowledge | accessed through | Tool or Interface | 1..* | 0..* |
| Knowledge | governed by | Policy | 0..* | 0..* |
| State definition | requires | State-management binding requirement | 1..* | 1 |
| Environment | contains | Environment element | 0..* | 0..1 |
| Interface | uses | Protocol | 0..1 | 0..* |
| Interface | governed by | Policy | 0..* | 0..* |
| Protocol | assigns participant | Role | 2..* | 0..* |
| Protocol | carried by | Interface | 1..* | 0..1 |
| Topology | contains node for | Agent, System, Human participant, or Environment endpoint | 1..* | 0..* |
| Topology | contains directed edge through | Interface | 0..* | 0..* |
| Control flow | contains | Control-flow step | 1..* | 1 |
| Control-flow step | invokes | Agent, Tool, Skill, Evaluation definition, or Approval requirement | 0..1 | 0..* |
| Control-flow step | transitions to | Control-flow step | 0..* | 0..* |
| Control-flow step | may select through | Model-selected transition definition | 0..1 | 1 |
| Model-selected transition definition | allows | Control-flow step | 1..* | 0..* |
| Policy | applies to | Definition, binding requirement, message occurrence kind, or application point | 1..* | 0..* |
| Authorization requirement | applies | Policy | 1..* | 0..* |
| Authorization requirement | considers | Authority grant | 0..* | 0..* |
| Authorization requirement | may require | Approval requirement | 0..* | 0..* |
| Evaluation definition | evaluates | Definition, runtime instance kind, execution occurrence kind, immutable artifact kind, execution trace, or system outcome | 1..* | 0..* |
| Trace requirement | describes observation of | System | 1 | 0..* |
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
| Message occurrence | sent by | Runtime principal identity | 1 | 0..* |
| Message occurrence | addressed to | Runtime principal identity or broadcast scope | 1..* | 0..* |
| Message occurrence | passes through | Interface | 1 | 0..* |
| Message occurrence | follows | Protocol | 0..1 | 0..* |
| Message occurrence | replies to or correlates with | Message occurrence | 0..* | 0..* |
| State occurrence | conforms to | State definition | 1 | 0..* |
| Authorization decision | evaluates for | Runtime principal identity | 1 | 0..* |
| Authorization decision | applies | Policy | 1..* | 0..* |
| Authorization decision | satisfies | Authorization requirement | 1 | 0..* |
| Approval request | satisfies | Approval requirement | 1 | 0..* |
| Approval request | requested by | Runtime principal identity | 1 | 0..* |
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

An `Environment element`, `Human participant`, `Control-flow step`, `Model
invocation`, `System outcome`, binding requirement, and resolved binding are
subordinate records rather than additional top-level entity kinds. Each
subordinate record has identity within its owning definition, runtime instance,
execution occurrence, or immutable artifact.

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

Roles, models, instructions, tools, skills, memory, knowledge, protocols,
policies, evaluation definitions, runtime definitions, and extensions are
reusable definitions. Reuse creates another directed `uses`, `assigned`, or
equivalent relation to the same identified definition. It does not clone the
definition.

State occurrences, message occurrences, approval requests, approval decisions,
authorization decisions, execution traces, trace records, and evaluation
results are not reusable definitions. A later occurrence may reference them as
evidence or history, but it cannot treat them as mutable shared templates.

### Reference resolution

Resolution starts at the root system, applies configuration profiles in their
declared order, loads package dependencies, and resolves every required
reference to one target.
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
| Message correlation | Valid only for non-causal grouping. Reply and causal relations must remain acyclic. |
| Trace causality | Invalid. Causal order must form a directed acyclic graph even if recorded interactions loop. |

## Cross-cutting invariants

The resolved model obeys these invariants in addition to each entity's local
invariants:

1. Every required reference resolves to exactly one target of the expected kind.
2. Every definition, runtime instance, execution occurrence, and artifact
   identity is unique within its declared scope.
3. Ownership and containment graphs are acyclic, and each owned entity has at
   most one owner in one resolved system.
4. Every boundary-crossing interaction uses a declared interface and direction.
5. Every effect is attributable to an agent, human principal, runtime principal,
   or external event.
6. Every governed effect passes through the policy application points and
   produces the authorization and approval occurrences required at that effect.
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

## Requirements traceability

This proposal covers the requirements that shape the conceptual model as
follows. Coverage here means that the model has a responsible entity, relation,
or invariant. It does not claim that later syntax, processing, or conformance
work is complete.

| Requirements | Conceptual coverage |
| --- | --- |
| REQ-001, REQ-002 | System, component identities, references, ownership, interfaces, and governing-control relations expose the principal facts for inspection and stable addressing. |
| REQ-003 | System, Agent, Interface, runtime binding requirements, Trace requirement, and Evaluation definition can describe a complete single-agent system. Topology is optional. |
| REQ-004 | Topology, Protocol, Control flow, shared reusable definitions, ownership, and policy relations cover the core multi-agent structure. Explicit routing, delegation, and handoff definitions remain to be defined. |
| REQ-010, REQ-011, REQ-016, REQ-017 | Package version, Configuration profile, Reference, identity scopes, dependency relations, and deterministic reference-resolution invariants cover composition and controlled resolution. |
| REQ-018 through REQ-020 | Extension identity, required-extension failure behavior, and preservation through package, configuration profile, and deployment resolution cover extension boundaries. Portable fallback still needs precise processing rules. |
| REQ-021 through REQ-026 | Identity, Environment, Policy, Authorization requirement and decision, Approval requirement, request, and decision, Tool, Interface, and boundary invariants represent principals, protected actions, secret references, supervision, and trust crossings. Review, override, interruption, escalation, and failure-policy vocabularies remain to be defined. |
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

## Open questions

1. Should a system require a declared owner identity, or can ownership remain
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
7. Which runtime instance, execution occurrence, and immutable artifact kinds
   belong in the core specification rather than a later observability proposal?
8. Can policy conflict resolution have one portable default, or must every
   applicable policy set declare it?
9. How should a definition express capability compatibility without importing
   provider-specific model and tool taxonomies?
10. Which extension effects must always be marked required because ignoring them
    could change security, control flow, or externally visible behavior?
11. What core term, if any, should name an externally advertised service, and
    how should it relate to an interface operation or packaged skill without
    equating discovery, assignment, authority, and implementation support?
12. May a configuration profile require a conformance profile, and if so, does
    that reference constrain deployment resolution without changing the base
    definition's portable meaning?
13. Which entities may act as the selection authority for a model-selected
    transition, and what minimum observation evidence supports audit without
    requiring disclosure of protected model inputs or reasoning?
