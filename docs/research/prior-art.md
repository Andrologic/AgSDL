# Prior art for AgSDL

Status: research note, non-normative
Last reviewed: 2026-09-02

## Purpose and method

This note surveys standards, protocols, formats, and implementation models that
can inform the Agentic Systems Definition Language. It does not propose AgSDL
syntax or change the normative specification.

The survey gives preference to primary sources maintained by the body that owns
each work. Older work appears only where it still supplies a useful concept
that newer specifications do not replace. Citations use a release edition, tag,
or commit when the publisher provides one. A citation marked as living
documentation had no published immutable edition at the time of review; its
retrieval date and, when available, repository commit preserve the reviewed
state. Every cited source was accessed on 2026-09-02.

Each source record separates two kinds of statement:

- **Source facts** summarize what the source defines and who maintains it.
- **AgSDL assessment** draws conclusions about possible reuse, limits, and
  terminology. These conclusions belong to this research note, not to the
  cited source.

No source below covers AgSDL's intended scope by itself. Most define an
integration boundary, a runtime programming model, or one cross-cutting concern.

## Agent definitions and orchestration

### OpenAI Agents SDK

**Source facts.** OpenAI maintains the Agents SDK. The [agent
model](https://github.com/openai/openai-agents-python/blob/v0.22.0/docs/agents.md)
and [orchestration
model](https://github.com/openai/openai-agents-python/blob/v0.22.0/docs/multi_agent.md)
reviewed here are from release `v0.22.0`.
An SDK agent combines a name, instructions, model settings, tools, handoffs,
guardrails, and an output type. The orchestration documentation distinguishes
manager-controlled calls to agents as tools from handoffs that transfer control
to another agent. It also distinguishes model-selected orchestration from
code-selected orchestration.

**AgSDL assessment.** The separation among agent definition, runner behavior,
handoff, guardrail, and structured output is useful. The manager-versus-handoff
distinction is also portable enough to investigate. The SDK is an implementation
model, not an interoperability standard. Its `Agent`, `Runner`, `context`,
`session`, `handoff`, and `guardrail` terms carry SDK-specific behavior. AgSDL
would risk implying that behavior if it reused those names without narrower
definitions.

### A2A Agent Cards and core protocol

**Source facts.** The A2A Project under the Linux Foundation maintains the
[A2A protocol specification 1.0.1](https://a2a-protocol.org/v1.0.1/specification/). An
Agent Card advertises an agent's identity, interfaces, capabilities, security
schemes, and skills. The protocol defines messages, content parts, stateful
tasks, task status, artifacts, streaming, push notifications, context
identifiers, and declared extensions. Agent Cards describe a remotely reachable
A2A server. They do not describe its internal agent graph.

**AgSDL assessment.** Agent Cards are the strongest current source for a
portable external agent description. AgSDL should be able to reference or map
to an Agent Card without treating it as a complete system definition. `agent`,
`skill`, `capability`, `task`, `message`, `artifact`, `context`, and `extension`
all collide with broader concepts in AgSDL's scope. In particular, an A2A skill
is advertised service metadata, not necessarily an Agent Skills package.

### FIPA agent architecture and interaction protocols

**Source facts.** The Foundation for Intelligent Physical Agents, now an IEEE
Computer Society standards activity, published a [catalog of standard FIPA
specifications](https://www.fipa.org/repository/standardspecs.html). It includes
an abstract architecture, agent management, an Agent Communication Language,
message transport, and reusable interaction protocols. The [FIPA Request
Interaction Protocol](https://www.fipa.org/specs/fipa00026/SC00026H.html)
defines request, refusal or agreement, success or failure, cancellation, and a
conversation identifier. The [FIPA Contract Net Interaction
Protocol](https://www.fipa.org/specs/fipa00029/SC00029H.html) defines a
call-for-proposals and selection pattern for distributing work.

**AgSDL assessment.** FIPA remains useful for separating message intent from
message content and transport, and for treating a multi-message exchange as a
named protocol with roles and terminal states. Its mental-state semantics,
directory services, ACL encodings, and platform model predate current LLM agent
systems and have little current adoption there. `agent`, `action`, `role`,
`conversation`, `protocol`, `request`, `inform`, and `contract` have formal FIPA
meanings that AgSDL should not inherit accidentally.

## Tools, capabilities, skills, prompts, and policies

### Model Context Protocol

**Source facts.** The Model Context Protocol project, hosted by the Linux
Foundation's Agentic AI Foundation, maintains the [MCP
specification](https://modelcontextprotocol.io/specification/2026-07-28/).
The 2026-07-28 revision defines a client-server protocol for discovering and
invoking tools, reading resources, and obtaining prompts. It uses declared
capabilities, JSON Schema-shaped tool inputs and outputs, typed content, and
protocol extensions. This revision replaces server-initiated sampling,
elicitation, and roots flows with multi round-trip results, removes hidden
protocol session state from the modern lifecycle, and moves tasks to an
extension. The [revision announcement](https://blog.modelcontextprotocol.io/posts/2026-07-28/)
records those changes and deprecations.

**AgSDL assessment.** MCP supplies precise external interface concepts for
tools, resources, prompts, discovery, invocation, content, and capability
negotiation. AgSDL should describe an MCP dependency by reference and version,
not copy MCP method schemas. MCP does not define an agent, an internal workflow,
or a portable permission model for every tool side effect. `tool`, `resource`,
`prompt`, `capability`, `task`, `content`, and `extension` need qualified use
because their MCP meanings are narrower than likely AgSDL meanings.

### OpenAPI

**Source facts.** The OpenAPI Initiative under the Linux Foundation maintains
the [OpenAPI Specification 3.2.0](https://spec.openapis.org/oas/v3.2.0.html).
It describes HTTP APIs through paths, operations, parameters, request and
response bodies, servers, callbacks, webhooks, reusable components, security
schemes, tags, and specification extensions. Its Schema Object is based on a
declared JSON Schema dialect.

**AgSDL assessment.** OpenAPI is a suitable reference for an HTTP tool or system
interface and for operation-level security requirements. AgSDL should not turn
every tool into HTTP or duplicate a full OpenAPI document. An OpenAPI operation
does not state agent-side intent, side-effect severity, approval requirements,
or model selection guidance. `operation`, `server`, `security`, `callback`,
`component`, and `extension` are collision risks.

### Agent Skills

**Source facts.** The Agent Skills open specification project maintains the
[Agent Skills
specification](https://github.com/agentskills/agentskills/blob/69ef37e9424c0a7ea9dd2293b559e43ec8176379/docs/specification.mdx).
The project did not publish a numbered specification edition at review time, so
this citation pins the living documentation to the reviewed commit. A skill is
a directory with a required `SKILL.md` file containing YAML metadata and
Markdown instructions. Optional scripts, references, and assets support the
instructions. The specification defines progressive disclosure from discovery
metadata to full instructions and then to on-demand resources. The
`allowed-tools` field is experimental.

**AgSDL assessment.** The package boundary, activation metadata, compatibility
metadata, progressive loading, and separation of instructions from executable
assets are reusable concepts. The format does not define the meaning of the
instructions, a portable execution sandbox, dependency resolution, signing, or
a stable permission model. `skill`, `tool`, `asset`, `reference`,
`compatibility`, and `metadata` could collide. AgSDL needs separate candidate
concepts for an invocable tool operation, an Agent Skills instruction package,
and a service advertised through A2A. None implies that an authority grant
permits its use or that a runtime implements it. The final terms and mappings
remain open pending a proposal.

### OpenAI Model Spec

**Source facts.** OpenAI maintains the [Model Spec, 18 December
2025](https://model-spec.openai.com/2025-12-18.html). It defines intended model
behavior, instruction authority levels, message roles, treatment of untrusted
data, autonomy boundaries, and rules for side effects. It distinguishes root,
system, developer, user, and guideline authority. OpenAI states that the public
Model Spec describes its intended behavior and that production models may not
fully reflect it.

**AgSDL assessment.** AgSDL needs explicit provenance and precedence for
instructions, plus a distinction between instruction text and enforceable
runtime policy. The Model Spec offers one concrete precedence model, not a
provider-neutral standard. AgSDL should not assume that all providers implement
its authority levels or message roles. `root`, `system`, `developer`, `user`,
`guideline`, `message`, `assistant`, and `tool` are therefore high-risk terms.

## Memory, knowledge, state, and provenance

### LangGraph memory and persistence

**Source facts.** LangChain maintains the [LangGraph memory
documentation](https://github.com/langchain-ai/docs/blob/b090b0076ae72fe8882570ff6b25033f8205ed85/src/oss/langgraph/add-memory.mdx).
The documentation has no independent edition, so this citation pins the living
documentation to the reviewed repository commit.
It separates short-term memory held in agent state from long-term memory held in
a store. Short-term state can be checkpointed by thread. Long-term records can
be organized by namespace and retrieved directly, by metadata, or by semantic
search.

**AgSDL assessment.** The distinctions among conversational history, mutable
runtime state, durable records, storage namespace, retention, and retrieval
method are useful. This is a framework contract rather than an interchange
standard. It does not provide a provider-neutral memory schema, truth model,
privacy policy, or consistency model. `memory`, `state`, `store`, `thread`,
`checkpoint`, and `namespace` can each hide different lifetimes and ownership.

### MCP resources

**Source facts.** MCP defines [resources](https://modelcontextprotocol.io/specification/2026-07-28/server/resources)
as application-controlled contextual data identified by URIs. Servers can list
resources and templates and return typed resource contents. Resource discovery
and access happen at runtime.

**AgSDL assessment.** A knowledge dependency can often be represented as an
external resource interface rather than embedded data. MCP resources do not
define knowledge quality, indexing, retrieval ranking, update policy, source
authority, or whether a returned item becomes durable memory. `resource` and
`context` need qualification in AgSDL.

### W3C PROV

**Source facts.** The W3C Provenance Working Group published the [PROV family of
documents](https://www.w3.org/TR/prov-overview/). Its conceptual model relates
entities, activities, and agents through generation, use, derivation,
attribution, association, delegation, and roles. The family includes normative
data-model, ontology, notation, and constraint specifications.

**AgSDL assessment.** PROV provides a mature vocabulary for tracing how a
knowledge item, memory record, result, or generated artifact came to exist.
AgSDL could map provenance claims to PROV without adopting RDF or PROV-N as its
serialization. PROV does not define conversational memory, retrieval, trust
scores, or agent execution. Its `agent`, `entity`, `activity`, `role`,
`collection`, and `bundle` terms have formal meanings and pose direct collision
risks.

## Messages, events, and workflows

### AsyncAPI

**Source facts.** The AsyncAPI Initiative under the Linux Foundation maintains
the [AsyncAPI Specification 3.1.0](https://www.asyncapi.com/docs/reference/specification/v3.1.0).
It describes message-driven APIs through servers, channels, operations,
messages, correlation identifiers, replies, security schemes, reusable
components, bindings, and specification extensions. Protocol bindings carry
transport-specific details.

**AgSDL assessment.** AsyncAPI is a strong external reference for asynchronous
agent interfaces, event channels, correlation, and protocol bindings. It does
not define agent intent, task lifecycle, delegation, or workflow semantics.
`message`, `channel`, `operation`, `reply`, `correlation`, `server`, `binding`,
and `component` could collide with AgSDL concepts.

### BPMN 2.0.2

**Source facts.** The Object Management Group maintains [Business Process Model
and Notation 2.0.2](https://www.omg.org/spec/BPMN/2.0.2). BPMN defines processes,
activities, events, gateways, sequence flows, message flows, participants,
collaborations, choreography, compensation, errors, and escalation. It has
machine-readable interchange artifacts and several conformance classes.

**AgSDL assessment.** BPMN provides mature control-flow and collaboration
concepts, especially explicit gateways, boundary events, compensation, and the
separation of sequence flow from message flow. Its executable semantics are
large and business-process-oriented. Importing them would turn AgSDL into a
workflow language and conflict with the current pre-syntax scope. `task`,
`activity`, `event`, `message`, `participant`, `process`, `gateway`, and
`orchestration` have established BPMN meanings.

## Schemas, observability, and authorization

### JSON Schema

**Source facts.** The JSON Schema project maintains [Draft
2020-12](https://json-schema.org/draft/2020-12). It separates core schema
mechanisms from validation vocabularies, identifies dialects with meta-schemas,
supports references and dynamic references, and defines annotations and
validation results. A vocabulary gives a set of keywords defined by URI. A
meta-schema declares required and optional vocabularies.

**AgSDL assessment.** JSON Schema is a likely validation dependency if AgSDL
eventually has a JSON-compatible serialization. Its dialect and vocabulary
model also offers useful lessons for extensions and version negotiation. JSON
Schema validates instance structure and selected assertions. It cannot by
itself define agent behavior, cross-run effects, authorization, or conformance
to runtime semantics. `schema`, `vocabulary`, `dialect`, `annotation`,
`reference`, and `validation` require careful definition.

### OpenTelemetry

**Source facts.** The Cloud Native Computing Foundation maintains the
[OpenTelemetry Specification
1.60.0](https://github.com/open-telemetry/opentelemetry-specification/tree/v1.60.0/specification)
and [Semantic Conventions
1.44.0](https://github.com/open-telemetry/semantic-conventions/tree/v1.44.0/docs).
OpenTelemetry defines APIs, SDK behavior, resources, context propagation,
traces, metrics, and logs. Semantic conventions assign stable names and
attributes to operations. Generative AI conventions are maintained in a
separate semantic-conventions repository and include agent and data-source
attributes.

**AgSDL assessment.** AgSDL should describe required observability signals and
map them to OpenTelemetry rather than invent a telemetry protocol. Trace and
span relationships can represent nested model calls, tool calls, and handoffs,
but telemetry describes observed execution, not intended topology or
conformance. Sensitive prompt and tool data also need explicit recording rules.
`resource`, `context`, `trace`, `span`, `event`, `attribute`, and `agent` carry
OpenTelemetry meanings.

### Open Policy Agent and Rego

**Source facts.** The Cloud Native Computing Foundation maintains [Open Policy
Agent and the Rego policy
language](https://github.com/open-policy-agent/opa/tree/v1.20.1) under release
`v1.20.1`. OPA separates policy decision-making from enforcement. A caller
supplies structured input; Rego evaluates policy and data to return a decision.
OPA also defines bundles, discovery, status, decision logs, and policy tests.

**AgSDL assessment.** The policy-decision-point and policy-enforcement-point
separation is directly useful. AgSDL can reference an external policy set and
declare where decisions must be enforced without embedding Rego. OPA does not
define agent instruction precedence, human approval UX, secret distribution,
or tool-side enforcement. `policy`, `rule`, `decision`, `input`, `data`,
`bundle`, and `enforcement` need precise qualification.

## Software-chain artifacts and packaging

### SPDX 3.0.1

**Source facts.** The Linux Foundation maintains the [SPDX Specification
3.0.1](https://spdx.github.io/spdx-spec/v3.0.1/). SPDX defines an open model for
bills of materials. A common core supports profiles for software, licensing,
security, build, AI, and other domains. Elements have identifiers and can be
connected through typed relationships. The specification defines serialization
and profile conformance points.

**AgSDL assessment.** SPDX can describe the software, model, dataset, license,
and build inventory associated with a packaged agentic system. AgSDL should
reference an SPDX document instead of duplicating bill-of-materials data. SPDX
does not describe runtime orchestration or behavioral semantics. `element`,
`artifact`, `package`, `profile`, `relationship`, `agent`, and `AI` have
SPDX-specific meanings.

### SLSA 1.2

**Source facts.** The Open Source Security Foundation maintains the [SLSA
Specification 1.2](https://slsa.dev/spec/v1.2/). It defines build and source
security tracks, graduated assurance levels, provenance, verification summary
attestations, and requirements for producers, build platforms, source-control
systems, and consumers. SLSA provenance records where, when, and how an artifact
was produced.

**AgSDL assessment.** SLSA supplies a model for verifiable claims about an
AgSDL package and generated deployment artifacts. It also shows why a claimed
level must name a track and verification evidence. SLSA does not attest that an
agentic system is behaviorally safe or conforms to AgSDL semantics. `level`,
`track`, `provenance`, `builder`, `source`, `artifact`, and `verification` must
not be reused as unqualified AgSDL terms.

### OCI Image and Distribution specifications

**Source facts.** The Open Container Initiative under the Linux Foundation
maintains the [OCI Image Specification
1.1.1](https://github.com/opencontainers/image-spec/blob/v1.1.1/spec.md) and
[Distribution Specification
1.1.1](https://github.com/opencontainers/distribution-spec/blob/v1.1.1/spec.md).
OCI descriptors bind a media type, digest, and size to content. Manifests can
package non-container artifacts with an artifact type, annotations, and a
subject relationship. Registries distribute manifests and blobs and expose
referrers associated with a subject digest.

**AgSDL assessment.** OCI offers an existing content-addressed distribution
mechanism for AgSDL packages, schemas, signatures, SBOMs, and attestations. It
does not define their internal semantics, dependency resolution, or safe
activation. `manifest`, `descriptor`, `artifact`, `subject`, `annotation`,
`reference`, `index`, and `layer` are established OCI terms.

## Extension mechanisms compared

**Source facts.** Several surveyed specifications provide extension points with
different compatibility rules:

- OpenAPI and AsyncAPI reserve `x-` prefixed specification extensions while
  retaining a fixed core object model.
- JSON Schema identifies extension vocabularies by URI and lets a dialect mark
  them required or optional.
- A2A advertises named extensions and whether a client must support them.
- MCP negotiates protocol capabilities and defines separately versioned
  extensions.
- OCI accepts namespaced annotations and unknown annotation keys, while media
  types identify new artifact kinds.
- SPDX uses profiles over a common core and defines conformance points.

**AgSDL assessment.** These mechanisms solve different problems. Free-form
annotations preserve data but do not define portable behavior. Required
vocabularies or extensions can protect semantics but reduce interoperability.
Profiles can state coherent subsets but require explicit conformance rules.
AgSDL will need separate mechanisms for harmless metadata, namespaced semantic
extensions, capability negotiation, and profiles. Calling all four an
`extension` would conceal material compatibility differences.

## Coverage matrix

The ratings measure coverage of each column's subject, not the quality or
maturity of a source:

- `Strong` means the source directly defines most of the subject's concepts and
  behavior well enough to support a candidate external reference or mapping.
- `Partial` means the source directly defines part of the subject, but excludes
  a material concept or restricts it to a narrower protocol, runtime, or role.
- An adjacent label, such as `Context only`, `Tool spans`, or `Artifacts`, names
  a useful analogy or supporting datum but not a contract for the subject.
- A blank cell means the survey found no material coverage for that subject.

Qualifiers after `Strong` or `Partial` state the boundary that affected the
rating. These research ratings do not establish compatibility with AgSDL.

| Source | Agent description | Multi-agent and orchestration | Tools and skills | Prompts and policy | Memory and knowledge | Communication | Workflow | Observability | Authorization | Packaging and provenance | Extensions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OpenAI Agents SDK | Strong | Strong | Strong | Partial | Partial | Partial | Partial | Strong | Partial |  | Partial |
| A2A | Strong, external | Partial | Partial |  | Context only | Strong | Task lifecycle | Partial | Security declaration | Artifacts | Strong |
| FIPA | Strong, platform-era | Strong | Capability discovery |  | Ontology only | Strong | Interaction protocols |  | Agent identity |  | Protocol library |
| MCP |  |  | Strong | Prompts only | Resources only | Strong client-server | Task extension | Logging hooks | OAuth boundary | Resource links | Strong |
| OpenAPI |  |  | Strong for HTTP |  |  | Request-response | Callbacks and webhooks |  | Security schemes |  | Strong |
| Agent Skills | Component only |  | Strong for skills | Instruction body | References only |  | Procedure text |  | Experimental allowed tools | Package directory | Metadata only |
| OpenAI Model Spec | Assistant only |  | Tool behavior | Strong | Conversation context | Message roles |  |  | Authority, not access control |  |  |
| LangGraph | Runtime agent | Graph runtime | Nodes and tools |  | Strong | State transitions | Strong |  |  | Checkpoints | Framework-specific |
| W3C PROV | Agent as responsibility | Delegation relation |  |  | Provenance only |  | Activities |  |  | Strong | Bundles |
| AsyncAPI |  |  | Interface only |  |  | Strong async | Replies and correlation |  | Security schemes |  | Strong |
| BPMN | Participants | Strong | Service task only |  | Data objects only | Message flows | Strong |  | Lanes only |  | Extension elements |
| JSON Schema |  |  | Input/output shape |  | Data shape | Payload shape |  | Validation output |  | Schema bundles | Strong |
| OpenTelemetry | Runtime attributes | Trace relationships | Tool spans | Prompt attributes | Data-source attributes | Messaging spans | Runtime trace | Strong |  | Trace evidence | Semantic conventions |
| OPA/Rego |  |  | Invocation decisions | Policy decisions | Policy data |  |  | Decision logs | Strong | Policy bundles | Built-ins and bundles |
| SPDX | AI profile elements | Relationships | Components |  | Datasets |  | Build profile |  | Security profile | Strong | Profiles |
| SLSA |  |  |  |  |  |  | Build process |  | Build controls | Strong | Tracks |
| OCI |  |  | Packaged content |  |  | Distribution API |  |  | Registry auth boundary | Strong | Strong |

## Gaps in current prior art

These are conclusions from the comparison, not claims made by any one source.

1. No surveyed standard describes both an agent's internal definition and the
   complete system graph around it. A2A and MCP deliberately stop at external
   protocol boundaries. Frameworks cover internal behavior but are not portable.
2. `Skill` has at least three incompatible uses: an A2A-advertised service, an
   Agent Skills instruction package, and a generic learned or executable
   capability. These are also independent of an invocable tool operation, an
   authority grant that permits use, and an implementation feature that a
   runtime supports.
3. Memory has no common interchange model. Frameworks disagree on whether it
   means conversation history, checkpointed state, durable records, retrieved
   knowledge, or model-managed state.
4. Prompt precedence and authorization policy are separate concerns in the
   available work. A model's instruction hierarchy does not enforce access to a
   tool, and an OPA decision does not determine which instruction a model follows.
5. Workflow standards specify deterministic process semantics, while current
   agent frameworks mix deterministic control with model-selected transitions.
   No surveyed standard gives a portable boundary between the two.
6. Interface schemas describe valid messages and calls, but they do not express
   side-effect reversibility, approval gates, trust boundaries, or recovery
   obligations in a common way.
7. Observability standards can record executions but do not prove conformance of
   an execution to an intended agentic system definition.
8. Supply-chain standards establish composition and provenance, not behavioral
   safety, model suitability, or runtime interoperability.

## Decisions AgSDL will need to make

The order below follows dependency order. Later decisions rely on earlier ones.
It is a research agenda, not a set of proposed answers.

1. Define the conformance boundary: document parsing, structural validation,
   portable semantics, runtime behavior, and implementation-specific claims.
2. Define `agent`, `system`, `component`, and `role`. Keep supported
   implementation behavior distinct from authority granted over a resource and
   from externally advertised service metadata. Decide their final names only
   through a terminology proposal.
3. Separate definition-time entities from runtime instances, executions, tasks,
   messages, state, and generated artifacts.
4. Define the system graph and ownership model: containment, reference,
   composition, delegation, handoff, call, routing, and supervision.
5. Define the boundary between deterministic orchestration and model-selected
   orchestration, including how implementations report unsupported semantics.
6. Define tool operation interfaces, side-effect metadata, failure modes, and
   approval gates. Treat mappings to MCP, OpenAPI, and other external contracts
   as separate hypotheses until proposals and tests establish them.
7. Define distinct concepts for Agent Skills packages and A2A-advertised
   services. Keep both separate from tool availability, authority grants, and
   runtime implementation features, then investigate mappings among them.
8. Define instruction sources, authority, composition, conflict resolution,
   mutability, and treatment of untrusted content without assuming one model
   provider's message roles.
9. Define memory, state, history, knowledge, and context as separate concepts,
   with scope, lifetime, ownership, retention, retrieval, and provenance.
10. Define communication independently of transport: message intent, payload,
    correlation, task lifecycle, delivery guarantees, cancellation, streaming,
    and artifact delivery.
11. Define permissions, credential references, trust boundaries, policy decision
    points, policy enforcement points, human authority, and audit evidence.
12. Define failure and recovery semantics, including timeout, retry, idempotency,
    compensation, escalation, partial results, and interrupted handoffs.
13. Define observability and evaluation requirements and their mapping to
    OpenTelemetry, including rules for sensitive data and trace correlation.
14. Define reference resolution, package identity, content integrity,
    dependencies, profiles, version compatibility, and supply-chain attestations.
15. Split extension design into annotations, namespaced semantic extensions,
    required capabilities, and profiles. Define unknown-extension behavior for
    each class.
16. Select serialization and schema technology only after the conceptual terms
    and cross-entity constraints above are stable, as required by Decision 0001.

## Overall conclusion

Composition is a candidate direction, not an integration result. Possible
mapping hypotheses include MCP or OpenAPI for tool interfaces, A2A for remote
agent interaction, AsyncAPI for asynchronous interfaces, OpenTelemetry for
telemetry, OPA for one possible policy-decision architecture, and SPDX, SLSA,
or OCI for software-chain evidence and distribution. Each hypothesis requires
its own proposal, semantic mapping, loss analysis, and executable tests before
AgSDL can claim integration, compatibility, or round-trip preservation. None of
these sources supplies the still-open AgSDL concepts for agent definitions,
topology, instruction authority, memory boundaries, portable orchestration
meaning, permissions, failure policy, or conformance.
