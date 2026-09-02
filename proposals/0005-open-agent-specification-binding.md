# Proposal 0005: Open Agent Specification binding

- Status: proposed
- Date: 2026-09-02

## Summary

This proposal defines the conceptual boundary for an AgSDL binding to Oracle's
Open Agent Specification, called Agent Spec. It uses Agent Spec 26.1.2 as the
external source contract. It proposes two operations: an opaque external
reference and a materialized semantic mapping with a complete coverage and loss
report.

The proposal does not select AgSDL syntax, add normative text, or claim that an
Agent Spec artifact runs equivalently across runtimes. It identifies the subset
that a future adapter may claim only after the corresponding AgSDL and Agent
Spec semantics have executable tests.

## Problem

Agent Spec already serializes agents, flows, models, tools, remote components,
and framework bindings. AgSDL covers many of the same subjects. Treating the
two languages as equivalent would still lose important distinctions:

- an Agent Spec root is not necessarily a complete AgSDL System;
- Agent Spec component identity does not establish a Principal Identity,
  lifecycle owner, authority, or artifact integrity;
- Agent Spec runtime configuration mixes portable intent with target details
  that AgSDL keeps in binding and deployment records;
- Agent Spec flow semantics include implicit data routing, lossy type
  conversions, shared conversation state, and runtime-selected behavior that
  AgSDL cannot silently infer;
- Agent Spec confirmation and human-in-the-loop flags do not define the scope
  and evidence required by the proposed AgSDL approval model;
- released SDK and adapter tests do not prove semantic equivalence between
  Agent Spec, AgSDL, and every target runtime.

Without an explicit boundary, importers will be tempted to manufacture missing
AgSDL facts, while exporters will omit governance or execution requirements and
still call the output portable.

## Scope

This proposal covers:

- reference to an Agent Spec artifact as an external dependency;
- version-specific import of an Agent Spec component graph into AgSDL
  definitions;
- export of a declared AgSDL subset to Agent Spec;
- identity, reference, version, extension, plugin, binding, and secret handling;
- structural mapping, loss reporting, round-trip evidence, and runtime evidence;
- the mapping of Agent Spec agents, flows, tools, models, remote components,
  multi-agent patterns, tracing, and evaluation concepts.

This proposal does not:

- choose a field name, file format, schema dialect, or canonical serialization;
- copy the Agent Spec JSON Schema or node library into AgSDL;
- make Agent Spec a required AgSDL dependency;
- define a universal Agent Spec runtime;
- accept Agent Spec defaults as AgSDL defaults;
- assert behavioral equivalence from parsing, validation, or one successful
  execution;
- define the general AgSDL data-flow, parallelism, routing, or exception model;
- accept proposal 0002 or proposal 0003 as normative text.

The source analysis for this proposal is
[`docs/research/open-agent-specification.md`](../docs/research/open-agent-specification.md).

## External source contract

The proposed initial binding targets Agent Spec language version `26.1.2`,
release tag `agent-spec-26.1.2`, repository commit
`0799958f9087c02ac8c56df808b4adf0fb3ad539`.

A binding implementation may support other Agent Spec versions, but each version
is a separate source contract. It must publish a mapping and evidence for every
claimed version. It cannot infer support for a development version from support
for 26.1.2.

Agent Spec extensions, plugins, SDKs, framework adapters, and runtimes have
identities and versions separate from the Agent Spec language. A claim about one
does not imply support for another.

## Terms

An **Agent Spec source artifact** is the exact serialized input observed by a
binding operation. Its reproducible identity uses an integrity value over the
observed bytes. A later binding profile may additionally use canonical content
only when it names and tests the canonicalization algorithm. The artifact record
also includes its media type, retrieval source when applicable, declared Agent
Spec version, and root component type.

An **Agent Spec source graph** is the set of components, values, references,
plugins, and disaggregated dependencies that a processor resolved from an Agent
Spec source artifact within its observed input boundary.

