# Proposal 0012: minimal candidate contract for 0.1.0

- Status: proposed, awaiting maintainer choices; no normative adoption.
- Date: 2026-09-05.
- Experimental completion revision: 2026-09-06.
- Basis: [Decision 0001](../docs/decisions/0001-specification-before-syntax.md),
  [Decision 0004](../docs/decisions/0004-approved-design-directions.md),
  proposals [0002](0002-core-conceptual-model.md),
  [0003](0003-conformance-and-versioning.md) and
  [0011](0011-first-exchange-contract.md).

## Problem and scope

Two independent validators need the same input boundary, identity comparison,
covered checks and findings. Proposal 0011 leaves those implementation choices
open. This proposal recommends a bounded answer and a separately selectable
simple control-flow contract. Every rule and spelling below is a recommendation,
conditional on approval, including examples and diagnostic categories. They are
not published feature identities or an adopted specification. Review the
concepts and choices before adopting representation, as Decision 0001 requires.

The proposed release scope has three separate units, provisionally called D,
G and R in this document. D covers documentary reading, inspection, validation
and exact exchange. G covers static meaning and validation of simple control
flows. R covers runtime requirement and selection declarations. A claim names
its operations and units; D does not imply G, R or execution support. None
establishes whole-model conformance under proposal 0003. There is no universal
runtime, product integration contract or engine default here.

## Concepts and invariants before representation

A document describes one System, Fragment or Package version boundary. Its
local definitions retain that boundary as lifecycle owner. Imported definitions
remain in separately supplied dependency documents with their original owners.
System participation is a use relation, independent of ownership. A System can
use only imported Agents. A Fragment exports definitions without becoming a
System. The Package version root remains an immutable artifact in proposal
0002's categories; the root envelope does not turn it into a definition.

A definition identity names a description. A Principal definition describes an
actor or actor class, and its scoped Principal identities name that actor.
Recommend interpreting `Agent represented by Identity` as the Agent's unique
definition identity, represented once by its key. Require exactly one `actsAs`
reference to a Principal definition. An Agent with one key and a Principal with
two identities therefore meets this identity check. No acting identity,
authentication, authority or runtime instance is inferred.

A declared reference is not evidence that its target exists externally.
A permitted missing relation is not a reference. D retains 0011's single
Interface-minimum deferral for a local Agent in a Fragment, with all declaration
conditions, and no others. System and Package version Agents cannot use it.
Identity, owner, Principal and behavioral-direction presence never defer.
A dangling local reference, wrong kind or contradiction remains a failure.

G describes scheduled invocations, not Agent identities or topology paths.
A transition declares control movement, not permission to perform an effect.
R describes needed capabilities separately from a deployment's chosen engine.
A model, provider, engine interface and hosting environment are different facts.

## Choices for maintainer review

Each row is a material recommendation. The following sections specify its
candidate details. The delegated experiment uses these recommendations; a later
adoption record identifies the resulting scope without inventing prior approvals.

| Choice | Recommendation | Alternative and consequence |
| --- | --- | --- |
| C1: release boundary | D mandatory for the proposed two-validator comparison; G and R separately selected, with separate evidence. | D alone yields a smaller exchange draft; making G mandatory adds graph fixtures and adoption work. |
| C2: identity | Exact scope/id/version tuples and the Agent identity interpretation above. | Separate Identity records add indirection; treating that relation as acting identity reopens 0002's cardinalities and runtime boundary. |
| C3: representation | One strict UTF-8 JSON document per artifact, explicit records and byte-preserving exchange. | YAML or normalized JSON needs additional parser and preservation rules; defer those codecs. |
| C4: references and phases | Offline supplied-artifact resolution only; D keeps 0011's unresolved scope. G can additionally request a bounded resolved-graph phase. | Network resolution needs policy and retrieval contracts; full graph validation requires more of 0002. |
| C5: fragments | Adopt only 0011's explicit Interface deferral inventory. | Reject incomplete fragments for simpler validation, or propose each additional allowance separately; blanket deferral conflicts with Decision 0004. |
| C6: unknowns and loss | Isolated annotations are ignorable by a core rule; semantic extensions need supported operation rules. Exact exchange only in the first release. | Lossy transforms need a separate permission contract and output tests; an author's optional flag is insufficient. |
| C7: findings | Per-operation and per-phase reports; fail, unsupported, inconclusive, then pass precedence. | One verdict hides evidence boundaries; global aggregation would revisit 0003 beyond this scope. |
| C8: simple graph | Finite acyclic, single active step, explicit I/O and outcomes; Boolean conditions and one-action human gates. | Documentary graph inventory alone avoids new semantics; parallelism, loops or general expressions need separate contracts. |
| C9: runtime declarations | Open exact engine identities, optional selection, explicit requirement evidence; no defaults. | Deferring R keeps engine metadata opaque. A vendor enum or inferred default contradicts the recorded user direction. |
| C10: delivery evidence | Two independent validation implementations and scope-labelled evidence, with no required product integration. | Adding execution conformance would require a separately reviewed general contract and observed runs by third-party implementations; structural evidence alone cannot support it. |

## Candidate grammar and operation boundary

The maintainer delegated continued preparation and experimentation on 2026-09-06.
That instruction is not a recorded acceptance of each C1-C10 choice. The rules
below close one experimental edition, `proposal-0012-candidate-2`. They define
candidate behavior precisely enough to implement and compare; they establish
no official AgSDL feature, diagnostic, syntax or conformance claim. Candidate-1
is a previous proposal spelling, not an accepted compatibility target.

### Notation and shared JSON rules

