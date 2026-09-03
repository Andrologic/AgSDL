# Proposal 0007: Agent User Interaction Protocol binding

- Status: proposed
- Date: 2026-09-02
- Target: conceptual external-protocol binding profile
- Depends on: proposals 0002, 0003, and 0004
- Research basis: `docs/research/agent-user-interaction-protocol.md`

## Problem

AgSDL needs to describe user-facing interactive executions without turning a
frontend SDK or wire event into universal system semantics. The Agent User
Interaction Protocol (AG-UI) supplies a current external contract for starting
agent runs and streaming events to applications. It covers progressive text,
tool calls, shared state, activity, nested work, human input, and run outcomes.

A direct field-for-field import would create several errors:

- protocol Message occurrences would be confused with assembled conversation,
  tool, state, trace, or control records;
- a visible frontend tool would look authorized and executed;
- an interrupt response would look like an accountable Approval decision;
- aborting an HTTP request would look like a verified remote stop;
- an AG-UI subagent label would look like A2A, Delegation, or Handoff;
- AG-UI state carriage would look like a complete portable state consistency
  model;
- a package version would look like a version for every AG-UI contract and
  encoding.

AgSDL needs an explicit binding proposal that preserves those distinctions and
defines the evidence required for a future conformance claim.

## Scope

This proposal defines conceptual semantics for:

- binding an AgSDL Interface and Protocol to an identified AG-UI contract;
- starting, observing, completing, interrupting, and resuming interactive runs;
- mapping AG-UI event messages to conversation records, State, Action,
  Approval, and Trace occurrences without inventing occurrences;
- binding client-provided tools to AgSDL Tools and Actions;
- separating AG-UI interruption, local stream control, transport behavior, and
  portable stop controls;
- composing AG-UI with separate A2UI, A2A, and MCP bindings;
- defining candidate implementation features and executable test obligations
  for later normative work.

This proposal does not define AgSDL serialization, copy AG-UI schemas, select a
transport, implement a runtime adapter, or create a present interoperability
claim. It does not make AG-UI, A2UI, A2A, MCP, a frontend framework, or an
agent runtime part of the AgSDL core. It does not map execution of
backend-defined Tools that run outside the application endpoint; such execution
needs a separate Tool binding.

## Proposed terms

### External contract set

An **external contract set** identifies the exact upstream contracts used by a
binding. For AG-UI it includes:

- the upstream repository and immutable release or commit identity;
- the contract maturity, such as published 0.x or a pinned 1.0 draft revision;
- each package or schema identity and version used for types, client behavior,
  encoding, or middleware behavior;
- the selected event families and deprecated forms accepted;
- the selected wire encoding and transport binding;
- compatibility transforms applied before or after validation;
- known exclusions and information loss.

The set is one resolution input. Updating any member creates a new resolved
binding assessment even when the human-readable protocol name is unchanged.
Published 0.x package behavior and 1.0 draft requirements are different
contract sets. A binding cannot combine them under one unqualified version or
use a draft rule as evidence that a published SDK implements it.

### AG-UI binding requirement

An **AG-UI binding requirement** is a portable requirement that an Interface
and its multi-message Protocol can be realized through an AG-UI contract set.
It selects required interaction properties without naming a runtime endpoint.

A **resolved AG-UI binding** identifies the endpoint, external contract set,
transport and encoding bindings, role assignment, capability evidence, applied
transforms, and test evidence for one deployment. It records each required
property as satisfied, unsatisfied, or indeterminate.

### Interactive run occurrence

An **interactive run occurrence** is one execution occurrence initiated through
the bound run operation. It has the AG-UI `threadId` and `runId`, the applicable
AgSDL definition versions, the initiating and acting Principal identities when
known, every terminal observation permitted by the selected contract, or an
explicit missing-terminal condition.

An AG-UI thread is a correlation scope. It is not an AgSDL System, Agent,
Principal, State definition, or durable execution guarantee. An AG-UI run is an
execution occurrence. It is not a Runtime instance or Control flow definition.

### Frontend tool binding