An **Agent Spec binding profile** is a versioned mapping contract between one
Agent Spec source contract and a named AgSDL specification version and
implementation-feature set. It lists every source construct the profile claims
to understand, its AgSDL mapping, preconditions, degradation policy, and tests.
It is not a conformance profile and does not customize an AgSDL definition.

A **reference-only binding** records an Agent Spec source artifact as an
external dependency without interpreting its internal component graph.

A **materialized import** transforms an Agent Spec source graph into AgSDL
definitions and subordinate records under an Agent Spec binding profile.

An **Agent Spec export** transforms a declared subset of AgSDL definitions into
an Agent Spec source artifact under an Agent Spec binding profile.

A **binding mapping report** is the operation-specific coverage statement and
loss report. It associates every observed source or target item with its mapping
outcome, diagnostics, assumptions, and evidence. It does not replace a
conformance verdict.

An **authorized overlay** is a separately identified input that supplies AgSDL
facts absent from the Agent Spec source. Examples include lifecycle ownership,
principal identity, policy, Effects, or a deployment binding. The report records
the overlay's provenance and keeps supplied facts distinct from source-derived
facts.

## Proposed semantics

### Binding identity and operation boundary

Every binding operation should identify:

- the Agent Spec binding profile and its version;
- the AgSDL specification version and claimed implementation features;
- the operation, either reference, import, export, round trip, or runtime test;
- the Agent Spec language version and exact source artifact identity;
- the processor and adapter versions;
- every Agent Spec SDK, plugin, runtime, or framework adapter used;
- the observed input boundary, resolver configuration, and authorized overlays;
- whether network access, subprocess creation, secret resolution, or execution
  was permitted;
- the mapping report and separate conformance verdicts produced.

A processor should not map an Agent Spec artifact whose `agentspec_version` is
absent by silently using its own current version. It should either reject the
input or record the exact selected source contract as an explicit assumption in
the mapping report. A reproducible positive result requires the selected version
to be fixed before mapping.

### Reference-only binding

A reference-only binding should identify:

- the artifact location or embedded artifact;
- a content integrity value;
- the expected Agent Spec language version and root component type;
- the permitted resolver and retrieval sources;
- whether disaggregated dependencies and plugins are required;
- the operation for which the dependency is required;
- the implementation feature required to consume it.

Validation can inspect these declarations without resolving the artifact. A
resolved-graph operation checks the retrieved artifact, declared version, root
type, integrity value, and required dependencies. Reference-only binding makes
no claim about the internal portable meaning of the Agent Spec graph.

### Materialized import boundary

A materialized import should normally produce an AgSDL Fragment. It may produce
a complete System only when the Agent Spec source plus authorized overlays
supply every mandatory System fact.

The generated Fragment is the lifecycle owner of every AgSDL definition that
the mapping creates locally. This ownership is required by the AgSDL document
form. The mapping report classifies the Fragment and its ownership relations as
synthesized mapping structure and does not present them as ownership asserted by
the Agent Spec source. A definition kept as an external AgSDL reference retains
the lifecycle owner declared by that external source.

For every other mandatory AgSDL relation or cardinality absent from the Agent
Spec source, the Fragment should declare an Unresolved requirement that names
the affected definition, expected target kind, required relation, and condition
for resolution. The materialized output is an unresolved reusable fragment. It
cannot receive a positive resolved-graph verdict until composition or an
authorized overlay satisfies every such requirement. If the binding cannot
represent a mandatory missing relation as an Unresolved requirement, or if the
requested operation requires a resolved graph, the import fails.

The adapter must not synthesize a System boundary, purpose, principal,
authority, policy, trust boundary, Effect, or deployment guarantee merely to
make the result appear complete.

Each imported AgSDL item should retain traceability to:

- the source artifact;
- the Agent Spec component identifier and concrete component type;
- the source location or reference chain;
- the binding rule applied;
- the authorized overlay, if any;
- every dropped, approximated, synthesized, target-specific, or uninterpreted
  source fact.

