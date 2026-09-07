# Reports and deterministic diagnostics

[Specification index](README.md).

The following report records use the same closed notation. These identifiers are scoped to the official `agsdl-0.1.0` edition. Checks follow syntax, shape, D declarations, then the selected unit;
within each stage they follow the rule table below. A prerequisite shape failure suppresses only rules
that need that malformed value. Unrelated well-formed records are still checked.
For duplicate keys or ambiguous identities, dependent lookup is not attempted.
Each rule emits one finding per failing or unknown subject location, not one
finding per possible explanation. If several reasons apply at that location,
retain them in details but keep one rule/location/outcome tuple.

| Report record | Fields |
| --- | --- |
| Report | `contract:"agsdl-0.1.0"`, `processor:Edition`, `operation:text`, `inputs:InputRecord[]`, `results:Result[]`, `inventory:Inventory`, `losses:Loss[]`, `outputs:OutputRecord[]` |
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
by a left-to-right strict UTF-8 JSON scan. An invalid UTF-8 continuation points
to that continuation byte, including a byte outside the range permitted after
the leading byte. A sequence truncated before its next continuation points to
EOF, at the input byte length.

P-SYNTAX has one exception for Unicode escapes: a lexically complete `\uXXXX`
escape containing an unpaired surrogate points to that escape's backslash.
A high surrogate followed immediately by `\u` requires scanning all four
hexadecimal digits of that second escape before checking the pair. If those
digits are malformed or truncated, report that lexical error at the offending
byte or EOF, not the first escape's backslash. If the second escape is complete
but is not a low surrogate, report the first escape's backslash. A complete
high surrogate without an immediately following `\u`, or a low surrogate
without a preceding high surrogate, reports its own backslash. This includes a
complete high surrogate at EOF; it does not reinterpret a later unrelated
escape before reporting the unpaired surrogate. An escape that is itself
lexically incomplete or malformed retains the ordinary lexical error location.

These exact byte witnesses define the diagnostic convention. Offsets
are zero-based; the hex column is authoritative and includes no trailing newline.


| Input bytes in hex | P-SYNTAX byte | Reason |
| --- | --- | --- |
| `225c756438303022` | 1 | Complete high surrogate without a pair. |
| `225c75643830305c753030343122` | 1 | Complete second escape is not a low surrogate. |
| `225c756463303022` | 1 | Unpaired low surrogate. |
| `225c7564383030` | 1 | Complete unpaired high surrogate at EOF. |
| `225c75643830305c7122` | 1 | No following `\u`; the later escape does not replace the surrogate error. |
| `225c756438473022` | 5 | Invalid hexadecimal digit in the first escape. |
| `225c75643830` | 6 | First escape truncated at EOF. |
| `225c75643830305c753030473122` | 11 | Invalid hexadecimal digit in the candidate second escape. |
| `225c75643830305c753030` | 11 | Candidate second escape truncated at EOF. |
| `22e25822` | 2 | Invalid UTF-8 continuation. |
| `22e282` | 3 | UTF-8 sequence truncated at EOF. |
| `22c3a95c756438303022` | 3 | High surrogate after the two-byte scalar U+00E9. |
| `22c3a95c75643830305c753030343122` | 3 | Complete non-low second escape after U+00E9. |
| `22c3a95c756463303022` | 3 | Low surrogate after U+00E9. |
| `22c3a95c75643830305c753030473122` | 13 | Malformed candidate second escape after U+00E9. |
| `22c3a9e25822` | 4 | Invalid continuation after U+00E9. |
| `22c3a9e282` | 5 | Truncated UTF-8 sequence after U+00E9. |

No parsed tree exists after syntax failure; preservation can still copy the
raw input.

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
No operation invents child absences beneath a malformed parent. For inspect,
exchange and lossyExchange, dependency child states are emitted only when the
entire dependencies value satisfies Dependency[]. Otherwise the whole value is
opaque and only its unchecked parent state is emitted, even if some elements
are individually well-shaped. This condition takes precedence over the shared
D-boundary row below. Validation operations retain per-record dependency checks
and states for individually well-shaped records; they do not make the entire
dependencies array opaque merely because another element is malformed.