A **frontend tool binding** maps one client-provided AG-UI tool description and
its call lifecycle to one AgSDL Tool and Action. It identifies the executor,
execution Principal, input and output mapping, target Resource mapping, Effect
and failure mapping, correlation rules, and result-return path. When the mapped
Action is protected, it also identifies the authorization requirement and
policy application point.

## Binding structure

### Interface roles and operations

The bound AgSDL Interface has two endpoint roles:

- the **application endpoint** represents the user-facing application side;
- the **agent endpoint** represents the exposed agent or system side.

A resolved binding identifies both concrete endpoints. If a selected feature
requires Principal attribution, an endpoint role without that identity leaves
the requirement unsatisfied.

The Interface has two operations relative to the agent endpoint:

- **start or continue interactive run** accepts the mapped AG-UI run input and
  is inbound;
- **observe run event** carries one AG-UI event and is outbound.

Both operations participate in an **interactive run protocol**. One event on
the stream is one protocol Message occurrence. A resolved binding may expose
capability discovery through another operation, but discovery does not alter
the run Protocol and does not negotiate authority.

Each start or continue request is a protocol Message occurrence sent by the
application endpoint to the agent endpoint. It conforms to the corresponding
Interface operation and carries the `threadId` and new `runId` correlation.
Nested conversation records can describe earlier exchanges and do not become
new Message occurrences merely because the request carries them.

The Interface contract declares which parts of run input are required:

- new user input or replayed conversation records;
- current State occurrence or no state;
- client-provided frontend Tool descriptions;
- application context;
- extension data corresponding to `forwardedProps`;
- resume entries for every open interrupt when continuing.

A processor preserves each part separately. It does not infer that every
message in the input was newly sent, that state is authoritative, that a listed
Tool is authorized, or that extension data has portable meaning.

When the selected contract set is a pinned 1.0 draft revision, the resolved
binding also records the declared `protocolVersion` of each side and any
downgrade transform. A lossy transform is visible in conformance evidence. An
unknown addition and a malformed known value remain different conditions. The
same requirements are not projected onto a 0.x binding whose selected package
contracts do not implement them.

### Interactive run protocol states

The candidate protocol uses the selected AG-UI lifecycle instead of creating a
second lifecycle:

| Source | Trigger | Sender | Receiver | Result |
| --- | --- | --- | --- | --- |
| `ready`, `completed`, or `failed` | start request | application | agent | `waiting` |
| `awaiting-input` | complete resume request | application | agent | `waiting` |
| `waiting` | `RUN_STARTED` | agent | application | `active` |
| `waiting` | initial `RUN_ERROR`, when allowed | agent | application | `failed` |
| `active` | nonterminal event | agent | application | `active` |
| `active` | successful `RUN_FINISHED` | agent | application | `completed` |
| `active` | interrupting `RUN_FINISHED` | agent | application | `awaiting-input` |
| `active`, `completed`, or `awaiting-input` | `RUN_ERROR`, when allowed | agent | application | `failed` |
| `completed`, `awaiting-input`, or `failed` | replayed `RUN_STARTED` on the same stream | agent | application | `active` |

`awaiting-input` is a thread-level continuation condition. The interrupted run
has ended. A resume request creates a new `runId` and interactive run
occurrence.

A published 0.x resolved binding states whether it follows the stricter
documented lifecycle that requires `RUN_STARTED` or the reference TypeScript
verifier behavior that also accepts an initial `RUN_ERROR`. It cannot claim one
while testing the other. A 1.0 draft binding instead follows the pinned draft's
normative lifecycle, including its rules for truncated streams and a late
`RUN_ERROR` after `RUN_FINISHED`.

### Ordering and correlation

The binding requires correlation at these levels when the corresponding feature
is selected:

- thread and run for lifecycle observations;
- message for progressive text and reasoning;
- tool call and optional parent message for tool proposals and results;
- state definition, scope, and baseline for snapshots and deltas;
- activity message for activity snapshots and deltas;
- control-flow step identity for mapped step observations;
- interrupt and prior run for resume;
- nested execution occurrence for subagent attribution.

