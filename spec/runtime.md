# R: configurations and reusable content

[Specification index](README.md).

Document.runtime remains optional and opaque to D/G/inspect/exchange. ValidateR
interprets RuntimeDeclaration. It has no engine execution or
resolved-R operation. G remains independent of configuration selection.

| Record | Fields |
| --- | --- |
| RuntimeDeclaration | `configurations:Configuration[]`, `selected?:text` |
| Configuration | `id:text`, `graph:Key`, `agents:AgentBinding[]` |
| AgentBinding | `agent:Ref`, `engine:Edition or null`, `parameters:JSON`, `requires:Edition[]`, `claims:CapabilityClaim[]`, `tools:ToolBinding[]`, `applications:Application[]` |
| ToolBinding | `tool:Ref`, `choices:Implementation[]`, `selected?:text` |
| Implementation | `id:text`, `implementation:Edition`, `parameters:JSON`, `claims:CapabilityClaim[]` |
| Application | `content:Ref`, `adapter:Edition`, `parameters:JSON` |
| CapabilityClaim | `capability:Edition`, `status:"supported" or "unsupported" or "unknown"`, `evidence:Hash or null` |
| Tool payload | `action:Ref`, `inputs:Ports`, `outputs:Ports`, `effects:"none" or "external" or "unknown"`, `failures:text[]`, `requires:Edition[]` |
| Instructions payload | `target:"Agent"`, `at:"before-invoke"`, `format:Edition`, `body:text`, `requires:Edition[]` |
| Skill payload | `inputs:Ports`, `outputs:Ports`, `preconditions:text`, `completion:text`, `dependencies:Ref[]`, `tools:Ref[]`, `requires:Edition[]` |

The three reusable payload shapes are additional entry points, not global D
payload constraints. R interprets them only when reached by configuration
bindings, direct Agent uses/directedBy relations or Skill dependencies. Role,
ControlFlow, Action, Principal and Resource payloads stay opaque. Skill ports,
preconditions and completion describe its bounded behavioral contract, not a
new callable graph node or executable expression language.

## Configuration selection and assignments

All configurations are shape-checked and structurally checked by R. Ids are
unique; selected names exactly one configuration. Missing selected is valid,
means not provided and selects nothing, including when there is one choice.
Unknown selected fails R-SELECTION; duplicate selected ids block selection
lookup after the duplicate finding. Configuration array order never picks one.
Every graph Key names exactly one Graph.definition in primary graphs; its target
is a local ControlFlow. R uses only graph/step identification and Agent refs to
check assignments. It does not execute or silently replace G path validation.
R's read-only graph projection requires an array of objects with readable
Graph.definition Keys to locate a configuration's graph. To enumerate its
Agents, steps must be an array of objects with a known G kind and a readable
Agent Ref on each invoke. It ignores other G fields for this purpose. Missing
or malformed projection data blocks R-SELECTION at the affected Configuration
for graph lookup, or R-BINDING there for Agent enumeration. It does not emit
P-SHAPE for G fields: validateG owns their shape. A known missing graph in a
fully readable graph index fails R-SELECTION. Duplicate matching definitions
block lookup. R does not infer an empty graph from unreadable data.

There is exactly one AgentBinding per distinct Agent used by an invoke in that
graph, and none for unused Agents. Equality uses scoped keys when locally
observable and the exact Ref declaration otherwise. R checks every Ref's local
kind or external dependency/scope declaration under the shared reference rules.
External content is not fetched or resolved by validateR, even when annex bytes
are supplied. Checks that need that content are explicitly excluded, with
compatibility unknown for a selected configuration. A graph may use an imported
Agent; a declaration match is not resolved identity evidence.

Repeated invokes of one Agent share its binding. To describe distinct Agent
roles with distinct engine choices in the same graph, use distinct Agent
definitions. Across configurations the same Agent and graph may select different
engines, parameters, implementations and applications without editing the graph.
Null engine explicitly means not provided. No known engine name receives special
trust; custom Edition ids follow exactly the same rules.

Tools required by an Agent are all targets of its local `uses` relations with
expectedKind Tool plus Tool targets of its selected Skill closure. Each required
Tool has exactly one ToolBinding; extra ToolBindings are rejected as undeclared
substitution. Every choice id in a ToolBinding is unique, and selected names
exactly one choice. A missing choice selection is not provided, even for one
choice. Empty choices is legal incomplete configuration. Alternative choices
are declarations only; no failure triggers automatic reselection. Their order
is not preference. The implementation claims the Tool identified by its own
binding, never rewrites its Action, ports, effects or failure labels.

