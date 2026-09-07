# D: document declarations

[Specification index](README.md).

| Record | Fields |
| --- | --- |
| Document | `contract:"agsdl-0.1.0"`, `root:Root`, `definitions:Definition[]`, `relations:Relation[]`, `exports:Key[]`, `dependencies:Dependency[]`, `unresolved:Deferral[]`, `extensions:Extension[]`, `annotations?:JSON`, `evidence?:JSON`, `graphs?:JSON`, `runtime?:JSON` |
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
Interface/ApprovalRequirement payloads; R interprets runtime and its reached
Tool/Instructions/Skill payloads. Thus `graphs:17`
can pass D, fails G shape, and is still preserved exactly. Unsupported G is not
unknown D core syntax. Extra members inside a G-interpreted payload fail G,
while unrelated payloads remain opaque. No declared scope may silently shrink
to avoid a local Agent failure.

## Dependencies, unknowns and extension handling

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
within the same boundary are allowed. A collision does not erase observations
inside an identified annex. When its dependency id and key select one exported
definition of the expected kind within that annex, inspect the selected payload
and its locally resolvable references. Keep its annex G Result and interpreted
payload boundary. Continue primary port checks that use those observable maps.
Comparisons that require an unambiguous identity across boundaries remain
blocked at the consuming Step, with no agreement or disagreement finding from
the ambiguous identity. This neither merges the definitions nor gives either
boundary priority.

Only direct primary dependencies are supported: when a selected annex payload
or relation needs an external Ref, report unsupported for that G check. No
transitive resolver, composition, overlay, profile application or cycle-breaking
policy exists here. An annex's D validation is required for resolveG and reported
separately; its own included dependencies cannot be supplied by the flat primary
map, so such an annex fails its accounting rather than triggering recursion.
Unused annex G/R containers remain unchecked. Imported ownership never changes.

The edition implements no semantic extension interpreter. For each requested
validation unit, required gives unsupported, unknown or absent classification
gives inconclusive. `ignoreRule:annotation-only` is a core permission:
the entire extension is a nonsemantic annotation for that unit and cannot
change core facts. A custom Kind declaration forces validateD required for its
extension; any other validateD mode on that extension fails classification.
This prevents an unknown kind from bypassing typed checks with an ignore label.
G uses validateG classification for both phases, R uses validateR; D prerequisite
classification remains independent. No extension code or ignore-rule definition
is loaded. Future semantic interpreters need a new edition contract, not an
implementation-specific pass in this one. The same closed ignore rule applies to every implementation.

Absence, explicit unknown, unsupported interpretation, excluded checks and
failed facts are distinct. Missing mandatory fields fail shape. Null permitted
hashes and unknown extension modes remain visible unknowns. No extension blocks
exact preservation merely because its interpretation is unavailable.