The selected transport restores complete producer order before semantic
mapping. If its channel can reorder, duplicate, omit, or replay events, the
resolved binding supplies the restoration, deduplication, and recovery rules.
A timestamp alone is not an ordering or deduplication key.

## Semantic mapping

### Run lifecycle

`RUN_STARTED` establishes the observed thread and run correlation. It maps to
the start Trace record for the interactive run occurrence. Its optional input
echo is evidence of what the producer reported, not proof that every nested
record was received from its original Principal in this run.

`RUN_FINISHED` maps to a terminal Trace record. A success outcome reports the
run's protocol completion. It does not prove that every proposed Tool executed,
that every Effect occurred, or that the system met its goal. An interrupt
outcome terminates the run and establishes open interrupt continuations.

`RUN_ERROR` maps to a terminal failure observation. Its source message and code
are preserved. A portable failure mapping exists only for codes or conditions
listed by the resolved binding. Unknown codes remain unknown.

`STEP_STARTED` and `STEP_FINISHED` map to Control-flow step observations only
when the binding resolves `stepName` to one AgSDL step identity. Otherwise they
remain implementation trace records. They never define allowed successors,
branch conditions, or completion criteria.

### Text, activity, and reasoning

A valid `TEXT_MESSAGE_START`, zero or more content fragments, and
`TEXT_MESSAGE_END` with one `messageId` materialize one conversation record.
Each source event remains a protocol Message occurrence with the agent and
application endpoint identities as sender and receiver. The assembled record is
not a second Message occurrence because no endpoint sent it as one message.
AG-UI role strings do not establish Principal identity, authentication, or
authority.

A chunk convenience event is normalized before semantic mapping. The original
chunk is the protocol Message occurrence. Its normalized lifecycle observations
can become Trace records, but not additional Message occurrences.

`MESSAGES_SNAPSHOT` maps to a materialized collection of conversation records.
The binding correlates records already known by identity. A record not
previously observed remains a snapshot-contained record whose original
occurrence and delivery status are unknown. A snapshot cannot prove original
delivery, acceptance, or processing.

Activity events map to progress observations. They map to State transitions or
conversation records only when a separate definition selects that meaning.
Reasoning events are protected observations or extensions. A binding declares
disclosure, retention, redaction, and access rules and must not treat model
reasoning as an authoritative explanation of a decision.

### State

An AG-UI state binding identifies exactly one AgSDL State definition version
and occurrence scope for each state stream. It declares:

- the data contract and whether unknown fields are preserved;
- the authoritative writer or conflict-resolution authority;
- the snapshot replacement rule;
- the RFC 6902 profile and baseline for deltas;
- revision, ordering, and duplicate handling;
- lifetime and persistence across runs or threads;
- the action taken on a missing baseline or failed patch;
- which intermediate values belong in the Execution trace.

`STATE_SNAPSHOT` creates or replaces the materialized State occurrence at its
declared point. `STATE_DELTA` records a proposed or accepted transition according
to the writer authority. Every mapped replacement or transition identifies its
initiating Agent, Runtime, Control-flow step, Action, or external event. A
binding that cannot establish that attribution reports the state feature as
unsatisfied. The AG-UI producer identified by `subagentRunId` is provenance,
not state ownership.

The bidirectional presence of state does not permit concurrent writes by
implication. A binding with several writers is unsatisfied until it supplies
and tests a conflict rule consistent with the State definition.

### Tool calls and actions

Tool-call events materialize one call proposal. They remain protocol Message
occurrences and optional Trace records. They do not create an Action occurrence
until an identified executor attempts the mapped Action.

The result path depends on the selected contract:

| Call kind | Executor | Result path |
| --- | --- | --- |
| Agent-side Tool | agent side | `TOOL_CALL_RESULT` can arrive in the same run |
| Frontend Tool advertised in run input | application | the run finishes successfully without `TOOL_CALL_RESULT`; the next run input carries a correlated tool message |
| Published 0.x tool-bound interrupt | agent side after resume | the interrupted run ends, the next run carries `resume`, and that run can emit `TOOL_CALL_RESULT` |

