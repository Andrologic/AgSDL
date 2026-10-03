# Proposal 0017: agents without Principal identities

Status: **EXPERIMENTAL PROPOSAL, not normative, not adopted, not published.**
Candidate edition: `agsdl-exp-0017-c1`. This is not an AgSDL 0.2 release.
The maintainer authorized removing Principal from the experiment, including
Agent principal references and approval recipient lists. See
[Decision 0009](../docs/decisions/0009-agent-only-experiment.md).
The published contract remains `agsdl-0.1.0` in release 0.1.1.

## Problem, scope and consequences

A second actor catalog is unnecessary to describe an Agent, its content and
its calls. Users, accounts, responsibility assignments, authentication and the
choice of human decision-makers belong to the consuming application. They are
not additional Agent Definitions. This candidate removes `principals`,
`Agent.principal` and `approval.approvers` without replacement fields.

Approval steps still declare a decision before a named call, with the same
ordered chain, data availability, deadlines and refusal paths. Scope and effects
remain explicit under their existing triggers. The renamed SCOPE rule checks
that scope alone; it does not require an actor. No new permission is inferred.

This file is the complete rule source for the new candidate, derived from
[0016 c2](0016-kiss-experiment-0.2.md). That earlier proposal remains unchanged.
Alternatives considered were keeping optional Principals or representing people
as Agents. Both retain an actor model that the maintainer chose to remove.
The remaining language, report boundaries and static-only operation are retained.
Any further simplification is outside this change and requires its own decision.

Existing actor assignments cannot be silently converted or claimed preserved.
Moving a c2 document to this edition requires an explicit authoring choice and
retention of any needed identity/recipient information in the consuming system.
The new marker prevents a c2 artifact from being accepted as this edition.
Changes after a reader baseline is frozen require another candidate marker and
review. Historical c2 evidence does not establish agreement on this candidate.

## Purpose and boundary

Test a descriptive Agent, named or embedded Instructions/Interface, a two-Agent
sequence, two explicit engine configurations, incompatible Tool declarations,
a governed invocation with sequential human approvals, and required unknown
external semantics. Only one operation, `validate`, is specified. It consumes
one byte artifact and returns a compact static report. It never executes,
fetches, transforms, preserves an output document or loads external code.

Retained from 0014: explicit call ports, named Agents and graphs, complete
configurations, Tool contract versus implementation, open engines, and visible
incompatibility. Replaced for this experiment: per-definition versions, the
standard-module version list, the Principal model, and reference-only Instructions/Interface. Complete settings remain separate
from engine-native parameters, but shared binding/settings catalogs are omitted.

Retained from 0015: exact input identity, scoped outcomes, gaps with causes,
independent observations and unordered report comparison. This experiment does
not claim the whole proposal: no imports, resource-interruption result, optional
inspection output, exchange, or field-level checks for complex Skill closures.
The bounded dependency rules below, including whole-record gates explicitly
listed in the rule table, control this candidate.

Skills, imports, packages, assemblies, conditions, parallelism, dynamic delegation,
macros, runtime APIs, hot reload, automatic migration, editors and product
integrations are excluded from this experiment, not from the future 0.2 scope.
No second authoring language or generated interchange representation exists.

## 1. Input, notation and identity

The host request is `validate(primaryBytes)`. Its only argument is the complete
artifact as bytes. Host misuse or a resource failure that prevents completion
is an API error with no report; partial reports cannot claim this operation.
A completed operation returns the Report in section 7 regardless of findings.
There is no specified CLI exit protocol in this contract.

Accept precisely one UTF-8 JSON value, with no BOM, duplicate decoded object
member names, invalid Unicode scalar values, trailing non-whitespace bytes,
NaN or Infinity. Reject unpaired surrogate escapes. Standard JSON number syntax
applies; opaque JSON numbers need not fit IEEE-754. Interpreted integers are
checked mathematically, not after rounding. JSON whitespace is space, tab, LF
and CR. String equality uses decoded scalar sequences with no normalization.
Object order never affects meaning. Arrays have order only where stated.

In all tables, records are closed, fields required unless suffixed `?`, and
arrays may be empty unless `+` follows the type. `text` is a nonempty Unicode
string; `id` matches `[A-Za-z][A-Za-z0-9_-]*` in full. `uint` is an integer in
0..9007199254740991; `positive` is an integer in 1..9007199254740991.
`JSON` is any JSON value. `map<T>` is an object with id keys and T values.
An invalid map key gets a shape finding at its value and that entry is not a
readable identity. `Ports` is map of `string`, `boolean` or `json`; all ports
are required. Exact type equality applies, with no coercion or selectors.

| Type | Fields |
| --- | --- |
| Edition | `identity:text`, `version:text` |
| Ref | `ref:id` |
| InstructionsChoice | exactly Ref, or exactly `value:Instructions` |
| InterfaceChoice | exactly Ref, or exactly `value:Interface` |
| Binding | exactly `input:id`, or exactly `step:id`, `port:id` |
| Claim | `capability:Edition`, `status:"supported" or "unsupported" or "unknown"`, `evidence:Hash or null` |
| Hash | string of 64 lowercase hexadecimal digits |

Edition identities and versions are exact opaque strings. They are open, not an
allowlist, compatibility range or code location. The candidate does not assign
special trust to any engine, adapter, format or capability name.

The SHA-256 of primaryBytes identifies the exact artifact. It is calculated
outside those bytes and appears only in the report or external execution pin.
A named Definition identity is exactly `(artifact SHA-256, local id)`. Definitions
are entries of instructions, interfaces, agents, tools and graphs.
Their ids are unique across all five maps. There is no Definition version, owner
field, external reference, import, canonicalization or hash embedded in a document.
The whole artifact owns its Definitions. Empty/absent catalogs contribute no ids.
An embedded value has an address at its containing JSON Pointer, not an anonymous
Definition identity. Configurations and Agent instruction slots are separately
scoped ids, not Definitions.

