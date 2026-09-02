# Agent User Interaction Protocol research

- Status: research note, non-normative
- Last reviewed: 2026-09-02
- Reviewed upstream snapshot: `release/2026-08-31`, commit
  `3f38925d0e6c19bf1f19502ee12e410e772ac142`
- Reviewed upstream draft: `main`, commit
  `a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e`

## Purpose and method

This note examines the current official Agent User Interaction Protocol
(AG-UI) sources for a possible AgSDL binding. It separates source facts from
AgSDL assessment. It does not define AgSDL syntax, accept proposal semantics,
or claim that an AgSDL implementation interoperates with AG-UI.

The review uses both the latest published AG-UI release available on the review
date and the current official 1.0 specification draft. The release contains
independently versioned packages. The relevant versions are `@ag-ui/core`
0.0.59, `@ag-ui/client` 0.0.59, `@ag-ui/proto` 0.0.59, and
`ag-ui-protocol` for Python 0.1.22. The GitHub release is therefore a
distribution event, not a single protocol version. The NPM and PyPI
latest-package records returned the same versions on the review date.

The 1.0 draft is a separate, unreleased contract. It introduces an
authoritative JSON Schema for structure and normative BCP 14 behavioral text.
This note does not treat draft requirements as properties of the published
0.x packages. Where the draft, release prose, and executable sources differ,
the difference is reported instead of choosing an undocumented merged
contract.

## Source status and authority

**Source facts.** The upstream repository describes AG-UI as an event-based
protocol between agent backends and user-facing applications. It says the event
model can use different transports and supplies HTTP with JSON over Server-Sent
Events as a reference path. An upstream maintainer instruction identifies the
TypeScript core types and client run loop as the source of truth for cross-SDK
parity. Python covers types and JSON encoding but has no reference client run
loop or Protobuf implementation.

The 1.0 draft says that its JSON Schema is authoritative for structure and its
prose is authoritative for behavior. It defines producer and consumer roles
and judges conformance per stream. Its changelog explicitly contrasts this
with 0.x, where shapes existed but behavior lived primarily in the TypeScript
client. The draft is marked as a draft throughout the official site and has
not replaced the latest published 0.x package line.

The repository README still describes approximately 16 standard event types.
The 0.0.59 TypeScript `EventType` enum contains 36 values, including convenience
chunk events, reasoning, activity, subagent, and five deprecated thinking
events. The Protobuf enum contains 19 values and its event union contains 21
messages. It omits activity, reasoning, thinking, tool result, and several other
JSON event forms. The upstream serialization documentation also calls JSON the
full-fidelity archival form and describes Protobuf as narrower.

The 1.0 draft schema contains 31 event values. It keeps the chunk, reasoning,
activity, and subagent families but retires the five deprecated `THINKING_*`
values. It also introduces in-band `protocolVersion` declarations on run input
and `RUN_STARTED`, with `MAJOR.MINOR` comparison and explicit downgrade rules.
These facts explain the event-count difference; they do not make a 0.x SDK a
1.0 implementation.

**AgSDL assessment.** An AgSDL reference must identify an upstream release or
commit, whether it selects a published contract or a draft, the concrete
package contracts, and the selected encoding. A bare
declaration such as "AG-UI 0.0.59" is ambiguous because it does not say which
package, event subset, run-loop behavior, or wire representation is required.
The README event count and generic compatibility claims are not precise enough
to define a binding.

## Published 0.x and the 1.0 draft

The two official lines must remain distinct in an AgSDL assessment:

| Concern | Published 0.x evidence | 1.0 draft requirement |
| --- | --- | --- |
| Authority | Package types, client behavior, documentation, and encoding implementations can differ | JSON Schema governs structure; normative prose governs behavior |
| Event set | TypeScript has 36 values; other SDKs and encodings expose smaller subsets | Schema enumerates 31 values and excludes deprecated thinking events |
| Version declaration | No general in-band protocol version in the reviewed core run contract | Consumer sends `RunAgentInput.protocolVersion`; producer declares its own version on `RUN_STARTED` |
| Ordering | Reference client and verifier behavior supply much of the evidence | One ordered event stream, with normative streaming, interleaving, lifecycle, and processing rules |
| Compatibility | Middleware and SDK behavior are contract-specific | Unknown material survives to translation and enforcement; malformed known values are fatal; lossy downgrade warns |
| SSE reconnection | Reference parser has no replay cursor contract | Binding explicitly ignores SSE `id` and `retry`; a truncated stream cannot resume and a rerun uses a new `runId` |

A resolved AgSDL binding may target the published 0.x contracts or a pinned 1.0
draft revision for experimentation. It must not claim that one conforms to the
other without executable evidence against the selected requirements.