The mapping report should account for all observed source components,
subordinate configuration objects, relationships, defaults, implicit behavior,
metadata, plugins, and disaggregated values. It should use the verdict and loss
separation proposed in proposal 0003. A loss report does not turn a failed or
unsupported required mapping into a pass.

### Component dispatch

The generic Agent Spec `Component` and `AgenticComponent` families should not
map to generic AgSDL entities. The binding dispatches on the concrete
`component_type`. Unknown component types follow the AgSDL unknown-information
rules. A plugin declaration alone does not authorize loading or executing plugin
code.

Agent Spec `id` values should remain stable source identities within the source
artifact. They must not be reclassified as AgSDL Principal Identities. When an
import creates an AgSDL definition identity, the mapping report preserves the
source identity and records the derivation.

Agent Spec `metadata` should be preserved as uninterpreted source information
unless a binding rule gives a field portable meaning. If the target cannot
preserve it, the adapter issues a loss report. Metadata cannot silently create
AgSDL policy, ownership, authority, conformance, or extension semantics.

### Agent mapping

An Agent Spec `Agent` should map to an AgSDL Agent with separate candidate
definitions for:

- its `system_prompt` as Instructions;
- its `llm_config` as a Model and binding requirements;
- each concrete tool as a Tool and at least one Action;
- its declared inputs and outputs as interface or invocation contract facts;
- message transforms and structured outputs as explicit requirements or
  extensions when AgSDL has no accepted core semantics for them.

The generated Fragment owns the mapped Agent. The binding does not infer the
Agent's Principal definition, Principal Identity, authority, enclosing System,
or externally reachable Interface. Unless a binding rule maps an explicit source
interaction contract to an Interface, the Fragment declares separate Unresolved
requirements for the Agent's mandatory Principal definition, Identity, and
Interface relations. An authorized overlay or later composition may satisfy
them. The mapping report alone does not satisfy a required relation.

`human_in_the_loop` should be preserved as an Agent Spec execution requirement.
It does not create an AgSDL Approval requirement because it does not identify a
request, approver, decision scope, action, resource, expiry, evidence, or failure
policy.

An Agent Spec `SpecializedAgent` should map as a derived or composed Agent only
when the adapter can preserve the exact instruction merge, tool addition,
human-in-the-loop override, and input/output rules. Otherwise the specialized
component remains a required external extension or produces an unsupported
mapping result.

### Model and runtime configuration mapping

An Agent Spec `LlmConfig` should split into:

- portable Model capability requirements that AgSDL can express;
- provider, endpoint, authentication, retry, certificate, and executor facts as
  binding requirements or target-specific extension information;
- resolved runtime selections only when a separately identified Deployment
  operation supplies and verifies them.

The adapter must not treat a provider model identifier as a portable guarantee
of behavior. Structured output declarations preserve an expected output
contract, but they do not prove that a model or runtime enforces it.

### Tool and remote component mapping

An Agent Spec `Tool` should map to a Tool definition and an Action contract.
Declared inputs and outputs contribute to that Action contract. The import
should leave Effect, protected Resource, governing Policy, Trust boundary,
authority, and side-effect classification unresolved when the source does not
state them.

Each mapped Tool must require at least one Tool binding requirement. The
concrete Agent Spec tool type and its execution-side or transport configuration
normally provide the source facts for that requirement. When they do not, the
Fragment declares an Unresolved requirement for a Tool binding requirement and
cannot receive a positive resolved-graph verdict. The same rule applies to every
mandatory Action relation, including acting Principal and target Resource kinds,
that the source cannot supply.

`requires_confirmation` should remain a source execution requirement. It cannot
satisfy an AgSDL Approval requirement or prove that an approval occurred.

Concrete tool types should receive these additional treatments:

- `ServerTool` and `ClientTool` retain the expected execution side and report
  any runtime registry dependency;
- `RemoteTool` contributes an external interface and binding requirement, while
  URL templates, headers, authentication, allow lists, and retry behavior remain
  explicit target or security facts;
