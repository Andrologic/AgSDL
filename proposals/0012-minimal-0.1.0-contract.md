# Proposal 0012: minimal candidate contract for 0.1.0

- Status: proposed, awaiting maintainer choices; no normative adoption.
- Date: 2026-09-05.
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
not published feature identities or an executable specification. Review the
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
candidate details; approval must identify rows accepted, amended or deferred.

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

## Candidate JSON representation for D

Use one JSON object, UTF-8 without BOM, no duplicate member names at any depth,
no invalid Unicode scalar values, no non-JSON numeric values. Core numbers are
integers from 0 through 9007199254740991; opaque payload numbers are retained as
source text and not interpreted by D. Object member order has no meaning;
array order is retained, with ordering semantics only where stated. No aliases,
implicit conversions, defaults, includes or executable expressions are read.
Unknown members outside `annotations`, `payload` or `extensions` fail the
candidate shape check. This does not permit hidden extensions in core fields.

The envelope requires `contract`, `root`, `definitions`, `relations`, `exports`,
`dependencies`, `unresolved` and `extensions`. Arrays may be empty subject to
checks below. `annotations` and `evidence` are optional opaque JSON values;
`graphs` and `runtime` are optional containers for G and R. D inventories those
two containers and reports their contents unchecked. `evidence` retains
occurrence and artifact material without validating its semantics or collapsing
it into definition records. Prototype `contract` is exactly
`proposal-0012-candidate-1`; adoption would replace it with the agreed immutable
edition. It is not a claim to the unreleased specification version `0.1.0`.

A key is exactly `{scope, id, version}`, each a nonempty Unicode string.
Compare decoded scalar sequences exactly, case-sensitively, without Unicode,
URI, path or numeric normalization. Version is opaque and exact, never a range
or `latest` selector. Equality compares all three components; kind is checked
separately. Within one document, a scope/id pair has one version and one record,
including its root; duplicates fail even if identical. Across dependencies,
different versions may coexist and each reference selects one exact tuple.
No compatibility follows from version order.

`root` requires `key` and `kind`, one of `System`, `Fragment`, `PackageVersion`.
It has no owner. Every `definitions` record requires `key`, `kind`, `owner`,
`payload`; `owner` equals the root key. All local keys share the root scope.
Optional `annotations` and `provenance` are retained. `kind` uses exact entity
names from 0002, with multiword names joined without spaces, such as
`ControlFlow`; only identity, ownership and relation declarations of kinds
outside the local Agent checks are validated by D. Unknown kinds require an
extension declaration, otherwise fail shape validation. `payload` is opaque
for D and cannot override the record key, kind, owner or relations. Deeper
kind invariants, including Principal identity content, remain unchecked by D.
Root payload and annotations are optional and likewise opaque.

A `relations` item requires `source`, `relation`, `target` and `expectedKind`.
Source is a local key including the root. Target is exactly a key for local
references, or `{dependency, key}` for external references; `dependency` names
one dependency entry. Presence of that wrapper determines locality, never URI
shape. `expectedKind` is a nonempty kind name. Local lookup is unique and its
kind matches. Relation names below supply the fixed candidate checks:

| Relation | Source and target constraint in D |
| --- | --- |
| `actsAs` | Agent to Principal; exactly one per local Agent. |
| `exposes` | Agent to Interface; at least one per local Agent, except the single permitted deferral. |
| `directedBy` | Agent to Instructions, Role, Skill or ControlFlow; at least one per local Agent. |
| `uses` | Any local source to a declared kind; System-to-Agent participation is inventoried without certifying System completeness. |
| `contains` | Any local source to a declared kind; local containment graph is acyclic. |

Ownership is encoded only by `owner`; there is no second `owns` edge or Identity
record for the same Agent key. Duplicate relation tuples fail. Other semantic
relations require extensions in this candidate subset. An `exports` item is a
local definition key; no duplicate or missing exports. Fragment exports at
least one; System exports are empty; Package version exports may be empty.
These explicit encoding restrictions narrow 0011 rather than adopting all of
0002's relation table. Information outside the encoding can be preserved as
original evidence or a declared extension, not silently treated as validated.

