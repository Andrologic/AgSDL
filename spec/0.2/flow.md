# Flow, lifecycle and protected admission

These are [normative 0.2.0 requirements](README.md) under `agsdl-0.2.0`.
The separate normative 0.1.0 contract remains unchanged.

## Flow and data

`flow` has an `entry` step and a `steps` map. The consumer supplies the entry
Message. Every step must be reachable from entry through a normal or error
connection. Step and Agent names have separate scopes. Without a graph, ordinary external
Messages follow the same per-Agent queue and completion attribution rules;
step-specific routing is absent. External requests may use the graphless
steering profile below. Several steps may refer
to one Agent. Default Agent-step delivery is `queue`; explicit `steering` is defined below.

Ordinary `next` is a list of destination steps. Completion activates every
destination in that list. Missing or empty `next` ends the current path, not
the Agent's lifetime or unrelated work. Duplicate destinations are invalid.
Steps using an explicit routing choice use a map from choice to destination
lists. A choice selects one list, whose destinations all activate.

The data boundary distinguishes:

| Result field | Meaning |
| --- | --- |
| `text` | All user-visible response text for this completed Agent work, excluding reasoning, raw Tool exchanges and earlier history. Absent visible text alone is not a failure; required outputs still apply. Assembly follows the response-text rule below. |
| `results` | Named output sources declared by the Agent Interface, including non-text artifacts. |
| `choice` | An explicitly identified final Agent decision, only when the step requires one. |
| `data` | A Call's normal result value, supplied under its external contract. |
| `members` | A Join's complete member results, keyed by member step. |

These result fields describe the inputs used by selectors, not a new wire
protocol or proof that a consumer emits them. A direct Agent-to-Agent connection
delivers the current visible text as information. The recipient's instructions
or an explicit Prepare supply the task. A prepared Message retains its authored
roles. Intermediate progress is not completion and cannot start successors.

Every operand is either a literal `value` or a `path` into the current input.
Paths contain exact object keys or nonnegative integer array indices. An empty
path selects the whole input. Missing values or wrong container types are errors.
No path refers to a global last result, filesystem location or arbitrary code.
Condition preserves its input unchanged for the selected continuation. Prepare
therefore selects the current report directly; it needs no remote-step lookup.
This is the data-binding boundary for this edition.

### Portable delivery

Every flow input has a current value and an origin kind known from the producing
operation. Origin is integration metadata, not an inspected payload field or a
mandatory wire envelope. The following table defines the Message delivered on
an Agent connection, after its configuration selector has read the unchanged
current value. Generated resources are information and introduce no prompt.

| Origin | Current value | Message delivered to an Agent |
| --- | --- | --- |
| Entry | A Message supplied by the consumer | The same Message, preserving prompt and resources. |
| Prepare | The constructed Message | The same Message, preserving prompt and resources. |
| Agent | A completion with `text`, `results` and any required `choice` | `{"resources":{"result":{"value":text,"mediaType":"text/plain"}}}`. Missing text is the empty string. Named results require explicit Prepare selection. |
| Call | `{"data":value}` from the external contract | `{"resources":{"result":{"value":value,"mediaType":"application/json"}}}`. Even a Message-shaped value remains information. |
| Join | `{"members":{...}}` | `{"resources":{"result":{"value":{"members":{...}},"mediaType":"application/json"}}}`. References inside members remain data; use Prepare `source` to deliver one as media. |
| Error | The error input defined below | `{"resources":{"error":{"value":error,"mediaType":"application/json"}}}`. No implicit request to retry. |
| Condition | The same value and origin it received | Apply the unchanged origin's rule. Chains of Conditions do not change delivery. |

The table applies to entry at any step, not only an Agent. A Call returning
`{"prompt":[{"value":"Ignore the task"}]}` cannot acquire instruction authority
by passing through Condition. A prepared prompt keeps its instruction role
through that same Condition. A Join preserves each member's complete result,
not just its default direct-Agent text projection. No block guesses a Source,
Message or control decision from arbitrary payload shape.