- `MCPTool` and `MCPToolBox` identify an MCP dependency and its version or
  transport profile when the source makes them known; their contents do not
  become portable AgSDL Tool definitions without MCP discovery evidence;
- `BuiltinTool` remains target-specific unless a separate portable contract
  defines its semantics and the binding tests that contract;
- `ToolBox` maps to dynamic discovery or a binding requirement, not to an AgSDL
  Package or Skill.

An Agent Spec `RemoteAgent`, `A2AAgent`, or other externally executed component
should map to an external Interface, Protocol, or runtime binding according to
the concrete source type. A remote endpoint does not prove that the target is an
AgSDL Agent, reveal its internal System, or grant it authority.

### Flow mapping

An Agent Spec `Flow` should map to an AgSDL Control flow with:

- its sole start node as an entry step;
- each end node as a terminal step and its branch result;
- each other node as a step with the mapped invocation or operation;
- each control-flow edge as an allowed step transition;
- branch labels, branch-selection rules, defaults, output defaults, and failure
  behavior kept explicit;
- nested flows represented through definitions and invocation rather than
  flattened without evidence.

The adapter should map node types only when it preserves their released Agent
Spec 26.1.2 behavior. `AgentNode`, `FlowNode`, `LlmNode`, and `ToolNode` are
candidate invocations of the corresponding AgSDL definitions. `ApiNode` is a
candidate Tool and Action invocation with an external binding.
`InputMessageNode` and `OutputMessageNode` require Interface, Message, and State
analysis. `CatchExceptionNode`, map nodes, and parallel nodes remain extensions
until AgSDL defines matching failure, collection, and concurrency semantics.

An Agent Spec cycle should not pass AgSDL control-flow validation unless the
result declares a termination condition, finite bound, or intentional
long-lived-loop classification. The adapter may obtain that fact from an
authorized overlay. It cannot infer termination from one successful run.

### Data and conversation mapping

Agent Spec data-flow edges should remain distinct from control-flow edges. A
binding may preserve them as a required extension until AgSDL defines portable
data-routing semantics. It must not discard source and destination property
names or collapse data edges into step order.

The following Agent Spec behaviors require explicit AgSDL representation or a
required extension:

- implicit name-based variable lookup when `data_flow_connections` is `null`;
- overwrite priority based on the last executed producer;
- conversion from any supported type to string;
- conversions between number and integer, including decimal loss;
- conversions between Boolean and numeric types;
- input and output inference from prompt placeholders;
- output defaults selected by the terminal branch.

The shared Agent Spec conversation should map to State, Memory, Message, or
Protocol facts only where the target concept and lifetime are known. The mapping
report must state that parent flows, subflows, and subagents share conversation
content in Agent Spec 26.1.2. A nesting relation cannot be presented as an
information-isolation boundary.

### Multi-agent mapping

Agent Spec `Swarm.relationships` should map to directed Topology edges between
the mapped participants. The edge permits communication. It does not by itself
prove Delegation, Handoff, authority, or responsibility transfer.

Swarm call-for-reply behavior should map to message or delegation semantics only
when the binding identifies the work item, roles, response path, failure path,
and authority context. Swarm full-conversation transfer is a Handoff candidate.
A complete AgSDL Handoff mapping also needs sending and receiving principals,
acceptance, transferred responsibility, context, return or termination, and
the separation of authority from responsibility.

Agent Spec `ManagerWorkers` should map to a coordination pattern, participant
Topology, and candidate Delegation relations. The manager label and worker list
do not grant authority or prove that a work item was accepted.

### References, disaggregation, and secrets

The adapter should resolve `$component_ref` only inside its declared resolver
boundary. It checks uniqueness, existence, expected concrete type, and cycles.
References outside the captured source artifact need an AgSDL external reference
with source, expected kind, version, integrity, and resolution policy.

Disaggregated Agent Spec components and values should appear as dependencies in
the mapping report. Missing required values stop materialized import. Additional
values supplied by a loader are inputs to the operation and remain within the
observed input boundary.

