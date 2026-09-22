# Proposal 0014: a smaller core for 0.2 discussion

Status: **PROPOSED, not adopted, not implemented.** All candidate rules below
are recommendations for maintainer arbitration, not additions to the current
contract. Publication remains 0.1.1 with contract `agsdl-0.1.0`; see the
[release status](../README.md#release-status-and-history). No 0.2 release marker
is allocated here. The sketches deliberately use `PROPOSED-0014` and are not
valid inputs to the current readers or schemas.

## Problem and scope

A single Agent should be understandable before selecting software to run it.
Two Agents should compose without duplicating facts already declared by their
interfaces. Changing engines should preserve Agent definitions, accountable
actors, content and graph meaning, while exposing incompatible choices.

The concrete [design examples](../docs/research/0.2-design-examples.md) cover a
single Agent, a two-Agent sequence, two configurations of that same sequence,
and a separate experiment reusing a small assembly twice. They are design
arguments, not execution evidence. Plan points 3 and 10 provide the usage basis
for recommendations in points 1 and 2 below. Reports belong to the separate
0015 work; this proposal states information a reader needs to communicate,
without defining report fields, aggregation, diagnostics or exit codes.

This is one proposed JSON representation for authors and exchange. There is no
second authoring language, expansion compiler, package manager or plugin loader.
No runtime, editor, network retrieval, dynamic delegation, recursive assembly,
hot modification or advanced orchestration is proposed for implementation.
Existing normative files, readers, fixtures and historical snapshots stay intact.

## Evidence and deductions

Repository facts come from [D](../spec/document.md), [G](../spec/graph.md),
[R](../spec/runtime.md), [identity rules](../spec/model.md), and the
[official examples](../examples/0.1.0/README.md). D requires one Principal link,
at least one behavioral direction and an exposed Interface per local System
Agent. A Role is one possible direction, not a mandatory kind. G repeats the
selected operation's ports and Action and the Agent's Principal at each invoke.
R already separates engine choices from definitions and forbids defaults and
inheritance. The example comparison distinguishes these obligations from
illustrative records and parameter values.

Deduction: reduce duplicate declarations first. Removing accountable actors or
call interfaces saves more characters but also removes information needed for
inspection. Moving security-sensitive declarations into a module saves little
unless that module's use remains explicit wherever the declarations matter.
The chosen direction follows the requested small, composable design philosophy;
it makes no new factual claim about Pi or any other external implementation.

## 1. Recommended minimum and identity boundaries

PROPOSED: the core describes one versioned document boundary, local Definitions,
exact typed references, accountable actors, Agent direction and explicit call
interfaces. Optional named semantic modules describe flow, engine bindings,
reusable skills and governed effects. A document describing only an Agent needs
no graph or engine. A description without an engine is not a runnable system.

A Definition identity is the tuple of document scope, local id and explicit
Definition version. Local ids are unique across kinds. A local `{"ref":"a"}`
selects that single Definition, with its explicitly declared version; it never
means latest. Document version and Definition version are independent. The
containing boundary is the lifecycle owner by a single core rule, rather than a
repeated `owner` field. This rule is identity scoping, not configuration
inheritance. Cross-document reuse is deferred from the minimum syntax, so local
references cannot trigger a search outside supplied bytes.

An accountable actor is a Principal Definition referenced by `actsAs` on the
Agent. It is neither the Agent's Definition identity nor a login or credential.
Keep it fixed when configurations change, following the distinction recorded in
[Decision 0007](../docs/decisions/0007-adopt-0.1.0-contract.md). A configuration is
a named complete selection of declared settings and engine bindings for a graph.
A step id identifies a static call site, not an execution occurrence. Actual
execution ids, invocation occurrences, authentication and state stay external.
The artifact hash and configuration id pin a prospective execution's selection.
Stop, edit and start a new execution when that pin changes; earlier approvals
cannot carry over. No in-flight modification or resumption semantics follow.

| Current notion | Proposed treatment | Reason and compatibility consequence |
| --- | --- | --- |
| Root, Key, owner | Keep boundary, Definition version and ownership; remove repeated scope/owner from local records and references. | Avoid repeating invariant facts. This is a new serialization, not a 0.1.0 alias. Conflicting old owners or multiple versions cannot be silently collapsed. |
| Principal / actsAs | Keep one explicit accountable actor per Agent in the minimum. Remove the repeated invoke Principal. | One Principal may be shared by several Agents when that is the author's claim. Identity is never inferred from an engine. Old mismatching invoke principals must be rejected during conversion, not repaired. |
| Role / directedBy | Keep explicit nonempty direction; use an ordered reference list of Instructions, or Skill when its module is required. Move opaque Role descriptions to descriptive metadata only when they carry no claimed semantics. | Role itself is not currently required. Existing Role-only or ControlFlow-only direction needs an explicit authored replacement with Instructions or Skill; migration is refused until that replacement is supplied. Moving ControlFlow into flow does not satisfy Agent direction. No conversion can invent instructions from either opaque payload. |
| Interface / exposes | Keep an explicitly selected Interface and operation, with ports and request/response direction declared once. | Even a single-operation Interface is not selected by default. Remove repeated call-site type maps; validate bindings against the referenced operation. An old disagreement is a conversion error, not information to discard. |
| Action / Resource | Move their declarations and call annotations to required `effect-scope` semantics wherever an author describes actions, resource scopes or approvals. | Their current payloads are opaque, but their identities anchor governance. Basic text transformations need no placeholder Action/Resource. Governed calls retain them; existing scope cannot be dropped in a migration. |
| ControlFlow / graphs | Keep an optional named flow module. Co-locate the graph with its Definition instead of repeating a ControlFlow key in a second container. | Core Agent descriptions do not require scheduling. Preserve explicit success/failure paths, typed bindings and acyclicity in the bounded sequence. This does not adopt nested graphs. |
| Instructions / Skill | Keep reusable Instructions in core; move Skill prerequisites, tool requirements and application order to `skills`. | Content identity and application point remain explicit. A Skill is behavioral content, not a callable subgraph. No recursive prerequisite closure or implicit application expansion. |
| Tool / Implementation | Keep the contract/implementation distinction in `bindings`; governed effects additionally require `effect-scope`. | Tool ports, effects and failures are not overwritten by an adapter choice. Unavailable implementations remain inspectable. |
| Configuration / AgentBinding | Keep complete explicit per-Agent selections in `bindings`; permit references to complete immutable local settings and binding records. | Sharing does not merge or override fields. Same Agent means same binding within a configuration, including repeated call sites. Missing selections remain missing. |
| CapabilityClaim / Application | Keep exact capability identities and explicit content application adapters in `bindings`. | Claims remain declarations, never proof of support or launch permission. Content cannot disappear because a selected engine lacks support. |
| ApprovalRequirement | Move with Action/Resource to `effect-scope`, dependent on flow for gates. | Preserve declared actors, context, scope, configuration pin and sequential approval meaning. No simplified approval syntax is adopted here. |
| Dependencies, exports, Fragment, PackageVersion, deferrals | Move beyond the minimum, pending a separately specified direct-import module. | Do not replace missing interfaces by defaults. Existing imports, exports, hashes and deferrals cannot be flattened automatically or treated as local ownership. |
| Model, Environment, Runtime, Deployment, Policy, Memory, Knowledge, State, Topology, Protocol | Move out of the core known-kind vocabulary; preserve descriptive material only when explicitly nonsemantic, otherwise require named semantics. | Current opaque payloads do not justify new behavior. No old record may be erased or reclassified by guesswork. |
| Extensions, annotations, evidence | Keep opaque preservation and explicit semantic requirement declarations. | Annotation labels cannot hide behavior. Unsupported interpretation differs from invalid structure and from unknown engine capability. |

Nothing is removed from the adopted contract by this table. Conversion would
require a separately reviewed mapping and retained source bytes. No automatic
upgrade, round-trip guarantee or lossless conversion is claimed. A proposed
0.2 basic sequence omitting effects is intentionally less expressive than a
0.1.0 sequence carrying Action/Resource/context; it is not its silent conversion.

## 2. Components, semantic modules and engine adapters

A reusable component is a named Definition or complete value record referenced
as data: Instructions, Interface, Skill, settings, binding, or the experimental
assembly. Referencing one neither installs code nor changes the language.

A semantic module is an exact identity/version whose published rules determine
how designated fields are interpreted and checked. An engine adapter is an exact
identity/version of a concrete implementation choice, with opaque native options.
Selecting `example/engine-a` or a private engine does not select a semantic
module, grant trust, or change portable meaning. The vocabulary is open; the
example identities are fictional, not an allowlist. There is no default engine.

PROPOSED dependency boundaries, with names provisional:

| Semantic module | Minimum dependency | Owns |
| --- | --- | --- |
| Core | None | Boundary, local identity, references, Principal, Agent, Interface, Instructions, opaque preservation and module declarations. |
| `flow` | Core | Static call sites, typed data bindings, success/failure paths. |
| `bindings` | Core + flow for graph configurations | Explicit configurations, complete settings/binding reuse, engines, Tool contracts, implementations, Applications and declared compatibility. |
| `skills` | Core; bindings when engine application is assessed | Acyclic content prerequisites, explicit ordered applications and declared Tool requirements. Tool bindings use bindings semantics. |
| `effect-scope` | Core + flow; bindings when configuration pins are assessed | Action/Resource annotations, context and sequential approval requirements. |
| `assembly-experiment` | Core + flow | Only the separate static assembly experiment, not recommended as a 0.2 commitment. |

Core Agent direction cannot use Skill unless `skills` is explicitly required.
A required module's prerequisites must also be explicitly listed at their exact
versions. Dependencies in this table do not authorize automatic loading or
insertion of missing declarations. There are no module version ranges or
compatibility inference. Names and final partitioning remain proposed; a future
module needs a complete contract and evidence before implementation claims.

PROPOSED reader behavior: retain an unknown module's bytes and report its exact
identity/version, location, required status and checks it prevents. A reader
that does not understand required `flow` can inspect the core and preserve the
document, but cannot claim to have validated the flow or the whole document.
Missing a declared prerequisite is a declaration defect; lacking an interpreter
is unsupported interpretation, not proof that the document is invalid. A known
bad reference remains a defect even when an independent module is unsupported.
Unknown semantic content cannot be ignored as annotation. Detailed report
encoding and outcome composition are intentionally left to the reports proposal.

Engine compatibility is a separate question. For example, an explicit
unsupported Tool capability makes the selected binding incompatible as declared;
it does not prove the document's structure invalid. An absent claim remains
unknown. Evidence hashes identify assertions, not verified execution evidence.
The incompatible choice, required Tool and content stay visible; no fallback,
removal or reselection is permitted. The examples retain this case explicitly.

### Sharing without hidden inheritance

PROPOSED: references select complete records. A settings reference supplies the
entire settings value; a binding reference supplies the entire binding value.
No inline overrides, deep merge, parent profiles, precedence search, placeholder
substitution or native-option translation are allowed. Different values require
a different complete record. Ordered content references remain explicit, including
prerequisites. Repetition can be meaningful, so there is no deduplication.

Portable settings have an exact format identity/version understood independently
of an engine. Native options stay on the engine binding. Two engines can use the
same settings only where their declarations and adapters support that settings
contract; reusing its id does not prove equivalence. Do not call temperature or
provider-specific prompt channels portable without such a contract. The sketches
use an explicit illustrative text-output contract and separate opaque options.

## 10. Assembly experiment and recommendation

The [separate assembly sketch](../docs/research/0.2-design-examples.md#assembly-experiment)
encapsulates two calls behind one explicit request/response interface and uses
it twice. It saves the repeated internal wiring but adds a boundary, port mapping,
call-site identity rules and failure propagation. Reuse is static, with no nested
assemblies, recursion, dynamic target, delegation or package resolution.

Recommendation: keep ordinary Definition/content/settings reuse in the proposal;
do not add assemblies to the recommended 0.2 minimum yet. Two invocations of the
same Agent do not need an assembly. Repeated multi-step units may justify one,
but this small example alone does not establish that its semantic cost pays off.
It is neither adopted functionality nor a delivery promise.

## Maintainer decisions needed before normative work

1. Is the explicit actor + direction + Interface minimum the right tradeoff?
   Recommendation: keep these facts, shorten their references. The single-Agent
   sketch shows its cost. Making Principal optional would leave the actor
   undeclared in some documents, without implying an absence of responsibility.
   Readers could not identify that actor from those documents; migration and
   governed-call requirements would need an explicit rule for that absence.
2. May basic flow omit Action/Resource/context while governed calls require the
   `effect-scope` module? Recommendation: yes only as an explicit new contract
   boundary, with no automatic conversion of existing scopes. The two-Agent
   sketch illustrates the reduced case; a protected search call would still
   declare its Action, Resource, context and approval requirements.
3. May complete settings and binding values be referenced across configurations?
   Recommendation: yes, without overlays. The two-configuration sketch shows
   shared settings and unchanged graph, including a deliberately incompatible
   Tool choice. A different native option needs a new binding record.

Retaining today's verbose serialization remains a viable alternative if these
tradeoffs are rejected. An Agent with only a prompt and an inferred engine is
shorter but loses explicit actor and interface facts. A general inheritance or
macro system could compress more text but would introduce another interpretation
problem. None is needed to assess the three decisions above. Assembly delivery,
import semantics and a full normative module grammar remain deferred rather
than extra adoption decisions hidden in this proposal.