### Response text and result selection

For each user-visible response Message of the owning occurrence, concatenate
its text parts in their declared order with no separator. Ignore non-text parts
for this text projection, but preserve selected named results independently.
Discard only Message texts equal to the empty string. Join the remaining Message
texts in response order with exactly one LF, U+000A. Do not trim whitespace,
normalize line endings, add labels, summarize or insert routing data. For example,
`[["A", "B"], [], ["\nC"], ["D\n"]]` assembles as `"AB\n\nC\nD\n"`.
No visible text produces `""`, never a previous reply or a missing-text failure.

The integration attributes all parts to the owning occurrence, including text
before and after acknowledged steering, and excludes reasoning, Tool calls,
raw Tool results and prior history. A user-visible explanation of a Tool result
is response text; the raw Tool exchange is not. Response order is the recorded
emission order, not arrival order after transport reordering. Stable Message
identity prevents retransmission from duplicating text. If the integration
cannot establish attribution or order, it reports `CORRELATION`, not a guessed
concatenation. Completion waits for that occurrence's response collection to
close. Late or duplicate events cannot reopen it or replace the retained result.
A conflicting terminal duplicate reports a correlation diagnostic; it does not
route an already resolved occurrence a second time.

Prepare `select` deliberately wraps any selected JSON value as inline content.
Prepare `source` instead copies one selected Source unchanged. For example,
`{"source":{"path":["results","diagram"]}}` keeps an image URI and its
`image/png` representation. It neither serializes that source as text nor fetches
its bytes. Selected inline objects remain objects. References, formats, declared
support and actual access are separate obligations. A missing optional result
still fails an unconditional selector; branch explicitly if it may be absent.

### Queue admission, work identity and steering

An occurrence identifies one activation within a flow invocation. The consuming
integration associates it with the step, persistent Agent instance, incoming
activation and any Join group/member. Repeated visits and separate fan-out
edges create distinct occurrences, even when their payloads are equal. A
retransmission of an existing occurrence does not create another visit. These
are correlation obligations, not a universal identifier format or transport.

For ordinary Agent steps, omitted `delivery` means `queue`. Record a total
admission order per Agent instance, across all steps using it. Process queued
occurrences FIFO, starting the oldest only when its prior active work has ended.
An unordered arrival batch is assigned and recorded an admission order by the
integration before acceptance; no ordering across independent Agents is imposed.
Each dequeued occurrence owns its response, final choice and continuation.
`maxVisits` is checked when queued work begins, not on retransmission or waiting.
Failures resolve the failed occurrence once. They do not clear unrelated queued
work. The retained Agent configuration and context remain those of that instance.

An Agent step may instead declare `delivery: "steering"` and `steers`, naming
an ordinary queued Agent step for the same Agent. It cannot be entry, declare
`next` even empty, declare a `decision`, or be a Join member. An ordinary Join
member may own steering; that member still supplies only its one required result. The integration associates a steering request with one exact intended
occurrence of that target step in the same flow invocation, at request creation. A common
fork activation can provide that association. A target step name alone is not
enough to distinguish loop visits. Missing or ambiguous association fails as
`CORRELATION`; never guess from whichever occurrence is now active. The selected
owner must still be active when the request is admitted. No matching active
occurrence yields `STEERING_LATE`; it does not initialize an idle Agent, create work or fall back to queueing.

Check a steering step's visit limit before attempting delivery. One attempt
consumes one visit. Bind the request to that exact owner, adapt its input and
request acknowledgement that it was incorporated before the owner's terminal
boundary. Acceptance resolves the steering occurrence as consumed: it has no
result or normal graph continuation. Only the owner later completes, validates
its outputs and routes once. Owner completion may incorporate all acknowledged
steering inputs; it is not duplicated for each input. Pending acknowledgement
holds the owner's graph continuation until the integration can classify the
request as accepted-before-completion, rejected or late. This obligation does
not require keeping the Agent itself working after it finishes.