A sensitive value must not be embedded in the AgSDL result. The adapter should
create or preserve a secret or credential reference and record which binding
must supply it. The fact that an Agent Spec loader accepts inline sensitive
values does not permit AgSDL to export or retain them.

### Plugins and unknown information

For each Agent Spec plugin component, the adapter should record:

- plugin name and version;
- concrete component type and claimed parent type;
- whether the plugin is required for the requested operation;
- the SDK or runtime implementation that recognizes it;
- the binding rule and tests that cover it;
- whether uninterpreted source information can be preserved exactly.

Inspection and structural import should not execute plugin code from an
untrusted source. A required unknown plugin stops semantic materialization. An
optional or preservable plugin follows the unknown-information behavior in
proposal 0003 and receives a separate report from invalid core input.

### Export boundary

An Agent Spec export should name the exact AgSDL implementation-feature subset
it supports. It should emit a binding mapping report that accounts for every
AgSDL definition and relation in the observed input boundary.

AgSDL concepts without Agent Spec 26.1.2 counterparts should not disappear.
The exporter should either:

- keep them in a separate AgSDL companion artifact referenced from the package;
- encode them through a named, versioned Agent Spec plugin covered by the
  binding profile and tests; or
- issue a loss report and refuse the operation when the information is required.

Likely non-exportable core information includes complete lifecycle ownership,
Principal and Identity distinctions, authority grants, protected Effects,
Trust boundaries, Policy application points, Approval decisions, deployment
separation, and AgSDL conformance claims.

An exporter should never place secrets in the Agent Spec output. It should not
target a lower `agentspec_version` while relying on newer component behavior.

## Mapping table

This table is the proposed minimum mapping inventory. `Conditional` means that
the mapping profile must state and test the listed preconditions. `No core
mapping` means the source remains an extension or unsupported for semantic
materialization.

| Agent Spec 26.1.2 construct | AgSDL target | Mapping status and condition |
| --- | --- | --- |
| `Component` | Source identity and traceability | Conditional on concrete-type dispatch |
| Root `Agent` | Fragment that owns Agent and dependencies | Conditional; missing mandatory Agent relations become Unresolved requirements |
| `Agent.system_prompt` | Instructions | Conditional on preserving placeholders and precedence |
| `LlmConfig` | Model plus binding requirement | Conditional; provider and endpoint details are not portable Model meaning |
| `Tool` | Tool, Action, and Tool binding requirement | Conditional; every other missing mandatory relation becomes an Unresolved requirement |
| `requires_confirmation` | Source execution requirement | No complete Approval mapping |
| `ToolBox` | Discovery or binding requirement | Conditional on runtime discovery evidence |
| `BuiltinTool` | Target-specific extension | No core mapping without a separate portable contract |
| `RemoteTool`, `MCPTool` | Tool, Action, external interface, and binding requirement | Conditional on protocol, endpoint, authentication, and security mapping |
| Root `Flow` | Fragment with Control flow | Conditional; not a System or Agent |
| `StartNode`, `EndNode` | Entry and terminal steps | Direct candidate with branch and output rules preserved |
| `ControlFlowEdge` | Step transition | Direct candidate with source branch semantics preserved |
| `DataFlowEdge` | Data-routing extension | No current core mapping |
| Implicit variable space | State or data-routing extension | No current core mapping |
| `AgentNode`, `FlowNode`, `LlmNode`, `ToolNode` | Step invocation | Conditional on concrete invocation and return semantics |
| `ApiNode` | Tool and Action invocation with binding | Conditional; authority and Effect remain separate |
| `BranchingNode` | Branch condition and transitions | Conditional on mapping and default behavior |
| `MapNode`, `ParallelMapNode`, `ParallelFlowNode` | Collection or concurrency extension | No current core mapping |
| `CatchExceptionNode` | Failure transition and policy extension | No current core mapping |
| `Swarm.relationships` | Topology edges | Conditional; no automatic Delegation or Handoff |
| Swarm full-conversation transfer | Handoff candidate | Conditional on principals, acceptance, responsibility, context, and termination |
| `ManagerWorkers` | Topology and coordination or Delegation candidates | Conditional; no authority inference |
| `RemoteAgent`, `A2AAgent` | External Interface, Protocol, or binding | Conditional; no inferred internal Agent or System |
| `Datastore` | Storage binding requirement and possible State or Memory dependency | Conditional on lifetime, consistency, ownership, and access semantics |
| Message transforms | Instructions, Memory, or State extension | No generic core mapping |
| `$component_ref` | Source-local reference | Conditional on controlled resolution and type checking |
| Disaggregated component | Dependency and external reference | Conditional on identity, version, integrity, and resolver boundary |
| Sensitive field placeholder | Secret or credential reference | Conditional; secret value excluded from output |
| `metadata` | Uninterpreted source information | Preserve exactly or report loss |
| Plugin component | AgSDL extension | Conditional on plugin identity, mapping, support, and tests |
| Agent Spec Tracing | Trace requirement, trace record, or execution trace | Conditional on identity, causal, version, redaction, and occurrence mapping |
| Agent Spec Eval | Evaluation definition or result | Conditional on subject, dataset, metric, environment, and evidence mapping |