In the tables, listed fields are required unless followed by `?`. Each record
is closed: no other members are allowed. `T[]` means an array of T, empty unless
a minimum is stated. `map<T>` means an object whose keys are nonempty strings
and values have type T. Map keys such as `__proto__` have ordinary data meaning.
`text` is a nonempty Unicode string; `JSON` is any JSON value, including null.
`uint` is an integer in 0..9007199254740991; `positive` excludes zero. A literal
in quotes is the only permitted string value. Absence is permitted only at `?`;
null is permitted only where explicitly listed or inside JSON. There are no
implicit values, conversions, merge rules or fetching operations.

Parsing accepts one UTF-8 JSON value without BOM, duplicate member names, invalid
Unicode scalar values or trailing non-whitespace content. JSON numbers use the
JSON number grammar; interpreted uint/positive values are checked mathematically
without binary floating-point rounding. Opaque numbers retain their original
lexeme without a magnitude limit. D shape requires the parsed root to be a
Document object; inspect/exchange can inventory or copy other JSON roots.
Object order has no semantic meaning. Arrays
retain order for locations; only steps connected by edges determine scheduling.
Equality of strings compares decoded Unicode scalar sequences exactly, without
case folding, Unicode normalization, URI normalization or version ordering.

| Type | Fields or values |
| --- | --- |
| Key | `scope:text`, `id:text`, `version:text` |
| Edition | `identity:text`, `version:text`; identity matches `[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*` in full |
| Ref | Key, or exactly `dependency:text`, `key:Key` |
| Hash | 64 lowercase hexadecimal characters |
| Kind | One known-kind string below, or exactly `extension:Edition`, `name:text` |
| Ports | map of `"string"`, `"boolean"` or `"json"` |
| Binding | Exactly `input:text`, or exactly `step:text`, `port:text` |

Key equality compares all three fields; a version is an exact opaque identity,
not a range, selector or compatibility promise. Edition equality compares both
fields. A local scope/id pair has one version and record, including the root.
Across supplied documents different versions can coexist. A Ref wrapper always
means external, even when its key shares a local scope. Kind equality compares
the string or all fields of the custom Kind. No custom Kind aliases a core kind.

The closed known-kind list for local definitions is `Agent`, `Principal`,
`Interface`, `Instructions`, `Role`, `Skill`, `ControlFlow`, `Action`, `Resource`,
`ApprovalRequirement`, `Tool`, `Model`, `Environment`, `Runtime`, `Deployment`,
`Policy`, `Memory`, `Knowledge`, `State`, `Topology`, `Protocol`. These names
activate only this candidate's checks, not all of proposal 0002. Other concepts,
including occurrences, are opaque evidence or declared extensions. Root kinds
are separate. A custom Kind's exact extension Edition must occur once in the
same document's extension array. Generic use/containment can name a custom
Kind; it cannot satisfy a core Agent, Interface or other typed minimum.

### Operations, phases and supplied inputs

A request is exactly `operation`, `primary` as a byte string, and `annexes` as a
map of byte strings. Operation is one of `inspect`, `validateD`, `validateG`,
`resolveG`, `validateR`, `exchange`, `lossyExchange`. An optional `losses` array
is allowed only with lossyExchange and uses the loss record below. Callers
provide the entire observed input boundary. Byte strings and maps describe the
host API, not a new transport. Annex map keys are exact dependency ids of the
primary document. No other files, URLs, secrets or processes are accessed.

| Operation | Coverage and phase |
| --- | --- |
| inspect | Syntax and D inventory, no semantic validation verdict. Return source tree and opaque slices when parseable; otherwise bytes and syntax finding. |
| validateD | D rules, phase `unresolved-document`. |
| validateG | D prerequisite plus G local rules, phase `unresolved-document`. External G obligations are recorded unchecked, outside this phase's positive scope. |
| resolveG | D prerequisite plus G local rules and direct external G target checks against supplied annexes, phase `resolved-graph`. This is a bounded G graph, not full model resolution. |
| validateR | D prerequisite plus R rules, phase `unresolved-document`; no deployment assessment. |
| exchange | Exact byte preservation and dependency accounting, phase null; independent of semantic validation. |
| lossyExchange | Refuse output, phase null; report all requested losses, or one whole-artifact loss if none supplied. |

The requested Result's unit and phase are fixed, independent of input validity:

| Operation | Result unit | Result phase |
| --- | --- | --- |
| inspect | inspect | null |
| validateD | D | unresolved-document |
| validateG | G | unresolved-document |
| resolveG | G | resolved-graph |
| validateR | R | unresolved-document |
| exchange | exchange | null |
| lossyExchange | exchange | null |

D prerequisite Results always have unit D and phase unresolved-document;
selected-annex G Results have unit G and phase resolved-graph. These assignments
also apply when parsing fails or an operation refuses output.

G/R operations include a separate D result in the report. A failing, unsupported
or inconclusive D result prevents dependent checks from claiming success. It
does not convert unchecked G/R rules into passes. No operation not requested,
apart from this explicit prerequisite, gets a result. G validates all graphs
present, R validates the runtime container present. Absence of either container
is valid and reported `absent`, with its rules not applicable; it grants no
engine selection or graph. No operation executes the described behavior.

### D envelope and reference declarations

