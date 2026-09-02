# Proposal 0005: A2UI external format binding

- Status: proposed
- Date: 2026-09-02
- Depends on: proposals 0002, 0003, and 0004
- Research basis: `docs/research/a2ui.md`

## Problem

Agents can generate declarative interfaces whose structure and data change
during an execution. AgSDL needs to describe that external capability without
adding a graphical editor contract to the core, copying A2UI schemas, or
presenting one renderer's behavior as portable AgSDL meaning.

A shallow mapping would call an A2UI surface an AgSDL interface and an A2UI
action an AgSDL Action. That loses important distinctions. The surface is
mutable presentation state, the A2UI action is a user-interaction message, and
the renderer can execute local functions or request remote functions. Catalog
support restricts implementation vocabulary but grants no authority. Transport
metadata can also return the full UI data model to an agent.

This proposal defines the information an eventual AgSDL binding would preserve
and the claims it must refuse to make.

## Scope

This proposal covers an external A2UI format binding for:

- protocol and artifact version identity;
- agent and renderer roles;
- surface lifecycle and component catalogs;
- component and data-model updates;
- user actions, renderer errors, and candidate function calls;
- transport requirements and transport-specific bindings;
- trust boundaries, protected Effects, and conformance evidence.

It does not:

- add surface, component, catalog, or renderer as core AgSDL entities;
- select AgSDL serialization or field names;
- reproduce A2UI JSON schemas or component catalogs;
- define visual appearance, accessibility sufficiency, or user-interface
  quality;
- standardize A2A, AG-UI, MCP, SSE, WebSockets, or REST;
- claim that AgSDL can parse, generate, render, or round-trip A2UI;
- make the A2UI `v1.0` candidate stable;
- treat structural validation as authorization or behavioral conformance.

## Proposed terms

An **A2UI format binding** is a proposed external-format mapping between one
identified A2UI protocol edition and the AgSDL definitions and occurrences that
give its use portable system meaning. It is neither an AgSDL Configuration
profile nor an AgSDL Conformance profile.

An **A2UI transport binding** is a separately identified mapping that carries
A2UI envelopes over one transport. It states framing, ordering, metadata,
correlation, identity, security, failure, and return-channel behavior. Selecting
an A2UI format binding does not select a transport binding.

An **A2UI mapping record** is adapter evidence for one conversion or inspected
external dependency. It identifies the source and target artifacts, versions,
mapping rules, preserved information, losses, diagnostics, and test evidence.
The record is not itself proof of runtime behavior.

These terms remain proposal-local until accepted into the specification.

## Proposed representation

### Binding identity

An A2UI format binding should identify:

- the exact A2UI protocol version advertised on the wire;
- whether that version is stable, candidate, legacy, or another upstream
  status at the time the binding is published;
- the immutable commit, digest, or release identity of the protocol prose,
  envelope schemas, catalog schemas, and extension documents used;
- the precedence among pinned prose, schemas, examples, and implementation
  behavior, plus every known conflict that changes accepted messages;
- the accepted version spelling and schema identity at every envelope,
  capability, metadata, and catalog location;
- supported directions and message kinds;
- supported catalog identities and immutable artifact identities;
- assumptions and unsupported A2UI features;
- the mapping-rule version and its conformance evidence.

A mutable URL, catalog identifier, media type, or version string alone is not
an immutable external component identity. A candidate binding must retain the
candidate status. A binding for one A2UI version cannot silently accept another
version because an upstream schema happens to accept both envelope values.

### Role mapping

Each A2UI agent, server, renderer, or client role maps to an identified endpoint
Principal. When an identified Deployment and Runtime definition establish the
endpoint, the mapping may also name the runtime instance that realizes it.
Otherwise the endpoint remains an external Environment element or external
endpoint. An A2UI agent or server maps to an AgSDL Agent definition only when
the system definition explicitly relates that endpoint to the Agent. No A2UI
role is assumed to be human, trusted, local, or inside the System boundary.

The binding should name the Interface exposed in each direction and the
Principal Identity expected at each endpoint. Authentication evidence and
Authority grants remain separate. A role name in an A2UI envelope or transport
binding supplies neither.

### Surface and state mapping

An active A2UI surface maps to:

- a runtime Resource whose lifecycle can be governed;
- a succession of State occurrences for its changing component graph and data
  model, governed by one or more State definitions that keep those parts
  distinguishable;