A dependency entry requires `id`, `rootKey`, `status`, `requiredFor`, `sha256`.
IDs are nonempty and unique; `rootKey` is exact. Status is `included`,
`external`, `omitted` or `unavailable`. `requiredFor` is an array drawn from
`validateD`, `resolveG`, `exchange`, with no duplicates. `sha256` is 64 lowercase
hex characters for the exact dependency bytes. Optional `location` is a
nonempty opaque string, never a fetch instruction. The only resolution policy
is the caller-supplied artifact map keyed by dependency id. No relative base,
registry discovery, secret resolution or network access is inferred. External
target keys have the dependency root's scope. D checks declarations and hashes
of supplied bytes, not dependency internals. `included` without supplied bytes
fails dependency accounting; an unfetched `external` target remains unchecked.
A missing required target fails a requested resolved-graph check. Hashes provide
content identity, not authentication. Imported records are never copied locally.

A permitted `unresolved` entry has exactly `subject` as a local Agent key,
`obligation: "agent-interface-minimum"`, `rule: "fragment-interface-deferral"`,
`relation: "exposes"`, `expectedKind: "Interface"`, `missingMinimum: 1`,
`target` as a key or explicit null, `satisfyBy: "typed-exposes-relation"`, and
`expiresBefore: "resolved-graph"`. Null means unknown target identity.
It applies only where no exposes relation exists; one entry per missing
obligation, no stale or duplicate entries. All other missing covered facts
fail. A later composition must record the supplied relation and its provenance
in a new artifact; it cannot rewrite the original Fragment's validation history.
The first candidate does not define an overlay or composition language.

## Unknown information, exchange and diagnostics

An extension envelope has exactly `identity` as an owner-qualified nonempty
string, `version` as an exact nonempty string, `operations` as an object and
`payload` as opaque JSON. Operations are `validateD`, `validateG`, `validateR`;
each requested validation operation needs an entry `required`, `unknown`, or
`{ignoreRule: key}`. An ignore rule is usable only if the processor implements
that exact rule and it proves which portable meaning remains for this operation.
An unsupported required extension yields unsupported; absent classification or
unknown applicability yields inconclusive. It is not a known shape violation
merely because interpretation is unavailable. Extension payload never changes
core meaning silently. `annotations` alone has a candidate core rule that it
cannot affect identity, reference, graph, runtime or authority meaning and may
be ignored in validation. This rule, not an optional flag, permits continuation.

Exact exchange returns the original artifact bytes unchanged, with each supplied
annex in its original boundary. Compare bytes directly; hashes identify report
inputs. Whitespace and unknown payloads survive. Inventory dependencies by
status and actual delivery. Copying a known invalid artifact can succeed while
validation fails. This is a preservation consumer operation, not a producer
conformance claim under 0003. Recommend excluding lossy output in 0.1.0:
requested loss is refused with a prospective loss report before any output.
Each loss names artifact hash, location, information, reason and absent or
applicable permission. No normalization or round-trip semantic claim follows.

Reports contain processor identity/version, candidate edition, operation,
primary artifact hash, annex hashes, unit, phase, input-boundary inventory,
extension support, checks, findings, deferred obligations and exclusions.
For parsed JSON, locations are JSON Pointer strings; parse failures use
zero-based UTF-8 byte offsets. A finding contains artifact hash, location,
rule/category, outcome and evidence. Candidate categories are `syntax`,
`shape`, `identity`, `owner`, `reference`, `integrity`, `cycle`, `agent-minimum`,
`deferral`, `extension`, `graph`, `runtime` and `preservation`; these are not
stable diagnostic codes. Compare category, rule, location and outcome between
implementations, not prose or ordering. Publish exact rule identifiers only
with the later normative inventory and fixtures.

For each requested unit/phase, retain all findings and aggregate known failure
before unsupported required checking, then inconclusive evidence, then pass.
Pass needs every applicable check completed or a permitted D deferral. A parse
failure stops dependent checks and records them unperformed. Unrequested units
have no verdict. D uses unresolved-document only; G's requested resolved-graph
verdict is separate and bounded to G dependencies and checks, not all of 0002.
No successful structural or exchange result supplies execution evidence.

## Candidate G: simple control flow

Conceptual example: accept text, invoke a drafting Agent, read its Boolean
`needsReview`, ask a human about one proposed publish action when true, then
invoke that action and finish. False bypasses publication and returns the draft.
Refusal ends as denied; timeout or invalid input ends as failure. Two sequential
Agent invocations use the same rules. A single Agent needs no synthetic topology.