Relations naming external Tool targets count toward required bindings by exact
Ref, but their payload and capability requirements remain unobserved by R.
External or malformed Skill dependencies similarly cannot be treated as an
empty closure. Shape failures block their dependent checks; external content
excludes them. ValidateR never manufactures proof of complete compatibility.

## Content composition, application and prerequisites

Instructions carry reusable content and explicit target/application point.
`before-invoke` means the requested application before each invocation of the
bound Agent, not a provider prompt role or a universal precedence level.
An Application names an engine-specific adapter for that content and point.
Its parameters may describe channel, rendering or native options; these are
opaque assertions and do not establish that an engine applies them correctly.
No adapter, channel, priority, insertion point or parameters are inferred.

Every Agent directedBy target of kind Instructions or Skill must appear in its
binding's applications. A Skill dependency is an Instructions or Skill Ref.
All dependencies must also have explicit Application entries earlier in the
same array than each occurrence of their dependent Skill. This gives one
visible application order without implicit expansion, inclusion, priority or
inheritance. Repeated applications are allowed and repeat the requested content;
there is no deduplication. Array order is requested application order, not proof
of runtime instruction priority. Additional applications must be reachable from
a directedBy Instructions/Skill root through Skill.dependencies. Unrelated
content cannot silently replace the Agent's direction. Role/ControlFlow direction
continues to count for D minima, but R does not interpret their behavior.

Skill dependencies and tools have no duplicate Refs. Dependencies must be acyclic in the observed
closure. This is static prerequisite composition; recursive behavior would need
a separately specified termination contract. A Skill's own text,
ports and dependency order do not implement a skill runtime. A missing required
Application fails R-CONTENT at AgentBinding; a later-only dependency fails at the dependent
Application. For every Skill whose dependency graph can reach itself, emit one
R-CONTENT cycle finding at that Skill payload. A missing local prerequisite
fails at its requesting Skill payload; an ambiguous or malformed one blocks
there while independent reachable records remain checked. If a prerequisite target is external, the rule excludes that lookup
and marks selected compatibility unknown. Requirements of every observed Tool,
Instructions and Skill remain required under all configurations. No generic
merge, overwrite, base-profile chain or implicit prompt inheritance is defined.

## Declared compatibility, not readiness

Structural validation runs on all configurations. The following assessment runs
only on the selected configuration; unselected configurations remain inspectable
without making a selected configuration fail for unfilled alternative choices.
Malformed records still fail P-SHAPE in every configuration.

For each selected AgentBinding, engine requirements are the set union of its
requires, the requires of every observed Instructions/Skill in the required
directedBy/dependencies closure, the format Editions of those Instructions,
and adapter Editions of declared Applications. Required content contributes
these intrinsic requirements even when its Application is missing.
Tool requirements are the requires in its Tool payload and are compared to the
selected Implementation claims. All claims identify exact Editions; duplicates
per claim array fail even if their status agrees. Unknown claim Editions are
retained but do not discharge a different requirement. No version ordering,
capability taxonomy or inference from an implementation's name exists.

For each required capability at each affected AgentBinding or ToolBinding:

1. No engine or no selected Implementation means `not-provided`.
2. Otherwise an explicit unsupported claim means `incompatible`, as declared.
3. Otherwise missing claim, unknown status, or supported with null evidence means
   `unknown`. An unobserved external requirement closure also means unknown.
4. Otherwise all required claims are supported with known evidence hashes:
   `declared-supported`. An observed empty requirement set also reaches this
   state if the engine/implementation is supplied.

Each missing required Application additionally contributes `not-provided` at
its AgentBinding, independently of the capability assessments. A missing local
required content target contributes not-provided there; an external target
contributes unknown. Neither omission erases requirements from other observed
content. For example, a supplied engine declaring an observed required capability
unsupported remains incompatible when that content's Application is missing:
R-CONTENT fails and R-COMPATIBILITY emits both fail and inconclusive.

Record one aggregate assessment State per binding with precedence incompatible,
not-provided, unknown, declared-supported. For findings, collect the contributing
capability and omission assessments: emit fail if any is incompatible and
inconclusive if any is not-provided or unknown, coalescing each location/outcome
separately. Malformed or ambiguous structural prerequisites block dependent
assessment checks and the aggregate State. Independent requirements still
produce their findings, including a known incompatibility when another portion
is blocked or unknown.
The declaration is not factual compatibility verification. Evidence hashes are
identities of assertions, not authentication or test results; no evidence content
is retrieved. Tools with effects unknown additionally make their assessment
unknown. Capability or content omissions never authorize silent removal,
replacement, or a ready claim. Even declared-supported excludes readiness and
actual evidence assessment. The MVP provides no launch-permission verdict.