- the renderer endpoint Principal that is the declared authority for resolving
  concurrent writes and identifies the current State occurrences, plus its
  runtime instance when an identified Deployment establishes one;
- the agent or server endpoint allowed to request updates;
- a correlation scope that prevents updates from crossing executions, users,
  tenants, or renderer sessions.

Each State definition should declare allowed fields, lifetime, writer roles,
concurrent-write authority, deletion behavior, and trace requirements. Surface
creation, update, and deletion are state transitions that produce new State
occurrences. Deletion ends the active surface state but does not erase retained
state history or trace records by implication. Reuse of a deleted identifier in
`v0.9.1` creates a new surface Resource identity and must not merge history or
authorization with the deleted surface. The `v1.0` candidate's renderer-session
uniqueness rule is a different constraint and remains version-specific.

### Catalog mapping

Each selected catalog maps to a Referenced component with an external governing
authority. The binding should record:

- catalog identifier as advertised by A2UI;
- immutable content identity and resolution evidence when reproducibility is
  claimed;
- protocol version and catalog-schema version;
- accepted component and function names;
- renderer implementation and version that realizes them;
- whether the agent or server accepts client-supplied inline catalogs, which
  renderer Principals may supply them, and under which provenance policy;
- unsupported properties, functions, composition rules, and extensions.

The renderer declares binding requirements for catalog validation, component
implementation, function execution, accessibility behavior, and error
reporting. A resolved renderer binding shows which requirements its identified
implementation claims to satisfy.

The supported catalog list is an implementation-feature claim. It does not
authorize an agent to invoke a function, load a URL, access a Resource, or
cause an Effect. Catalog function caller restrictions in the `v1.0` candidate
remain implementation constraints. An AgSDL Policy and Authorization decision
still govern protected Actions.

### Progressive update mapping

An A2UI binding adds a Protocol view of the surface lifecycle. Its binding-
defined safety states should distinguish absent, active but incomplete,
renderable, invalid or degraded, and deleted surfaces. A2UI does not name this
complete state set. A binding may use different state names, but it should
preserve the distinctions when they affect user interaction or failure
behavior.

For each supported envelope kind, the binding should declare:

- permitted sender and receiver roles;
- valid source surface states and resulting states;
- ordering and correlation requirements;
- atomicity boundary;
- validation phase and diagnostic behavior;
- whether the renderer may display or accept interaction with partial state;
- recovery for invalid messages, dangling component references, unknown
  catalogs, unresolved data paths, and duplicate creation;
- trace records needed to reconstruct applied and rejected updates.

A transport batch is not treated as atomic when the selected A2UI transport
binding says receivers continue after one message fails. Repaint deferral does
not turn sequential partial application into a transaction.

### Data-model mapping

An A2UI surface data model maps to execution State, not Memory or Knowledge by
default. A binding should state:

- its State definition, schema or open-data constraint, lifecycle, and owner;
- agents, renderers, components, and functions allowed to read or write paths;
- the authority that resolves concurrent writes;
- data classifications and protected paths;
- whether local inputs update the model before agent acknowledgement;
- deletion and replacement semantics for the selected A2UI version;
- absolute JSON Pointer and A2UI-relative collection-path behavior;
- synchronization scope, destination, minimization, retention, and failure
  behavior.

When full data-model synchronization is enabled, the outbound metadata is an
information-flow Effect across a Trust boundary. The declaration must identify
the destination Principal and applicable Policy. A synchronized value does not
become Memory unless a separate Memory definition and update operation retain
it beyond the declared surface or execution lifetime.

### User-action mapping

An A2UI `action` maps first to a Message occurrence at a renderer-to-agent
Interface operation. The mapping preserves the event name, surface occurrence,
source component, claimed timestamp, resolved context, sender, intended
recipient, and transport correlation. A `v1.0` candidate mapping also preserves
the optional resolved `userMessage` without treating it as trusted evidence of
what the human saw or intended.

The action message may request an AgSDL Action. When it does, the binding must
name that Action and map material context fields to its inputs and target
Resources. It should report unmapped or missing material fields. An A2UI event
name alone is not a stable AgSDL Action identity.

The message does not prove:

- which human interacted with the component;
- that the human saw accurate or complete information;
- that the interaction was intentional;
- that an Approval requirement was satisfied;
- that an Authorization decision permitted a protected Action;
- that the requested Action ran or produced an Effect.