Recommend a finite acyclic graph with one entry and one active step. Every step
is reachable from entry and every path ends at a terminal. Step kinds are
`invoke`, `condition`, `approval`, `end`; their explicit successor labels below
are exhaustive. No implicit next step, parallel branch, arbitrary cycle, retry,
model-selected transition or general expression evaluation exists in G.

Each graph has a local ControlFlow `definition` key, `entry`, `inputs`, `outputs`
and `steps`. Step ids are unique nonempty strings scoped to that graph.
I/O contracts are finite maps from port names to `string`, `boolean` or `json`.
All declared inputs/outputs are required; undeclared ports fail. `json` accepts
any JSON value but has no selector or implicit coercion. A binding is a graph
input port or a prior step output port, both identified explicitly; matching
types must be equal. Only invoke steps produce step output ports. The producing invocation must
dominate its consumer, and every path to that consumer must traverse the
producer's `success` edge. Its `failure` edge makes none of its outputs
available. These rules apply to end-step output bindings as well. No ambient
state or merge inference supplies a value.
G validates these static properties without invoking a participant.

| Step | Candidate content and outcomes |
| --- | --- |
| invoke | Agent reference, its Interface reference, input/output port maps, bindings for all inputs, `success` and `failure` successors. The Interface must be exposed by the Agent. Success requires all output values; missing/ill-typed output takes failure without partial outputs. |
| condition | One Boolean binding, `true`, `false`, `failure` successors. Only literal Boolean values select true/false; missing or non-Boolean value takes failure. No truthiness or expression string. |
| approval | ApprovalRequirement reference, protected immediate successor invoke id, bindings identifying proposed Action definition, Resources, requesting Principal and material context; positive integer `timeoutMs`; `approved`, `denied`, `failure` successors. Approved targets that protected invocation. |
| end | Outcome `success`, `failure` or `denied`, no successors. Success binds all graph output ports; failure/denied emit no success output and name a nonempty reason. |

Recommend that an approval step dominates its protected invocation. The only
incoming edge of that invocation is this step's `approved` edge; neither its
`denied` nor its `failure` path may reach the protected invocation. The
ApprovalRequirement identifies allowed human
Principal definitions, presented context, approve/deny decisions and expiry.
Its decision is scoped to one request and proposed Action/context and expires
at the earlier of its stated expiry or the graph timeout. No response at the
deadline, expired/mismatched evidence or inability to establish validity takes
failure; a valid denial takes denied. There is no default approval, reuse for
later actions or implied Authorization decision. Other required authorization
checks remain separate and must still be mediated by an external runtime.
Validation checks the declarations and edges, not human identity or enforcement.
Execution evidence formats and mediation coverage require a later reviewed
runtime mapping before anyone claims executable approval support.

Graph I/O is an additional G contract for the named Interface invocation; it
does not infer or validate every Interface operation invariant in 0002. Require
explicit agreement of supplied Interface I/O declarations with the invoke port
maps before a resolved G pass. Missing external Agent/Interface/approval content
fails that phase. D can still pass its reference declaration checks. G
unresolved-document checks cover local shapes, paths and local type evidence;
unobserved external type agreement is listed unchecked, never as established.
The JSON spellings for G are design candidates to be completed with an exact
field inventory after C8 review, before schemas or two-implementation claims.

## Candidate R: open runtime declarations

Recommend `runtime` as a declaration object with `requirements` and optional
`selection`. Each requirement identifies an exact owner-qualified capability
contract/version and its required subject definition key. Capabilities describe
needs such as session resumption or mediation of a specified effect; no vendor
name proves a capability. These examples mint no capability identities.

`selection` identifies exact engine and interface identity/version strings,
separate optional model identity/version, provider identity, hosting reference,
and evidence references for each requirement. There is no vendor enum or
inference between those fields. An absent selection is valid documentary input,
recorded as unselected. An unknown custom engine is retained as declared, with
support unassessed. A custom engine contract may remain undefined; naming it
does not establish capabilities or compatibility.

