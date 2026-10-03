# Persistent-Agent flow candidate

Status: **bounded experimental candidate `agsdl-exp-flow-0.2-c1`, not adopted,
published or the complete 0.2 release scope.** This directory turns the basic
walkthroughs into machine-readable examples and static checks. It follows the
accepted directions in [0019](../../proposals/0019-agent-prompt-and-resources.md)
and [0020](../../proposals/0020-blueprint-flow-0.2.md), with the proposed block
contract in [0021](../../proposals/0021-logic-block-contract-0.2.md).

This document defines c1's proposed rules. The schema derives from these rules;
the reader checks their stated static subset. Existing official and frozen
experimental contracts retain their meaning. Final adoption needs a separate
decision. Read [the release-scope gaps below](#remaining-release-scope) before
using this candidate to assess readiness.

## Read or check an example

| Example | What it exercises |
| --- | --- |
| [Conversation](examples/conversation.json) | One Agent, a reusable configuration and an explicit Engine binding; no initial prompt or graph. |
| [Test loop](examples/test-loop.json) | A persistent developer, custom test Call, deterministic Condition and prepared correction Message. |
| [Parallel reviews](examples/parallel-reviews.json) | Two final decisions grouped for the same developer completion, followed by one correction Message. |
| [Output correction](examples/output-correction.json) | A missing required report produces a diagnostic and a correction Message for the same Agent. |
| [First satisfactory review](examples/first-review.json) | Explicit acceptance rule, with stop-and-wait as the default for remaining work. |
| [Steering](examples/steering.json) | Explicit owner, consumed steering occurrence and a separate error path. Parallel launch does not guarantee the owner is still active; a late delivery is an expected possible failure. |
| [Selected media](examples/selected-media.json) | Preserve a named image Source through Prepare and an identity Condition. |
| [Multimedia and reuse](examples/multimedia-and-reuse.json) | Reusable skill instructions, two Engine choices, multiple media and required versus optional outputs. |

All Engine, Tool, implementation and contract identities are fictional. Their
settings describe example requirements, not installed software or granted
permissions. The fictional Engine contract interprets `workspace` and `access`
in configuration settings; they are not universal Engine-setting names. The examples do not run tests, read resources or start Agents.

From the repository root, using Python 3 and its standard library:

```sh
python3 experimental/agent-flow-0.2/reader.py experimental/agent-flow-0.2/examples/test-loop.json
python3 experimental/agent-flow-0.2/test_reader.py -v
```

Exit codes are 0 for a valid checked document, 1 for an invalid document or
unsupported parse input, and 2 for command usage or file-access failure.
Reports identify their scope and always say `executionSupport: not-assessed`.
With `jsonschema` installed, check the schema and compare shape validation
against a separate implementation:

```sh
python3 experimental/agent-flow-0.2/test_reader.py --schema
```

That comparison covers shapes only. It is not a second independent semantic
reader and does not validate runtime behavior.

## Document and content

A document requires `contract`, `id`, `agents`, `configurations` and `bindings`.
`content`, `skills` and `flow` are optional. Maps use distinct names matching
ASCII letter followed by ASCII letters, digits, underscore or hyphen. Unknown
fields are invalid except inside explicitly open inline values, settings and
external requirement parameters. Duplicate JSON object members, non-JSON
numbers and unpaired Unicode surrogates are rejected. The Python reader keeps
decimal values exact while checking integer constraints; excessive parser
depth or numeric representation limits produce a parse failure, not success.

The [schema](schema.json) lists the closed shapes, required fields and types.
Omitted optional maps and lists are empty unless a rule below states otherwise.
An object key inside a literal `value` or `settings` object is never interpreted
as an AgSDL reference. Validators neither fetch content nor load implementation
code.

A content source contains exactly one `value` or `uri`, and an optional
`mediaType`. Inline strings are literal. URI availability, resolution and access
belong to the selected integration and remain unassessed by this static reader.
The examples use absolute URIs; portable relative-URI bases remain release work.
A content use may instead contain only `ref`, naming a source in `content`.
Those source declarations do not themselves contain references, so reference
cycles cannot form in this catalog.

A Message contains optional `prompt` and `resources`. `prompt` is an ordered
list of instruction content uses; `resources` is a map of named information
content uses. Names identify information without assigning it instruction
authority. Both can carry text, structured values or media references. Actual
Message addressing and delivery use the consumer's integration, not a transport
defined here.

## Agents, configuration and reusable behavior

Each Agent names one fixed configuration, or supplies `select` and `cases`
for a declared pre-initialization choice. The selector reads the first current
flow value before delivery adaptation; its value must be a string naming a case.
A missing value, wrong type or unknown case fails without a default. Evaluate a
dynamic choice when the first queued work begins, before initializing the Agent.
Retain a successful selection once for that instance;
later Messages use the retained configuration without evaluating the selector
again. They need not repeat the selection data. Even a later value naming a
different case is ordinary input, not a reconfiguration request. A fixed
configuration can be prepared before its first Message. This is the proposed
concrete rule for the accepted pre-initialization direction. An Agent can add `prompt`, `resources`, `skills`
and an `interface`. The Agent is one persistent participant, including human
participation where the integration supplies it. Visiting an Agent step again
uses its existing instance and context. There is no per-visit initialization,
context reset, implicit spawning or hot configuration replacement.

For example, in the [output-correction example](examples/output-correction.json),
a dynamic configuration could select `project` from the first Message's
`resources.mode.value`. The correction Message contains only `output-errors`:
it reaches the same Agent using `project`, with no selection data to reconstruct.
A later Message carrying a different mode still cannot change that instance.

For Call → Condition → Agent, selection therefore reads `data` from the Call
result. For Prepare → Condition → Agent, it reads the prepared Message.
Condition changes neither value nor origin. Selection failure leaves the Agent
uninitialized and produces `CONFIGURATION`; a later explicitly authored attempt
may select again only while no configuration has been retained. Once selected,
the configuration remains fixed even if initialization or delivery fails. An
initialization failure does not authorize replacing a partially initialized
instance or replaying effects; recovery needs the integration to report a usable
instance or requires stop, edit and start.

No initial prompt means no implicit initial task. A configuration's explicit
Engine binding is required even when the Agent waits for its first Message.
Configuration has optional Model edition, Tool bindings, settings and capability
requirements. No provider or Model default is inferred. The consumer enforces
its declared access and delivery policy.

`bindings` separates an external versioned `contract` from the selected
versioned `implementation`, with optional `settings` and `requires`. Each edition
has an open `identity` and `version`; their spelling establishes no support.
A configuration names its Engine binding and maps local Tool names to Tool
bindings. Calls and decision integrations also reference declared bindings.
The external contracts establish their intended role and capabilities; c1 checks
reference existence, not compatibility or whether an implementation satisfies
that contract. Opaque settings cannot redefine the AgSDL step semantics.

Reusable skills contain prompt sources, resource sources and optional capability
requirements. They have no Engine assignment. Expand selected skills in their
declared order, then append the Agent's own prompt. Merge resource maps without
overwriting: duplicate skill selections or colliding resource names are invalid.
Two Agents selecting one skill or configuration still have separate contexts.
Configuration or skill changes follow stop, edit and start.

An optional Interface declares accepted input formats, permitted output formats
and named result constraints. Media types are open strings. Each named result
has permitted `mediaTypes`; `required` defaults to false. Permitting several
formats does not require all of them. Required named results must exist at
completion and use one allowed format. A result's formats must fit any declared
overall output formats. Content format, structure, actual availability and
delivery remain distinct requirements. c1 has no structured-value shape
constraint or compatibility-evidence evaluator; these are release-scope gaps.

Requirements are external contract editions plus optional parameters. Presence
of a requirement is not evidence it is met. Missing support, simultaneous media
delivery, Model/Engine/Tool compatibility and access remain unassessed, never
silently classified as supported. A video URI must not be treated as text or a
transcript without an explicit conversion contract.

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

The proposed data boundary distinguishes:

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
This is a proposed simplification of data binding under 0021.

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
choice is not injected into it. c1 does not implement a text-marker parser or
require a universal Tool protocol.

A `call` step names a binding and optionally maps argument names to operands.
Binding settings and selected arguments determine the invocation; Agent prose
is not parsed into a command. The fictional test-suite contract returns
an integer `data.exitCode` and a text `data.report`. A malformed result fails
the Call contract before any Condition runs. Code zero passes, other returned codes request
correction, and a process-launch failure is technical failure. A custom
implementation can satisfy this contract without changing the graph. Its
effects and permissions still require actual support.

A `condition` evaluates `test` and selects `true` or `false`. c1 supports
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
context. Its output is one Message to the next Agent. c1 does not implement
these operations; it validates their declared shape and static references.

### Grouping, loops and failures

A c1 `join` declares `after` and `members`, with optional `mode`. Omitted mode
means `all`; `first` requires an `accept` predicate evaluated on each current
member result. `remaining` is permitted only in `first` mode and defaults to
`stop-and-wait`; its explicit alternative is `finish`. Acceptance or stop-policy
fields on an all-required Join are invalid. This bounded form supports a direct
fork-and-join only: the anchor's ordinary `next` lists exactly the distinct
members, and every normal outcome of each member connects only to this Join.
The Join receives no other inputs, and members receive work only from normal
anchor completion, never its error path.
Neither the Join nor a member can be the flow entry. Members have no independent
error continuation in c1; in all-required mode a failed required member fails
its group, whose `onError` can provide recovery. First-satisfactory mode handles
member failure as specified below. Membership is not the number of incoming arrows.

Each anchor completion starts a distinct group. In `all` mode, Join waits for
one completed result from each member of that group and emits `members`. Negative business
results can complete a group; technical failures cannot stand in for them.
Late or duplicate results cannot reopen a completed group or fill another
round. The association is a consumer obligation; static declarations cannot
prove it. Direct convergence to an Agent delivers separate Messages instead.

In `first` mode, select the first conforming result satisfying `accept`. Preserve
that result under `members` with only its source member present. The proposed
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

For a first-satisfactory Join with `maxVisits: 1`, this proposed timeline applies:

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
A failed required output uses the proposed error input
`{"error":{"code":"OUTPUT_CONSTRAINT","message":"...","details":[...]}}`.
Each detail identifies an output path, a violated rule and the expected formats
or choices. The [output-correction example](examples/output-correction.json)
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
after failure. Independent failures are separate occurrences, not alternative
successes. A malformed first-Join acceptance operand fails that Join as `OPERAND`;
after a winner, remaining terminal statuses only resolve its wait.

Each terminal occurrence dispatches its normal destinations or its error
destinations once, never both. Join member failures resolve through the Join
policy instead of independent error routes; late members cannot re-dispatch a
resolved Join. No error authorizes automatic retry, rollback, duplicate effects,
Agent replacement, cancellation of other work or a successful required result.
Static checker's `INVALID_REQUEST` and `INVALID_RECORD` are command/record errors,
not additional graph failure codes or Agent correction inputs.

### Checking recorded outputs

[check_completion.py](check_completion.py) validates a supplied completion record
against the selected Agent step. A record has optional `text`, `responseMessages`, `results` and
`choice`; each named result is a content source. `responseMessages` is an ordered array
of arrays of visible text parts, already filtered and attributed by the caller.
When supplied, the checker assembles it by the rule above. If `text` is also
supplied it must equal that assembly; a mismatch is `INVALID_RECORD`. With only
`text`, the checker cannot verify assembly. A successful report includes the
assembled `text`, or supplied `text`, or the empty string. It does not claim
that the record includes every actual response. Missing required results,
incompatible declared formats or a missing/unknown required choice produce
`OUTPUT_CONSTRAINT`. Absent text with valid required artifacts succeeds. Merely
writing a completion sentence does not substitute for a required artifact.

The command accepts a document path, an Agent step name and a JSON result path:

```sh
python3 experimental/agent-flow-0.2/check_completion.py DOCUMENT.json STEP RESULT.json
```

It checks recorded declarations only: it does not fetch a URI, inspect file
bytes, verify MIME content, associate a real execution or enforce termination.
The integration must check actual delivery and support. Invalid document/step
requests yield `INVALID_REQUEST`; malformed records yield `INVALID_RECORD`.
A `choice` supplied for an Agent step without a declared `decision` also yields
`INVALID_RECORD`; ordinary text containing a choice word remains plain text.
Those errors are distinct from an Agent's correctable output constraint failure.
Exit codes are 0 for a conforming record, 1 for a rejected record/request and
2 for command, file or parsing failure. No command schedules a correction.
A runtime must route the error through the authored flow and supply the declared
Message itself.

### Checking recorded delivery

[check_delivery.py](check_delivery.py) checks a claimed boundary record, without
running the graph or retaining live Agent state:

```sh
python3 experimental/agent-flow-0.2/check_delivery.py DOCUMENT.json AGENT RECORD.json
```

A record contains `origin`, `input`, `message` and the claimed `configuration`.
Origin is one of the six producing origins in the delivery table; an intervening
Condition retains that origin and input. Optional `retainedConfiguration` states
a previously selected configuration. The checker verifies that it belongs to
the Agent's alternatives and skips selection on this new input. Without that
field it evaluates the selector on `input` before checking the delivered Message.
It compares Message values without changing instructions, Sources or input data.
Entry and Prepare Message `ref` uses must exist in the document content catalog;
objects inside literal `value` are not interpreted as references. Recorded Join
results require a nonempty map of valid member names and complete result shapes:
Agent completion, Message, Call result, Join result or preserved error input.
An identity Condition may preserve any of those shapes. Shape alternatives can
overlap, especially an empty Message and empty Agent completion; accepting that
shape does not infer its origin. Exact membership/cardinality for a particular
source Join, member output constraints and nested provenance remain unassessed
because this command selects a destination Agent, not a source Join.
It rejects an unresolved selector as `CONFIGURATION`, a malformed record or
inconsistent claim as `INVALID_RECORD`, and an invalid document or unknown Agent
as `INVALID_REQUEST`. Exit codes are 0, 1 and 2 as for the completion checker.

This checks recorded data, not whether origin, retention, Condition identity,
response filtering or actual delivery occurred. Agent completion shapes are
checked here; use the completion checker for its output constraints. External
Call contracts, content availability, lifecycle ordering, acknowledgement and
runtime attribution remain integration obligations. The record has no capacity
to certify those claims. Pending status codes are rejected as terminal errors.

## Static checks and evidence limits

The reader implements these rule codes:

| Code | Checked condition |
| --- | --- |
| `PARSE` | Input can be read without duplicate keys, invalid Unicode, non-JSON values or unsupported parser limits. |
| `SHAPE` | Document matches the bundled closed schema and marker. |
| `REFERENCE` | Referenced content, skills, configurations, bindings, Agents and destination steps exist. |
| `DUPLICATE` | A skill, choice or destination is not repeated where it would duplicate application or work. |
| `RESOURCE_COLLISION` | Skill expansion cannot overwrite a resource. |
| `OUTPUT_FORMAT` | A named result's formats fit the overall allowed output formats. |
| `ROUTES` | Agent decision declarations and routing maps agree. |
| `STEERING` | Steering names an ordinary step for the same Agent, has no independent normal continuation or decision, and the consumed steering request is not a Join member. |
| `JOIN_POLICY` | A first-satisfactory Join has an acceptance rule, and policy fields match its mode. |
| `JOIN_GROUP` | The declared group satisfies c1's bounded fork-and-join structure. |
| `UNREACHABLE` | Every step is reachable from entry. |

Shape failure ends semantic checking of that document. A report locates a rule
violation by JSON Pointer; whole-shape and parse failures use the root pointer.
The report's validity means only these checks passed. It does not prove that
every path terminates, an input selector will exist at runtime, a predicate is
satisfied, permissions hold or an implementation is available.

The named cases in [test_reader.py](test_reader.py) exercise these rules without
executing a described graph. The optional schema-library check cross-checks
shape validation only. A second semantic implementation and independent review
remain necessary before claiming cross-reader agreement for this new model.

## Remaining release scope

This c1 is a testable foundation, not a proposal to silently remove accepted
features from 0.2. Unknown syntax is rejected rather than ignored. The
[preparation index](../../docs/0.2/README.md#before-a-02-release) tracks completion;
this table identifies c1's boundaries. Proposed forms still need adoption.
Execution evidence is required only for the implementation support claimed.

| Direction outside c1 | Remaining work before the complete 0.2 candidate |
| --- | --- |
| Proposed composition | Review and adopt a local reusable graph form with parameter binding and stable Agent identity. |
| Protected actions | Explicit approval admission bound to the action, scope and actual invocation. |
| Interfaces and support | Structured-value constraints, support claims/evidence, delivery paths and relative URI bases. |
| Lifecycle integration evidence | Queue and steering obligations, text assembly, source selection and error inputs are defined above. Static record checks do not prove attribution, delivery, correction or cancellation in an implementation. |
| Validation and release | Broader graph rules, an independent semantic reader, review, migration guidance and adoption decision. |

No release tag, official contract replacement or publication follows from this
experiment. Its role is to make implementation questions reproducible while
maintaining the agreed scope in the preparation index.