Each frontend Tool description resolves to one AgSDL Tool definition and
Action. Name matching alone is insufficient. Before an attempt, the executor
validates the complete arguments against the mapped input contract and resolves
the target Resources against the Action contract.

When the mapped Action is protected, its policy application point obtains the
required authentication evidence, applies the declared Policies, and records a
distinct Authorization decision immediately before the attempt. The decision
binds the acting Principal, Action, target Resources, material context, Policy
versions, result, and decision time. An unprotected Action has no authorization
requirement by implication.

Invalid arguments create no Action occurrence. A denied or indeterminate
Authorization decision prevents the attempt and is recorded without an Action
or Effect occurrence. Once the executor attempts the Action after validation
and, when protected, a permitted Authorization decision, the binding creates an
Action occurrence identifying the executor, acting Principal, target Resources,
and outcome even if execution fails. A correlated result records the reported
outcome, but does not by itself prove an external Effect.

If the application edits arguments, the trace preserves the original and
replacement values and the executor validates the replacement. For a protected
Action, the binding reevaluates authorization and Approval when their material
context changed.

Agent-side Tools are outside this frontend execution feature. Their AG-UI events
can be imported as call proposals and reported results, but mapping their
execution to Action and Effect occurrences requires a separate Tool binding
that identifies the executor, acting Principal, target Resources, and any
protection. A conformance report lists that mapping as not claimed, unsatisfied,
or separately satisfied instead of claiming general AG-UI Tool execution. MCP tools
exposed by AG-UI middleware also need an MCP binding and transformation record.

### Interrupts and human approval

Every AG-UI interrupt creates an explicit Protocol wait condition. Its
identifier, reason, prompt, response contract, expiry, tool correlation, and
extension metadata are preserved in Trace records.

An interrupt maps to an AgSDL Approval request only when all of these conditions
hold:

- it resolves to one Approval requirement;
- the request identifies the exact proposed Action, Resources, requesting
  Principal, and material parameters;
- the eligible human approver qualifications and authentication requirement
  are known;
- the information presented to the human is identified;
- allowed decisions, expiry, invalidation rules, single-use rule, and no-response
  behavior are declared;
- protected execution remains blocked until a matching permitted Authorization
  decision exists.

The `tool_call` reason and `toolCallId` can provide correlation but do not
satisfy the remaining conditions. `input_required`, `confirmation`, and custom
reasons are not approvals by default.

A resume entry maps to an Approval decision only when the binding:

- authenticates one human Principal as the responder;
- correlates the response with the open request on the same thread;
- validates the payload against the selected response contract;
- maps the payload to one allowed decision;
- verifies expiry and material-context integrity;
- records the applicable definition and policy versions.

`resolved` means that the interrupt received a response. It does not mean that
the proposed Action was approved. `cancelled` means the respondent abandoned
the interrupt without a meaningful payload. It is distinct from a denial
expressed inside a resolved payload.

For the reviewed 1.0 draft, the external contract set records that the
authoritative schema permits `cancelled` while the prose says `abandoned`. The
binding validates structure against `cancelled` and does not accept
`abandoned` unless an explicit compatibility transform declares that loss.

The resume request addresses every open interrupt as one complete protocol
input. If the selected 0.x contract includes the documented exact-tuple replay
rule, replaying the same `(threadId, interruptId, status, payload)` must be safe
at the interrupt layer. The binding does not infer that rule from the 0.x client
or apply it to the 1.0 draft. Tool and Effect idempotence remain separate
requirements.

### Nested agents, A2A, and handoffs

`SUBAGENT_*` and `subagentRunId` can attribute observations to a nested
execution occurrence. They map to an AgSDL Agent or Runtime only through a
resolved identity map.
They do not establish:

- a Delegation definition or occurrence;
- a Handoff of responsibility;
- a transfer or narrowing of authority;
- a separate State occurrence scope;
- an A2A endpoint, Agent Card, task, message, or artifact.