An approval-themed component therefore remains presentation. An AgSDL Approval
decision requires the identity, scope, material context, lifetime, and evidence
defined by the applicable Approval requirement.

### Function-call mapping for the candidate

The `v1.0` candidate's renderer and agent function calls map to bidirectional
Interface operations with correlation identifiers and result or error
messages. An agent-to-renderer call must preserve the renderer-initiated session
precondition. Every call mapping should preserve caller and target roles, local
or remote routing, request correlation, and the required response or error. A
function that can change a Resource or information flow maps to an AgSDL Action
and possible Effects. The binding should declare timeouts, duplicate-call
handling, cancellation, late results, and failure behavior.

Static catalog metadata such as allowed callers, return type, or required user
activation can contribute to a binding requirement. It cannot replace Policy,
authentication evidence, an Authority grant, or an Authorization decision.
Because this feature belongs to a candidate specification, a stable
`v0.9.1` binding must reject it or report it as unsupported rather than
silently approximating it.

### Transport mapping

The A2UI format binding declares transport requirements without choosing an
implementation. At minimum, interactive progressive use needs:

- ordered, framed agent-to-renderer messages;
- a return path for actions and errors;
- correlation among execution, surface occurrence, and endpoint identities;
- metadata carriage when capabilities or full data models use metadata;
- declared delivery, retry, duplicate, acknowledgement, and reconnection
  behavior;
- peer authentication, confidentiality, integrity, freshness, and replay
  controls required by policy;
- size, rate, depth, component-count, and update-count limits;
- failure behavior when any required property is unavailable.

An A2UI transport binding names the external specification and version that
provide these properties and maps each A2UI envelope and metadata item to it.
Transport selection cannot change the surface lifecycle, Action mapping, or
authority requirements. A binding to A2A, AG-UI, MCP, or another carrier needs
separate executable tests before an adapter claims support.

## Proposed trust requirements

An A2UI binding should expose these Trust boundaries when present:

- agent output to renderer parsing and validation;
- renderer state to agent through action context or full model sync;
- renderer to catalog implementation code;
- renderer to remote media, URL handlers, or function endpoints;
- displayed content and controls to the user;
- transport intermediaries between endpoint Principals.

The effective Policy should define:

- accepted publishers, versions, digests, and catalog sources;
- acceptance of client-supplied inline catalogs and handling for unknown
  extensions;
- component, function, URL scheme, origin, and remote-resource restrictions;
- data-path read and write limits;
- sensitive-data display and synchronization rules;
- user-interaction rules for incomplete or invalid surfaces;
- Action authorization and approval gates outside model-generated content;
- resource budgets and failure behavior;
- trace, redaction, retention, and incident evidence.

The renderer must treat agent-generated labels, choices, URLs, component
relationships, validation messages, and function arguments as untrusted input.
The agent must treat renderer capabilities, inline catalogs, action context,
timestamps, component identifiers, errors, and synchronized data as untrusted
input. Each side validates the selected schema and applies independent Policy
before relying on the content.

Declarative rendering is not a complete sandbox. Local widget and function
implementations can process sensitive data, contact external origins, open
URLs, or cause other Effects. A catalog allowlist narrows dispatch but cannot
establish implementation integrity, visual honesty, accessibility, isolation,
or absence of hidden behavior.

## Conformance and test plan

This proposal does not create an A2UI conformance profile or implementation
feature. It defines the prerequisites for doing so later.

An eventual adapter claim should identify one AgSDL specification version, one
A2UI format binding version, one exact A2UI source version, supported message
directions and kinds, selected transport bindings, catalog set, and test-suite
version. Tests should include at least:

- structural fixtures accepted and rejected by the pinned A2UI schemas;
- conflict fixtures that exercise the binding's chosen version keys, component
  form, metadata placement, and DataPart batching rule;
- ordered lifecycle transitions, including updates before creation, duplicate
  creation, deletion, and version-specific identifier reuse;
- partial component graphs, later completion, invalid references, and failure
  recovery;
- catalog mismatch, unknown component, unavailable renderer implementation,
  and untrusted inline catalog cases;
- data replacement, deletion, binding resolution, local edits, and full-model
  synchronization with protected fields;
- escaped absolute JSON Pointer segments and relative collection paths;
- action correlation, spoofed source data, duplicate delivery, stale actions,
  and protected Action denial;