## Conceptual mapping example

This example illustrates the proposed report behavior. It does not establish
AgSDL or Agent Spec syntax.

An Agent Spec 26.1.2 artifact defines a payment-review `Agent`. The Agent has a
system prompt, an LLM configuration, and a `RemoteTool` named `submit_payment`.
The Tool declares `requires_confirmation=true`, accepts supplier, amount, and
currency inputs, and calls an HTTPS endpoint. The artifact contains no separate
owner, principal, protected resource, effect, approval scope, or authorization
policy.

A materialized importer can produce a Fragment that exports:

- an Agent derived from the Agent Spec `Agent`;
- Instructions derived from the system prompt;
- a Model with binding requirements derived from the LLM configuration;
- a Tool and `submit payment` Action with the declared input contract;
- a remote interface binding requirement derived from the HTTPS Tool.

The generated Fragment owns these local definitions. That ownership is a fact
about the AgSDL mapping artifact, not a claim that Agent Spec identified the
payment system's lifecycle owner.

The mapping report records the exact source component identifiers and rules. It
also records that confirmation is required by the source, while a complete
AgSDL Approval requirement is absent. The Fragment declares Unresolved
requirements for the mapped Agent's Principal definition, Identity, and
Interface, the Action's acting Principal and target Resource kinds, and the
source-required approval details. The report also identifies the absent Effect,
Policy, Trust boundary, and Authority grant without treating optional absent
relations as cardinality failures. The URL and authentication configuration
remain binding facts. The importer cannot call the unresolved result a resolved
graph or deployable System, or claim that confirmation authorizes the payment.

An authorized overlay may later supply the missing principals, identities,
interfaces, bank account Resource, funds-transfer Effect, approval scope,
policy, trust boundary, and deployment bindings. The report attributes those
facts to the overlay and records which Unresolved requirements they satisfy. It
does not relabel them as facts found in the Agent Spec artifact.

## Validation and conformance

### Structural source validation

A future binding suite should verify at least:

- exact and missing Agent Spec versions;
- root component type and component identifier uniqueness;
- local, nested, disaggregated, missing, mistyped, duplicated, and cyclic
  references;
- plugin declarations and unrecognized component types;
- input and output schema requirements and inferred property consistency;
- flow entry, terminal, edge membership, branch, and data connection rules;
- sensitive-field exclusion and controlled resolver behavior;
- mapping report completeness and stable diagnostic categories.

These checks support source-validation and structural-mapping verdicts only.

### Round-trip conformance

An adapter claiming reversible conversion should pass fixtures in both
directions for every claimed construct. Comparison should cover normalized
portable meaning, source identities, defaults, references, extensions, metadata,
and loss reports. Byte equality is neither required nor sufficient unless the
profile explicitly claims exact artifact preservation.

Round-trip coverage should include negative fixtures in which the adapter must
refuse required loss. A successful Agent Spec SDK serialization round trip does
not prove an AgSDL round trip.