| Scope | States recorded |
| --- | --- |
| Every operation with a parsed primary object | graphs and runtime: absent when missing; unchecked when present but opaque to this operation; declared when present and interpreted by G or R. No child states under an absent container. |
| D boundaries, used by every operation including inspect/exchange/lossyExchange | Unknown at each null dependency sha256 in a well-shaped Dependency. Unchecked at each external target pointer /relations/i/target in a well-shaped Relation, without looking up its content. No states inside runtime. |
| G only | Unchecked at each external Ref whose target-dependent checks are excluded in validateG; no internal R states. Resolved target evidence is represented by checks/results, not a synthesized state tree. |
| R only | The runtime states defined below. |
| inspect/exchange/lossyExchange dependency inventory | At /dependencies record absent if the primary parsed object lacks that member, declared if the full Dependency[] grammar is satisfied, unchecked if present but malformed, primary parsing failed, or the parsed root is not an object. When malformed, retain the entire /dependencies value as one opaque slice; when parsing failed, no JSON slice exists. These states are inventory observations, not validation findings. |
| Required resolveG annexes | Apply D states to each annex with its own input id. The G-only row retains its validateG condition; resolveG adds no unchecked State for a transitive Ref in a selected payload or relation. Report that resolution limit through checks/findings. No graph or runtime internals of annexes are inventoried. |

In particular validateD or inspect of runtime:{} records unchecked at /runtime
and its opaque slice, with no /runtime/selected state. ValidateR of that value
fails its missing configurations field shape and does not invent selected state
under the malformed RuntimeDeclaration. States are compared as sets including
input/pointer/state; only the runtime assessment details specified below are comparison keys.
Other detail prose and array order are not comparison keys.

