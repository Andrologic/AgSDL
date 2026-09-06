# Proposal 0013: modular MVP contract for 0.1.0

- Status: proposed experimental candidate, not normative adoption.
- Date: 2026-09-06.
- Edition marker: `proposal-0013-candidate-1`.
- Basis: proposal 0012 candidate-2 at repository revision
  `009a51eb301688f06d29bb7e2f1784e3c4a4cc98`.

## Scope, authority and continuity

The maintainer's interview establishes the following directions for the 0.1.0
POC/MVP: general-purpose descriptions without a required product; reusable Agent
and graph definitions distinct from engine software, configuration and concrete
execution; several configurations for the same graph; different engines per
Agent; open engine identifiers without a default; explicit tool implementations
and engine-specific parameters; reusable Instructions/Skills where compatible;
no silent removal or substitution of required capabilities; and a configuration
fixed throughout one execution. Stop, change configuration and start a new
execution replaces hot reload, state migration or resumption.

These are design directions, not adoption of the record shapes below. The
interview does not settle which concrete actor a configuration may bind.
This proposal states its limited Principal interpretation explicitly. Sequential
approval composition and addressable Interface operations implement the proposed
MVP direction without adding parallel approval, quorum or reusable approval.

[Decision 0004](../docs/decisions/0004-approved-design-directions.md),
[scope](../docs/scope.md) and [proposal 0002](0002-core-conceptual-model.md) remain
the conceptual basis. No file under spec changes. No engine, authorization
service, compatibility verifier or described agent runs in this contract.

This edition is a delta over [0012](0012-minimal-0.1.0-contract.md), not a rewrite.
Use its exact bytes at the basis revision when implementing inherited rules.
The 121 candidate-2 cases, schemas, readers and their hashes are historical
experimental evidence; they do not establish support for this edition. Keep
both markers distinct, with no automatic upgrade or mixed-edition annexes.

Inherited unchanged except where an explicit replacement below applies:

- strict JSON/UTF-8 parsing, numeric domains and lossless lexemes, exact Key and
  Edition equality, document ownership, exports, direct dependency resolution,
  extension interpretation and preservation boundaries;
- all D records and semantics, including Agent actsAs/directedBy/exposes minima
  and the single Fragment Interface deferral;
- G finite paths, typed Ports/Bindings, local/reference checks, success-edge
  availability, fixed documentary exclusions and dependency collision rules;
- the seven host operations, supplied byte boundary, Report grammar and tuple
  comparison, finding aggregation, partial checks and exact byte locations;
- exact exchange and unconditional lossy refusal. The marker in every Document
  and Report is this edition's marker. Dependency validation uses this edition.

Replaced: the Interface payload, invoke/approval records, approval-chain rules,
and the entire R RuntimeDeclaration/Requirement/Selection/EvidenceClaim grammar
and rules. R no longer selects one engine for the whole document. No old R
record is implicitly translated. New payload interpretation is limited below.

## Terms, identity and the Principal boundary

| Term | Meaning in this candidate |
| --- | --- |
| Agent definition | The existing versioned Agent, with its Key, lifecycle owner, interfaces and behavioral requirements. It does not name engine software. |
| Engine | Software that executes an Agent. An Edition identifies a claimed engine contract/version, not an Agent, deployment instance or acting identity. |
| Configuration | One named complete set of choices for a graph: engine assignments, tool choices, content applications and parameters. It realizes the constrained-choice purpose of a configuration profile in 0002, without profile inheritance. |
| AgentBinding | The configuration's assignment for exactly one resolved Agent definition. Repeated invocations of that Agent use the same assignment in this configuration. |
| Execution | One concrete use of a graph and a selected configuration. Occurrence identity, timing, authentication and state belong to a runtime outside these static records. |
| Tool implementation | A named concrete adapter/function/service choice claiming to realize a Tool contract. Its Edition and opaque parameters do not prove that it exists or implements that contract. |

A Configuration id is local to one RuntimeDeclaration, not a global definition
Key. The pair of the containing artifact's byte hash and configuration id pins
its content for a prospective execution. The graph and all referenced definitions
retain their own Keys/versions and dependency hashes. A changed configuration
requires a new execution; editing its containing artifact changes the pin even
if its human-readable id is reused. No mutable execution record or launch API is
introduced. A runtime cannot present an edited configuration as the same pinned
execution, or claim migrated state under these static checks.