| Record | Fields |
| --- | --- |
| Document | `contract:"proposal-0012-candidate-2"`, `root:Root`, `definitions:Definition[]`, `relations:Relation[]`, `exports:Key[]`, `dependencies:Dependency[]`, `unresolved:Deferral[]`, `extensions:Extension[]`, `annotations?:JSON`, `evidence?:JSON`, `graphs?:JSON`, `runtime?:JSON` |
| Root | `key:Key`, `kind:"System" or "Fragment" or "PackageVersion"`, `payload?:JSON`, `annotations?:JSON` |
| Definition | `key:Key`, `kind:Kind`, `owner:Key`, `payload:JSON`, `annotations?:JSON`, `provenance?:JSON` |
| Relation | `source:Key`, `relation:"actsAs" or "exposes" or "directedBy" or "uses" or "contains"`, `target:Ref`, `expectedKind:Kind` |
| Dependency | `id:text`, `rootKey:Key`, `status:"included" or "external" or "omitted" or "unavailable"`, `requiredFor:("validateD" or "resolveG" or "exchange")[]`, `sha256:Hash or null`, `location?:text` |
| Deferral | `subject:Key`, `obligation:"agent-interface-minimum"`, `rule:"fragment-interface-deferral"`, `relation:"exposes"`, `expectedKind:"Interface"`, `missingMinimum:1`, `target:Key or null`, `satisfyBy:"typed-exposes-relation"`, `expiresBefore:"resolved-graph"` |
| Extension | `identity:text`, `version:text`, `operations:ExtensionOperations`, `payload:JSON` |
| ExtensionOperations | `validateD?:ExtensionMode`, `validateG?:ExtensionMode`, `validateR?:ExtensionMode` |
| ExtensionMode | `"required"`, `"unknown"`, or exactly `ignoreRule:"annotation-only"` |

An Extension's identity/version satisfy Edition. Edition duplicates fail.
All definitions share the root's scope and have exactly the root key as owner;
the root has no owner and is not a definition owned by itself. The package root
remains an immutable-artifact boundary. No synthetic System, Identity record,
instance or ownership edge is inferred. Provenance is retained as an assertion,
not verified evidence of authenticity. Opaque provenance/payload cannot change
key, owner, kind or relation meaning in this edition.

Every relation source exists locally, including the root. Local targets exist
uniquely with matching expectedKind. External targets name one declared
dependency, have its rootKey scope, and are not looked up by D. `actsAs` is
Agent to Principal, `exposes` Agent to Interface, `directedBy` Agent to
Instructions/Role/Skill/ControlFlow. `uses` and `contains` allow any source and
any declared Kind. Duplicate relation tuples fail. The local contains graph
has no directed cycle or self-edge; ownership is already constrained to root.
Each local Agent has exactly one actsAs, at least one directedBy, and at least
one exposes unless the one allowed deferral applies. External declared targets
count toward relation presence, not evidence of target content.

Exports are unique local definition keys. Fragment exports are nonempty,
System exports empty, PackageVersion exports may be empty. A Deferral is valid
only for a local Agent in a Fragment with zero exposes relations, one declaration
per subject, all other Agent minima intact. Non-null target is an exact future
Interface key constraint; null explicitly states it is unknown. No dangling
reference is excused. Resolving G cannot satisfy a missing relation by invention;
if G needs that Agent's missing Interface, its graph fails. D deferrals outside
G's dependency closure remain explicitly excluded from bounded G resolution.

D reads the outer JSON of all fields, but interprets only the closed D records.
Definition payloads, root payload, annotations, provenance, evidence and the
entire graphs/runtime values are opaque in D. G interprets graphs and selected
Interface/ApprovalRequirement payloads; R interprets runtime. Thus `graphs:17`
can pass D, fails G shape, and is still preserved exactly. Unsupported G is not
unknown D core syntax. Extra members inside a G-interpreted payload fail G,
while unrelated payloads remain opaque. No declared scope may silently shrink
to avoid a local Agent failure.

### Dependencies, unknowns and extension handling

Dependency ids, rootKeys and requiredFor entries are unique within their arrays. Status `included` requires
an annex; other statuses require its absence. Undeclared annex ids fail
accounting. Hash null means explicitly unknown, never absent or mismatched.
A non-null hash is checked against supplied bytes. If validateD is in requiredFor
and hash is null, D is inconclusive, even when no annex was supplied. D otherwise
accepts null and reports integrity unchecked. D never requires annex availability
solely from requiredFor; local declaration and supplied-content checks remain
separate. `location` is an opaque hint, not a resolution base or retrieval grant.

ResolveG requires every dependency named by a G Ref or marked resolveG in
requiredFor to be included, parseable as this edition, hash-known and matching.
Missing bytes or invalid content fails; null declared hash is inconclusive,
not permission to invent integrity. Verify its rootKey against the parsed root.
Each external G Ref from the primary document resolves to exactly one exported
definition of the expected core kind in its annex. Local G Refs resolve within
their owning document without an export requirement, including local references
inside selected annex payloads and relations.
A selected key appearing in more than one document boundary, including the
primary, fails G-RESOLVE rather than merging definitions; repeated references
within the same boundary are allowed. Only direct primary dependencies are supported: when a selected annex payload
or relation needs an external Ref, report unsupported for that G check. No
transitive resolver, composition, overlay, profile application or cycle-breaking
policy exists here. An annex's D validation is required for resolveG and reported
separately; its own included dependencies cannot be supplied by the flat primary
map, so such an annex fails its accounting rather than triggering recursion.
Unused annex G/R containers remain unchecked. Imported ownership never changes.