### Runtime conformance

A behavioral claim requires execution tests against each named Agent Spec
runtime or framework adapter. Every result should bind:

- Agent Spec language, SDK, plugin, adapter, framework, and runtime versions;
- AgSDL specification, binding profile, adapter, and suite versions;
- the exact source and mapped artifacts;
- input fixtures, environment, model and tool doubles or external dependencies;
- observable control transitions, data values, messages, tool requests,
  approvals, failures, traces, and terminal outputs;
- unsupported, skipped, unobserved, and nondeterministic behavior.

Passing on one runtime does not extend the verdict to another runtime. Passing
with one input set does not establish general behavioral equivalence.

### Required fixture groups

The first executable suite should include:

1. one standalone Agent with explicit version, prompt placeholders, model
   requirements, tools, and structured outputs;
2. one linear Flow with explicit data edges and one branching Flow with terminal
   output defaults;
3. one cyclic Flow with and without an authorized AgSDL termination overlay;
4. one implicit data-space Flow that exercises multiple writers and every
   Agent Spec type conversion;
5. nested Agent and Flow invocations that expose shared-conversation behavior;
6. parallel, map, and exception nodes as required unsupported cases until their
   AgSDL semantics exist;
7. a Swarm with call-for-reply and full-conversation handoff modes;
8. a ManagerWorkers configuration that cannot be misread as an Authority grant;
9. remote, MCP, built-in, toolbox, A2A, plugin, disaggregated, and sensitive-field
   cases with controlled loading;
10. source artifacts with absent, supported, deprecated, and unsupported Agent
    Spec versions;
11. export fixtures containing AgSDL governance and security facts that must
    remain in a companion artifact or force refusal;
12. separate structural, round-trip, and runtime result records.

Until those fixtures and their normative AgSDL requirements exist, the project
should describe this work as a mapping proposal, not an implemented interoperable
binding.

## Security considerations

Agent Spec artifacts are active configuration even though conforming
serializations are not intended to contain embedded code. Untrusted inputs may
still target unsafe loader behavior. Valid artifacts can select remote
endpoints, model services, runtime tools, MCP transports, authentication flows,
plugins, generated code paths, and conversation sharing.

An AgSDL processor should provide an inspection mode that performs no network
retrieval, subprocess launch, plugin execution, secret resolution, tool
invocation, model request, or target code generation. Resolution and execution
require separate declared operations and authority.

The binding should preserve or report:

- prompt placeholders that can move untrusted data into instructions;
- URL, header, body, and query templates that can enable data disclosure or
  server-side request forgery;
- tool identifiers that may resolve to different implementations;
- shared conversations across nested components and remote endpoints;
- lossy type conversion and last-writer state behavior;
- unbounded cycles, fan-out, retries, model calls, and tool calls;
- parallel operations without ordering, atomicity, or coordinated interruption;
- exception information that can expose secrets or infrastructure details;
- runtime controls missing from Agent Spec 26.1.2;
- inline sensitive values, which the AgSDL result must replace with references.

No structural mapping can prove that these controls hold during execution.

## Compatibility impact

This proposal adds no normative compatibility promise. If accepted later, the
binding profile version will change independently from AgSDL and Agent Spec
language versions.

An Agent Spec patch version should not be presumed compatible merely because
its numeric version differs only in the final component. The 26.1.2 language
text allows a patch update to contain breaking changes. Each supported pair
therefore needs explicit compatibility evidence.

Changes to an Agent Spec plugin, SDK, framework adapter, runtime, model provider,
tool implementation, or resolver can invalidate mapping or runtime evidence
without changing either language version. A report should mark prior behavioral
evidence stale until the applicable suite passes again.

## Consequences

The proposal lets AgSDL acknowledge Agent Spec as a serious external language
without letting its current syntax or runtime model decide AgSDL's core design.
Reference-only binding is useful before AgSDL has syntax. Materialized mapping
has a clear path once the relevant AgSDL concepts become normative.