**Principal candidate choice, not an interview decision:** retain Agent actsAs
Principal definition and invoke.principal equality from candidate-2. Interpret
that Principal definition as the declared accountable actor or actor class,
never as authenticated occurrence identity. Configuration selects no Principal
and confers no authority. The actual acting identity remains external execution
evidence. For example, the same reviewer Agent acting as the declared
`review-service` Principal can be assigned engine A in one configuration and
engine B in another; neither assignment proves an actor's identity.

An alternative would allow configuration A to bind a customer-A Principal and
configuration B a customer-B Principal to the same Agent. That changes the
actsAs minimum and invoke.principal agreement, and may change approval scope.
It is not implied by engine portability. This edition deliberately retains the
existing restriction rather than silently choosing that alternative. Whether
to permit such rebinding is open before adoption; the present candidate remains
implementable without deciding runtime authentication or that broader actor model.

## Closed record inventory

The notation, required fields, absent versus null, text/Edition/Ref/Key/Hash,
Ports and Bindings are as in 0012. Every record below is closed. `JSON` is opaque
losslessly preserved content; it cannot override any interpreted field.
`Edition[]` has no duplicate Editions, checked by the owning semantic rule
below rather than a second P-SHAPE finding. Array order has meaning only where stated.
There are no implicit defaults, environment lookups or downloads.

### G operation and approval records

Graph, condition and end Step records are inherited. An invoke retains all its
old fields and adds required `operation:text`. An approval retains all its old
fields and adds required `call:text`. These new fields are not optional even for
a single operation or a single gate.

| Record | Fields |
| --- | --- |
| Interface payload | `operations:Operation[]` nonempty |
| Operation | `id:text`, `direction:"inbound" or "outbound" or "bidirectional"`, `mode:"request-response"`, `action:Ref`, `inputs:Ports`, `outputs:Ports` |
| ApprovalRequirement payload | Unchanged: `approvers:Ref[]` nonempty, `validForMs:positive` |

Operation ids are unique within the selected Interface. They are addressed by
Interface Ref plus operation id, never by searching other interfaces. Every
operation is a complete request/response contract; multi-message protocols and
notification dispatch need a separate future contract. This bounded interaction
mode is the existing invoke abstraction, not a restriction on open engine ids.
Direction is relative to the Agent exposing the Interface. Invoke selects an
inbound or bidirectional Operation; selecting outbound fails G-TARGET. Selected
operation Action and Ports equal invoke.action/inputs/outputs under inherited
identity and exact-type rules. No operation is chosen by order or default.

G shape-checks the entire selected Interface payload, including all Operation
records. G-TARGET checks id uniqueness there; semantic Action resolution and
port agreement apply only to the selected operation. Bad fields on an unrelated
operation do not block readable fields on the selected one. Duplicate selected
id blocks its dependent lookup; an absent id fails at the consuming Step.
Annex payload findings use the annex G Result and operation record location;
id duplication points to its later Operation record. The primary comparison
still points to its Step. Unselected payloads remain opaque as in candidate-2.

### R configuration and reusable payload records

Document.runtime remains optional and opaque to D/G/inspect/exchange. ValidateR
interprets this replacement RuntimeDeclaration. It has no engine execution or
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
kind or external dependency/scope declaration under the inherited rules.
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
a separately specified termination contract from 0002. A Skill's own text,
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
requires, the requires of every observed applied Instructions/Skill, and the
format Editions of applied Instructions and adapter Editions of Applications.
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

Record one aggregate assessment State per binding with precedence incompatible,
not-provided, unknown, declared-supported. For findings, collect the contributing
capability assessments: emit fail if any is incompatible and inconclusive if any
is not-provided or unknown, coalescing each location/outcome separately. Assessment is blocked, not fabricated, when its
structural prerequisites are malformed or ambiguous. A known incompatible
capability is still reported when an independent requirement is unknown.
The declaration is not factual compatibility verification. Evidence hashes are
identities of assertions, not authentication or test results; no evidence content
is retrieved. Tools with effects unknown additionally make their assessment
unknown. Capability or content omissions never authorize silent removal,
replacement, or a ready claim. Even declared-supported excludes readiness and
actual evidence assessment. The MVP provides no launch-permission verdict.

## Sequential approvals for one call