Reformatting or changing only a configuration changes the artifact identity and
therefore every exact Definition identity. A conceptually unchanged Agent can
still have unchanged declaration bytes; that is not exact identity across
artifacts. A prospective execution is pinned by artifact hash plus configuration
id. A graph step id identifies a static call site, never an execution occurrence.
Authentication, execution ids, state and timestamps are external. Stop, edit and
start a new execution after an artifact/configuration selection changes. Old
approvals cannot be reused; there is no hot modification or resumption contract.

## 2. Closed document grammar

| Record | Fields |
| --- | --- |
| Document | `edition:"agsdl-exp-0017-c1"`, `agents:map<Agent>`, `instructions?:map<Instructions>`, `interfaces?:map<Interface>`, `tools?:map<Tool>`, `graphs?:map<Graph>`, `configurations?:map<Configuration>`, `selected?:id`, `extensions?:Extension[]`, `annotations?:JSON` |
| Instructions | `target:"Agent"`, `at:"before-invoke"`, `format:Edition`, `body:text` |
| Interface | `operations:map<Operation>` nonempty |
| Operation | `direction:"inbound" or "outbound" or "bidirectional"`, `mode:"request-response"`, `inputs:Ports`, `outputs:Ports`, `effects:"none" or "external" or "unknown"` |
| InstructionSlot | `id:id`, `content:InstructionsChoice` |
| Agent | `instructions:InstructionSlot[]+`, `interface:InterfaceChoice`, `tools?:Ref[]` |
| Tool | `inputs:Ports`, `outputs:Ports`, `effects:"none" or "external" or "unknown"`, `failures:text[]`, `requires:Edition[]` |
| Extension | `edition:Edition`, `use:"required" or "annotation"`, `payload:JSON` |

There is one edition for all standard fields; no second standard-module list,
version or enable flag. Presence implies all the corresponding checks. Absent
optional fields remain absent, without synthesized defaults or hidden records.
Empty agents is legal but does not describe an Agent. Every supplied Instructions,
Interface and Tool is shape-checked even if unused. Unknown members outside
annotations, parameters, settings.value and extension payloads fail shape.

An Agent has one Interface choice and an ordered array of named instruction slots. An embedded
Interface has exactly the same shape and semantics as a named Interface. Every
invoke names an operation id in the selected Agent Interface's operations map,
including embedded Interfaces. There is no operation selected by order or by
being the only one. Multiple Interfaces per Agent are outside this experiment.

Each instruction slot has a unique id within its Agent and holds one whole
Instructions value or one reference to one named Instructions Definition. A
mixture, override, inherited body or merge is invalid shape. Array order on the
Agent is the requested behavioral content order. A binding's Applications must
name every slot once in exactly that order; changing engines cannot reorder it.
This uses one ordered slot declaration, not a second ordering list or alphabetic
rule. Two slots may reference identical Instructions and both are applied. No
deduplication, implicit prompt channel or runtime priority is inferred. The
Application.slot id addresses the Agent's slot in either content form.

Every Ref has a single expected kind fixed by its field: instruction choice →
Instructions, interface choice → Interface,
Agent tools / ToolBinding.tool → Tool, invoke.agent / AgentBinding.agent → Agent,
Configuration.graph → Graph. Missing, wrong-kind and ambiguous targets have
specified findings below; no first/last winner or search elsewhere exists.

Extensions introduce no interpreters in this edition. `annotation` explicitly
makes the entire payload nonsemantic. Every well-shaped required extension is
reported unsupported, independent of its spelling. Duplicate extension Editions
fail uniqueness, even if their payloads agree. No unknown semantic member is
accepted merely by wrapping some other value in an annotation.

## 3. Graphs and governed invocations

| Record | Fields |
| --- | --- |
| Graph | `entry:id`, `inputs:Ports`, `outputs:Ports`, `steps:Step[]+` |
| invoke Step | `id:id`, `kind:"invoke"`, `agent:Ref`, `operation:id`, `bindings:map<Binding>`, `success:id`, `failure:id`, `scope?:Scope` |
| approval Step | `id:id`, `kind:"approval"`, `call:id`, `validForMs:positive`, `timeoutMs:positive`, `approved:id`, `denied:id`, `failure:id` |
| success end Step | `id:id`, `kind:"end"`, `outcome:"success"`, `bindings:map<Binding>` |
| other end Step | `id:id`, `kind:"end"`, `outcome:"failure" or "denied"`, `reason:text` |
| Scope | `action:text`, `resources:text[]+`, `context:Binding` |

Action and Resource scopes are literal authored descriptions here, not a new
Definition catalog or executable permission language. Resource strings have no duplicates. Scope never grants permission.

Step ids are unique within each graph. Entry and all successors identify a
single step. Each graph is acyclic, every step is reachable from entry and every
maximal path ends at an end step. Only invokes produce values, and only on their
success edges. Invocation of an outbound operation is invalid. A success returns
all operation outputs; unusable/missing outputs mean failure with no partial
outputs. These are declared meanings, not execution evidence.

Invoke binding names equal the selected operation's input names. Success-end
binding names equal graph output names. Binding types equal the required types.
A graph input binding selects that input; a step binding selects an invoke and
one selected-operation output. For each step binding, removing the producer's
success edge must make its consumer unreachable from entry. Successor labels
are separate edges even when targets coincide. Context bindings have type json.
There are no branch expressions or conditions in this candidate.

An invoke is governed if any of these observable triggers holds:

- its selected operation has effects external or unknown;
- any Tool declared by its Agent has effects external or unknown;
- it has a scope;
- any approval step names it as call.

A governed invoke requires explicit scope. There is no requirement for every
governed invoke to have a gate: declaring an effect is not declaring that human
approval is required. Every approval names an invoke. The consuming application
chooses who receives the request and which human decision to accept. Recipient
identity, account selection and authorization are not represented in this edition.