The cost is deliberate friction. Importers and exporters must expose missing
facts and unsupported semantics. Many Agent Spec documents will initially map
to Fragments with unresolved requirements instead of complete Systems. That is
preferable to a simple conversion that changes behavior while reporting success.

The mapping inventory also identifies AgSDL design work that deserves its own
proposal, especially data routing, concurrency, failure handling, conversation
state, route selection, and derivation or specialization.

## Alternatives considered

### Adopt Agent Spec as the AgSDL serialization

This would provide immediate JSON, YAML, SDK, and adapter implementations. It
would also bind AgSDL to Agent Spec's component hierarchy, reference form,
defaults, type conversions, and incomplete governance model before AgSDL has
accepted its own semantics. It is rejected.

### Treat an Agent Spec root as an AgSDL System

This would make import simple. It would synthesize or omit system boundary,
ownership, principal, authority, policy, trust, and deployment facts. It is
rejected.

### Embed the whole Agent Spec artifact in an AgSDL extension

This preserves bytes and supports reference-only binding, but it supplies no
semantic mapping or coverage report. It is accepted only as the reference-only
operation, not as materialized interoperability.

### Map only names, prompts, models, tools, nodes, and edges

This produces attractive diagrams and runnable prototypes. It loses implicit
data flow, conversation sharing, type coercions, approvals, runtime defaults,
security boundaries, and unsupported components. It is rejected as a general
binding and may exist only as a declared lossy operation with required loss
reported before output.

### Use Agent Spec adapters as conformance evidence

The adapters are valuable implementations and test inputs. Their presence does
not prove complete source coverage, reversible mapping, or equivalent execution.
They remain external systems tested as separate subjects.

### Wait until both specifications are final

This avoids churn but loses useful design feedback from a working external
language. A non-normative, version-specific proposal records the boundary now
without freezing syntax or compatibility.

## Unresolved questions

1. How should a future serialization distinguish the generated Fragment's
   lifecycle ownership from the source-provenance relation to Agent Spec
   components?
2. What portable AgSDL model should represent data-flow edges, shared variable
   spaces, overwrite priority, and lossy type conversion?
3. Which parallel fork, join, cancellation, atomicity, and failure facts belong
   in the core rather than an optional profile?
4. How should AgSDL represent derivation when an Agent Spec
   `SpecializedAgent` merges instructions and tools into a base Agent?
5. Can a shared conversation map to State, Memory, Protocol, or a distinct
   concept without conflating definition and occurrence?
6. Which Agent Spec node types should the first binding profile support?
7. Can an Agent Spec plugin carry an AgSDL companion record without requiring
   every Agent Spec runtime to interpret it?
8. What canonical comparison form should round-trip tests use after AgSDL
   selects a serialization?
9. Which stable Agent Spec conformance artifacts, if any, will replace the draft
   cross-runtime suites observed during this review?
10. Should an absent `agentspec_version` always fail AgSDL materialized import,
    or may a named ingestion policy fix and record a source version?
11. Which source facts are sufficient to map a Swarm transfer to a complete
    AgSDL Handoff rather than a source-specific extension?
12. How should a mapping report identify an external artifact whose sensitive
    fields were intentionally omitted but whose non-secret dependency identities
    are also unavailable?

## Acceptance criteria

This proposal is ready for semantic review when:

- the source baseline and every external claim are reproducible from primary
  versioned sources;
- every Agent Spec 26.1.2 component family has a mapping, extension, or
  unsupported disposition;
- reference, import, export, round-trip, and runtime claims remain distinct;
- missing AgSDL governance and security facts cannot be silently synthesized;
- the proposal agrees with proposals 0001 through 0004 and Decision 0001;
- unresolved AgSDL data-flow and concurrency design remains explicitly open;
- `./scripts/check.sh` succeeds.

Acceptance of this proposal would approve the conceptual binding boundary. It
would not implement the binding. Normative text, syntax, schemas, an adapter,
and executable fixtures would still require later reviewed work.