The edition implements no semantic extension interpreter. For each requested
validation unit, required gives unsupported, unknown or absent classification
gives inconclusive. `ignoreRule:annotation-only` is a candidate core permission:
the entire extension is a nonsemantic annotation for that unit and cannot
change core facts. A custom Kind declaration forces validateD required for its
extension; any other validateD mode on that extension fails classification.
This prevents an unknown kind from bypassing typed checks with an ignore label.
G uses validateG classification for both phases, R uses validateR; D prerequisite
classification remains independent. No extension code or ignore-rule definition
is loaded. Future semantic interpreters need a new candidate contract, not an
implementation-specific pass in this one. The closed ignore rule makes the
candidate oracle identical in two independently implemented readers.

Absence, explicit unknown, unsupported interpretation, excluded checks and
failed facts are distinct. Missing mandatory fields fail shape. Null permitted
hashes and unknown extension modes remain visible unknowns. No extension blocks
exact preservation merely because its interpretation is unavailable.

## G: closed simple-graph grammar

Conceptual example: draft through one Agent Interface, branch on its Boolean
needsReview output, obtain human approval for a second Agent invocation when
true, then finish. False returns the draft directly. The protected invocation
is still an Agent call; its Action reference describes the proposed action of
that call, not a second instruction or an `invokeAction` opcode.

When G is requested, graphs is Graph[]. An empty array is valid. Each graph's
definition uniquely selects a local ControlFlow. All graphs in this container
are checked; nested graphs, parallelism, arbitrary cycles and expressions are
outside G and fail its closed grammar if encoded as step kinds or fields.

| Record | Fields |
| --- | --- |
| Graph | `definition:Key`, `entry:text`, `inputs:Ports`, `outputs:Ports`, `steps:Step[]` with at least one step |
| invoke Step | `id:text`, `kind:"invoke"`, `agent:Ref`, `interface:Ref`, `action:Ref`, `resources:Ref[]` nonempty, `principal:Ref`, `context:Binding`, `inputs:Ports`, `outputs:Ports`, `bindings:map<Binding>`, `success:text`, `failure:text` |
| condition Step | `id:text`, `kind:"condition"`, `test:Binding`, `true:text`, `false:text`, `failure:text` |
| approval Step | `id:text`, `kind:"approval"`, `requirement:Ref`, `timeoutMs:positive`, `approved:text`, `denied:text`, `failure:text` |
| success end Step | `id:text`, `kind:"end"`, `outcome:"success"`, `bindings:map<Binding>` |
| other end Step | `id:text`, `kind:"end"`, `outcome:"failure" or "denied"`, `reason:text` |
| Selected Interface payload | `inputs:Ports`, `outputs:Ports`, `action:Ref` |
| Selected ApprovalRequirement payload | `approvers:Ref[]` nonempty, `validForMs:positive` |

Every G/R Ref obeys the same local/external declaration rules as D relations,
including dependency existence and scope matching; opaque D treatment does not
waive these checks when G/R interprets it. All selected graph refs are typed: agent Agent, interface Interface, action
Action, resources Resource, principal and approvers Principal, requirement
ApprovalRequirement. Resources and approvers have no duplicate Refs. Other
payloads, including Action/Principal/Resource and ControlFlow, are not evaluated.
G invents neither an acting identity nor authorization evidence from them.
An invoke's Interface is exposed by its Agent through one D relation, its
principal equals that Agent's actsAs target, and its action equals the Interface
payload action. Equality here uses resolved keys when targets are available;
validateG checks known local matches and records external comparisons unchecked.
Refs inside a selected annex record use that annex as their local scope; the
primary invocation still identifies it using the external wrapper.

Interface inputs/outputs equal the invoke's maps, including names and types.
The bindings map has exactly the invoke input names. Success terminals bind
exactly graph outputs; failure/denied terminals bind none. Context has type
json; condition test has type boolean. Binding input names exist in graph
inputs; step bindings name an invoke and one of its output ports. Types match
exactly, with no string-to-json coercion or selectors. All ports are required.
Only invoke produces ports. For every step-output binding, every path from entry
to its consumer must traverse that producer's success edge. Removing the success
edge must make the consumer unreachable. This also excludes self-use and
failure-path outputs. For an approval step, additionally check all bindings of
its approved invoke, including context, at the approval step itself, because
the request presents those values before the invocation occurs.

Step ids are unique. Every successor and entry names a step. The graph is
acyclic, every step reachable from entry, every maximal path ends at an end
step. The only end steps have no successors. Successor labels are distinct
edges even if their target ids coincide. Conditions choose exactly true/false
for Boolean values; unusable values lead to failure. Invocations produce all
declared outputs on success; unusable/missing outputs lead to failure with no
partial outputs. These are declared meanings, not observations of a run.

An approval's approved successor is an invoke and has that approved edge as its
only incoming edge. Neither denied nor failure may reach that invocation.
At most one approval protects one invoke. The requirement, action, resources,
requesting Principal definition, input values and context of the proposed call
are the request's declared scope. Approval refers only to that immediate call.
The request permits decisions approve/deny by one of the requirement's declared
human Principal definitions. Validation checks references, not whether a real
human controls an identity. The maximum wait/validity interval begins on entry
to the approval step and is min(timeoutMs, validForMs) milliseconds. There is no
graph-level timeout. A valid approval within that interval selects approved;
a valid refusal selects denied. At or after the deadline, no response or
unusable/expired/mismatched decision selects failure. Matching, authentication,
authorization and timing evidence are not simulated by a validator. The
candidate defines no executable decision intake API, retries or approval reuse.
This is a declaration of a human gate, not proof of permission or enforcement.

ValidateG checks available local targets/payloads and all graph shapes, edges,
bindings and local agreements. An external Ref's declaration is checked, then
target-dependent checks are explicitly excluded at this phase, even if annexes
were supplied. ResolveG checks the same rules using its direct target set;
missing required G references fail and none may use a D deferral to pass.
The G verdict covers G's selected target payloads only, not full Interface,
Action, approval or System validity from proposal 0002.