Gates for one call form one finite ordered chain. Following approved edges must
reach that call, through only other approvals for that same call. The invoke has
only the final gate's approved incoming edge; every gate except the first has
only its predecessor's approved incoming edge. The first gate can be entry or
have ordinary incoming edges. No denied/failure edge from any gate may reach its
call or a later gate. Entry cannot bypass the chain by starting at the invoke or
an internal gate. This excludes alternate paths, parallel approval and quorum.
All call inputs and scope context must already be available at every gate, using
the producer-success rule with the gate as consumer. Gates produce no ports.

Each gate presents the call's Agent, selected operation,
action/resources, input values, context and the prospective configuration pin.
Its decision deadline is entry time plus min(timeoutMs, validForMs). Equality
with a deadline is expired. Denial selects denied; no response, invalid decision
or expiry of any needed earlier approval selects failure. If expiry is detected
at call admission, take that invoke's failure edge without invoking it. All
earlier approvals remain valid through admission and apply only to this call in
this execution. Static checks verify references and chain/data structure, not
authentication, permission, timing or runtime enforcement.

## 4. Configurations and declared compatibility

| Record | Fields |
| --- | --- |
| Configuration | `graph:Ref`, `agents:AgentBinding[]` |
| AgentBinding | `agent:Ref`, `engine:Edition or null`, `parameters:JSON`, `requires:Edition[]`, `claims:Claim[]`, `applications:Application[]`, `tools:ToolBinding[]`, `settings?:Settings` |
| Settings | `format:Edition`, `value:JSON` |
| Application | `slot:id`, `adapter:Edition`, `parameters:JSON` |
| ToolBinding | `tool:Ref`, `implementation:Edition or null`, `parameters:JSON`, `claims:Claim[]` |

Each Configuration graph resolves to one Graph. There is exactly one binding
for each distinct Agent invoked by that graph, and none for unused Agents.
Repeated calls of the same Agent share its binding. Different engine choices
within one configuration require different Agent Definitions. Different
configurations can select different engines for the same unchanged Agent
record. They never change its direction.

Each binding's Applications name every instruction slot exactly once and in the
order declared by the Agent. Each required Agent Tool has exactly one ToolBinding, with
no undeclared substitution. `requires`, Agent.tools, Tool.requires and Tool.failures
have no duplicates. Claims have unique capability Editions per claim array.
The candidate offers one explicit implementation per ToolBinding, not ordered
fallback alternatives. A null engine or implementation means not provided.
Missing required grammar fields are shape errors, not null selections.

Document.selected, if supplied, names one Configuration. Missing selected means
no selection, even for a single configuration. All configurations receive
structural checks; only the selected one receives declared compatibility checks.
No default engine, inheritance, merge, per-call override or automatic fallback
exists. Parameters are engine/adapter-specific opaque JSON. Settings are a whole
value with an explicit independent format contract, not a native-option overlay.
Reuse of a settings format does not prove engines implement it equivalently.

Engine requirements for a selected binding are the union of binding.requires,
the format Edition of every instruction slot, every Application.adapter, and
settings.format when present. Tool requirements are its Tool.requires. Requiring
an Edition does not fetch or verify anything. There is no capability inference
from an engine name. For each required Edition assess:

1. Null engine/implementation: inconclusive, not provided.
2. Otherwise an exact unsupported claim: fail, declared incompatibility.
3. Otherwise missing claim, unknown status, or supported with null evidence:
   inconclusive, support unknown.
4. Otherwise supported with a non-null hash: no finding, declared support only.

An empty requirement set that is completely known, with a supplied readable
engine/implementation, performs no claim lookup and produces no finding from
claim assessment. Malformed claims still receive configuration SHAPE/UNIQUE
observations. An incomplete or unreadable requirement set retains its gap;
readable subsets are still assessed. Independent coverage and effects checks
remain applicable. Tool effects unknown additionally produce inconclusive.
Evidence hashes identify assertions, not verified evidence. Missing Applications
or ToolBindings are structural defects; they do not erase observable intrinsic
requirements. Known incompatibilities survive independent unknowns or gaps.
A compatibility fail never asserts that the structural document is invalid.
No configuration or Tool/content is removed, changed or substituted by validation.

## 5. Deterministic checking and dependencies

The operation emits exactly six results: syntax, core, flow, configuration,
compatibility and external. No aggregate whole-document verdict is supplied.
Scopes and rule inventories are fixed below; results cannot select fewer rules.
Rule codes double as diagnostic and gap check codes. All locations are JSON
Pointers from the input root, with `~0`/`~1` escaping. Empty string locates root.
A missing mandatory field locates its existing parent; other bad fields locate
the field. A source catalog entry is located at its value, not a fabricated id
member. Parsed source array indices remain significant.

### Shape and readable facts

SHAPE recursively checks all closed records and primitive domains owned by its
unit. It emits one fail per bad field, coalescing missing members at their parent.
Wrong-type containers produce a single finding there, with no descent. Independent
siblings are still checked. Missing/malformed/unknown Step.kind produces one
SHAPE at the step, checks only common id, and does not infer a variant or report
variant fields as extra. End.outcome is a second discriminator with the same
rule, retaining id/kind checks. Choice objects must contain exactly one of ref
and value; otherwise emit SHAPE at the choice and inspect neither branch.
Binding branch selection uses member presence: exactly one of input and step
selects its branch, even when that member's value is malformed. Both or neither
(including an empty object or port-only object) emits one SHAPE at the Binding,
with no descent. In a selected branch, ordinary closed-record checking applies: a
missing port locates the Binding, a malformed input/step/port locates that field,
and extra members locate themselves. Any such defect blocks that Binding's DATA
clause with cause shape, without blocking readable sibling Bindings.
Malformed Ref emits SHAPE at its bad ref field or at the object for missing ref.
No extra-key failure suppresses an otherwise readable field.