## Interaction boundary

**Source facts.** `RunAgentInput` carries a `threadId`, a new `runId`, optional
`parentRunId`, state, message history, client-provided tool descriptions,
context, open `forwardedProps`, and optional resume entries. The TypeScript
HTTP client sends this object in an HTTP `POST` request and accepts an event
stream in response. The abstract client contract exposes the same run input and
event stream without requiring HTTP.

In the published line, an output run normally begins with `RUN_STARTED` and terminates with
`RUN_FINISHED` or `RUN_ERROR`. The reference verifier also accepts `RUN_ERROR`
as the first event, although the events documentation says `RUN_STARTED` and a
terminal event are mandatory. One serialized stream may contain several
sequential runs. `threadId` correlates runs in a conversation, `runId`
identifies a run, and `parentRunId` records optional branch lineage.

The 1.0 draft makes the request and ordered response stream normative. It also
admits a late `RUN_ERROR` after `RUN_FINISHED`, distinguishes pre-stream HTTP
failure from in-stream run failure, and classifies a stream loss without a
terminal event as truncation. Those are draft requirements, not inferred 0.x
guarantees.

**AgSDL assessment.** AG-UI is a candidate binding for one bidirectional AgSDL
Interface. Starting or resuming a run is an inbound Interface operation
relative to the agent or system. The returned event stream is an ordered set of
outbound exchanges governed by a multi-message Protocol. The HTTP request, SSE
framing, WebSocket, webhook, and Protobuf choices are transport or encoding
bindings. They are not part of the portable Interface operation by default.

`RunAgentInput` is one request occurrence. Its nested message array can contain
history from earlier runs, so each nested record must not be treated as a new
Message occurrence merely because the request carries it. State, context,
tools, and `forwardedProps` also retain their distinct meanings.

## Event families and progressive output

The following table classifies the TypeScript 0.0.59 event families. It is a
mapping analysis, not a replacement for the upstream schemas.

| AG-UI family | Upstream role | Candidate AgSDL interpretation | Information that is not established |
| --- | --- | --- | --- |
| `RUN_STARTED`, `RUN_FINISHED`, `RUN_ERROR` | Bound one run and report its terminal outcome | Execution and trace occurrences linked to the bound definitions | Runtime conformance, successful effects, or a portable error taxonomy |
| `TEXT_MESSAGE_START`, `CONTENT`, `END` | Build one text message progressively by `messageId` | One Message occurrence plus fragment observations | Three separate semantic messages or transport-independent delivery evidence |
| `TEXT_MESSAGE_CHUNK` | Convenience form expanded by the client | Same Message occurrence after normalization | A distinct portable occurrence |
| `TOOL_CALL_START`, `ARGS`, `END` | Build one tool-call request progressively by `toolCallId` | Proposed Action occurrence or invocation observation, subject to a resolved Tool mapping | Execution, authorization, approval, or an Effect |
| `TOOL_CALL_RESULT` | Report a result associated with a tool call | Tool-result or Action-outcome observation | Which side executed the Tool or whether an external Effect occurred |
| `STATE_SNAPSHOT`, `STATE_DELTA` | Replace state or apply ordered RFC 6902 operations | State occurrence and transition observations when a State definition is bound | State schema, writer authority, conflict resolution, persistence, or concurrency semantics |
| `MESSAGES_SNAPSHOT` | Replace the client's materialized message collection | Snapshot observation of prior and current messages | New delivery of every contained Message occurrence |
| `ACTIVITY_SNAPSHOT`, `ACTIVITY_DELTA` | Maintain structured in-progress UI activity | Progress observation or optional presentation extension | Portable Control flow or completion evidence |
| `STEP_STARTED`, `STEP_FINISHED` | Mark named execution steps | Trace records correlated with a Control-flow step when a binding supplies that correlation | A Control flow definition, allowed successors, or branch semantics |
| `REASONING_*` | Stream readable or encrypted reasoning-related data | Protected observation or extension under explicit disclosure policy | A required portable decision explanation or reliable causal account |
| `SUBAGENT_*` and `subagentRunId` | Attribute nested work in one AG-UI stream | Trace attribution to an Agent or runtime participant when identity mapping exists | A2A communication, Delegation, Handoff, authority transfer, or a separate state scope |
| `RAW` | Preserve an event from another source | External occurrence preserved as an extension | Meaning of the enclosed event |
| `CUSTOM` | Carry application-defined data by name | Named extension occurrence | Portable semantics without a separately identified extension contract |
| Deprecated `THINKING_*` | Legacy input translated to reasoning events by compatibility middleware | Versioned compatibility input only | A current preferred event family |