If nested work uses A2A, the deployment declares a separate A2A binding and
causal links between the AG-UI observations and A2A occurrences. The same rule
applies to MCP calls reached through middleware.

A2UI and other generative UI contracts are separate too. They define component
and rendering semantics that AG-UI can carry but does not supply.

### Raw and custom events

`RAW` preserves an external event envelope. `CUSTOM` selects
application-defined semantics by name. A binding treats both as extensions. It
identifies the extension owner, namespace, version, requirement level, and
preservation rule. A required extension that the consumer cannot interpret
makes the resolved binding unsatisfied. An optional extension has a declared
portable fallback.

## Portable flow control

AG-UI interruption and resume are portable only for the terminal-run protocol
defined above. The following properties require separate declarations:

| Control | Required declaration and evidence |
| --- | --- |
| Local detach | Which observer stops consuming and whether execution continues |
| Request abort | Which transport operation is cancelled and whether the remote endpoint acknowledged it |
| New-work refusal | Which Interface operations and scopes reject new starts |
| Queue cancellation | Which queued work identifiers were removed and by which authority |
| Active-run interruption | Which runtime, model, Tool, and delegate operations were signalled, their response target, and their observed terminal state |
| Emergency stop | Authorized Principal, scope, propagation, safe state, containment, evidence preservation, and recovery authority |
| Stream reconnect | Event identity, last accepted position, replay window, deduplication, resynchronization, and failure behavior |

The reference TypeScript `abortRun()` and `detachActiveRun()` satisfy only local
client behavior. A deployment cannot use them as evidence for remote stop or
Effect prevention.

## Transport and encoding bindings

The event semantics and transport are separate. A resolved binding selects one
or more transport and encoding profiles. Each selection declares:

- media types, request method, endpoint, framing, and authentication;
- event subset and field fidelity;
- ordering, delivery, acknowledgement, retry, and backpressure behavior;
- disconnect, timeout, and reconnect behavior;
- maximum payloads and resource limits;
- confidentiality, integrity, origin authentication, and replay protection;
- transformations between the wire representation and the semantic event set.

Published 0.x Protobuf is a subset of its JSON event set, so a 0.x binding lists
supported mappings and reports loss. The 1.0 draft instead requires its HTTP
and Protobuf binding to match the draft schema and shared byte corpus. Evidence
from the 0.x package does not prove that draft requirement.

## Candidate conformance model

The following names are provisional candidate implementation features. They
cannot be claimed until accepted normative text defines them and a published
suite supplies executable evidence, as required by proposal 0003.

### Candidate feature: AG-UI observation import

The processor consumes an identified AG-UI event stream and emits protocol
Message occurrences, materialized conversation records, and mapped AgSDL
occurrences. It preserves required extensions and reports every unknown or
lossy mapping without inventing an assembled Message or Action occurrence.

Candidate tests include valid and invalid lifecycle streams, interleaved
message and tool fragments, snapshots after progressive events, unknown custom
events, deprecated inputs, and JSON versus Protobuf fidelity cases.

### Candidate feature: AG-UI interactive run

The runtime realizes the bound operations and applies the selected lifecycle.
It preserves every terminal event, including a permitted late `RUN_ERROR`, or
records evidence loss. It also preserves the required thread, run, parent,
definition, and Principal correlation.

Candidate tests include normal success, initial error according to the selected
lifecycle variant, permitted late error, unfinished progressive entities at
termination, forbidden events after close, branch lineage, and missing-terminal
transport loss.

### Candidate feature: AG-UI frontend tool execution

The runtime maps selected client tools to AgSDL Tools and Actions, validates
their arguments, attributes each attempt to its executor and Action occurrence,
and reports result and Effect evidence. For a protected Action, it also applies
the declared authorization requirement and policy application point.

Candidate tests include malformed and fragmented arguments, parallel calls,
unknown tools, unresolved target Resources, unprotected execution, protected
denial without an Action occurrence, edited parameters, failed attempted
execution with an Action occurrence, duplicate results, the next-run frontend
result path, the separate 0.x interrupt path, external partial Effects, an
excluded agent-side Tool, and an MCP-backed tool that requires a second binding.