## R: closed runtime-declaration grammar

When R is requested, runtime is RuntimeDeclaration. R has no resolved or ready
operation. Open Edition identifiers are declarations, not a registry or proof
that an engine or capability contract exists.

| Record | Fields |
| --- | --- |
| RuntimeDeclaration | `requirements:Requirement[]`, `selection?:Selection` |
| Requirement | `id:text`, `capability:Edition`, `subject:Key` |
| Selection | `engine:Edition`, `interface:Edition`, `model?:Edition`, `provider?:text`, `hosting?:Ref`, `evidence:EvidenceClaim[]` |
| EvidenceClaim | `requirement:text`, `claim:"satisfied" or "unsatisfied" or "indeterminate"`, `artifact:Hash or null`, `location?:text` |

Requirement ids are unique; subject selects a local definition, not the root.
Duplicate capability/subject pairs fail. All requirements are needed by the
subject; empty requirements is valid. No implied capability taxonomy exists.
Provider, when present, uses the identity pattern of Edition but has no implied
model or engine relationship. Hosting expects Environment; R checks local kind
or external declaration only, never deployment resolution. Evidence requirement
names exist, one EvidenceClaim per requirement at most; missing claims are valid
and reported absent. Null artifact means unknown evidence identity. Claim is
an unverified assertion retained verbatim, even when it says satisfied or when
an engine is unknown. Evidence location is an opaque hint, never dereferenced.
No source truth, capability compatibility or claim plausibility is assessed.

No selection is valid and reported absent; no engine is inferred. Present
selection is reported declared, with support unassessed for every engine,
including known product names and custom engines. Model/provider/hosting remain
absent when not supplied. R pass means well-formed declarations only; the report
always excludes readiness, evidence assessment and execution. A later assessment
could interpret known gaps as unsatisfied and unknown support as indeterminate,
but that operation is outside this edition. No automatic fallback is encoded.

## Exact results, locations and experimental diagnostics

The following report records use the same closed notation. These are candidate
identifiers scoped to candidate-2, not stable official diagnostics. Checks follow syntax, shape, D declarations, then the selected unit;
within each stage they follow the rule table below. A prerequisite shape failure suppresses only rules
that need that malformed value. Unrelated well-formed records are still checked.
For duplicate keys or ambiguous identities, dependent lookup is not attempted.
Each rule emits one finding per failing or unknown subject location, not one
finding per possible explanation. If several reasons apply at that location,
retain them in details but keep one rule/location/outcome tuple.

| Report record | Fields |
| --- | --- |
| Report | `contract:"proposal-0012-candidate-2"`, `processor:Edition`, `operation:text`, `inputs:InputRecord[]`, `results:Result[]`, `inventory:Inventory`, `losses:Loss[]`, `outputs:OutputRecord[]` |
| InputRecord | `id:text`, `sha256:Hash`; primary id is `primary`, annex ids are `annex/` followed by supplied map key |
| Result | `input:text`, `unit:"D" or "G" or "R" or "inspect" or "exchange"`, `phase:"unresolved-document" or "resolved-graph" or null`, `verdict:"pass" or "fail" or "unsupported" or "inconclusive"`, `findings:Finding[]`, `checks:Check[]` |
| Finding | `rule:text`, `location:Location`, `outcome:"fail" or "unsupported" or "inconclusive" or "deferred"`, `details:text` |
| Location | Exactly `pointer:string`, or exactly `byte:uint`; empty pointer is root |
| Check | `rule:text`, `state:"completed" or "excluded" or "blocked"`, `locations:Location[]` |
| Inventory | `tree:JSON`, `states:State[]`, `opaque:Slice[]`; tree is null on parse failure |
| State | `input:text`, `pointer:string`, `state:"absent" or "unknown" or "declared" or "unchecked"`, `detail:text` |
| Slice | `input:text`, `pointer:string`, `start:uint`, `end:uint`; half-open UTF-8 byte span |
| Loss | `input:text`, `location:Location`, `information:text`, `reason:text`, `permission:null` |
| OutputRecord | `id:text`, `sha256:Hash` |

`string` in Location/State/Slice permits empty string. Parsed locations are JSON
Pointers: escape ~ as ~0 and / as ~1; array indices are zero-based decimal.
Missing-field shape findings point to its parent record; wrong type/extra field
findings point to that value. All other rules point to the affected record,
except cycle/path rules to Graph or relations array as specified below.
Syntax errors point to the first offending byte, or byte length for unexpected
EOF. Duplicate member names point to the opening quote of the second name.
For simultaneous encoding and JSON defects report the earliest byte detectable
by a left-to-right strict UTF-8 JSON scan. No parsed tree exists after syntax
failure; preservation can still copy the raw input.

Inputs include every supplied artifact, sorted primary then annex id. Results
are ordered prerequisite D for primary, D for each required annex sorted by id
when resolveG requests them, then requested operation result. ValidateD emits
only its D result; inspect/exchange emit only their own result. Annex D input
uses its own bytes with an empty annex map. Its syntax/version failures become
failed dependency checks in resolveG; unsupported/inconclusive D evidence stays
unsupported/inconclusive. G/R requested result aggregates prerequisite D findings
without copying them: a blocked check entry names `P-PREREQUISITE` and its state;
verdict precedence below includes those prerequisite results. No pass follows a
failed prerequisite, even for an absent G/R container.