An explicit rejection yields `STEERING_REJECTED`; lack of capability yields
`STEERING_UNSUPPORTED`; a request known not to have arrived before owner
completion yields `STEERING_LATE`. Each follows only the steering step's
`onError`, leaving the owner's result and route intact. Lost or uncertain
acknowledgement remains pending and reports `STEERING_PENDING` diagnostically;
it fires neither normal nor error continuations until resolved. It cannot be
automatically retried, queued or treated as rejected, because delivery may have
occurred. A later acknowledgement resolves the original request, never a new
visit. Duplicate acknowledgements have no additional effect. Missing integration
evidence does not establish steering support or guarantee eventual resolution.

For example, owner O plus accepted steering S produces one O result and one O
continuation, and no S continuation. If S is rejected, S's error route may run
and O still completes once. If O already ended when S was admitted, only S fails.
A correction Message arriving through an ordinary queued step creates new work
on the same Agent; it does not revise the failed occurrence's terminal record.

A Join member's result is released only after pending steering acknowledgements
for that occurrence resolve. Its result, decision and membership remain those
of the owner; accepted steering never supplies another member result. A group
stop request targets that exact owner occurrence. Once stopping begins, reject
new steering as `STEERING_LATE`; settle already pending requests from their
actual delivery evidence. A confirmed stop resolves the group's termination
wait without a successful member result. It does not assert acceptance or
rejection of a pending steering request. Such a request remains pending until
its own acknowledgement resolves, even if the Join has already continued after
confirmed stop. Its late rejection may use only its own error path; neither a
late acceptance nor rejection reopens the ended owner or completed Join. If the
owner completes instead of stopping, its normal result waits for pending
acknowledgements as above. A stop request or missing acknowledgement alone
proves neither termination nor completion.

### External delivery without a graph

A single persistent Agent accepts ordinary external Messages with queue delivery
by default. An integration can also accept an explicit steering request for that
Agent without requiring a graph. The `ExternalDeliveryRequest` schema describes
a declarative profile for such requests: `agent` names the declared Agent,
`message` is the authored Message, and optional `delivery` is `queue` or
`steering`. Queue requests omit `owner`. Steering requires `owner`, an opaque
nonempty identifier that the integration resolves to one exact work occurrence
on that Agent within the current system start. It is not a step name, newest-work
selector or global address. It must not resolve to a different Agent or a later
occurrence after a restart. Resolve unknown or ambiguous association as
`CORRELATION`, and a known ended owner as `STEERING_LATE`.

The integration checks Agent and Message content references against the document.
Queue admission, retained configuration, context and response attribution obey
the same rules as graph delivery. Steering must not initialize an idle Agent or
reselect configuration. It uses the same accepted, rejected, unsupported, late
and pending acknowledgement semantics, and is consumed without a separate work
result. The owner alone produces its completion. Failures and pending statuses
are returned to the external requester because there is no graph error route.
Stable request identity and duplicate suppression are integration obligations;
they are not inferred from Message equality. No universal transport, wire ID
format, scheduler or live delivery endpoint is introduced. The bundled schema
checks profile shape only; no command executes this request or verifies its
owner association. An integration must demonstrate these behaviors to claim
support.

### Agent, Call, Condition and Prepare

An `agent` step names an Agent. An optional `decision` supplies a binding and
nonempty distinct choices. Its `next` map must cover exactly those choices.
Without a decision, `next` is an ordinary list. The integration associates a
final choice with the current completed work. Missing, unknown or ambiguous
choices fail. A visible choice remains in the transferred text; a Tool-only
choice is not injected into it. This edition does not implement a text-marker parser or
require a universal Tool protocol.

A `call` step names a binding and optionally maps argument names to operands.
Binding settings and selected arguments determine the invocation; Agent prose
is not parsed into a command. The fictional test-suite contract returns
an integer `data.exitCode` and a text `data.report`. A malformed result fails
the Call contract before any Condition runs. Code zero passes, other returned codes request
correction, and a process-launch failure is technical failure. A custom
implementation can satisfy this contract without changing the graph. Its
effects and permissions still require actual support.