Replace candidate-2's immediate-invoke restriction with an explicit `call` link.
Every approval names an invoke in the same graph. Its approved edge targets that
invoke or another approval with the same call. Following approved edges must
reach that call. A chain can contain any finite positive number of gates; each
gate is a distinct decision request even if requirements repeat.

For each protected call, its gates form one ordered chain: the invoke has only
the final gate's approved incoming edge; every gate after the first has only its
predecessor's approved incoming edge. The first gate can have ordinary incoming
edges or be entry. No denied or failure edge from any gate may reach its call or
any later gate in that chain. G-PATH still requires an acyclic, reachable graph.
A failed G-PATH check blocks chain reachability and incoming-path checks as in
0012; readable call links and target kinds still receive independent checks.
These rules forbid alternate gate paths, skipping, parallel approval and quorum
without inventing a second orchestration system. Unprotected invokes remain legal.

Each gate's request scope is its call's selected Interface operation, Action,
resources, Principal definition, input values and context, plus the selected
configuration pin for a prospective execution. G validates the declared call
link and binding availability at every gate, not the existence of an execution
or a configuration selection. All call inputs/context must be available before
each gate under the inherited producer-success rule. Gates produce no ports.

Each gate's decision deadline remains entry time plus min(timeoutMs, validForMs).
All earlier approvals must still be valid when entering later gates and when
admitting the call. Refusal selects the active gate's denied edge; no response,
invalid decision, or expiry of any needed decision selects its failure edge.
If expiry is detected at call admission, take the call's failure edge without
invoking it. Equality with a deadline counts as expired. Finite positive windows
do not prove that human decisions can arrive in time; static validation imposes
no invented timing inequality between gate durations.

All approvals are consumed only by that call in that execution. Stopping and
restarting, or changing the configuration pin, invalidates their use. There is
no reusable token API, decision intake service, authorization engine, migration
or runtime timing evidence here. The chain declares required control structure;
it neither authenticates an approver nor proves enforcement or permission.

## Deterministic operations, reports and validation rules

Use inherited Report fields and verdicts. R Result phase remains
unresolved-document. R uses D as prerequisite, not G. Extra R rule ids below
belong only to this edition. R runs P-SHAPE, X-MODE, R-SELECTION, R-BINDING,
R-TOOL, R-CONTENT, R-COMPATIBILITY. The old R-REQUIREMENT rule is replaced.
The four documentary exclusions remain exact as in 0012. Readiness and evidence
assessment remain excluded at /runtime. No new execution verdict is introduced.

| Rule | Covered check and finding/block location |
| --- | --- |
| R-SELECTION | Configuration ids unique; selected exists; graph Key selects one Graph and ControlFlow. Later duplicate Configuration or affected Configuration; bad selected at RuntimeDeclaration. |
| R-BINDING | Exact Agent coverage and kinds, duplicate claim Editions and requires, engine requirement declaration structure. AgentBinding; missing AgentBinding at Configuration. |
| R-TOOL | Required Tool coverage, typed Tool Action, Tool payload shape, duplicate failures/requirements and Implementation claim Editions, choice ids and selection; ToolBinding, missing binding at AgentBinding, later duplicate Implementation, selected Tool payload record for its semantic defect. |
| R-CONTENT | Typed content, exact reachable set, required applications present, prerequisite order/cycles, payload requirement duplicates and typed Skill tools. Application; missing application at AgentBinding; cycle at affected Skill payload. |
| R-COMPATIBILITY | The selected configuration assessment above. AgentBinding or ToolBinding; one finding per location/outcome after aggregation as below. |
| G-TARGET delta | Operation existence/id/direction, selected Action and ports; locations as specified in the G section. |
| G-APPROVAL delta | Call link, chain structure, sole approved incoming edges, no refusal bypass. Affected approval Step; bad final incoming edges point to its final approval Step. |
| G-DATA delta | Call inputs/context unavailable at a gate point to that approval Step. |

Known structural violations fail their named rule. Incompatible assessment gives
R-COMPATIBILITY fail; not-provided/unknown give inconclusive; declared-supported
completes without a finding. Preserve independent fail and inconclusive findings
when both occur at one binding. Unknown support is not unsupported interpretation:
unsupported remains reserved for the inherited extension/direct-resolution limits.
Known local target missing/wrong kind fails the owning R rule at the requesting
record. Duplicate or malformed identity blocks dependent lookup; no first/last
winner. Direct dependency declarations obey D, including integrity and accounting.