A readable fact means the particular required field/subtree has its specified
type and domain. Whole-record shape is a dependency only where explicitly named.
An optional absent catalog is a known empty catalog; a malformed catalog is not.
A named Definition lookup requires a readable Ref and the five catalog containers
and their keys. Values need not be well-shaped to establish ids. If a container
or key is malformed, absence of an unseen id cannot be established; a uniquely
observed id can still resolve if no other unreadable catalog/key could duplicate
it, so in this candidate all lookups are blocked until the identity catalog is
complete. Duplicate ids block only lookups of those ids. Wrong kind is a known
reference failure. A resolved target with a malformed required field blocks only
checks needing that field; its own SHAPE finding remains at source.

Each rule below has dynamic check subjects. Missing/wrong prerequisite data
produces a gap at that subject instead of inventing a semantic failure. A known
missing/wrong-kind reference produces REF fail at the reference and blocks its
consumers. Ambiguity produces REF gap, not a second missing-target failure.
For a rule with several independent clauses, evaluate readable clauses, coalesce
findings, and also emit a gap if another clause cannot run. A fail and a gap can
coexist for one code/location. There is no whole-core-pass prerequisite that
suppresses valid independent observations elsewhere.

If an owner collection is absent, it has no subjects. If malformed, emit one
gap for each affected rule at that collection, without invented child subjects.
If a required owner field is missing, use its parent. Readable sibling entries
remain separate subjects. Nested semantic rules use the subject specified in
the table, never every missing primitive separately. When syntax fails, no tree
exists: emit SYNTAX fail at root, then one CHECKS gap at root in every other
result, without any other checks. If the edition field is missing or not the
candidate literal, core emits SHAPE there or at root; every non-core/non-syntax
unit emits only CHECKS gap at root. Core still shape-checks the candidate grammar
and catalogs for diagnostic purposes, without accepting the foreign edition.

### Rule inventory

A gap's cause is `shape` for unavailable/malformed fields, `reference` for failed
or ambiguous lookups, `path` for failed graph path prerequisites, or `unsupported`
for required external interpretation. Unknown compatibility is a diagnostic,
not a blocked check. Multiple causes for a code/location are a unique unordered
array, not multiple gap records. Rules not enumerated here do not exist.

| Unit / code | Subjects, dependencies, failure location and meaning |
| --- | --- |
| syntax / SYNTAX | Entire input. Any lexical/encoding/duplicate-member error emits one fail at root. No byte offset is required in this smaller experiment. |
| core / SHAPE | Root fields other than graphs/configurations/selected/extensions; envelope field names and edition; all instruction/interface/Agent/Tool contents. Extra root fields belong here. |
| core / ID | Each entry in the five Definition maps. Catalog keys suffice; every entry whose id occurs more than once gets fail at that entry. Graph content shape is not required. Malformed catalog/key prevents the complete duplicate check: gap at each malformed catalog or entry. Observed duplicates still fail. |
| core / REF | Each Ref within core-owned records. Depends on identity catalog and readable ref. Missing/wrong-kind target fails at Ref object; ambiguous target or incomplete catalog gives gap there. |
| core / SLOT-ID | Each Agent.instructions array. Readable slot ids suffice: duplicates fail once at array. Missing/malformed slot id adds a shape gap at array without hiding observed duplicates. |
| core / UNIQUE | Each Agent.tools array, Tool.requires and Tool.failures array. Readable array and complete element shapes required. Duplicate exact Ref/Edition/string fails once at array. |
| flow / SHAPE | All graph contents, including scope and approval records. |
| flow / REF | Each invoke.agent Ref; ordinary REF rules and locations. |
| flow / OPERATION | Each invoke step. Depends on agent resolution, Agent.interface choice and its resolution/value, operations map keys and operation id. Absent operation or outbound direction fails at invoke; malformed direction blocks its direction clause. Malformed unselected operation does not block selection of another. |
| flow / STEP-ID | Each steps array; readable step objects and ids. Duplicate id fails once at array. A malformed id/object adds gap at array while observed duplicates still fail. |
| flow / PATH | Each Graph at its entry in graphs. Depends on readable entry, unique complete step ids, known kinds/outcomes and all successor ids. Absent successor/entry, cycle, unreachable step or unterminated maximal path fails once at Graph. Wrong-shape projection or duplicate ids gives gap at Graph. Port, binding and Agent validity do not gate PATH. |
| flow / DATA | Each invoke or success-end step. Depends on its bindings map, readable target port map, readable graph inputs, producer step lookup and producer operation output maps. Check exact binding-name set; each readable binding selects a known input or invoke output of equal type. Missing input/producer/port, wrong producer kind/type, or name mismatch fails once at consumer. Malformed binding/port or failed producer operation blocks the affected clauses. Availability clause also requires PATH success; violation fails at consumer, unavailable PATH gives gap with cause path. Scope.context is checked here as another binding with required type json. |
| flow / SCOPE | Each invoke. Governing trigger is the disjunction defined in section 3. Resolve operation effects, Agent Tool effects and readable approval.call links; scope presence is observable even if malformed. If any trigger is true, require scope presence, failing at invoke if absent. Present malformed scope gives gap. If no trigger is true but a trigger is unreadable, give gap, never infer ungoverned. Known triggers enforce scope requirements despite another unreadable trigger; that unreadable trigger adds no SCOPE gap once scope is fully checkable. No actor lookup exists. |
| flow / APPROVAL | Each approval step. Readable call id and complete unique step catalog needed to check it names an invoke; absent/wrong-kind call completes this rule with fail at gate and has no chain subject or extra APPROVAL gap; ambiguous gives gap. Whole readable gate fields and PATH success are required for chain and timing-declaration clauses. Violations of the chain rules fail at each gate of the affected call; unavailable PATH gives gap at each gate. No comparison between timeout and validity is required. |
| flow / APPROVAL-DATA | Every approval step; call lookup is a prerequisite, not subject discovery. Missing/wrong-kind/ambiguous call gives a reference gap at gate; malformed call gives shape gap. Check the call's bindings and scope.context as DATA would, using the gate as availability consumer and diagnosing at the gate. Depends on DATA's field prerequisites and PATH. Missing scope required by governance yields gap reference to unavailable call scope, cause shape; SCOPE owns the failure. |
| flow / UNIQUE | Each supplied scope.resources array. Fully shaped array required; duplicates fail at array. |
| configuration / SHAPE | configurations contents and selected when present. |
| configuration / REF | Each Configuration.graph, AgentBinding.agent and ToolBinding.tool. Ordinary REF rules. |
| configuration / SELECTION | selected when present. Readable id and configurations keys needed; absent named configuration fails at /selected, malformed/missing configurations gives gap there. Missing configurations counts as known empty for a present selected and therefore fails. |
| configuration / ASSIGN | Each Configuration at its entry. Depends on resolved graph and its steps' known kinds plus readable invoke Agent refs; binding array and every binding.agent Ref must be readable. Compare exact distinct Agent ref sets and exactly one binding per Agent. Missing, extra or duplicate binding fails at Configuration. Graph PATH is not a dependency. Malformed projection gives gap; no missing Agent inferred. |
| configuration / CONTENT | Each AgentBinding. Requires unique binding Agent within its Configuration, resolved Agent instruction slot ids and Applications array with readable slot ids. Agent slot ids must be complete and unique. Application slot sequence must equal the Agent slot sequence, not merely its set. Missing/extra/duplicate/reordered slots fail at binding; malformed enumeration gives gap. Application adapters/parameters do not gate slot enumeration. |
| configuration / TOOLS | Each AgentBinding. Requires unique binding Agent, resolved Agent.tools and complete ToolBinding.tool refs. Missing/extra/duplicate Tool binding fails at binding; malformed enumeration gives gap. Absent Agent.tools means known empty. |
| configuration / UNIQUE | Every binding.requires and every engine/Tool claims array. Fully shaped array required; duplicate Editions or Claim.capability Editions fail once at array. |
| compatibility / ENGINE | Each AgentBinding in selected configuration. Requires selected lookup, unique binding Agent, resolved Agent; check requirements and engine/claims using section 4. Each readable requirement subset is assessed independently. Malformed requires, settings format, Application adapter or slot format adds gap at binding, without hiding other known requirements. Missing Application does not hide instruction format requirements. Slot format recognition does not depend on target/at/body shape. Duplicate Claim.capability blocks only that capability; an incomplete capability-identity index blocks all claim lookup, as defined below. Fail/inconclusive coalesce at binding. |
| compatibility / TOOL | Each ToolBinding in selected configuration. Requires unique parent binding Agent and unique Tool binding in that parent, resolved Tool. Assess readable Tool.requires against implementation/claims using section 4. Duplicate claims block only their capability; an incomplete capability-identity index blocks lookup. Unknown Tool.effects contributes inconclusive; malformed effects contributes gap. Diagnostics/gaps at ToolBinding. |
| external / SHAPE | extensions array and entries. Payloads opaque. |
| external / UNIQUE | extensions array. Readable entries' Edition fields suffice; duplicates fail at array; unreadable identities add gap at array without hiding observed duplicates. |
| external / REQUIRED | Each extension with readable use and Edition. Required emits unsupported at extension and gap there with cause unsupported; annotation emits nothing. Malformed use/Edition gives gap. Payload shape has no extra constraints. |