### Candidate feature: AG-UI state synchronization

The runtime applies snapshots and deltas to a bound State occurrence under its
declared authority, revision, conflict, and recovery rules.

Candidate tests include a missing baseline, invalid RFC 6902 operation,
duplicate and reordered delta, concurrent writers, full resynchronization,
cross-run persistence, and trace retention of overwritten values.

### Candidate feature: AG-UI interrupt continuation

The runtime terminates an interrupted run, preserves required state and message
materialization, validates a same-thread all-open resume, handles any other
input according to the selected contract set, and creates a new run. An
approval subfeature also proves the Approval mapping and, for a protected
Action, the additional Authorization mapping.

Candidate tests include parallel interrupts, partial resume, wrong thread,
unknown identifier, expiry, schema mismatch, denial, cancellation, approve with
edited arguments, changed policy version, an unauthenticated responder, and the
1.0 draft's `cancelled` versus `abandoned` divergence. Exact-tuple replay is
added when the selected 0.x contract requires it.

### Candidate feature: AG-UI stop control

This feature is not satisfied by upstream client abort alone. A target profile
would need an explicit control operation, runtime acknowledgement, propagation
requirements, safe-state evidence, and fault-injection tests across nested
agents and Tools.

## Conceptual example

A procurement assistant exposes an AG-UI-bound Interface. The application sends
a start request containing a new user conversation record, current form State,
and a frontend Tool that can submit a purchase order. The run emits text events,
then a tool-call proposal.

The frontend tool binding maps the proposal to the protected **submit purchase
order** Action. The run finishes successfully without `TOOL_CALL_RESULT`. The
application asks an authenticated purchasing manager to approve the proposal.
The manager edits the quantity, so the application reevaluates approval and
authorization for the changed proposal. A matching permitted Authorization
decision lets the application attempt the Action and create its Action
occurrence. Separate service evidence records whether the external order Effect
occurred. The next run input carries the correlated tool message with the
reported result. No interrupt or `resume` entry is involved in this frontend
Tool path.

Counterexamples:

- The runtime executes the frontend Tool because it appeared in
  `RunAgentInput.tools`, without resolving the Action, validating its arguments,
  identifying the executor, or applying declared protection.
- The runtime records `resume.status = resolved` as approval without inspecting
  the payload or authenticating the manager. Resolution has been confused with
  an Approval decision.
- The user closes the browser, `abortRun()` fires, and the system records the
  purchase as cancelled. Local transport abort has been confused with remote
  stop and Effect reconciliation.
- A middleware calls an MCP purchasing Tool, but the description declares only
  AG-UI. The external tool interface, transport, authorization, and information
  loss are unbound.

## Security considerations

The user-to-application, application-to-agent, application-to-Tool, and
application-to-state paths can cross different trust boundaries. A resolved
binding identifies each boundary, endpoint Principal, Resource, and failure
policy. It identifies authentication mechanisms and policy application points
where the mapped Actions or boundary controls require them.

Run input, streamed content, Tool arguments, interrupt prompts, response
schemas, resume payloads, state, raw events, and custom values are untrusted
until the applicable contract and policy validate them. Open metadata and
`forwardedProps` may carry sensitive information or authority-bearing values;
the binding classifies, limits, redacts, and preserves them according to policy.

Progressive rendering can expose content before a complete validation result.
The application declares whether it buffers protected content, supports
correction, or visibly marks provisional output. Tool arguments remain
proposals until complete and validated, and until authorized or approved when
either is required.

Approval UI quality and legal consent remain outside this binding. The binding
can require authenticated, scoped Approval evidence. It cannot prove that a
person understood a prompt or that external consent law was satisfied.

Stream compaction, snapshots, and last-write-wins metadata can erase evidence.
Trace policy states which fragments and prior values must be retained before
compaction. Encrypted reasoning remains opaque data and cannot be treated as
verified decision evidence merely because it is encrypted.