P-SHAPE owns every malformed field/parent in the interpreted scope, even for
unselected configurations. R also shape-checks observed reusable payloads at their
source records. In this edition validateR observes only primary payloads; it
emits no annex R Result. Partial checks retain completed only for observed
checks or known empty domains; affected-record blocked/excluded locations follow
0012. A missing container needed for enumeration blocks at its existing parent,
not an invented absent child. Syntax failure blocks the whole requested unit.

Missing runtime excludes P-SHAPE and all R-* at /runtime, X-MODE still runs.
Empty configurations completes structural R rules. Missing selected excludes
R-COMPATIBILITY at /runtime, as no configuration assessment was requested.
A present selected with malformed/ambiguous target blocks R-COMPATIBILITY there.
Unselected configurations do not exclude structural rules. Empty subjects within
a readable selected configuration complete the applicable rule. External R refs
complete declaration checks and exclude target-dependent checks at their
requesting record; missing direct bytes do not make R a resolved operation.
G resolves only its inherited direct target closure, not R configuration content.

### Inventory replacement for R

Keep all inherited non-runtime State and opaque rules. Replace the R-only row
with the following exhaustive additions, only under well-shaped parent records:

- /runtime/selected is absent or declared. Missing selected creates no
  assessment states; configuration declaration states below are still recorded.
- Each Configuration record is declared. Each AgentBinding engine field is absent
  when null, declared otherwise. Each ToolBinding selected field is absent or
  declared. These are declarations of each configuration, not inferred defaults.
- Each null CapabilityClaim evidence is unknown at its evidence field.
- Every external R Ref whose content is excluded is unchecked at that Ref field.
- Only selected AgentBinding/ToolBinding records receive a State with detail
  exactly not-provided, incompatible, unknown or declared-supported: state is
  absent, declared, unknown or unchecked respectively. Blocked assessments receive
  unchecked with detail exactly blocked. These assessment details, like old
  missing-claim ids, are comparison keys; other detail prose remains ignored.

The configurations remain in the source tree. Engine/Application/Implementation parameters are opaque JSON, including those
of a selected Implementation. R interprets observed
Tool/Instructions/Skill payload fields listed above; no opaque slice covers their
whole record after interpretation. Their free text fields and parameter JSON
remain maximal opaque values at their own pointers. All unselected definition
payloads retain inherited slices. External payloads have no invented slices.
G does not interpret any R payload solely because runtime names it.

## Schemas, alternatives and compatibility

[The modular schemas](../experimental/modular-candidate-1/schemas/README.md)
derive only shapes. They reuse stable candidate-2 types by file references and
supply replacement D/G/R and payload entry points. They do not establish identity
uniqueness, prerequisite closure, timing, capability truth or verdicts.

Migration is explicit: choose a marker; wrap each old Interface operation in
operations and give it an explicit id/direction; add invoke.operation and
approval.call; replace old runtime with configurations and per-Agent assignments.
No id, direction, actor or selection is inferred by a migration tool under this
proposal. D semantics remain bounded and retain the Principal limitation above.
Mixed markers fail shape in the validating edition; opaque exact exchange can
still preserve other-edition bytes without relabelling them.

Configuration content is untrusted input. A reader never executes adapter
parameters, retrieves evidence or authenticates a Principal from these fields.
Tool availability and supported claims grant no authority. The execution system
must enforce the configuration pin and decision scope; static validation cannot
prove that it did so. Credential references remain distinct from identities and
permissions under 0002; no credential acquisition protocol is added here.

Rejected alternatives for this candidate: one global engine prevents per-Agent
assignments; changing the graph for every engine conflates behavior and binding;
a generic inheritance/merge system adds conflict rules without a current need;
parallel approval/quorum or hot reload requires additional occurrence/state
semantics. A universal compatibility checker cannot derive implementation support
from opaque declarations. These are scope limits, not future feature promises.

Open before adoption: whether configuration may rebind the accountable Principal
definition; any broader protocol, runtime enforcement or execution-conformance
contract. Lot B must derive reviewed examples/oracles from this exact edition,
then readers can implement it independently. This lot adds no executed corpus,
engine proof, release, compatibility certification or adopted spec text.