Named Interface/Instructions targets similarly receive shape errors at their
source. Wrong/missing selected operation prevents downstream port/effect checks,
with gap cause reference. Duplicate step ids block that id's lookup and PATH,
while unrelated known-id lookup remains possible when all step ids are readable.
ASSIGN enumerates the steps array using known kinds and readable invoke Agent
refs; it does not look up steps by id. A missing or duplicate step id alone adds
no ASSIGN gap. STEP-ID and PATH retain their own findings or gaps. An unreadable
kind or invoke Agent ref still blocks ASSIGN's projection. Duplicate AgentBinding.agent blocks
CONTENT/TOOLS/ENGINE and child TOOL for those bindings only, not sibling Agents.

For ENGINE/TOOL, unreadable engine/implementation field blocks assessment (shape).
Null selection produces inconclusive regardless of claims, without claiming an
incompatibility that would require a supplied choice. With a supplied choice,
unknown or missing claim emits inconclusive even when another requirement fails.
If all requirements cannot be enumerated, inspect the readable subsets but add
a gap. Unreadable or structurally incomplete Application/Tool coverage produces the
explicit compatibility gaps below; a pass never silently drops that coverage.
A malformed optional selected yields one compatibility CHECKS gap at /selected;
a known missing selection target does too with cause reference. If no configuration
is selected, compatibility is absent: no ENGINE/TOOL subjects or gaps.


### Subject discovery, local identity projections and omissions

These rules make the table's prerequisites precise; they add no new syntax.
Subjects are discovered before testing their prerequisites. Semantic REF checks
exist for each declared Ref field; a missing required Ref creates a gap at its
parent with cause shape. An optional absent Ref has no subject. SHAPE owns the
missing-field finding. For a malformed containing record or owner collection,
use the nearest existing malformed value and one gap per affected code there;
never invent child subjects below it. Once the whole-unit CHECKS gate applies,
this discovery stops for that unit.

For flow, a nonobject step or unknown/missing/malformed kind creates gaps at that
step for REF, OPERATION, DATA, SCOPE, APPROVAL, APPROVAL-DATA and UNIQUE, all cause
shape. This states unknown applicability without inventing a variant. SHAPE and
STEP-ID/PATH still follow their own rules. For a known end with unreadable
outcome, only DATA needs that local applicability gap; no invoke/approval rule
is invented. A known failure/denied end has no DATA subject. For a known invoke,
missing/malformed bindings does not remove the DATA subject; for a known gate,
failed call lookup does not remove APPROVAL-DATA. Optional scope absent has no
resource-UNIQUE subject. A present malformed scope gives a UNIQUE shape gap at
scope if resources cannot be inspected. A known invoke has no APPROVAL subject;
a known gate has no OPERATION or SCOPE subject. A malformed graph/steps container
collapses REF, STEP-ID, PATH, OPERATION, DATA, SCOPE, APPROVAL, APPROVAL-DATA and
UNIQUE gaps to that malformed value; a missing steps field uses the Graph.