Declared definitions/relations are the source tree itself, not a synthesized
normalized graph. Opaque slices are the maximal unexamined JSON values for the
requested unit: D opaque fields defined in [D](document.md), G/R unselected payloads/containers,
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
| G-TARGET | Graph ControlFlow key/type/uniqueness; local typed Refs, selected payload refs, Agent exposure/principal and selected Operation Action agreement, Resource/approver duplicate refs; affected Graph, Step or selected payload record. External target-dependent parts excluded in validateG. |
| G-PATH | Unique step ids, entry/successor existence, acyclicity, reachability, terminal paths; Graph record, one failure for any defect. |
| G-DATA | Port-map agreement, binding names/types, success-edge availability; Step record. Call pre-invocation availability failure at any gate points to approval Step. |
| G-APPROVAL | Call link, chain structure, sole approved incoming edges, no refusal bypass; affected approval Step, final incoming-edge defect at final approval Step. |
| G-RESOLVE | Missing required annex, invalid annex/rootKey, cross-document selected-key collision, missing/unexported/wrong-kind external target fails; unknown declared hash inconclusive; transitive selected Ref unsupported; dependency record for artifact issue, consuming Step for target issue. |
| R-SELECTION | Configuration ids unique; selected exists; graph Key selects one Graph and ControlFlow. Later duplicate Configuration or affected Configuration; bad selected at RuntimeDeclaration. |
| R-BINDING | Exact Agent coverage and kinds, duplicate claim Editions and requires, engine requirement declaration structure. AgentBinding; missing AgentBinding at Configuration. |
| R-TOOL | Required Tool coverage, typed Tool Action, Tool payload shape, duplicate failures/requirements and Implementation claim Editions, choice ids and selection; ToolBinding, missing binding at AgentBinding, later duplicate Implementation, selected Tool payload record for its semantic defect. |
| R-CONTENT | Typed content, exact reachable set, required applications present, prerequisite order/cycles, payload requirement duplicates and typed Skill tools. Application; missing application at AgentBinding; cycle at affected Skill payload. |
| R-COMPATIBILITY | The [selected configuration assessment](runtime.md#declared-compatibility-not-readiness). AgentBinding or ToolBinding; one finding per location/outcome after the aggregation defined below. |
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
Graph, but not local type/target checks. All validators implement
these same rules; no user-selected arbitrary subset produces a unit pass.

## Rule execution and exact exclusion records

Only the following rule sets execute. An operation's incidental parsing or
shape probing for inventory does not add findings outside this matrix.

| Result unit and operation | Rules executed |
| --- | --- |
| D for validateD or a validation prerequisite | P-SYNTAX, P-SHAPE for D, every D-* rule, X-MODE for validateD. |
| G for validateG | P-SHAPE for interpreted G fields, X-MODE for validateG, G-TARGET, G-PATH, G-DATA, G-APPROVAL. D prerequisite owns syntax and D findings. |
| G for resolveG | Same G rules plus G-RESOLVE; required annex D results own their D rules. Annex G results run P-SHAPE for selected payloads and G-TARGET only. |
| R for validateR | P-SHAPE for R, X-MODE for validateR, R-SELECTION, R-BINDING, R-TOOL, R-CONTENT, R-COMPATIBILITY. |
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
are not allowed in a report for this edition.

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
for resolveG, G-RESOLVE at /graphs. X-MODE still runs. An empty graphs
array has no subjects and completes these rules with []; resolveG still checks
any explicit requiredFor resolveG dependencies. To preserve that requirement,
G-RESOLVE also completes or fails its dependency portion when graphs is absent,
while its graph portion is excluded. Runtime selection and assessment exclusions are specified below.

External target-dependent local G checks excluded in validateG use the consuming
Step location in G-TARGET or G-DATA, as applicable. Their declaration/type checks
still complete where observable. D external relation targets need no lookup
Check: D-REFERENCE completes its declaration scope and inventory records each
relation's target pointer unchecked. External R Refs similarly complete their
declaration checks and record the Ref field unchecked; target-dependent checks
are excluded at the requesting record. These do
not imply resolved content. An opaque value produces a slice, not extra rule ids.

In resolveG, an external Ref inside a selected annex payload or relation is
outside direct resolution. Its target-dependent G-TARGET portion is excluded
at the affected payload or relation record in the annex G Result. For example,
a selected Operation Action Ref at /definitions/0/payload/operations/0/action
uses the Check location /definitions/0/payload/operations/0. Observable declaration/type checks still complete.
The primary G Result records G-RESOLVE unsupported at each consuming Step and
excludes that Step's G-TARGET agreement portion when it needs the transitive
target. Independent port checks still run. An otherwise valid annex G Result
can pass with that exclusion; the primary G Result remains unsupported.
The exhaustive State table adds no state for this resolveG exclusion.

For a cross-document selected-key collision, the primary G Result records
G-RESOLVE fail and G-TARGET blocked at the consuming Step for identity-dependent
agreement. Completed portions remain recorded for independently observed
checks, including annex payload checks and primary port-map checks. A selected
payload observable within its identified annex is interpreted, so it has no
opaque Slice at the payload record solely because of the collision.

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

## Runtime rule execution

Known structural violations fail their named rule. Incompatible assessment gives
R-COMPATIBILITY fail; not-provided/unknown give inconclusive; declared-supported
completes without a finding. Preserve independent fail and inconclusive findings
when both occur at one binding. Unknown support is not unsupported interpretation:
unsupported remains reserved for the extension/direct-resolution limits.
Known local target missing/wrong kind fails the owning R rule at the requesting
record. Duplicate or malformed identity blocks dependent lookup; no first/last
winner. Direct dependency declarations obey D, including integrity and accounting.

P-SHAPE owns every malformed field/parent in the interpreted scope, even for
unselected configurations. R also shape-checks observed reusable payloads at their
source records. In this edition validateR observes only primary payloads; it
emits no annex R Result. Partial checks retain completed only for observed
checks or known empty domains; affected-record blocked/excluded locations follow
the location rules above. A missing container needed for enumeration blocks at its existing parent,
not an invented absent child. Syntax failure blocks the whole requested unit.

Missing runtime excludes P-SHAPE and all R-* at /runtime, X-MODE still runs.
Empty configurations completes structural R rules. Missing selected excludes
R-COMPATIBILITY at /runtime, as no configuration assessment was requested.
A present selected with malformed/ambiguous target blocks R-COMPATIBILITY there.
Unselected configurations do not exclude structural rules. Empty subjects within
a readable selected configuration complete the applicable rule. External R refs
complete declaration checks and exclude target-dependent checks at their
requesting record; missing direct bytes do not make R a resolved operation.
G resolves only its direct target closure, not R configuration content.

## Runtime inventory

The R-only row consists of these exhaustive states, only under well-shaped
parent records:

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
  unchecked with detail exactly blocked. These assessment details are comparison keys; other detail prose remains ignored.

The configurations remain in the source tree. Engine/Application/Implementation parameters are opaque JSON, including those
of a selected Implementation. R interprets observed
Tool/Instructions/Skill payload fields defined in [R](runtime.md); no opaque slice covers their
whole record after interpretation. Their free text fields and parameter JSON
remain maximal opaque values at their own pointers. All unselected definition
payloads retain their opaque slices. External payloads have no invented slices.
G does not interpret any R payload solely because runtime names it.