A future deployment assessment records each requirement as satisfied,
unsatisfied or indeterminate against versioned evidence, separate from R's
structural result. Missing selection or evidence cannot yield readiness. A
known gap is unsatisfied; unknown support is indeterminate. No automatic
fallback or degradation is proposed. Session, streaming, cancellation, ambient
configuration and approval behavior need exact interface coverage as outlined
in the [runtime research](../docs/research/runtime-engine-interfaces.md).
R's final field grammar and capability contracts remain adoption prerequisites;
R does not prescribe an implementation or execute an engine.

## Candidate D example and refusal variants

This example is a complete D candidate Fragment, not a conforming AgSDL artifact.
Principal and Instructions payload semantics remain unchecked by D.

```json
{
  "contract": "proposal-0012-candidate-1",
  "root": {"key": {"scope": "example", "id": "drafting", "version": "1"}, "kind": "Fragment"},
  "definitions": [
    {"key": {"scope": "example", "id": "agent", "version": "1"}, "kind": "Agent", "owner": {"scope": "example", "id": "drafting", "version": "1"}, "payload": {}},
    {"key": {"scope": "example", "id": "author", "version": "1"}, "kind": "Principal", "owner": {"scope": "example", "id": "drafting", "version": "1"}, "payload": {"identities": [{"scope": "team", "id": "author"}, {"scope": "review", "id": "author"}]}},
    {"key": {"scope": "example", "id": "instructions", "version": "1"}, "kind": "Instructions", "owner": {"scope": "example", "id": "drafting", "version": "1"}, "payload": {"text": "Draft a reply."}}
  ],
  "relations": [
    {"source": {"scope": "example", "id": "agent", "version": "1"}, "relation": "actsAs", "target": {"scope": "example", "id": "author", "version": "1"}, "expectedKind": "Principal"},
    {"source": {"scope": "example", "id": "agent", "version": "1"}, "relation": "directedBy", "target": {"scope": "example", "id": "instructions", "version": "1"}, "expectedKind": "Instructions"}
  ],
  "exports": [{"scope": "example", "id": "agent", "version": "1"}],
  "dependencies": [],
  "unresolved": [{"subject": {"scope": "example", "id": "agent", "version": "1"}, "obligation": "agent-interface-minimum", "rule": "fragment-interface-deferral", "relation": "exposes", "expectedKind": "Interface", "missingMinimum": 1, "target": null, "satisfyBy": "typed-exposes-relation", "expiresBefore": "resolved-graph"}],
  "extensions": []
}
```

Candidate D result is pass with the Interface obligation separately deferred.
Remove its declaration: fail `agent-minimum`. Change the root to System and
clear exports: fail `deferral` and the unsatisfied minimum. Add a dangling local
exposes edge: fail `reference`, not a permitted missing minimum. Duplicate the
Agent record: fail `identity`. A valid external Interface declaration without
retrieval can pass D, with content unchecked; requesting G resolution with that
required artifact absent fails its separate phase. Exact copying of each
invalid variant can still pass exchange, never producer conformance.

## Blocking choices, compatibility and delivery

Before adoption, record acceptance or amendment of C1-C10. In particular:

- 0011 excludes resolved graphs; G adds a separately bounded operation. It
  cannot be presented as silently expanding 0011 or certifying System validity.
- The Identity interpretation and encoded-owner restriction need reconciliation
  in adopted model text. They are recommendations, not prior editorial fixes.
- G approval semantics need the maintainer's agreement on one-action scope and
  timeout/refusal behavior. They do not settle execution evidence or authority.
- The exact G/R field inventories, Interface I/O representation, diagnostic rule
  inventory and capability contracts must be written and reviewed after scope
  selection. Until then G/R are concrete conceptual contracts, not parser-ready.
- Execution conformance is outside the proposed structural delivery evidence.
  Any later execution claim requires a reviewed general contract and observed
  runs; no particular product supplies or determines portable semantics.

Adoption would create the first bounded syntax, not compatibility with an
existing AgSDL codec. No framework mapping or execution-equivalence promise is
made. Unknown content and references are untrusted data; validation neither
loads code nor grants authority. Byte retention can retain sensitive source
material, so an exchange consumer must use the caller's authorized artifact
boundary rather than discover additional files.

The [delivery plan](../docs/plans/2026-09-05-0.1.0-delivery.md) orders approval,
normative work and independent evidence. Completion of this proposal means the
maintainer can choose a concrete scope. It does not mean 0.1.0 is finished.