## Consequences

Positive consequences:

- AG-UI can realize a user-facing Interface without becoming AgSDL core syntax.
- Protocol events remain Message occurrences while conversation, tool, and
  state records materialize without invented occurrences.
- State, frontend tools, human approval, interruption, and stop controls keep
  their distinct security and control meanings.
- A2UI content and A2A or MCP middleware use composed bindings with explicit
  loss analysis.
- Version and encoding drift becomes visible in the resolved external contract
  set.

Costs:

- Authors must supply semantic information that AG-UI intentionally leaves to
  applications, especially identity, conditional authorization, state
  authority, Effects, and error mapping.
- A useful conformance claim needs fixtures and live fault-injection tests, not
  only structural inspection.
- JSON and Protobuf targets may need different binding profiles.
- Existing integrations that use free-form custom events or framework metadata
  need extension identities before they can claim preservation.

## Alternatives considered

### Treat AG-UI as a transport

Rejected. AG-UI defines run, event, state, tool, and interrupt behavior above
transport. Calling it a transport would hide those protocol semantics and make
HTTP, SSE, WebSocket, and Protobuf choices impossible to model separately.

### Import AG-UI events into the AgSDL core

Rejected. Many events are progressive observations or UI materialization
instructions. Their names and package contracts evolve independently. The core
already has broader Message, State, Action, Approval, Trace, Interface, and
Protocol concepts.

### Map every interrupt to human approval

Rejected. AG-UI also uses interrupts for structured input and confirmation,
and its core record lacks several approval and authorization facts required by
AgSDL.

### Treat frontend tools as MCP tools

Rejected. AG-UI client tools and MCP server tools have different discovery,
execution, transport, and result contracts. Middleware can bridge them through
two explicit bindings.

### Treat AG-UI as a generative UI specification

Rejected. AG-UI carries interaction events but does not define component trees,
widget catalogs, or rendering behavior. Those need an A2UI or other generative
UI binding.

### Claim adapter conformance from upstream SDK tests

Rejected. Upstream tests provide evidence about AG-UI packages and selected
cross-SDK encodings. They do not test an AgSDL mapping, target deployment,
policy enforcement, state authority, approval identity, or remote stop.

## Compatibility impact

AgSDL has no normative syntax, accepted binding profile, or published runtime
conformance feature. This proposal breaks no conforming AgSDL document.

If accepted, later syntax should reference an external contract set rather than
copy AG-UI schemas. Schemas can validate the AgSDL reference and mapping
structure only after the language serialization is selected. Runtime and
adapter features should remain unclaimable until executable suites cover their
declared event families, transport, failure behavior, and security application
points.

## Unresolved questions

1. Should the first AG-UI profile select JSON over HTTP and SSE only, leaving
   WebSocket, webhook, and Protobuf to separate profiles?
2. Should a published 0.x profile require `RUN_STARTED`, or follow the
   TypeScript verifier that accepts `RUN_ERROR` as the first event?
3. Which progressive fragments must the minimum Trace profile retain after
   materialization or compaction?
4. Does AgSDL need a first-class progress occurrence, or can activity remain a
   trace or presentation extension in the first draft?
5. Which JSON Schema dialect and validation behavior apply to frontend Tool
   parameters and interrupt response schemas?
6. How should a binding identify state revisions and request a fresh snapshot
   without standardizing a transport-specific control operation?
7. Should `parentRunId` map to a general execution lineage relation, and what
   prevents a cross-thread or cyclic lineage?
8. Which AG-UI metadata keys need registered mappings, and which must remain
   required or optional extensions?
9. Can a future stream-resume profile standardize event identity and replay
   independently from AG-UI's interrupt continuation?
10. What minimum remote-stop evidence is testable across an application,
    runtime, nested agents, Tools, and external services?
11. Should reasoning and encrypted reasoning be excluded from a base profile by
    default because their disclosure and evidentiary meanings vary?
12. Which cross-SDK fixtures are stable enough to reuse as upstream inputs, and
    which AgSDL-specific fixtures must remain independently governed?