AgentBinding identity projection reads only binding.agent.ref. ToolBinding
identity projection reads only binding.tool.ref. For local evaluation, only an
observed duplicate of the same readable identity blocks that binding. A sibling
with an unreadable identity does not block a readable sibling's CONTENT, TOOLS,
ENGINE or TOOL. Exact collection coverage (ASSIGN or TOOLS) remains blocked when
its identity enumeration is incomplete. An unreadable AgentBinding identity
produces CONTENT and TOOLS shape gaps at that binding, and ENGINE plus parent TOOL shape gaps there
when selected. Its existing child ToolBindings each receive TOOL shape gaps;
an empty tools array has no children. A malformed tools container instead gets
one TOOL shape gap at that container. Observed duplicate parent identities give
those same dependent gaps with cause reference, without blocking sibling Agents.
A ToolBinding with unreadable/duplicate own identity receives TOOL gap at itself
with cause shape/reference, respectively. Definition lookup still uses the
complete global catalog rule above; these are different identity projections.

Claims have a capability-identity index separate from their value checks. The
index, when a claim lookup is needed, requires an array of objects with fully readable capability Editions;
it does not require status or evidence. If an element cannot supply its capability,
all claim lookups for that binding are blocked with cause shape. If identities
are complete, duplicate capability Editions block only that capability with
cause reference. For a unique matching capability, malformed/missing status
blocks only its assessment (shape). A supported status additionally needs readable
evidence; malformed/missing evidence blocks that assessment (shape), null means
inconclusive. Unsupported and unknown statuses do not depend on evidence, though
configuration SHAPE still checks it. An invalid status/evidence on another
capability cannot suppress an observable incompatibility. A capability not required
is not assessed. UNIQUE retains its separate whole-array shape prerequisite.

For selected bindings, ENGINE also checks Application coverage using CONTENT's
projection. A readable missing/extra/duplicate/reordered Application sequence
contributes an ENGINE gap at the AgentBinding with cause reference; an unreadable
sequence contributes cause shape. Duplicate Agent slot ids contribute reference;
unreadable Agent slot ids contribute shape. Still assess every observable
intrinsic instruction format and declared adapter. Missing Applications supply
no invented adapter requirement. A null engine contributes inconclusive and does
not erase these coverage gaps.

TOOL has a parent coverage subject at every selected AgentBinding, in addition
to each ToolBinding assessment. Its parent projection is the same as TOOLS.
A readable missing/extra/duplicate Tool binding gives TOOL gap at AgentBinding,
cause reference; unreadable enumeration gives cause shape. This parent subject
emits gaps only, never compatibility diagnostics. It does not depend on engine
Application order or engine claims. Absent Agent.tools and an empty ToolBindings
array is complete empty coverage. A missing ToolBinding has no invented child
subject, implementation or claim; the parent gap prevents a complete compatibility
pass. A present ToolBinding with null implementation is a child TOOL inconclusive,
not a coverage omission. Known child incompatibilities remain observable beside
parent gaps. Unreadable parent Agent identity blocks this parent coverage with
cause shape; observed duplicate parent identity uses reference.

A duplicate application slot or reordering does not change the declared requirement
union; it causes the specified coverage gap. Tool/Agent reference resolution
failures add reference gaps at their consuming table subjects. Multiple independent
causes at one subject are unioned. Do not add downstream causes merely because
one necessary prerequisite is already blocked: unavailable PATH contributes path,
failed lookups contribute reference, malformed facts contribute shape, exactly
for the clauses described above.

### Adversarial witnesses with exact observations

These witnesses modify the named example only for explanation. They are rules
of this candidate, not implementation-derived expectations. D means Diagnostic,
G means Gap; tuples omit unchanged empty result arrays. Every unlisted diagnostic
or gap array is empty unless the row expressly scopes its observation to one
subject. Presence and outcomes follow sections 6 and 7.

| Mutation | Exact diagnostics and gaps |
| --- | --- |
| In two-agent-sequence, replace step 1 bindings.text by an object containing input, step and port. | D(flow,SHAPE,/graphs/pipeline/steps/1/bindings/text,fail); G(flow,DATA,/graphs/pipeline/steps/1,{shape}). |
| In two-configurations, delete agents/0/agent of primary; set reviewer's plain-text claim to unsupported. | D(configuration,SHAPE,/configurations/primary/agents/0,fail); G(configuration,REF,/configurations/primary/agents/0,{shape}); G(configuration,ASSIGN,/configurations/primary,{shape}); G(configuration,CONTENT,/configurations/primary/agents/0,{shape}); G(configuration,TOOLS,/configurations/primary/agents/0,{shape}); G(compatibility,ENGINE,/configurations/primary/agents/0,{shape}); G(compatibility,TOOL,/configurations/primary/agents/0,{shape}); D(compatibility,ENGINE,/configurations/primary/agents/1,fail). No child TOOL subject exists in the empty tools array. |
| In two-configurations, writer claim 0 becomes unsupported and claim 1 status becomes 17. | D(configuration,SHAPE,/configurations/primary/agents/0/claims/1/status,fail); G(configuration,UNIQUE,/configurations/primary/agents/0/claims,{shape}); D(compatibility,ENGINE,/configurations/primary/agents/0,fail); G(compatibility,ENGINE,/configurations/primary/agents/0,{shape}). |
| In two-configurations, writer applications becomes empty. | D(configuration,CONTENT,/configurations/primary/agents/0,fail); G(compatibility,ENGINE,/configurations/primary/agents/0,{reference}). Intrinsic format requirements are still assessed and declared supported here. |
| In tool-incompatible, selected writer tools becomes empty. | D(configuration,TOOLS,/configurations/primary/agents/0,fail); G(compatibility,TOOL,/configurations/primary/agents/0,{reference}). No child TOOL fail survives, because no implementation is selected there; the required Tool remains in Agent.tools. |
| In application-order-conflict, use the supplied reversed Applications. | D(configuration,CONTENT,/configurations/ordered/agents/0,fail); G(compatibility,ENGINE,/configurations/ordered/agents/0,{reference}). The Agent's instruction order is unchanged; no sorting or repair is allowed. |
| In tool-incompatible, set tools.lookup.requires to [] and the selected writer ToolBinding claims to [{}]. | D(configuration,SHAPE,/configurations/primary/agents/0/tools/0/claims/0,fail); G(configuration,UNIQUE,/configurations/primary/agents/0/tools/0/claims,{shape}). Compatibility passes: the complete empty requirement set needs no claim lookup, the implementation is supplied and effects are none. |

