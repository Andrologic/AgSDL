# Content, configuration and declarations

These are [normative 0.2.0 requirements](README.md) under `agsdl-0.2.0`.
The separate normative 0.1.0 contract remains unchanged.

## Document and content

A document requires `contract`, `id`, `agents`, `configurations` and `bindings`.
`content`, `skills`, `flow`, `compositions` and `baseUri` are optional. Maps use distinct names matching
ASCII letter followed by ASCII letters, digits, underscore or hyphen. Unknown
fields are invalid except inside explicitly open inline values, settings and
external requirement parameters. Duplicate JSON object members, non-JSON
numbers and unpaired Unicode surrogates are rejected. The Python reader keeps
decimal values exact while checking integer constraints; excessive parser
depth or numeric representation limits produce a parse failure, not success.

The [schema](../../tooling/0.2/schema.json) lists the closed shapes, required fields and types.
Omitted optional maps and lists are empty unless a rule below states otherwise.
An object key inside a literal `value` or `settings` object is never interpreted
as an AgSDL reference. Validators neither fetch content nor load implementation
code.

A content source contains exactly one `value` or `uri`, and an optional
`mediaType`. Inline strings are literal. URI availability and access remain integration obligations.
[Explicit URI origins](#uri-origin) define static relative-reference resolution.
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
configuration can be prepared before its first Message. This is the
concrete rule for the accepted pre-initialization direction. An Agent can add `prompt`, `resources`, `skills`
and an `interface`. The Agent is one persistent participant, including human
participation where the integration supplies it. Visiting an Agent step again
uses its existing instance and context. There is no per-visit initialization,
context reset, implicit spawning or hot configuration replacement.

For example, in the [output-correction example](../../tooling/0.2/examples/output-correction.json),
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

No initial prompt means no implicit initial task. A supplied initial prompt
provides instructions; it does not by itself introduce an extra work occurrence.
Work is activated through the [Message and flow rules](flow.md#flow-and-data),
including [external delivery without a graph](flow.md#external-delivery-without-a-graph),
and follows their admission rules. A configuration's explicit Engine binding
is required even when the Agent waits for its first Message.
Configuration has optional Model edition, Tool bindings, settings and capability
requirements. No provider or Model default is inferred. The consumer enforces
its declared access and delivery policy.

`bindings` separates an external versioned `contract` from the selected
versioned `implementation`, with optional `settings` and `requires`. Each edition
has an open `identity` and `version`; their spelling establishes no support.
A configuration names its Engine binding and maps local Tool names to Tool
bindings. Calls and decision integrations also reference declared bindings.
The external contracts establish their intended role and capabilities.
[Exact support declarations](#exact-support-declarations) assess claims, never
whether the implementation actually satisfies its contract. Opaque settings cannot redefine the AgSDL step semantics.

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
delivery remain distinct requirements. Optional [structured results](#structured-results)
add value constraints without fetching referenced payloads.

Requirements are external contract editions plus optional parameters. Presence
of a requirement is not evidence it is met. Missing support, simultaneous media
delivery, Model/Engine/Tool compatibility and access require the separately
scoped claim assessment below and actual integration evidence. A video URI must not be treated as text or a
transcript without an explicit conversion contract.

## Structured results, URI origins and support

### Structured results

A named Interface result may add `valueSchema`. This is a closed constraint
language, not arbitrary JSON Schema. Every node requires `type`, one of
`null`, `boolean`, `number`, `integer`, `string`, `array`, `object`. Optional
`enum` is a nonempty array of literal JSON values. `array` alone permits `items`
with another constraint. `object` alone permits `properties`, mapping arbitrary
property names to constraints, `required`, a distinct list naming declared
properties, and `additionalProperties`, a Boolean defaulting to true. Other
keywords and keywords for another type fail. Missing `items` or `properties`
imposes no child constraint. Each enum value must satisfy the node's other
constraints; duplicates under JSON equality fail. Required properties must
exist; optional properties are checked when present. Numbers compare exactly,
with mathematical integers accepted and Booleans distinct from numbers. Strings
are never parsed as JSON. There are no formats, coercions, references or fetching.

The completion checker assesses inline result values. A failed constraint gives
`OUTPUT_CONSTRAINT`. A URI-backed constrained result records its path in
`unassessed`; `constraintAssessment` is `unassessed` even if the declaration is
otherwise valid. `valid` then describes the checked record only, never a verified
payload or permission for successful continuation. The consumer must obtain and
check that payload before normal continuation. Missing required results still
fail. Unconstrained URI bytes and actual MIME content remain outside the check.

### URI origin

A document, incoming Message or completion may supply `baseUri`, an absolute
hierarchical URI without fragment. Bases and sources use the ASCII URI syntax of
[RFC 3986](https://www.rfc-editor.org/rfc/rfc3986#section-5.2); Unicode needs percent
encoding. Resolution follows its section 5.2 algorithm, including dot-segment
removal for references with their own scheme. Percent-encoded dots stay literal;
query and fragment are preserved, including explicit empty components.
A relative URI uses only its originating artifact's explicit base. No working directory, input filename,
receiver base or network lookup supplies a fallback. A missing base retains the
source as unresolved with an `unassessed` entry; it is not a shape error. Invalid
URI syntax or an invalid supplied base fails `URI`.

Document content, skills, Agent sources and authored Prepare content originate
at the document base. Message-local sources originate at that Message's base;
a Message `ref` still originates at its document catalog entry. Completion
results originate at that completion's base. Normalize known relative sources
to absolute URIs before forwarding, skill expansion or Prepare `source` copying;
retain the original source path and base in diagnostic observations. An unresolved
source cannot acquire the next Message's base: a consumer must retain its missing
origin and report it, or stop transfer as `CONTENT_UNAVAILABLE`. Literal `value`
objects, including keys spelled `uri` and `baseUri`, stay literal. Prepare `select`
wraps data and does not discover Sources inside it. Call and Join arbitrary data
likewise are not recursively interpreted as content. An explicitly selected Source
retains its known producing origin, including a member completion in a Join.
Resolution changes no access rights and proves neither availability nor sandboxing.

### Exact support declarations

A Binding or Configuration may add `claims`, each with `requirement`, `status`
(`supported`, `unsupported`, `unknown`) and optional `evidence`, a lowercase
64-digit SHA-256 reference. Claims apply only to that exact binding or
configuration declaration, including its implementation/settings and selected
Engine, Model and Tools. Changing that declaration changes applicability.
The complete Requirement matches by exact structural JSON equality, including
parameters; absent parameters differ from an explicit empty object. There is
no subset matching, version ordering or promotion of a Tool or Model claim to
an end-to-end configuration claim. Duplicate claims for one full requirement
fail `CLAIM`, even when identical. Duplicate requirements fail `DUPLICATE`.

The reader reports binding requirements and each Agent's applicable configuration
requirements plus its selected skills' requirements. Dynamic alternatives are
reported separately as conditional on selection; they are never merged into a
fictional selected configuration. Missing or unknown claims, and supported
claims without evidence, yield `unknown`. Unsupported yields `incompatible`;
supported with evidence yields `declared-supported`. Aggregate precedence is
incompatible, unknown, declared-supported. An empty requirement set yields
`not-requested`, never whole-system support. Evidence is not retrieved or verified.
These assessments do not change structural validity; incompatibility remains
visible beside independent unknowns. Every report keeps execution support
unassessed. Core needs are listed separately as unassessed at their declarations:
Agent continuity, configuration selection, input/output formats and content
roles, structure checks, delivery, steering, Join stopping, approval admission
and composition expansion. External claims never discharge these core needs in
this edition. A consumer must assess its actual path before executing it.
