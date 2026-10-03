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
for a declared pre-initialization choice. The selector reads the first input;
its value must be a string naming a case. A missing value, wrong type or unknown
case fails without a default. Evaluate a dynamic choice when the first work
arrives, before initializing the Agent. Evaluate it once for that instance;
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
connection. Step and Agent names have separate scopes. Several steps may refer
to one Agent. Default message handling is queueing; c1 has no steering syntax.

Ordinary `next` is a list of destination steps. Completion activates every
destination in that list. Missing or empty `next` ends the current path, not
the Agent's lifetime or unrelated work. Duplicate destinations are invalid.
Steps using an explicit routing choice use a map from choice to destination
lists. A choice selects one list, whose destinations all activate.

The proposed data boundary distinguishes:

| Result field | Meaning |
| --- | --- |
| `text` | All user-visible response text for this completed Agent work, excluding reasoning, raw Tool exchanges and earlier history. Absent visible text alone is not a failure; required outputs still apply. Exact text assembly remains release work. |
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

A `prepare` constructs `message`. Its resources may use normal content or
`select`, an operand whose selected value becomes inline information. An optional
media type describes that selected value. Authored prompt sources remain
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
Report unsupported stopping and wait for completion or explicit recovery; do
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
of side effects. Exact contracts for other failure kinds remain release work.

### Checking recorded outputs

[check_completion.py](check_completion.py) validates a supplied completion record
against the selected Agent step. A record has optional `text`, `results` and
`choice`; each named result is a content source. Missing required results,
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
features from 0.2. Unknown syntax is rejected rather than ignored.

| Direction outside c1 | Remaining work before the complete 0.2 candidate |
| --- | --- |
| Steering | Delivery acknowledgement, attribution to active work and interaction with graph continuations. |
| Composition | Local reusable graph expansion and parameter binding with stable Agent identity. |
| Protected actions | Explicit approval admission bound to the action, scope and actual invocation. |
| Interfaces and support | Structured-value constraints, support claims/evidence, delivery paths and relative URI bases. |
| Completion and errors | Exact visible-text assembly, non-text transfer selection and remaining failure-kind contracts. Recorded output constraints have a checker; delivery and correction still need consuming implementation evidence. |
| Validation and release | Broader graph rules, an independent semantic reader, review, migration guidance and adoption decision. |

No release tag, official contract replacement or publication follows from this
experiment. Its role is to make implementation questions reproducible while
maintaining the agreed scope in the preparation index.