Start, content, and end events depend on order and correlation. The same is true
for streamed tool arguments. Snapshot and delta events need an agreed baseline,
and deltas apply in order. The upstream verifier checks many lifecycle and
correlation constraints. Those checks make event structure more precise, but
they do not add sender Principal identity, delivery acknowledgements, or a
global event identity.

## State and message materialization

**Source facts.** AG-UI state is unconstrained JSON in the TypeScript core.
`STATE_SNAPSHOT` replaces the client state and `STATE_DELTA` carries an array
described as RFC 6902 JSON Patch. The input can send current state back toward
the agent. The documentation describes both sides as able to modify shared
state, but the core types do not select a writer, revision, compare-and-swap
rule, merge rule, or conflict authority.

Messages use stable record identifiers and role-discriminated shapes. Message
snapshots replace the client's materialized conversation. Stream compaction may
replace progressive events with snapshots while preserving the materialized
client result. Metadata merges with last-write-wins behavior in several
materializers.

**AgSDL assessment.** An AG-UI state binding can carry a State occurrence only
after it identifies the AgSDL State definition, scope, lifetime, data contract,
and transition authority. AG-UI's bidirectional carriage does not satisfy the
AgSDL requirement for one declared authority that resolves concurrent writes.
Revision, conflict, and resynchronization behavior need a separate binding
requirement when more than one writer exists.

Event compaction can preserve a UI materialization while losing trace timing
and intermediate values. A binding must distinguish a materialized message or
state view from an Execution trace. It must also state whether progressive
fragments, overwritten metadata, and intermediate state are required evidence.

## Client-provided tools

**Source facts.** AG-UI distinguishes backend tools from client-provided tools.
The client places the latter in `RunAgentInput.tools` as a name, description,
and JSON Schema-shaped parameters object. The agent emits tool-call events and
the application can execute the selected client tool. Tool arguments arrive as
JSON text fragments. A tool result becomes a tool message correlated by
`toolCallId`. A tool-message `error` field distinguishes a failed client-side
execution from successful content.

**AgSDL assessment.** A frontend tool can map to an AgSDL Tool only when the
binding also identifies its Action, inputs, outputs, Effects, failures,
execution Principal, policy application point, and implementation location.
AG-UI tool visibility and selection prove neither authorization nor execution.
The binding must record whether the agent backend, UI process, middleware, or
another system executes the call. It must preserve the original proposal,
material argument changes, the decision that authorized execution, and the
result when those facts are required for audit.

MCP-backed tools remain MCP operations even if AG-UI middleware exposes their
schemas and events. That middleware is a composition of an AG-UI binding and an
MCP binding with a transformation. It is not evidence that the two protocols
have identical tool semantics.

## Interrupts, human decisions, and resume

**Source facts.** Neither reviewed line uses an `INTERRUPT`
event. A run ends with `RUN_FINISHED` whose outcome contains a non-empty array
of Interrupt records. A client later starts a new run on the same thread and
sends one resume entry for every open interrupt. An interrupt has an identifier,
reason, optional message, optional `toolCallId`, optional response schema,
optional expiry, optional metadata, and optional subagent attribution.

The defined core reasons are `tool_call`, `input_required`, and `confirmation`.
Other reason strings are extensions. In the published TypeScript contract and
the 1.0 draft schema, resume status is `resolved` or `cancelled`; an approval
denial belongs inside the resolved payload rather than being a resume status.
The 1.0 draft prose instead calls the second status `abandoned`. Because the
draft declares its schema authoritative for structure, `abandoned` is not a
legal value at the reviewed revision. This is an upstream defect that a binding
must record, not silently reconcile.

The documentation requires same-thread correlation and complete coverage of
open interrupts. The reviewed 0.x client checks that the resume input covers
every pending interrupt identifier and applies expiry handling. It does not
inspect the input messages to prohibit unrelated new content. The exact-tuple
resume replay rule belongs to the 0.x documentation; the client does not retain
and compare those tuples. The 1.0 draft normatively requires coverage and
same-thread continuity, but does not carry forward that exact-tuple rule. It
leaves an unrecognized resume entry as a warning-level producer condition.
State needed for continuation must be emitted before the interrupting terminal
event.

For a tool-bound interrupt, the proposed audit sequence crosses two runs: the
original tool arguments, the resume response and optional full replacement
arguments, then the tool result. Checkpoint restoration and replay from state
and messages are implementation choices, not different observable outcomes.