Inventory tree is the primary parsed JSON value; opaque numeric values can be
exposed as lossless host representations, with slices as the comparison source.
Inventory states are operation-scoped, never discovered inside opaque values.
Use the following exhaustive state inventory, only for well-shaped parent
records. Validation emits shape findings for malformed parents; inspect/exchange do not.
No operation invents child absences beneath a malformed parent.

| Scope | States recorded |
| --- | --- |
| Every operation with a parsed primary object | graphs and runtime: absent when missing; unchecked when present but opaque to this operation; declared when present and interpreted by G or R. No child states under an absent container. |
| D boundaries, used by every operation including inspect/exchange/lossyExchange | Unknown at each null dependency sha256 in a well-shaped Dependency. Unchecked at each external target pointer /relations/i/target in a well-shaped Relation, without looking up its content. No selection, model, provider, hosting or evidence states inside runtime. |
| G only | Unchecked at each external Ref whose target-dependent checks are excluded in validateG; no internal R states. Resolved target evidence is represented by checks/results, not a synthesized state tree. |
| R only | Selection absent when missing, otherwise declared. Within a present well-shaped Selection, model/provider/hosting are absent or declared according to presence. Unknown at each null EvidenceClaim artifact. A missing claim records absent at /runtime/selection/evidence with detail naming its Requirement id, one state per missing claim. No missing-claim states if selection is absent. Present selection also records unchecked at /runtime/selection/engine for support and at each EvidenceClaim for evidence assessment. External hosting additionally records unchecked at /runtime/selection/hosting for target content, alongside its declared-presence state. |
| inspect/exchange/lossyExchange dependency inventory | At /dependencies record absent if the primary parsed object lacks that member, declared if the full Dependency[] grammar is satisfied, unchecked if present but malformed, primary parsing failed, or the parsed root is not an object. When malformed, retain the entire /dependencies value as one opaque slice; when parsing failed, no JSON slice exists. These states are inventory observations, not validation findings. |
| Required resolveG annexes | Apply D states to each annex with its own input id; additionally G external-target states only for selected G payloads/relations. No graph or runtime internals of annexes are inventoried. |

In particular validateD or inspect of runtime:{} records unchecked at /runtime
and its opaque slice, with no /runtime/selection state. ValidateR of that value
fails its missing requirements field shape and does not invent selection state
under the malformed RuntimeDeclaration. States are compared as sets including
input/pointer/state; only missing-claim details require exact Requirement ids.
Other detail prose and array order are not comparison keys.

Declared definitions/relations are the source tree itself, not a synthesized
normalized graph. Opaque slices are the maximal unexamined JSON values for the
requested unit: D opaque fields listed above, G/R unselected payloads/containers,
annotations/evidence/provenance and extension payloads. Inspect and exchange use
D boundaries. Compare slices by their source bytes, not a host JSON serializer.
For a parsed nonobject root, inspect/exchange retain one opaque slice at "".
No normalized JSON codec is required.

| Rule | Deterministic check and finding location |
| --- | --- |
| P-SYNTAX | Shared JSON encoding/parse constraints; byte location. On failure all shape/semantic rules are blocked. |
| P-SHAPE | Closed record grammar, required/optional fields, enums and primitive domains for requested scope; malformed field or parent as above. Wrong contract marker is a shape failure. |
| D-IDENTITY | Duplicate scope/id among root/definitions, wrong local scope; offending later definition in array or record with wrong scope. |
| D-OWNER | Owner not equal to root key; definition record. |
| D-REFERENCE | Every D source/local target exists and kind matches, external wrapper names dependency and matching scope, custom Kind has declared Edition; relation or custom-kind definition record. |
| D-RELATION | Source/expected target kinds allowed, duplicate relation tuple; offending relation, later one for duplicates. |
| D-CYCLE | Local contains cycle including self-edge; relations array, one finding for any cycles. |
| D-EXPORT | Export missing/duplicate, root export minimum/form; later invalid export item, or exports array for minimum/form. |
| D-AGENT | Each local Agent minima; Agent record, one finding for any unsatisfied minima. Valid Interface deferral exempts only that minimum. |
| D-DEFERRAL | All deferral preconditions, duplicate/stale declaration; deferral record. Valid deferral emits deferred at that record, not a pass for the missing relation. |
| D-DEPENDENCY | Dependency id/rootKey/requiredFor uniqueness, declared delivery status vs actual annex map, undeclared annex; dependency record, later entry for duplicates; root pointer for undeclared annex. |
| D-INTEGRITY | Supplied known hash mismatch fails; required validateD hash null inconclusive; dependency record. |
| X-MODE | Duplicate Editions/custom Kind mode conflict fails at extension record; otherwise required unsupported, unknown/absent mode inconclusive there; annotation-only completes with no finding. Applies independently to each requested unit. |
| G-TARGET | Graph ControlFlow key/type/uniqueness; local typed Refs, selected payload refs, Agent exposure/principal and Interface action agreement, Resource/approver duplicate refs; affected Graph, Step or selected payload record. External target-dependent parts excluded in validateG. |
| G-PATH | Unique step ids, entry/successor existence, acyclicity, reachability, terminal paths; Graph record, one failure for any defect. |
| G-DATA | Port-map agreement, binding names/types, success-edge availability; Step record. Approval pre-invocation availability failure points to approval Step. |
| G-APPROVAL | Approved target is invoke, sole incoming approved edge, denied/failure unreachable to protected invoke; approval Step record. |
| G-RESOLVE | Missing required annex, invalid annex/rootKey, cross-document selected-key collision, missing/unexported/wrong-kind external target fails; unknown declared hash inconclusive; transitive selected Ref unsupported; dependency record for artifact issue, consuming Step for target issue. |
| R-REQUIREMENT | Unique ids and capability/subject, local subject lookup; later offending Requirement. |
| R-SELECTION | Hosting reference/kind, evidence requirement existence/uniqueness; Selection or offending EvidenceClaim. No interpretation of claims. |
| E-PRESERVE | Output bytes and input boundary identical, supplied annex accounting consistent; root pointer on refusal/failure. Known hash mismatch fails at dependency record. |
| E-LOSS | lossyExchange refused; root pointer and separate prospective Loss records. |