The complete [duplicate-step assignment witness](../experimental/kiss-0.2/examples/duplicate-step-assign.json)
is:

```json
{"edition":"agsdl-exp-0017-c1","agents":{},"graphs":{"g":{"entry":"e","inputs":{},"outputs":{},"steps":[{"id":"e","kind":"end","outcome":"failure","reason":"x"},{"id":"e","kind":"end","outcome":"failure","reason":"x"}]}},"configurations":{"c":{"graph":{"ref":"g"},"agents":[]}}}
```

Its exact observations are D(flow,STEP-ID,/graphs/g/steps,fail) and
G(flow,PATH,/graphs/g,{shape}). Configuration passes without an ASSIGN gap:
the known kinds establish an empty invoke Agent set despite duplicate step ids.
All other diagnostic and gap arrays are empty. Syntax and core pass;
compatibility and external are absent/not-applicable. Flow fails.

For a missing kind on sequence step 0, the exact flow observations are:
SHAPE fail at step 0; REF, OPERATION, DATA, SCOPE, APPROVAL, APPROVAL-DATA and
UNIQUE shape gaps at step 0; PATH shape gap at /graphs/pipeline; DATA gap
{reference,path} at step 1 because its producer's kind is unknown; DATA gap
{path} at step 2. STEP-ID can still check all ids. SCOPE at step 1 has a shape
gap because step 0 might be an approval governing it. There are no other findings
or gaps in this witness. The absent configuration/compatibility/external units
remain not-applicable. This does not infer step 0's variant from its other fields.

For a missing approval target (governed-call step 0 call becomes missing), the
exact flow observations are APPROVAL fail and APPROVAL-DATA reference gap at
step 0, plus APPROVAL fail at step 1: step 0 is no longer a gate for send and
its approved edge illegally reaches the internal chain's only gate. To avoid
an arbitrary chain interpretation, the chain rules also require every incoming
approved edge from an approval to a first gate to name that same call; an ordinary
incoming edge excludes an approval's approved edge for another call. All other
findings/gaps are empty. PATH still passes. This closes a mismatched-call chain
without inferring which call was intended.

### Actor removal witnesses

In governed-call, no principals catalog, Agent principal or gate approvers field
is present. Every present unit passes without actor or recipient lookup. Removing
only the call's scope gives D(flow,SCOPE,/graphs/release/steps/2,fail) and
G(flow,APPROVAL-DATA,/graphs/release/steps/0,{shape}) plus the same gap at step 1.

In agent-embedded, adding principals:{} gives only D(core,SHAPE,/principals,fail).
Adding Agent.principal:{ref:"writer"} instead gives only
D(core,SHAPE,/agents/writer/principal,fail). These are extra fields, never catalogs
or references to interpret. In governed-call, adding approvers:[] to gate 0 gives
D(flow,SHAPE,/graphs/release/steps/0/approvers,fail) and shape gaps for APPROVAL
at gates 0 and 1 because the whole gate is required for chain checks. No REF or
actor diagnostic is synthesized from that field.

In governed-call, set gate 0 call to missing and timeoutMs to null. The exact
observations are D(flow,SHAPE,/graphs/release/steps/0/timeoutMs,fail),
D(flow,APPROVAL,/graphs/release/steps/0,fail),
D(flow,APPROVAL,/graphs/release/steps/1,fail), and
G(flow,APPROVAL-DATA,/graphs/release/steps/0,{reference}). A terminal missing-call
failure does not acquire an extra APPROVAL gap from unrelated timing shape.

## 6. Unit boundaries and absence

Each result has fixed scope edition `agsdl-exp-0017-c1`, phase `local`, input
`primary`, and the following unit/subject. Presence concerns its container, not
its validity. A present malformed container is present. If parsing failed or
root is not an object, presence is undetermined except syntax, which is present.
For any parsed nonobject root (null, array, string, number or Boolean), syntax
is present/pass with empty diagnostics and gaps. Core is undetermined/fail with
exactly one SHAPE fail at root and one CHECKS gap at root, causes [shape]. Flow,
configuration, compatibility and external are each undetermined/inconclusive,
with no diagnostics and exactly one CHECKS gap at root, causes [shape]. Their
fixed result subjects remain those in the table below. No child subjects,
individual rule gaps or edition-field findings are discovered for this case.
This explicit whole-unit gate takes precedence over generic subject discovery.

| Unit | Subject | Presence and absence |
| --- | --- | --- |
| syntax | empty pointer | Always present; its pass proves only JSON parsing. |
| core | empty pointer | Present for a parsed object. No whole-model claim. |
| flow | /graphs | Absent iff root object has no graphs. Present empty map passes. |
| configuration | /configurations | Present if configurations or selected exists; absent if both absent. |
| compatibility | /selected | Absent iff selected absent. Present even for an invalid selection. |
| external | /extensions | Absent iff extensions absent. Present empty array passes. |