**AgSDL assessment.** An AG-UI Interrupt is first a wait or input-request
occurrence. It becomes an AgSDL Approval request only if the binding supplies
all missing approval facts: the exact proposed Action and Resource, material
parameters, requesting Principal, eligible human approver, presented context,
allowed decisions, expiry, invalidation rules, and no-response behavior.

A resume payload is not automatically an Approval decision. The binding must
authenticate the responding human Principal, bind the response to the Approval
request and policy version, interpret the payload as an allowed decision, and
preserve any edits as a changed Action proposal. A changed material parameter
can require a new approval under the Approval requirement. Free-form interrupt
metadata or a client capability boolean cannot replace those rules.

When the selected 0.x contract includes the documented exact-tuple replay rule,
that rule is useful but narrow. It is neither a demonstrated client mechanism
nor a 1.0 draft requirement. It does not establish idempotence for the resumed
run, the Tool, or an external Effect. Those need their own operation
identifiers, deduplication rules, and reconciliation evidence.

## Stop, detach, reconnect, and replay

**Source facts.** The TypeScript `HttpAgent.abortRun()` aborts its local
`AbortController`. `detachActiveRun()` stops local event processing. Neither
method sends a protocol event that confirms the remote runtime stopped. The
capability model contains `interventions`, `feedback`, and transport
`resumable` booleans. The latter mentions sequence numbers, but the reviewed
core event and run-input schemas contain no general sequence number,
acknowledgement, replay cursor, or last-event identifier.

The reference SSE parser ignores SSE `id` and `retry` fields and processes only
`data` fields. The 1.0 draft makes that behavior normative for its HTTP and SSE
binding, explicitly provides no stream resumption, and requires a new `runId`
after a broken connection. The serialization documentation describes append-only storage,
reload, reconnection, attachment, compaction, and branching as implementation
patterns. These descriptions do not supply one end-to-end reconnect protocol
in the core types.

**AgSDL assessment.** Four controls must remain separate:

- an AG-UI interrupt ends one run and permits a later same-thread resume;
- local stream detachment stops observation without stopping execution;
- transport abort closes or cancels a local request without proving remote
  termination;
- a portable stop or emergency stop is a governed control action with declared
  scope, propagation, safe state, response target, and completion evidence.

An AG-UI binding must not claim portable cancellation, reconnection, or
exactly-once delivery from the reviewed core contract. A deployment may add
those properties through a transport profile or extension, but it must identify
the mechanism and tests. After loss, a fresh state or message snapshot can
resynchronize a UI view; it cannot reconstruct omitted trace evidence by
itself.

## Errors

**Source facts.** `RUN_ERROR` is the sole run error event and normally
terminates its run. The 1.0 draft also admits it after `RUN_FINISHED` to report
a failure discovered after the run was reported closed. It carries a
human-readable message and optional code. Tool-message
`error` reports a client-side tool failure without making the enclosing run
error. `SUBAGENT_ERROR` terminates attributed nested work. Transport, decoding,
schema verification, state-patch, tool, policy, and external-effect failures do
not share a standardized cross-category error taxonomy.

**AgSDL assessment.** A binding can preserve the AG-UI error code, message,
source event, run correlation, and terminal position. It needs a separate map
to AgSDL failure conditions before a processor can reason portably about retry,
fallback, compensation, authorization denial, invalid input, or partial Effect.
An omitted or unknown code remains unknown rather than being inferred from the
message text.

## Boundary with A2A, MCP, and AgSDL

**Source facts.** Upstream documentation presents AG-UI as the agent-to-user
application protocol, MCP as the tool and context protocol, and A2A as the
agent-to-agent protocol. The repository contains middleware that can expose MCP
tools in an AG-UI run and another integration that can route work to A2A
agents. These are transformations implemented by middleware, not a shared wire
contract.

**AgSDL assessment.** The boundaries are:

- AG-UI binds interactive run input, event output, UI state materialization,
  and application-mediated actions at a user-facing Interface.
- A2A binds discovery and remote agent task or message exchanges. An AG-UI
  subagent event does not prove an A2A exchange, Delegation, or Handoff.
- MCP binds discovery and invocation of external tools, resources, and prompts.
  An AG-UI frontend tool is not an MCP tool unless a separate MCP binding says
  so.
- AgSDL defines intended system structure, portable control, policy,
  authorization, state ownership, and evidence requirements. It can reference
  AG-UI as a binding but must not import AG-UI event names as universal AgSDL
  semantics.
- An AG-UI event is a wire-level exchange and may be a Trace record. It maps to
  a Message occurrence, State occurrence, Action occurrence, Approval request,
  or other AgSDL occurrence only when the applicable correlation and semantic
  conditions are satisfied.

## Candidate test obligations