P-SHAPE applies to selected Interface/ApprovalRequirement payloads when G can
observe them. G findings in annex payloads have a Result whose input is that
annex, unit G, same phase, emitted before the primary G result; aggregate them
as prerequisites. Ref comparison does not recursively activate all kind rules.
For shape failures emit one P-SHAPE finding at each malformed field/parent;
multiple missing fields at one parent coalesce. Semantic rules with absent
prerequisites list blocked locations; valid unaffected records still run.
G-PATH failure blocks availability and approval reachability checks in that
Graph, but not local type/target checks. All candidate validators implement
these same rules; no user-selected arbitrary subset produces a unit pass.

### Rule execution and exact exclusion records

Only the following rule sets execute. An operation's incidental parsing or
shape probing for inventory does not add findings outside this matrix.

| Result unit and operation | Rules executed |
| --- | --- |
| D for validateD or a validation prerequisite | P-SYNTAX, P-SHAPE for D, every D-* rule, X-MODE for validateD. |
| G for validateG | P-SHAPE for interpreted G fields, X-MODE for validateG, G-TARGET, G-PATH, G-DATA, G-APPROVAL. D prerequisite owns syntax and D findings. |
| G for resolveG | Same G rules plus G-RESOLVE; required annex D results own their D rules. Annex G results run P-SHAPE for selected payloads and G-TARGET only. |
| R for validateR | P-SHAPE for R, X-MODE for validateR, R-REQUIREMENT, R-SELECTION. |
| inspect | P-SYNTAX only. A parseable input gives pass for inventory production regardless of D shape or semantics; parse failure gives fail. No P-SHAPE finding is emitted. |
| exchange | E-PRESERVE only. Parsing and a full Dependency[] shape predicate inform inventory/accounting, never P-SYNTAX or P-SHAPE findings. Copying bytes with absent/unreadable dependencies gives pass with the exact inventory state above, not a declared package-completeness claim. Accounting or known hash failures on a readable Dependency[] refuse output. |
| lossyExchange | E-LOSS only; verdict fail and no output. Parsing/shape probing may produce inventory, never validation findings. |

The result checks array contains one Check per rule/state pair. Completed rules
use locations:[] even when several subjects were examined. A rule partially
completed and partially blocked/excluded has a completed entry and separate
blocked/excluded entries listing unique relevant locations. Blocked means a
malformed or ambiguous prerequisite prevented an applicable check; excluded
means the contract does not attempt that check in this operation. Sort rules
lexicographically, states lexicographically, and locations by pointer text or
byte value; no duplicate locations. Other findings/state-array order is not
significant for comparison. A rule with no subjects completes with [] except
for the explicit container exclusions below. Rule ids outside this inventory
are not allowed in a candidate-2 report.

All validation Result units D/G/R contain these documentary boundary Check
records, always excluded, even if a prerequisite failed:

- X-EXECUTION at pointer "" in every validation Result.
- X-FULL-MODEL at pointer "" in every validation Result.
- X-READINESS at pointer /runtime and X-EVIDENCE-ASSESSMENT at pointer /runtime
  in primary R Result only. They remain excluded if runtime is absent.

These four ids have no finding and never execute. Inspect/exchange/annex G
results do not invent R exclusions. They are limits of the named unit, not
checks that could otherwise have been passed. A reader must not treat them as
blocked and thereby turn a bounded pass into inconclusive.

In the primary G Result, absent graphs excludes P-SHAPE, G-TARGET, G-PATH, G-DATA, G-APPROVAL and,
for resolveG, G-RESOLVE at /graphs. Absent runtime excludes P-SHAPE,
R-REQUIREMENT and R-SELECTION at /runtime. X-MODE still runs. An empty graphs
array has no subjects and completes these rules with []; resolveG still checks
any explicit requiredFor resolveG dependencies. To preserve that requirement,
G-RESOLVE also completes or fails its dependency portion when graphs is absent,
while its graph portion is excluded. Present well-shaped runtime without
selection excludes R-SELECTION at /runtime/selection. No model/provider/hosting
absence excludes R-SELECTION as a whole; their optionality is ordinary shape.

External target-dependent local G checks excluded in validateG use the consuming
Step location in G-TARGET or G-DATA, as applicable. Their declaration/type checks
still complete where observable. D external relation targets need no lookup
Check: D-REFERENCE completes its declaration scope and inventory records each
relation's target pointer unchecked. R external hosting similarly completes its
declaration scope and records /runtime/selection/hosting unchecked. These do
not imply resolved content. An opaque value produces a slice, not extra rule ids.

For unavailable prerequisites, blocked locations are the affected record needing
the value, with "" for a whole-unit prerequisite P-PREREQUISITE. This special
rule appears only as blocked in dependent primary G/R Results and uses pointer
""; it has no finding and is omitted when D passes. Validation rules unaffected
by that prerequisite still run when their input shape is available. The rule
matrix and prerequisite verdict precedence determine the final result.

