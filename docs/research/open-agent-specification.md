# Open Agent Specification and AgSDL

Status: research note, non-normative
Last reviewed: 2026-09-02

## Purpose and method

This note examines Oracle's Open Agent Specification, called Agent Spec in its
own documentation, as a possible external integration for AgSDL. It distinguishes
source facts from AgSDL analysis. It does not establish AgSDL syntax, accept a
binding profile, or claim interoperability.

The review uses primary sources published by the Agent Spec project. The stable
baseline is release `agent-spec-26.1.2`, published on 2026-06-02 at commit
[`0799958f9087c02ac8c56df808b4adf0fb3ad539`](https://github.com/oracle/agent-spec/tree/0799958f9087c02ac8c56df808b4adf0fb3ad539).
The main references are:

- the [Agent Spec 26.1.2 release](https://github.com/oracle/agent-spec/releases/tag/agent-spec-26.1.2);
- the [versioned language specification](https://oracle.github.io/agent-spec/26.1.2/agentspec/language_spec_26_1_2.html)
  and its [source at the release tag](https://github.com/oracle/agent-spec/blob/agent-spec-26.1.2/docs/pyagentspec/source/agentspec/language_spec_26_1_2.rst);
- the [versioned security considerations](https://oracle.github.io/agent-spec/26.1.2/security.html);
- the [technical report, arXiv:2510.04173](https://arxiv.org/abs/2510.04173);
- the project authors' 2026 paper, ["Open Agent Specification: Enabling
  Cross-Framework Comparison of AI
  Agents"](https://doi.org/10.1145/3786335.3813130);
- the released [PyAgentSpec implementation and tests](https://github.com/oracle/agent-spec/tree/agent-spec-26.1.2/pyagentspec)
  and [TypeScript implementation and tests](https://github.com/oracle/agent-spec/tree/agent-spec-26.1.2/tsagentspec).

The repository's `main` branch had moved beyond the stable release at review
time. Development content is cited only when assessing work that has not shipped.
It does not define the baseline used by this note. Every source above was
accessed on 2026-09-02.

## Identity, status, and stated objective

### Source facts

Oracle maintains the public `oracle/agent-spec` repository under Apache-2.0 or
UPL-1.0. Release 26.1.2 contains the language documentation, PyAgentSpec,
TSAgentSpec, adapters, examples, validation code, tracing, and evaluation code.
PyAgentSpec 26.1.2 is classified as alpha on its
[package record](https://pypi.org/project/pyagentspec/26.1.2/).

Agent Spec describes itself as a declarative, framework-independent language
for agents and workflows. Its two principal executable component kinds are
conversational agents and structured flows. A runtime implements those
components directly or through an adapter to a framework.

The technical report compares the intended role of Agent Spec with ONNX. It
states goals of cross-framework portability, import and export, validation, and
consistent execution. Those statements express the project's objective. They do
not by themselves prove semantic preservation by a particular adapter.

### AgSDL assessment

Agent Spec is relevant prior art, not a synonym or predecessor for AgSDL. It
addresses a large part of AgSDL's agent, model, tool, and control-flow inventory
with a concrete serialization and SDK. AgSDL has a broader intended subject. It
also describes system boundaries, ownership, principals, authority, trust,
deployment requirements, evidence, and explicit conformance limits.

The abbreviation `OAS` should not identify Agent Spec in AgSDL material. It is
already widely associated with the OpenAPI Specification and does not appear as
the preferred short name in the reviewed Oracle documents. This note uses
`Agent Spec` and qualifies its terms where a collision is possible.

## Representation model

### Source facts

The base `Component` carries an identifier, concrete type, name, optional
description, and free-form metadata. `ComponentWithIO` adds lists of input and
output properties. Each property uses JSON Schema vocabulary and must at least
state a `title` and `type`.

Agent Spec serializes a concrete component with `component_type`. It uses
`agentspec_version` at the top level. JSON and YAML are supported by the SDK,
and the specification allows other serializations. Serialized configurations
are not intended to contain executable code. An inspector still treats an
untrusted artifact and its loader as potentially active input.

A component reference has the form:

```json
{"$component_ref": "component-id"}
```

Identifiers must be unique in a configuration. A reused nested component must
be represented by reference. Agent Spec also supports disaggregated components
and values. A separate `$referenced_components` dictionary supplies them to a
loader, and deserialization fails when a required referenced value is absent.
The loader checks type compatibility between a component reference and the
supplied component.

The basic reference does not carry a target kind, source URI, version
constraint, content digest, resolver identity, or retrieval policy. Those facts
may exist outside the reference or in surrounding component configuration, but
the reference form does not establish them.

The `metadata` member can hold extra information for consumers such as editors.
Agent Spec separately defines plugins for new component types. A plugin names
itself and its version, declares the component types it supports, and adds SDK
serialization, deserialization, and runtime execution logic.

### AgSDL assessment

Agent Spec's component graph is useful input to an AgSDL processor, but
`Component` is too broad to become one AgSDL definition kind. A binding has to
dispatch on the concrete Agent Spec component type.

`$component_ref` can preserve identity inside a captured Agent Spec artifact.
It does not satisfy AgSDL's proposed external-reference requirements on its own.
An AgSDL import that materializes the target graph needs a controlled resolver,
expected target kind, source identity, version, and integrity evidence. A
reference-only integration can keep the Agent Spec artifact opaque and attach
those facts to the external artifact reference instead.

Free-form Agent Spec metadata is neither portable AgSDL meaning nor an AgSDL
extension declaration. A transforming processor must preserve it as
uninterpreted source information or report its loss. A recognized Agent Spec
plugin is still an external extension. The availability of plugin code in one
SDK or runtime does not make its semantics portable across AgSDL processors.

## Agents, models, tools, and state

### Source facts

An Agent Spec `AgenticComponent` is an interactive entry point that consumes a
conversation or structured context and returns messages or structured data. Its
concrete kinds include `Agent`, `Flow`, `RemoteAgent`, `Swarm`, and
`ManagerWorkers`.

An `Agent` contains a system prompt, an LLM configuration, tools, toolboxes, a
human-in-the-loop flag, and message transforms. The runtime tells the model
about available tools. Tool-name collision behavior is not fixed. The
specification recommends optional namespacing and permits a runtime to reject a
collision.

An `LlmConfig` identifies model and provider configuration. Several concrete
types include endpoint, authentication, retry, or provider-specific fields. A
generic LLM configuration also exists. Agent Spec defines expected structured
outputs but states that version 26.1.2 does not define how a runtime enforces
structured generation.

A `Tool` is a callable procedure with declared input and output properties. Its
subtypes cover server-side, client-side, remote HTTP, MCP, and runtime-provided
built-in tools. `requires_confirmation` asks an execution environment to obtain
user or operator confirmation. A `ToolBox` discovers or aggregates tools at
runtime. An MCP toolbox can constrain discovered tool names and signatures.

Agent Spec 26.1.2 includes datastore components and message or conversation
summarization transforms. The language specification still lists general memory
and planning among subjects for future versions.

### AgSDL assessment

An Agent Spec `Agent` can supply facts for an AgSDL Agent, Instructions, Model,
Tool, Action, and binding requirements. It cannot by itself supply a complete
AgSDL System. It lacks the required system boundary, lifecycle owner, principal
model, interfaces, trust boundaries, policies, and deployment separation.

Provider endpoints, credentials configuration, built-in tool names, and runtime
executor names belong in AgSDL binding requirements or resolved bindings. They
must not silently become portable Model or Tool semantics. The same distinction
applies to an Agent Spec `RemoteAgent`, which names a remote execution mechanism
but does not establish the remote principal, authority, or internal agent graph.

`requires_confirmation` and `human_in_the_loop` are weaker than the proposed
AgSDL approval model. They do not identify the request, authorized approver,
bound action and resource, expiry, decision evidence, or failure policy. An
import may preserve these flags as source requirements, but it must report that
they do not constitute an AgSDL Approval requirement or an Authorization
decision.

A discovered toolbox does not prove that any listed tool remains available,
matches an earlier signature, is authorized, or is safe to invoke. It maps best
to a runtime discovery or binding requirement. A processor can materialize a
specific discovered tool only with a time-bounded observation and source
identity.

## Flow and data semantics

### Source facts

An Agent Spec `Flow` is a directed, potentially cyclic execution graph. It has
one start node, one or more end nodes, a node list, control-flow edges, and
optional data-flow edges. The released PyAgentSpec validators enforce structural
conditions such as one start node, membership of edge endpoints, and terminal
node constraints.

A control-flow edge identifies a potential transition from one named branch of
a node to another node. The source node's implementation selects the branch at
runtime. Multiple edges from the same outgoing branch are forbidden. Edges do
not express parallel execution. Parallel map and parallel flow nodes establish
explicit fork and join boundaries, but Agent Spec does not guarantee ordering,
timing, atomicity, or synchronization among parallel branches.

A data-flow edge maps one named output to one named input. When several outputs
feed the same input, the last executed producer has priority. Authors may omit
data-flow edges by setting `data_flow_connections` to `null`. The runtime then
uses a shared, name-based variable space in which later writes overwrite values.
Agent Spec permits conversions from any supported type to string, between
integer and number, and between Boolean and numeric types. It notes possible
decimal loss.

The standard node library covers model calls, HTTP calls, agent and subflow
invocation, branching, tool invocation, input and output messages, sequential
map, parallel map, parallel flows, and exception capture. A flow may contain a
conversation as well as the separate input/output data space. The parent flow,
subflows, and subagents share conversation content. The security documentation
warns that this mechanism is not an isolation boundary.

`Swarm` supplies a directed graph of permitted agent-to-agent relationships and
a `never`, `optional`, or `always` handoff mode. Calling another agent for a
reply and transferring the whole conversation are distinct operations.
`ManagerWorkers` assigns one manager component and a list of worker components.

### AgSDL assessment

Agent Spec control-flow edges correspond closely to proposed AgSDL step
transitions. Start and end nodes correspond to entry and terminal steps. The
specific node kind can identify an invocation of an Agent, Model, Tool, Action,
or nested Control flow. This mapping remains conditional on preserving the
source node's branch rules and failure behavior.

Data-flow edges do not have a complete counterpart in the current AgSDL
conceptual proposal. They may inform future state or data-routing work. An
import must not reinterpret them as control flow. The shared variable space,
last-writer priority, implicit name matching, and Agent Spec type conversions
are source semantics that need either explicit AgSDL representation or a
required extension. Quietly normalizing them would change behavior.

Cycles need a declared AgSDL termination condition, finite bound, or intentional
long-lived-loop classification. Agent Spec permits cycles but does not require
one of those AgSDL facts. A cyclic flow therefore cannot receive an unqualified
AgSDL control-flow mapping.

Agent Spec parallel nodes establish useful structure, but their lack of ordering
and atomicity guarantees must remain visible. An AgSDL mapping also needs to
report shared-state and interactive-step hazards. The Agent Spec security guide
specifically warns against confirmations, user interaction, and uncontrolled
state changes inside parallel branches.

A `Swarm` relationship can contribute a Topology edge. Its call-for-reply mode
does not necessarily transfer responsibility, so it is not automatically an
AgSDL Handoff. The full-conversation transfer mode is a Handoff candidate, but
an importer still has to identify principals, acceptance, return or termination,
context transfer, and authority boundaries. `ManagerWorkers` expresses a
coordination pattern, not proof of delegation or authority.

## Versioning, loading, and security

### Source facts

Agent Spec versions use `YEAR.QUARTER.PATCH`. The 26.1.2 specification says every
configuration should include `agentspec_version`; a loader uses its current
version when the field is absent. It also says patch releases must not introduce
features or behavioral changes, while warning that any update, including a
patch, may contain breaking changes. Maintainers of runtimes, SDKs, and adapters
are responsible for reporting which Agent Spec versions they support.

Sensitive fields are omitted during export and supplied to the loader through a
component registry. The language specification also permits loading an input
that already contains a sensitive value. The security guide says exported
artifacts are not secure storage, recommends integrity and authenticity checks,
and warns that a tool identifier may resolve to a different implementation in a
new environment.

PyAgentSpec loader policies can allow or block component classes. Stdio MCP
transports are blocked by default because loading or running them can create a
subprocess. Network targets, retry behavior, and timeout coverage vary by
component and runtime.

The security guide records controls that version 26.1.2 cannot configure,
including memory and CPU limits, concurrency ceilings, general LLM cancellation,
and some internal timeouts. It also records the lack of conversation isolation
between subflows and subagents.

### AgSDL assessment

An omitted `agentspec_version` is not reproducible input for an AgSDL binding.
The binding must either reject it or record the exact version selected by the
loader before mapping starts. The version of the Agent Spec SDK, adapter,
runtime, and any plugins must remain separate from the language version.

Disaggregated secrets are compatible with AgSDL's proposed secret-separation
goal only when the AgSDL result retains a credential or secret reference rather
than the secret value. A source loader's ability to accept inline secrets cannot
weaken that rule.

Loader success proves neither artifact integrity nor safe activation. Import
must be possible in a no-network, no-subprocess mode. Any later resolution or
execution is a separate operation with its own observed input boundary and
authority.

## Validation and conformance evidence

### Source facts

The stable repository contains many executable tests for PyAgentSpec and
TSAgentSpec. They cover serialization, deserialization, schemas, structural
validation, references, version gates, security behavior, individual adapters,
tracing, and evaluation. Adapter code also contains explicit unsupported cases,
and some integration tests skip when optional dependencies or external model
configuration are unavailable.

The technical report describes a conformance test suite that would compare
execution outcomes across runtimes. No merged, versioned cross-runtime
conformance suite or conformance-result format was found in release 26.1.2.
The 2026 cross-framework paper reports experiments across LangGraph, CrewAI,
AutoGen, and WayFlow on three benchmarks. It finds meaningful differences in
accuracy, latency, and execution behavior even when the systems start from a
shared Agent Spec representation. This is execution evidence for those reported
experiments, not a general equivalence result or a versioned suite shipped with
the stable language release.

As of the review date, the repository listed two relevant draft contributions:

- [pull request 117, "Conformance Test Suite"](https://github.com/oracle/agent-spec/pull/117);
- [pull request 120, "Conformance Test Suite - Benchmarks - Tau2"](https://github.com/oracle/agent-spec/pull/120).

These drafts are evidence of active work, not part of the stable contract.
Agent Spec Eval and Agent Spec Tracing define useful evaluation and observation
APIs in the [26.1.2 evaluation documentation](https://oracle.github.io/agent-spec/26.1.2/agentspec/evaluation.html)
and [26.1.2 tracing documentation](https://oracle.github.io/agent-spec/26.1.2/agentspec/tracing.html).
They do not replace structural, mapping, round-trip, or runtime-equivalence
tests for an AgSDL adapter.

### AgSDL assessment

The released SDK tests support claims about those implementations at that tag.
They do not establish that every valid Agent Spec document has the same meaning
in every runtime, or that an AgSDL conversion preserves that meaning.

An AgSDL integration should initially claim only source inspection and mapping
coverage. A reversible-conversion claim requires versioned round-trip fixtures.
A behavioral-equivalence claim additionally requires execution tests for a
named Agent Spec runtime or adapter, target version, environment, observation
set, and input set. Unsupported and skipped cases remain outside the claim.

## Coverage comparison

The table compares the reviewed Agent Spec baseline with the proposed AgSDL
model. `Direct` means the source has an explicit construct close enough to
justify a candidate mapping. `Partial` means important AgSDL facts are absent or
the source semantics are narrower. `Adjacent` means the source addresses the
topic but describes a different subject. `Absent` means no corresponding stable
construct was found.

| Concern | Agent Spec 26.1.2 | Candidate AgSDL treatment |
| --- | --- | --- |
| Conversational agent | Direct | Agent plus separate Instructions, Model, Tool, and Interface facts |
| Structured workflow | Direct | Control flow, steps, transitions, invocations, and explicit source-only semantics |
| Multi-agent pattern | Partial | Topology plus qualified coordination, Delegation, Handoff, and Protocol facts |
| Input and output types | Direct | Interface or component contract, with Agent Spec conversion rules kept explicit |
| System boundary and purpose | Absent | Required AgSDL System facts cannot be synthesized silently |
| Lifecycle ownership | Absent | Remains unresolved or supplied by an authorized overlay |
| Principal and identity | Absent | Do not equate a component identifier with a Principal Identity |
| Authority and protected action | Absent | Tool availability and confirmation do not grant authority |
| Human approval | Partial | Preserve source flags and report missing approver, scope, evidence, and failure behavior |
| Trust boundary | Absent | Derive only from separately supplied deployment or policy evidence |
| Model definition and provider binding | Partial | Split portable Model requirements from resolved provider configuration |
| Tool contract and effect | Partial | Map Tool and Action; require explicit Effect, policy, and binding analysis |
| Memory and mutable state | Partial | Datastore, transforms, conversation, Memory, State, and Knowledge remain distinct |
| Internal component reference | Direct | Resolve within the captured artifact; wrap external resolution with AgSDL controls |
| Package and integrity | Partial | Record the source artifact, dependencies, digest, plugins, and omitted values |
| Deployment | Adjacent | Runtime configuration informs bindings but is not an AgSDL Deployment by itself |
| Trace and evaluation | Partial | Map definitions and evidence only where identities and versions remain traceable |
| Conformance | Partial | Reuse stable tests as source evidence; add AgSDL mapping and runtime suites |

## Candidate component mappings

These mappings are hypotheses for proposal and testing. None is accepted
normative behavior.

| Agent Spec construct | Candidate AgSDL construct | Required qualification or reported gap |
| --- | --- | --- |
| Root `Agent` | Fragment owning Agent, Instructions, Model, Tool, Action, and binding requirements | Missing mandatory Agent relations become unresolved Fragment requirements; a complete System needs further boundary, ownership, interface, principal, and policy facts |
| Root `Flow` | Fragment containing Control flow and steps | Interactive entry behavior and conversation handling need separate Interface, Protocol, and State analysis |
| `AgenticComponent` | No generic one-to-one mapping | Dispatch on the concrete type |
| `LlmConfig` | Model plus binding requirements | Provider endpoint and credentials stay binding-specific |
| `Tool` | Tool, Action, and Tool binding requirement | Missing mandatory Action relations become unresolved Fragment requirements; source I/O does not identify Effects, authority, policy, or trust crossing |
| `RemoteTool` or `MCPTool` | Tool, Action, Interface or external binding requirement | Preserve protocol version, endpoint, authentication, resolver, and runtime limitations |
| `BuiltinTool` | Required extension or target-specific binding | Runtime-specific semantics cannot become portable core meaning |
| `ToolBox` | Dynamic discovery or binding requirement | Discovered contents are observations, not immutable definitions |
| `Flow` | Control flow | Cycles, shared conversation, implicit data space, and type coercions need explicit treatment |
| `StartNode` and `EndNode` | Entry and terminal control-flow steps | Preserve multiple terminal branches and output defaults |
| `AgentNode`, `FlowNode`, `LlmNode`, `ToolNode` | Step invocation of the corresponding definition or Action | Verify I/O routing, failure, conversation, and return behavior |
| `ApiNode` | Tool and Action invocation with an external binding | HTTP configuration does not state authority or effect semantics |
| `BranchingNode` | Branch condition and transitions | Mapping, default branch, and input coercion must be preserved |
| `ParallelFlowNode` or `ParallelMapNode` | Parallel control-flow extension until core semantics exist | No order or atomicity may be inferred |
| `CatchExceptionNode` | Failure transition and policy candidate | Recoverable exception boundary and redaction behavior need explicit mapping |
| `Swarm.relationships` | Topology edges | A call is not automatically Delegation or Handoff |
| `Swarm.handoff` | Handoff candidate | Add principals, work item, acceptance, termination, context, and authority separation |
| `ManagerWorkers` | Coordination pattern and topology | Do not infer an Authority grant from manager assignment |
| `RemoteAgent` or `A2AAgent` | External Interface, Protocol, or runtime binding | A remote endpoint does not reveal an internal Agent or System definition |
| `$component_ref` | Local source identity during import | External AgSDL references need kind, version, integrity, and controlled resolution |
| `metadata` | Preserved uninterpreted source data | It is not portable AgSDL meaning without a named mapping |
| Agent Spec plugin component | Required or optional extension | Record plugin name, version, component type, and processor support |

## Terminology collisions

| Term | Agent Spec meaning | AgSDL risk |
| --- | --- | --- |
| Agent | In-process conversational component with an LLM, prompt, and tools | AgSDL Agent is a portable definition and has separate principal, identity, runtime, and system relations |
| Agentic component | Any interactive executable entry point, including a Flow | Treating every such component as an AgSDL Agent would collapse workflows and remote services into agents |
| Component | Generic serialized unit | It does not imply AgSDL definition kind, ownership, or lifecycle |
| Flow | Executable graph with control and optional data edges | AgSDL Control flow is not a whole System, Agent, Interface, or Protocol |
| Node | Flow vertex with implementation-defined behavior | It may map to a step plus an invoked definition, not a general system component |
| Tool | Callable procedure | AgSDL separates Tool, Action, Effect, binding, availability, and authority |
| ToolBox | Runtime discovery and aggregation source | It is neither an AgSDL Package nor a Skill |
| Handoff | Optional or mandatory transfer of a Swarm conversation | AgSDL Handoff transfers responsibility and requires explicit occurrence and authority separation |
| Memory | Planned broad Agent feature; current state also uses conversations, datastores, and transforms | AgSDL distinguishes Memory, Knowledge, State, storage binding, and execution occurrences |
| Metadata | Free-form consumer information | AgSDL extensions require identity, version, recognition, and preservation rules |
| Plugin | SDK and runtime code for added component types | AgSDL extension support must not require arbitrary code execution during inspection |
| Version | Agent Spec language target with fallback to loader current version | AgSDL separates language, definition, dependency, extension, adapter, runtime, and suite versions |
| Conformance | Project objective and implementation claim | AgSDL requires a named subject, capability, suite, evidence boundary, and verdict |
| Adapter | Framework conversion implementation | It is an independent AgSDL conformance subject, not evidence about all runtimes |

## Integration options

### Reference-only binding

An AgSDL description references an immutable Agent Spec artifact and declares
the artifact version, digest, expected root type, resolver, and required Agent
Spec processor capability. This option preserves the external contract without
claiming that AgSDL understands its internal meaning. It is the safest first
integration and can support inventory, dependency, provenance, and deployment
planning.

### Materialized import

An adapter resolves an Agent Spec artifact and emits AgSDL definitions plus a
mapping report. The report must cover every observed source component,
relationship, default, implicit behavior, plugin, and disaggregated dependency.
It identifies dropped, approximated, synthesized, unknown, or target-specific
information. Required source semantics without an AgSDL representation stop the
operation unless an explicit, testable degradation policy applies.

Materialization should produce a Fragment unless the source plus an authorized
overlay supplies every fact required for a complete System. The generated
Fragment owns the AgSDL definitions created by the mapping, and the report keeps
that AgSDL lifecycle relation distinct from Agent Spec source provenance. Every
other mandatory AgSDL relation absent from the source becomes an unresolved
requirement of the Fragment. The adapter must not invent principals, policies,
trust boundaries, Effects, or runtime guarantees.

### Export to Agent Spec

Export is valid only for a declared subset of AgSDL. The export report must
identify AgSDL definitions that Agent Spec cannot express. In particular, an
Agent Spec root cannot carry the full AgSDL governance, authority, deployment,
and conformance model. Such information needs a companion artifact or a named
Agent Spec plugin whose preservation and support are tested.

An exporter cannot claim reversible conversion until round-trip tests show that
all required portable meaning in the claimed subset survives. Successful load
or execution in one Agent Spec runtime is not a round-trip result.

## Executable evidence needed before compatibility claims

A future Agent Spec binding suite should include at least:

- positive and negative fixtures for duplicate, missing, mistyped, cyclic, and
  disaggregated references, including a no-network and no-subprocess mode;
- explicit and implicit data-flow fixtures, multiple-writer priority, defaults,
  JSON Schema compatibility, and every permitted lossy type conversion;
- branches, cycles, nested flows, shared conversations, parallel nodes,
  exceptions, and model- or runtime-selected behavior;
- tools, toolboxes, confirmation flags, sensitive fields, plugins, remote
  components, MCP, and A2A with supported and unsupported variants;
- missing and explicit `agentspec_version` values across supported version
  pairs;
- a complete mapping report for every fixture and stable diagnostic categories
  for every rejected mapping;
- AgSDL to Agent Spec to AgSDL round trips for each claimed reversible subset;
- runtime tests for each claimed behavioral mapping, pinned to the Agent Spec
  runtime or framework adapter, dependency versions, inputs, environment, and
  observable results;
- security cases proving that inspection performs no external retrieval,
  subprocess launch, secret resolution, or tool activation.

The suite should publish unsupported components and unobserved behavior. A pass
for source parsing, mapping, round trip, or one runtime execution remains a
separate verdict.

## Conclusion

Agent Spec 26.1.2 is the strongest concrete precedent reviewed here for a
declarative agent and workflow interchange format. Its released language and
SDKs can inform AgSDL's eventual serialization, I/O typing, reference, flow,
adapter, tracing, and evaluation work.

It does not cover AgSDL's complete system, governance, authority, deployment,
and conformance scope. Its runtime defaults, data coercions, shared conversation,
plugin execution, and framework adapters must remain external semantics. The
appropriate current step is a version-specific binding proposal with explicit
coverage and loss reporting. Parser, schema, and adapter code should wait until
AgSDL has selected syntax and can ship executable conformance fixtures.
