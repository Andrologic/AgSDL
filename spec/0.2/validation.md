# Static validation and supplied-record checks

These are [candidate requirements pending maintainer adoption](README.md) for
`agsdl-exp-flow-0.2-c1`. They do not replace the normative 0.1.0 contract.
Each check covers its stated declarations or supplied record. A successful
check does not establish execution support. Commands run from the repository root.

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
| `COMPOSITION` | Parameter/output coverage, serial body restrictions and supported Join boundary. |
| `APPROVAL` | Finite ordered gate chain, actual target and absence of bypass. |
| `SCOPE` | Explicit scope on gated actions and Calls declaring external/unknown effects. |
| `VALUE_SCHEMA` | Consistent required properties and typed, distinct enumeration values. |
| `URI` | Valid explicit URI syntax and absolute hierarchical base. |
| `SOURCE` | An authored literal Prepare source selector supplies a Source. |
| `CLAIM` | No duplicate or conflicting claim for one exact requirement. |

Shape failure ends semantic checking of that document. A report locates a rule
violation by JSON Pointer, adding the invocation path for expanded steps; whole-shape and parse failures use the root pointer.
The report's validity means only these checks passed. It does not prove that
every path terminates, an input selector will exist at runtime, a predicate is
satisfied, permissions hold or an implementation is available.

The named cases in [test_reader.py](../../experimental/agent-flow-0.2/test_reader.py) exercise these rules without
executing a described graph. The optional schema-library check cross-checks
shape validation only. A second semantic implementation and independent review
remain necessary before claiming cross-reader agreement for this new model.

## Checking recorded outputs

[check_completion.py](../../experimental/agent-flow-0.2/check_completion.py) validates a supplied completion record
against the selected Agent step. A record has optional `text`, `responseMessages`, `results`, `baseUri` and
`choice`; each named result is a content source. `responseMessages` is an ordered array
of arrays of visible text parts, already filtered and attributed by the caller.
When supplied, the checker assembles it by the [response-text rule](flow.md#response-text-and-result-selection). If `text` is also
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

## Checking recorded delivery

[check_delivery.py](../../experimental/agent-flow-0.2/check_delivery.py) checks a claimed boundary record, without
running the graph or retaining live Agent state:

```sh
python3 experimental/agent-flow-0.2/check_delivery.py DOCUMENT.json AGENT RECORD.json
```

A record contains `origin`, `input`, `message` and the claimed `configuration`.
Origin is one of the six producing origins in the [delivery table](flow.md#portable-delivery); an intervening
Condition retains that origin and input. Optional `retainedConfiguration` states
a previously selected configuration. The checker verifies that it belongs to
the Agent's alternatives and skips selection on this new input. Without that
field it evaluates the selector on `input` before checking the delivered Message.
It compares Messages after explicit URI-origin normalization and catalog expansion,
without changing roles or literal input data. Unresolved sources remain unassessed.
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

Both delivery and admission check the explicitly supplied origin before
adaptation or capture, for Agent and Call targets alike. A contradictory
`text`/`responseMessages` pair, missing Message catalog reference or invalid
content URI/base is `INVALID_RECORD`. Literal `value`, Call `data` and error
details remain data. Join members retain their shape-only boundary because the
record does not establish each member's producing origin.

This checks recorded data, not whether origin, retention, Condition identity,
response filtering or actual delivery occurred. Agent completion shapes are
checked here; use the completion checker for its output constraints. External
Call contracts, content availability, lifecycle ordering, acknowledgement and
runtime attribution remain integration obligations. The record has no capacity
to certify those claims. Pending status codes are rejected as terminal errors.

## Checking recorded admission

`check_admission.py DOCUMENT STEP RECORD` checks a supplied consistency record.
It requires `occurrence`, `origin`, `input`, `invocation`, `admittedAt` and
`decisions`; `retainedConfiguration` is optional for an Agent. The invocation is
recomputed from declarations and recorded input; it contains the complete document
as `declaration`, the addressed target, occurrence, input/origin, resolved scope and, for a Call,
binding plus evaluated arguments, or for an Agent, its name, configuration and
adapted Message. Each decision contains `gate` address, `occurrence`, `invocation`,
`binding` declaration, `enteredAt`, `decidedAt`, `decision: approved` and
`authorityConfirmed: true`. Times are nonnegative integer ticks in one declared
millisecond time domain; no wall clock is consulted. Exact matches, ordering and
both deadlines are checked. An accepted record establishes only its internal
consistency, never that authority was authenticated, values captured immutably,
a queue respected, or an action executed. A caller cannot use this checker as an
authorization service. No runtime or decision intake service is implemented.

## Checking prepared content

The deterministic `prepare_message` helper in [sources.py](../../experimental/agent-flow-0.2/sources.py) checks
supplied preparation data. `agent_content` expands skill and Agent initialization
content using the same source-origin rules, without initializing an Engine.
The preparation helper's optional `source_bases` map associates selected
input JSON Pointers with their original bases, including nested Join members.
It returns URI observations beside the Message; an unresolved observation must
travel with that Source or block delivery. Passing a new receiving base is not
an alternative to preserving that origin. This helper evaluates authored data
transformations only; it never runs an Agent, Call or graph.