An absent unit has outcome not-applicable and empty arrays, except a failed
syntax/edition/root prerequisite gives the CHECKS gap described above and an
inconclusive outcome even if absence is observable. Core is not a blanket
prerequisite: independent flow/configuration/external errors remain observable
when core has other defects. A unit's pass means only its fixed checks completed.
Unsupported required external interpretation is reported by external, so a core
pass alongside external unsupported never means the whole document passed.

## 7. Closed report grammar and agreement

| Record | Fields |
| --- | --- |
| Report | `edition:"agsdl-exp-0017-c1"`, `processor:Edition`, `operation:"validate"`, `input:Input`, `results:Result[]` exactly the six units |
| Input | `id:"primary"`, `sha256:Hash` |
| Result | `unit:"syntax" or "core" or "flow" or "configuration" or "compatibility" or "external"`, `phase:"local"`, `subject:text or empty string`, `presence:"present" or "absent" or "undetermined"`, `outcome:Outcome`, `diagnostics:Diagnostic[]`, `incomplete:Gap[]` |
| Outcome | `"pass"`, `"fail"`, `"unsupported"`, `"inconclusive"`, `"not-applicable"` |
| Diagnostic | `code:rule-code`, `location:JSON-Pointer`, `outcome:"fail" or "unsupported" or "inconclusive"`, `message?:text` |
| Gap | `code:rule-code or "CHECKS"`, `location:JSON-Pointer`, `causes:("shape" or "reference" or "path" or "unsupported")[]+` |

Rule codes are exactly those in the table, scoped by unit. Gap CHECKS is used
only for the explicit whole-unit gates, never as shorthand for arbitrary gaps.
No input id or edition is repeated in every Result: the Report supplies both.
No prerequisite result list is needed: this single-input fixed dependency table
specifies all gates; it cannot be reconfigured by the report producer.

For each result aggregate diagnostics in precedence fail, unsupported,
inconclusive. Any gap contributes inconclusive, except unsupported contributes
unsupported. Choose the highest contribution; if none, absent → not-applicable,
otherwise pass. Undetermined presence always has a gap and cannot pass. Preserve
all diagnostics and gaps, including lower-precedence ones. An incompatibility
is a compatibility fail, not a core/flow/configuration fail. No runtime readiness
or full-language validity result exists.

Diagnostics are unique by code/location/outcome. Gaps are unique by code/location,
with their cause sets unioned. Arrays of results, diagnostics, gaps and gap causes
are unordered keyed collections; duplicate keys/cause values invalidate a report.
Compare input hash, operation, edition, all result fields, diagnostic tuples and
gap cause sets exactly. Ignore processor Edition and optional message wording
for semantic agreement. Ordering in source Applications and graph data remains
meaningful. Different source bytes produce different hashes and cannot be
reported as identical inputs even if their semantic observations match.

There is no inventory, successful-check trace, source excerpt, byte-slice table,
output artifact, or exchange promise. A read-only validator need not conserve
unknown information in a second document. Future rewriting or exact-exchange
operations need separate contracts before making preservation claims. Keeping
unknown data and preserving its exact bytes remain different guarantees.

## 8. Examples, comparisons and migration

The [experiment guide](../experimental/kiss-0.2/README.md) identifies exact JSON
examples and their intended observations. They are not 0.1.0 inputs. The examples
exercise both valid and deliberately failing/unsupported declarations. Structural
success is independent of a declared incompatible implementation.

Relative to 0014's sketches, the edition and local ids remove standard-module
version combinations and repeated Definition versions. Removing Principal avoids
a second actor catalog and approval recipient references. Embedding removes a named catalog
entry and a reference for single-use content, but creates two parser branches.
Named/embedded contents still need identical payload checks and Application slot
resolution; naming everything remains valid and easier for shared content.

Relative to 0.1.0, request/response types are declared only on the Interface,
not repeated at every invoke. Instruction slots add local names but avoid
switching Application identity rules between named and embedded values. Each
Agent retains an explicit Interface and behavioral content. A simple graph no
longer declares placeholder Action/Resource/context or a repeated actor declaration.
This is reduced coverage, not lossless compression. Governed calls retain
explicit scope; identity and decision recipients remain application concerns. Configuration bindings, Tool choices and content
Applications still cost declarations; open engines were already supported.
There are no inheritance savings or runtime interoperability claims.

| Migration class | Examples and limits |
| --- | --- |
| Mechanical only after source validation and an explicit candidate target choice | Copy literal Instructions bodies/format/application point and Interface port maps into named records; replace local references by ids when collision-free; remove repeated invoke ports only after checking agreement. The output has a new artifact identity. |
| Human decision required | Role-only/ControlFlow-only direction needs authored Instructions; choose slot ids/order; decide whether existing Action/Resource descriptions fit literal Scope; classify effects; select settings format and explicit adapters. Existing actor/recipient information must be handled explicitly outside this edition; it is not preserved by a converter. |
| Not covered | Imports, exported fragments, Skills, conditions, assemblies, deployment, extensions requiring interpretation, full 0.1.0 reports or byte-preserving conversion. No converter or round-trip guarantee is provided. |

Keeping reference-only values would simplify parsing but would not test the
approved single-use embedding tradeoff. A general module solver or macro system
would add work beyond these cases. Rejecting all checks after one malformed
record would be simpler but conceal independent errors, so the bounded rule
table fixes the necessary dependencies instead.

## Security, proof condition and unresolved future work

All names, descriptions, parameters and messages are untrusted data; no field
is an instruction to the reader to execute code, open paths or retrieve URLs.
An engine name and an evidence hash confer no authority. Approval declarations
neither authenticate people nor enforce permissions. A consumer must not treat
structural pass or declared support as permission to execute.

The candidate needs two separately implemented readers, positive and adversarial
cases, and exact report comparison for this marker. Retain the input and source
hashes with each run. Agreement does not prove execution, authentication or
universal correctness. The current bounded evidence is documented separately in
the [assessment](../experimental/kiss-0.2/ASSESSMENT.md). Further scope and
normative adoption remain separate decisions.