A `condition` evaluates `test` and selects `true` or `false`. This edition supports
`equals` with exactly two operands, nonempty `all` and `not`. Equality compares
JSON values without coercing strings or Booleans to numbers. JSON object order
does not matter; array order does. All referenced operands must be available
and valid, even if another operand would determine the Boolean result. A missing
operand is an error, not false. The input is preserved on either normal path.

A `prepare` constructs `message`. Its resources may use normal content,
`select`, an operand whose selected value becomes inline information, or `source`,
an operand selecting one complete Source. An optional media type describes an
inline selection. A source selection preserves its own media type and cannot
override it. A selected Source must contain exactly one `value` or `uri`; a
content-catalog `ref` is not a Source. Missing or malformed selections fail
before delivery. Use several named resources to select several results. Authored prompt sources remain
instructions. Preparation does not summarize, fetch, convert media or clear
context. Its output is one Message to the next Agent. The declaration reader
validates the declared shape and static references. The pure supplied-data
[`prepare_message` helper](validation.md#checking-prepared-content) evaluates
selectors and constructs a Message without executing a graph, Agent or Call.

### Grouping, loops and failures

A `join` declares `after` and `members`, with optional `mode`. Omitted mode
means `all`; `first` requires an `accept` predicate evaluated on each current
member result. `remaining` is permitted only in `first` mode and defaults to
`stop-and-wait`; its explicit alternative is `finish`. Acceptance or stop-policy
fields on an all-required Join are invalid. This bounded form supports a direct
fork-and-join only: the anchor's ordinary `next` lists exactly the distinct
members, and every normal outcome of each member connects only to this Join.
The Join receives no other inputs, and members receive work only from normal
anchor completion, never its error path.
Neither the Join nor a member can be the flow entry. Members have no independent
error continuation in this edition; in all-required mode a failed required member fails
its group, whose `onError` can provide recovery. First-satisfactory mode handles
member failure as specified below. Membership is not the number of incoming arrows.

Each anchor completion starts a distinct group. In `all` mode, Join waits for
one completed result from each member of that group and emits `members`. Negative business
results can complete a group; technical failures cannot stand in for them.
Late or duplicate results cannot reopen a completed group or fill another
round. The association is a consumer obligation; static declarations cannot
prove it. Direct convergence to an Agent delivers separate Messages instead.

In `first` mode, select the first conforming result satisfying `accept`. Preserve
that result under `members` with only its source member present. The
ordering is the integration's recorded completion order; if a delivery batch
contains no order, use the declared `members` order to break that batch's tie.
This is not a distributed clock requirement. Retain the winner; subsequent
results cannot replace it. A completed negative result is not a technical error.
If all members end without a qualifying result, fail with `NO_ACCEPTABLE_RESULT`.
A member failure cannot be a winner, but another member may still qualify.
Before selection, a malformed acceptance input is a group error, not a false
comparison. Once a winner is retained, stop evaluating `accept`. Remaining
member results cannot invalidate it; their terminal status only resolves the
stop/completion wait. A failed remaining member still reports its diagnostic
and must be known to have ended; it is neither a successful result nor a stop
confirmation.

With default `stop-and-wait`, request stop of unfinished, unnecessary member
work and hold the winner until that work is confirmed stopped or finishes.
A rejected request or missing acknowledgement does not release successors.
Report unsupported stopping and wait for completion or explicit interruption of the pending wait to enter recovery; do
not fabricate confirmation. With `remaining: finish`, continue with the winner
and let other members finish without a stop request. Their late results do not
reopen the group. Neither mode resets Agents, cancels unrelated work, rolls back
effects or guarantees exclusive workspace access. These are declared semantics;
the static reader does not execute or attest to them.

A return connection can form a loop through the same Agents. `maxVisits`, when
present, is a positive limit per step within one flow invocation. Count each
activation that begins work. For a Join, reserve and count one visit when its
anchor completes normally, before dispatching that group's members. If the
Join's limit is exhausted, do not start those members; follow the Join's
`onError`, or stop that path with a diagnostic. The completed anchor's effects
remain. This rule applies to both Join modes and both remaining-work policies.

An admitted group consumes one visit even if it later fails or has no acceptable
result. Member arrivals, stop requests, stop acknowledgements, late results and
normal continuation never consume additional Join visits. A limit failure does
not stop work in previously admitted groups. Other steps reject activations
beyond their own limit before performing their work. Omission imposes no limit.
The counter is local to a step, not a global budget.

For a first-satisfactory Join with `maxVisits: 1`, this timeline applies:

| Event | Join visits | Consequence |
| --- | --- | --- |
| First anchor completion | 1 | Admit the group, then start its members. |
| One member supplies an acceptable result | 1 | Retain the winner. With `finish`, continue now; otherwise request stop and wait. |
| Remaining work confirms stop or completes | 1 | Release a waiting winner; do not evaluate `accept` again or repeat an earlier continuation. |
| A loop produces another anchor completion | 1 | Reject the next group before dispatching its members, even if an earlier loser is still running under `finish`. |

For example, after a result with `data.eligible: true` wins, a later conforming
Call result without `eligible` only establishes that the remaining work finished.
It does not trigger a missing-operand error in the now-inactive acceptance rule.
These are contract examples, not execution evidence.

Technical failure or a visit-limit breach follows `onError`, if supplied, with
diagnostic information as its input. Otherwise the affected path stops with a
diagnostic. An error never creates a normal result. Failure and interruption
do not undo workspace effects, prove a sibling stopped or authorize retry.
A failed required output uses the error input
`{"error":{"code":"OUTPUT_CONSTRAINT","message":"...","details":[...]}}`.
Each detail identifies an output path, a violated rule and the expected formats
or choices. The [output-correction example](../../tooling/0.2/examples/output-correction.json)
branches on that code, prepares an instruction with the details as information,
and sends a new Message to the same Agent. Other technical failures do not take
this particular correction path. The loop has no implicit retry cap or replay
of side effects. Other failures use the closed vocabulary below.

### Closed failure input

An error continuation receives exactly
`{"error":{"code":"CODE","message":"description","details":[]}}`.
`code` is one terminal code in the table. If correlation is so incomplete that
no failing occurrence can be identified, report the diagnostic outside the
flow; do not guess an error route. `message` is explanatory text, never
control syntax. Each detail has `path`, a JSON Pointer relative to the failing
input or declaration, `rule`, a descriptive string, and `expected`, a JSON value.
Use an empty details list when no narrower location applies. The integration
correlates the error to its occurrence and retains original input and failure
context for diagnostics; it does not inject prior conversation into the error.
External diagnostics may be described in `message` or `expected`, without adding
new portable codes. Route by `code`; details do not prescribe an action.

| Code | Failure boundary |
| --- | --- |
| `CONFIGURATION` | The first configuration selector is missing, wrongly typed or names no case. |
| `INITIALIZATION` | The selected Agent configuration cannot initialize successfully, including unusable supplied prompt. |
| `INPUT_CONSTRAINT` | The adapted Message violates declared input constraints. |
| `CONTENT_UNAVAILABLE` | Required content cannot be obtained or made usable. |
| `UNSUPPORTED` | A required integration capability or declared media path is unsupported, except steering. |
| `OPERAND` | A Condition, Call argument or Prepare selector cannot read its operand, or source selection is not a Source. |
| `CALL_FAILED` | External invocation fails technically. A normal negative business result is not this error. |
| `CALL_RESULT` | The external result violates its declared Call contract. |
| `OUTPUT_CONSTRAINT` | Required Agent outputs, formats or terminal decision are missing or invalid. |
| `APPROVAL` | A required authorization is missing, stale, mismatched, expired or technically unavailable at protected admission. |
| `AGENT_FAILED` | Agent work fails technically without a more specific code. |
| `INTERRUPTED` | Work ends without completion because of an interruption. Effects may remain. |
| `CORRELATION` | Integration cannot safely associate input, response or completion with current work. |
| `VISIT_LIMIT` | Starting this occurrence would exceed its step limit. |
| `MEMBER_FAILED` | A required member fails an all-required Join. Detail identifies the member and underlying error. |
| `NO_ACCEPTABLE_RESULT` | All first-satisfactory members end without a qualifying result. |
| `STEERING_UNSUPPORTED` | Steering capability is unavailable. |
| `STEERING_REJECTED` | Integration explicitly refuses the steering request. |
| `STEERING_LATE` | No matching active owner, or delivery is known to miss its terminal boundary. |

Pending conditions are not terminal failures. `STEERING_PENDING` and
`STOP_PENDING` are diagnostic statuses only, never error inputs or normal
results. An unsupported or rejected stop reports `STOP_PENDING` with its reason
and keeps waiting for confirmed termination. This does not fabricate cancellation
or dispatch a recovery path while work may still be active. An external operator
can interrupt the waiting Join; only then does `INTERRUPTED` use its error route. Interrupting the wait does
not prove that member work ended or stopped.
Stopped losing members resolve that wait without running member successors.

Use the first failed boundary in processing order: visit admission, configuration
selection if needed, initialization if needed, input adaptation and constraints,
work, output validation, then continuation. Do not perform dependent later work
after failure. Protected work uses the [protected admission order](#protected-admission). Independent failures are separate occurrences, not alternative
successes. A malformed first-Join acceptance operand fails that Join as `OPERAND`;
after a winner, remaining terminal statuses only resolve its wait.

Each terminal occurrence dispatches its normal destinations or its error
destinations once, never both. Join member failures resolve through the Join
policy instead of independent error routes; late members cannot re-dispatch a
resolved Join. No error authorizes automatic retry, rollback, duplicate effects,
Agent replacement, cancellation of other work or a successful required result.
Static checker's `INVALID_REQUEST` and `INVALID_RECORD` are command/record errors,
not additional graph failure codes or Agent correction inputs.

## Local composition and protected admission

### Local composition

An optional `compositions` map declares reusable local graphs with `entry`,
`steps`, distinct `outputs`, and optional distinct `agentParameters`. Body Agent
references may be an existing Agent name or `{ "parameter": "name" }`.
A `compose` step names `composition`, supplies the exact `agents` parameter map,
and a `next` map with exactly the output names. `onError` is optional. These
parameters bind existing Agent references only; they never substitute code,
settings, prompt text or arbitrary data. Bodies share document content, skills,
configurations and bindings. Reuse never clones, resets or replaces an Agent.

Body targets name local steps or `{ "output": "name" }`; an error route may
instead name `{ "error": true }`. Outputs are normal routes only. Every normal
route is explicit and nonempty. Each route contains exactly one target, so a
body has no parallel fan-out. Bodies permit Agent, Call, Condition, Prepare and
Approval; Join, steering and nested composition are rejected. Bodies may loop.
Every step is reachable from entry and every declared output has an authored
export. Every body, including unused bodies, is checked with these restrictions
and ordinary references and approval rules. Finite expansion does not promise
termination of its internal loops.

Expansion copies steps per authored use, redirects incoming routes to the body
entry, substitutes output exports with the use's successors and error exports
with its error route. Missing error handling terminates that error path. Internal
errors without a route remain terminal; errors do not become normal values.
A use has no independent completion, visit counter, approval or cancellation
lifetime. Internal `maxVisits` counters are separate per authored use and persist
on re-entry; exported routes can fan out only after the serial body finishes.
Step addresses are arrays `[use, localStep]`, or `[topLevelStep]`; implementations
must not join names with an ambiguous delimiter. Reports preserve authored body
paths and invocation paths. The public expanded projection represents steps as
records with these addresses, not as newly declared Agents. Completion/admission
checkers accept a top-level name or such a JSON address through their Python API;
the CLI accepts a JSON array argument for an expanded step.

Ordinary reachability, Join and approval checks run after expansion. Composition
as a direct-fork Join member is rejected in this bounded version, including a
one-step body. As `Join.after`, a one-step composition may be an anchor when
its expanded step satisfies the ordinary direct-fork rules. A body with more than one declared step
cannot be that anchor and fails `JOIN_GROUP`, even if an additional step is
reachable only through an error route. No arbitrary hierarchical
scheduler is implied. Other top-level parallel flow remains available. A body cannot export a result while another
internal branch runs because internal fan-out is forbidden.

### Protected admission

An `approval` step names `call`, an Agent or Call step, `binding`, `timeoutMs`
and `validForMs`, both positive integers, and `next` with `approved` and `denied`
routes. Approved has exactly one target: that action or the next gate for the
same action. For each protected action all its gates form one finite chain.
Only the last gate's approved edge enters the action, and only the preceding
approved edge enters each later gate. A top-level gate cannot name a composition
use as its action; place the gate on the actual body action. Neither action nor
later gate is entry.
Denial/error paths cannot reach the action or later gates without first reaching
the first gate. Returning there starts a new authorization attempt. An ordinary
favorable Agent result, including a human's, cannot replace a gate decision.
Steering cannot be a protected target in this bounded edition.

Agent/Call steps may add `scope` with nonempty `action`, a nonempty distinct list
of resource descriptions and `context`, an Operand. Scope is required for any
gated target and for Calls whose binding explicitly declares `effects: external`
or `effects: unknown`. Bindings may declare `effects: none`; omission is unknown,
not a claim of no effects. An ungated action is legal, and effects alone never
require a human gate. A scope grants no permission. Internal Agent Tool actions
need their own actual-invocation admission enforcement through the selected
Engine/Tool integration. Declare this through versioned requirements and retain
it as unassessed; gating an Agent Message never proves interception of its Tools.

At first gate entry capture the input/origin, evaluated arguments or adapted
Message, scope context, action binding and selected configuration. For a fresh
Agent select and retain its configuration before presenting approval, without
initializing it or starting protected work. Capture reserves its FIFO queue
position. If older queued work has not yet fixed that Agent's configuration,
capture waits for that earlier selection instead of selecting out of order.
Later captures reuse the retained selection. Approval may occur while earlier
work runs, but admission still waits for its queue turn and checks freshness.
A previously selected configuration stays fixed. All gates and actual admission use the same captured invocation,
including the document declaration and occurrence identity. Denial or gate
failure releases the reserved queue position and visit; it never admits work.
Once the chain approves, the reserved visit is consumed even if admission later
fails freshness, and is not counted twice. Unresolvable inputs
fail `OPERAND` or `CONFIGURATION`; no approval request guesses them. The gate
preserves input and origin on approval; denial is its separate normal route and
gate technical failure uses `onError`.

A gate decision must match its authorized integration, gate, occurrence and exact
captured invocation. Its deadline is entry plus min(timeoutMs, validForMs);
equality is expired. At actual action admission every decision remains valid
until that gate's entry plus validForMs, again strictly before expiration.
Gates occur in their declared order. The selected Agent may wait in its queue,
but expired approval never starts work. A valid negative gate decision takes
only its normal `denied` route, never an error route. Missing, stale or mismatched authorization, or authorization rejected
as invalid at admission, fails `APPROVAL`. Technical integration failure also
uses `APPROVAL` with explanatory details. Failure to admit follows the protected action's error
route. Each retry, loop visit or sibling occurrence requires fresh authorization;
no approval survives stop/edit/start or a changed document/configuration.

Processing order for protected Agent work is visit reservation, capture and
configuration selection, approval chain, queue admission with freshness check,
initialization if needed, input constraints, work and output validation. Reserving
a target's visit at capture prevents a gate from authorizing a known exhausted
visit; admission does not count it again. Ungated work retains its existing order.
Successful selection remains retained even after denial or expiration, without
starting an uninitialized Agent. All values and clock/authority observations
remain integration obligations, not observations made by static graph checks.