No AgSDL syntax, validator, runtime adapter, or accepted AG-UI conformance
profile exists in this repository. The following obligations are therefore
inputs to a proposal, not executable AgSDL tests or passing claims:

- validate the selected upstream schema and encoding for every fixture;
- reject a binding that mixes published 0.x behavior with unimplemented 1.0
  draft requirements;
- verify in-band version declarations, unknown-versus-malformed processing,
  downgrade warnings, and late-error behavior when the 1.0 draft is selected;
- reject invalid run, message, tool-call, interrupt, and resume sequences;
- assemble progressive messages and tool arguments without creating duplicate
  semantic occurrences;
- preserve unknown `RAW` and `CUSTOM` data as identified extensions or report
  their loss;
- apply snapshots and deltas against a declared baseline and detect divergence;
- prove the selected contract's same-thread and all-open-interrupt behavior,
  plus exact-tuple replay when the selected 0.x contract set requires it;
- distinguish approval, cancellation, denial, expiry, invalid input, and run
  error according to declared mappings;
- verify frontend Tool authorization and effect evidence independently from
  tool-call visibility;
- inject stream loss, duplicate events, reordered fragments, local abort, and
  remote non-termination, then report the declared failure behavior;
- test every AG-UI-to-MCP or AG-UI-to-A2A transformation separately and report
  information loss.

## Primary sources

Repository file links below are pinned to one of the two reviewed commits.

- [Release 2026-08-31](https://github.com/ag-ui-protocol/ag-ui/releases/tag/release/2026-08-31)
- [NPM `@ag-ui/core` 0.0.59](https://www.npmjs.com/package/@ag-ui/core/v/0.0.59)
- [NPM `@ag-ui/client` 0.0.59](https://www.npmjs.com/package/@ag-ui/client/v/0.0.59)
- [NPM `@ag-ui/proto` 0.0.59](https://www.npmjs.com/package/@ag-ui/proto/v/0.0.59)
- [PyPI `ag-ui-protocol` 0.1.22](https://pypi.org/project/ag-ui-protocol/0.1.22/)
- [Repository overview](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/README.md)
- [TypeScript event schemas](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/typescript/packages/core/src/events.ts)
- [TypeScript core package manifest](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/typescript/packages/core/package.json)
- [Python protocol package manifest](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/python/pyproject.toml)
- [TypeScript messages, run input, tools, interrupts, and resume schemas](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/typescript/packages/core/src/types.ts)
- [Capability schemas](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/typescript/packages/core/src/capabilities.ts)
- [Reference client run loop](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/typescript/packages/client/src/agent/agent.ts)
- [Reference HTTP client](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/typescript/packages/client/src/agent/http.ts)
- [Reference lifecycle verifier](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/typescript/packages/client/src/verify/verify.ts)
- [Interrupt contract](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/docs/concepts/interrupts.mdx)
- [State contract](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/docs/concepts/state.mdx)
- [Frontend tool contract](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/docs/concepts/tools.mdx)
- [Event serialization and compaction](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/docs/concepts/serialization.mdx)
- [SSE and Protobuf encoder](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/typescript/packages/encoder/src/encoder.ts)
- [Protobuf event subset](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/typescript/packages/proto/src/proto/events.proto)
- [Cross-SDK fixtures](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/sdks/fixtures/README.md)
- [Cross-SDK source-of-truth and parity rules](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/.github/skills/agui-cross-sdk-parity/SKILL.md)
- [AG-UI, A2A, and MCP positioning](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/docs/agentic-protocols.mdx)
- [MCP middleware behavior](https://github.com/ag-ui-protocol/ag-ui/blob/3f38925d0e6c19bf1f19502ee12e410e772ac142/middlewares/mcp-middleware/README.md)
- [1.0 draft status and authority](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/index.mdx)
- [1.0 draft changelog from 0.x](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/changelog.mdx)
- [1.0 draft JSON Schema](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/schema.json)
- [1.0 draft run input](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/basic/run-input.mdx)
- [1.0 draft versioning and compatibility](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/basic/versioning.mdx)
- [1.0 draft streaming rules](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/basic/patterns/streaming.mdx)
- [1.0 draft lifecycle rules](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/events/lifecycle.mdx)
- [1.0 draft interrupt and resume rules](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/basic/patterns/interrupt-resume.mdx)
- [1.0 draft processing model](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/basic/processing.mdx)
- [1.0 draft HTTP and SSE binding](https://github.com/ag-ui-protocol/ag-ui/blob/a8a1bcba0b82e4ebb8c4579ef6a86cd1bb01316e/docs/spec/draft/basic/transports/http-sse.mdx)