Aggregation is fail before unsupported before inconclusive before pass. Deferred
findings do not prevent D pass, but remain outstanding. Excluded checks do not
claim success. A completed rule with no finding is satisfied for its scope;
blocked checks make the unit inconclusive unless a higher-precedence finding
or prerequisite already decides it. Unrequested checks are absent. Validation
results never imply execution evidence, even when all three units pass.

Exact exchange returns every supplied artifact's bytes unchanged using original
ids; OutputRecord hashes describe those bytes, transferred separately. Syntax
or semantic invalidity alone does not prevent copying. If the primary is
parseable and has well-shaped dependencies, enforce delivery accounting and
known hashes; if dependency declarations cannot be read, record them unchecked,
copy the supplied boundary only, and claim no declared package completeness.
RequiredFor exchange additionally requires included bytes and a known hash;
otherwise refuse exchange, with fail for missing bytes, inconclusive for null
hash. No output is delivered on refusal. Exchange inventories unknown content
without interpretation and is not producer conformance. LossyExchange always
returns fail, E-LOSS and no output, even if a caller asserts omission permission;
this edition grants none. A default loss names primary root and information
`unspecified requested loss`. Neither byte equality nor a loss report proves
semantic equivalence.

## Candidate examples and experimental oracles

The following minimal Fragment passes D with one explicit deferral. Payloads
are deliberately nonsemantic for D, including the Principal's two identities.

```json
{
  "contract": "proposal-0012-candidate-2",
  "root": {"key": {"scope": "example", "id": "fragment", "version": "1"}, "kind": "Fragment"},
  "definitions": [
    {"key": {"scope": "example", "id": "agent", "version": "1"}, "kind": "Agent", "owner": {"scope": "example", "id": "fragment", "version": "1"}, "payload": {}},
    {"key": {"scope": "example", "id": "actor", "version": "1"}, "kind": "Principal", "owner": {"scope": "example", "id": "fragment", "version": "1"}, "payload": {"identities": ["team/author", "review/author"]}},
    {"key": {"scope": "example", "id": "direction", "version": "1"}, "kind": "Instructions", "owner": {"scope": "example", "id": "fragment", "version": "1"}, "payload": "Draft a reply."}
  ],
  "relations": [
    {"source": {"scope": "example", "id": "agent", "version": "1"}, "relation": "actsAs", "target": {"scope": "example", "id": "actor", "version": "1"}, "expectedKind": "Principal"},
    {"source": {"scope": "example", "id": "agent", "version": "1"}, "relation": "directedBy", "target": {"scope": "example", "id": "direction", "version": "1"}, "expectedKind": "Instructions"}
  ],
  "exports": [{"scope": "example", "id": "agent", "version": "1"}],
  "dependencies": [],
  "unresolved": [{"subject": {"scope": "example", "id": "agent", "version": "1"}, "obligation": "agent-interface-minimum", "rule": "fragment-interface-deferral", "relation": "exposes", "expectedKind": "Interface", "missingMinimum": 1, "target": null, "satisfyBy": "typed-exposes-relation", "expiresBefore": "resolved-graph"}],
  "extensions": []
}
```

| Mutation or supplied case | Candidate oracle |
| --- | --- |
| Remove the deferral above | D fail, D-AGENT at /definitions/0. |
| Duplicate the Agent record | D fail, D-IDENTITY at the later definition; dependent ambiguous lookups blocked. |
| Add graphs:17 | D still passes; validateG fails P-SHAPE at /graphs. |
| Add a well-shaped external Interface relation with null dependency hash and no validateD requirement | D checks declaration, does not fetch; target/integrity unchecked. A G use of the missing annex fails resolveG. |
| Unknown custom Kind with required extension | D unsupported, X-MODE, while identity/reference checks still run; exchange can preserve. |
| Unsupported extension marked annotation-only while declaring a custom Kind | D fail, X-MODE; optional classification cannot hide a kind. |
| D-valid System with a fully local valid invocation graph, exports empty and no dependencies | resolveG passes; local targets require no export, and no annex is fetched. |
| Invoke success and failure both reach an end consuming its output | G fail, G-DATA at that end Step. |
| Approval approved and denied both reach its protected invoke | G fail, G-APPROVAL at the approval Step. |
| Runtime with empty requirements and no selection | R pass, selection absent, readiness excluded. |
| Runtime with custom engine and asserted satisfied evidence with null artifact | R may pass shape/relations, hash unknown and evidence unassessed; no ready result. |

An experimental corpus supplies complete local D records for each G case,
including Interface action/I/O, Agent relations and a finite graph. The grammar
and rules above are its oracle; schemas enforce them without adding semantics.
Every rule needs positive, negative and relevant unknown/excluded variants.
Two readers compare verdicts, rule/location/outcome tuples, inventory slices
and exclusions, not diagnostic prose or timing. No fixture or comparison has
been executed by this documentation step.

## Adoption, compatibility and delivery

The recommended candidate-2 choices are now specified for experimentation.
C1-C10 remain recommendations, not ten approvals inferred from a delegation.
Experimental comparison comes before a separate adoption review reconciling
these bounded rules with proposals 0002/0003/0011 and Decisions 0001/0004.
In particular G adds bounded direct resolution outside 0011's D operation;
Identity interpretation and human-gate meaning still require adoption review.

The candidate has no official compatibility or runtime claim. Future execution,
semantic extensions, transitive resolution, normalization and lossy transforms
need their own reviewed contracts. Missing such features is a stated boundary,
not an unspecified behavior inside D/G/R. No particular product determines
portable requirements. The [delivery plan](../docs/plans/2026-09-05-0.1.0-delivery.md)
orders experimental fixtures, two independent readers and adoption review.
A complete experimental contract is not a completed or published 0.1.0 release.