- transport loss, reorder, replay, reconnect, metadata loss, and peer identity
  failure;
- `v1.0` candidate function-call boundary, correlation, timeout, and
  authorization cases when that version is claimed;
- mapping reports that enumerate preserved, transformed, dropped, defaulted,
  and unsupported information.

Passing upstream A2UI schema or conformance tests proves only the upstream
subject and scope those tests cover. Passing AgSDL structural tests would prove
only the AgSDL artifact. An interoperability or round-trip claim additionally
needs adapter tests against independent producer and renderer implementations,
with a declared equivalence boundary and loss report.

AgSDL has not selected a serialization and has no adapter contract. Adding
fixtures or schemas now would either invent syntax or test a non-normative
example. The executable plan remains blocked on acceptance of the relevant
representation and adapter semantics. Until then, every A2UI claim is reported
as research or proposed support, never implemented interoperability.

## Consequences

The core model stays independent of UI frameworks and A2UI versions. A system
can still declare the portable state, interfaces, Actions, Effects, Policies,
and binding requirements behind a generated interface.

Implementations carry more explicit records. They cannot hide a mutable catalog
behind its display name or treat a user click as authorization. Candidate and
stable A2UI bindings remain separate, which costs maintenance but prevents a
candidate change from silently altering a stable system definition.

The proposal also makes a limited result honest. AgSDL can describe what an
A2UI integration would require, but it cannot yet issue an A2UI adapter or
runtime conformance claim.

## Alternatives considered

### Add generated UI concepts to the core

Rejected. Surface, catalog, component, and renderer are A2UI-specific. Existing
Resource, State, Interface, Protocol, Action, Effect, Runtime, and binding terms
cover the portable concerns.

### Embed the A2UI schemas and catalogs in AgSDL

Rejected. Copies would drift, blur governing authority, and make external
format details appear to be AgSDL semantics. Immutable references and adapter
tests are more precise.

### Treat A2UI as a transport

Rejected. A2UI defines UI envelopes and state transitions while relying on a
separate carrier. Format and transport bindings need different identities.

### Treat a catalog allowlist as an authorization policy

Rejected. It limits dispatch to known component and function names. It neither
identifies an acting Principal nor grants authority over protected Resources.

### Define one binding for `v0.9.1` and `v1.0`

Rejected. The candidate changes role terminology, surface creation, deletion,
catalog composition, extensions, and function calls. One binding would conceal
unsupported behavior and incompatible lifecycle rules.

## Security considerations

Agent-generated interfaces can phish, mislabel consequential controls, conceal
context, collect sensitive input, load remote content, and request local or
remote Effects. Progressive updates can expose a user to an incomplete control
before later messages provide warnings or validation. Full data-model sync can
disclose every field on a surface to the remote endpoint.

The binding therefore keeps UI presentation separate from authenticated human
identity, Approval, Authorization, Action execution, and Effect evidence. It
also requires explicit catalog provenance, renderer implementation identity,
transport security, data-flow policy, and failure behavior. These declarations
do not enforce themselves. Deployment and execution evidence remain necessary.

## Compatibility impact

This proposal changes no normative specification or schema. Existing conceptual
documents remain valid. If accepted later, an A2UI binding will be optional and
separately versioned.

The reviewed stable basis is A2UI `v0.9.1` at upstream commit
`715abe092b9ba12174a579c2de75b6dd0c90a502`. The `v1.0` material at that commit
is candidate input only. A later upstream stable `v1.0` needs a new review and
binding identity even if its version string remains `v1.0`.

## Unresolved questions

1. Which accepted AgSDL construct should own external format bindings once the
   specification selects serialization?
2. Should a surface component graph and its data model use one State definition
   or two related State definitions?
3. Which minimum lifecycle states must every generated-interface binding expose
   to prevent interaction with unsafe partial state?
4. How should an adapter identify equivalent Actions when A2UI action names are
   local strings rather than stable external operation identities?
5. Which catalog properties belong in a portable binding requirement, and which
   remain renderer target checks?
6. What loss categories and independent implementations are required before an
   AgSDL-A2UI round-trip claim is meaningful?
7. Should full data-model synchronization be forbidden by a future security
   profile unless an explicit field-level disclosure policy exists?
8. How should a future stable A2UI `v1.0` binding relate to the candidate
   snapshot reviewed here if upstream changes no version string?
