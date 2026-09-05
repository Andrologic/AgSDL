# Proposal 0011: first reading, inspection, and exchange contract

- Status: proposed candidate for maintainer review
- Date: 2026-09-05
- Depends on: Decision 0004 and proposals 0001 through 0003

## Problem and authority

Two readers need a shared answer to what a description declares, what is
missing, and what survives exchange. Requiring either reader to implement all
agent behavior, policy semantics, or framework bindings would prevent a useful
first contract. A reader that only inventories definitions must also avoid
presenting its limited checks as proof that an entire System is valid.

[Decision 0004](../docs/decisions/0004-approved-design-directions.md) approves
preparing this bounded contract. It does not approve the choices below. This
proposal selects candidate inputs, checks, and outcomes for review before
normative adoption. It publishes no implementation-feature identity, version,
certification, syntax, diagnostic code, or API. No current processor can derive
an AgSDL conformance claim solely from this proposed contract.

## Candidate scope

The proposed contract covers declaration reading, structural inspection,
unresolved-document validation of the scope below, and preservation during
exchange. The subjects are a supplied artifact, a consumer performing one of
those operations, a validator checking the selected scope, and a producer
exchanging the supplied artifact. Implementations may support these operations
separately, with the coverage and evidence required by
[proposal 0003](0003-conformance-and-versioning.md#proposed-conformance-model).
REQ-009 remains a capability to express a claim, not a duty to publish one.

The candidate validation scope is fixed for this proposal:

- the root form, definition inventory, lifecycle ownership, exports, and
  declared dependencies of the supplied document;
- scoped definition identifiers, declared kinds and versions, local references,
  and external-reference declarations;
- declared ownership and containment edges, including local cycle checks;
- for each local Agent, its definition Identity, Principal definition relation,
  Interface relation minimum, and presence of a behavioral-direction relation;
- extension boundaries, operation-specific requiredness, and declarations of
  missing obligations affecting these checks.

All definitions and their declared references in the supplied document enter
the inventory. Root records are included; occurrence records may be inventoried
but their own relations and invariants are not validated by this scope. An
operator cannot omit an inconvenient local Agent from this scope and still
claim its validation result. Checks on Agent targets require their
identity, kind, version, and reference declarations, but do not recursively
activate all invariants of each target kind. For example, the Interface
operation-to-Action contract and Policy evaluation are outside this scope.
Those exclusions are reported, not labeled satisfied or deferred.

An inspection may read a broader description containing Tools, Actions,
Policies, deployment facts, or execution records. Their declared presence,
locations, and relationships may be shown without interpreting their payloads.
A positive result covers only the fixed scope above. It is neither full
unresolved-document conformance under proposal 0003 nor proof of validity for
the complete AgSDL graph. Reading a System root does not certify System
completeness. Runtime instances and occurrences remain distinct from
definitions even when they share a label.

Excluded operations are external retrieval, graph composition, resolved-graph
validation, normalization, rewriting semantics, framework conversion, execution,
deployment assessment, authentication verification, and authorization decisions.
Exchange here transfers information already supplied. It does not supply or
verify missing components. AGS or another editor could be a consumer of a later
adopted contract; this proposal defines no editor or other-project contract.

## Inputs and minimum facts

Each requested operation identifies the supplied artifacts, their exact
revisions or content identities, the requested operation, the rule edition
being evaluated, extension support, and the observed input boundary. Candidate
reviews identify the proposal revision rather than invent an AgSDL version.
A future conformance operation would require an adopted specification version.

Reading and inspection may return a partial inventory when those facts are
missing. They must distinguish absent declarations, explicitly unknown values,
unsupported interpretation, and information they could not observe. Such a
report is not a positive validation result.

For positive validation of this scope, the supplied material must expose:

| Information | Candidate minimum and covered check |
| --- | --- |
| Document root | Exactly one System, Fragment, or Package version root, with identity and declared root form; a fragment root never causes creation of a System. |
| Local definitions | Every local definition's scoped identifier, kind, version identity, location, and exactly one lifecycle owner of the kind required by proposal 0002's document-root rules. The root identifies the ownership boundary; it does not own itself. |
| Exports and edges | A Fragment exports at least one definition. Preserve every declared export and each definition reference's source, relation, target, and local or external status; each local target exists uniquely and has the expected kind and compatible declared version. |
| Ownership and containment | Their declared edges, unambiguous owners, and no cycle in the supplied local graph. Imported declarations retain source ownership; a use or containment edge does not transfer it. |
| Dependencies | Identity, delivery status, expected kind, applicable version constraint, and whether each dependency is required for the requested operation; included, externally referenced, omitted, and unavailable remain distinct. |
| Local Agents | Exactly one definition Identity relation and one Principal definition relation, at least one Interface relation or permitted deferral, and at least one declared direction through Instructions, Role, Skill, or Control flow. |
| Extensions | Owner-qualified identity, version, payload boundary, and requiredness for the operation; an optional extension identifies the portable fallback and its governing rule. |
| Missing obligations | The affected scoped definition, governing obligation and proposed deferral rule, relation, expected target kind, known target identity or explicit absence, missing cardinality, and condition for satisfaction. |

Local reference checking covers declaration integrity and kind matching, not
the truth of all statements inside the target. Candidate version checking uses
exact equality with an explicitly supplied version identity. Any other
compatibility relation needs an identified rule supported by both readers;
without one, the compatibility check is inconclusive. Numeric order alone
proves nothing.

Dependencies supplied as separate artifacts are inventoried with their own
source boundaries. They do not become local definitions of the requesting
document. Checking the document's external declarations does not certify those
artifacts; validating another document requires a separate scope result.

A declaration outside the named validation scope can be inventoried as missing
without becoming an additional covered obligation. A required unknown that
could alter a covered check prevents a positive result, even if its payload is
outside the scope. A producer cannot obtain a narrower verdict by hiding that
dependency or marking it optional without an applicable rule.

## Identity and provenance

The recommended interpretation of proposal 0002's Agent-to-Identity relation
is the Agent's definition identifier, distinct from identities of its Principal.
This is a choice for maintainer validation, not a correction already accepted
in proposal 0002. Under this choice, an Agent with one definition identifier
and a Principal with two scoped identities does not violate the Agent's
exactly-one Identity relation. Recommend also retaining the inverse of one
Agent per such definition Identity, so distinct Agents cannot share it in the
same scope. Both choices require review. The reader neither chooses an acting
identity nor infers authentication or authority from these declarations.

The candidate structural checks require unambiguous definition identifiers
and scopes before reference checking. Equal labels in different scopes do not
merge definitions. Equal identifiers in the same scope do not select an
arbitrary winner. The precise external representation and comparison rules for
scopes remain an adoption prerequisite.

For every supplied definition and relation, preserve whether it was local to
the source, imported, or supplied by an overlay. Where a transformation created
it, retain the source artifact and version, source location or reference chain,
and mapping or overlay provenance actually supplied. Missing provenance is
reported as unknown; the reader must not invent it. A known provenance conflict
affecting source identity or ownership fails the corresponding covered check.
Unverified provenance is not proof that the asserted source is authentic.

An imported Agent keeps its source lifecycle owner. Participation in a System
is recorded separately and does not imply local ownership. A System using only
imported Agents is therefore not rejected for having no locally owned Agent.
Participation uses the proposed System-to-Agent use relation. This limited
verdict still does not validate all System participation, interface, or
completeness requirements.

## External references without implicit retrieval

A reference declaration identifies its source and expected target, target kind,
version constraint, resolution base and policy, permitted resolver sources, and
integrity information required by the governing rule. The candidate exchange
rule requires an immutable target identity or declared integrity evidence for
an external dependency needed to reproduce a covered check. A mutable location
alone may be inspected and preserved but cannot meet that requirement.

No reading, inspection, validation, or exchange operation in this contract
fetches a target, resolves a secret, loads extension code, or executes supplied
material. Explicitly supplied dependency artifacts enter the observed input
boundary, with their provenance; their presence is not a claim that resolution
or whole-graph validation occurred.

A well-formed external Interface reference already supplies a declared relation.
Its unretrieved target is different from an absent Interface relation and needs
no missing-relation deferral. The report marks target content and availability
unchecked. Invalid local reference declarations fail their covered checks.
An integrity mismatch detected in supplied content is a failure, not a
permitted missing fact. A later resolved-graph operation under proposal 0003
would fail for any unavailable required target; this contract offers no such
operation or verdict.

## Candidate deferral inventory

The following inventory is deliberately narrow and remains proposed. It applies
only to unresolved-document validation of this contract's scope, through
[proposal 0003's phase mechanism](0003-conformance-and-versioning.md#validation-by-phase-and-declared-missing-obligations).
It supplies no general permission for a binding to postpone all mandatory facts.
The Interface exception covers the concrete incomplete-Fragment witness in
the readiness review while retaining the Agent's addressable definition and
declared actor. This is a scope choice, not a claim that Principal deferral
could never be designed safely.

| Obligation | Candidate treatment and conditions |
| --- | --- |
| Local Agent exposes at least one Interface | Permit a missing minimum only in a Fragment root document. The Agent must otherwise meet every covered check. One explicit Unresolved requirement must identify that Agent, relation, expected Interface kind, missing minimum of one, any known target constraints, and satisfaction by a correctly typed Interface relation. The allowance expires before resolved-graph validation. |
| The same Interface minimum in a System or Package version root document | No allowance in this first inventory. Inspection and preservation remain possible; a known missing minimum fails this scope's validation. Package-specific allowances may be proposed separately. |
| Definition identity, kind, version, and lifecycle owner | No deferral. Ambiguous or absent required identity, conflicting or missing owner, and ownership or containment cycles fail the covered checks. |
| Agent represented by Identity and acts as Principal definition | No missing-relation deferral. The interpretation above is a maintainer choice; this inventory does not make it accepted. A valid external Principal reference may remain unretrieved. |
| Agent behavioral-direction presence | No deferral. At least one correctly declared relation to Instructions, Role, Skill, or Control flow must be present; interpreting its behavioral content remains outside this scope. |
| Local-reference integrity, external-reference declarations, extension boundaries, and requiredness | No deferral. A missing or invalid required declaration cannot be replaced by an Unresolved requirement. Unknown applicability prevents a positive result. |
| Supplied contradictions or detected integrity failures | No deferral or relabeling as missing information. Report the failed covered check. |
| Other mandatory obligations | No additional deferrals authorized here. An obligation outside this scope is reported as unchecked, never as satisfied by this inventory. |

The Interface exception does not allow a dangling local reference, a wrong-kind
target, or a contradictory supplied relation. It covers absence of the minimum
only. A report must retain the missing obligation even when this phase passes.
Later satisfaction records the supplied relation and provenance; it does not
retroactively assert that the source artifact contained it.

An import under [proposal 0010](0010-open-agent-specification-binding.md#materialized-import-boundary)
may declare more missing facts than this inventory permits. For example, an
locally materialized Agent without a Principal relation can be inventoried and
preserved, with a failed candidate scope verdict. Declaring its missing Principal remains useful.
A mapping report or retained incomplete artifact does not itself claim a
positive phase verdict or require deletion of the incomplete material.

## Unknown information and preservation

Requiredness is relative to an operation and its governing rule. An unknown
extension that changes identity comparison prevents positive validation of
identity checks. The same payload may be preserved during exchange without
understanding that comparison. Exact preservation cannot stand in for a
semantic check that the requested operation requires.

Follow [proposal 0003's unknown-information rules](0003-conformance-and-versioning.md#unknown-information).
An optional label alone is insufficient: continuing a covered operation needs
an applicable rule making the information ignorable and identifying the
portable meaning that remains. If requiredness itself cannot be determined,
the semantic operation is inconclusive and cannot succeed by assumption.
Inspection may still report the payload's location and the unanswered question.

The candidate default exchange operation preserves the complete supplied
artifact exactly, including uninterpreted content and its original context.
It preserves the declaration of an external dependency, not unfetched target
content. The exchange report inventories included, externally referenced,
omitted, and unavailable dependencies. A receiver checks that inventory against
the material actually received before claiming package completeness.

The first contract proposes preservation in the original artifact context,
without moving definitions or changing identifiers. For example, if supplied
occurrence evidence associates one Action with two Authorization decisions,
exchange retains both associations and their application-point context. It
neither aggregates them nor creates an occurrence for a pre-attempt decision.
Those checks establish retention only; authorization accounting and permission
remain outside this validation scope.

A separately requested lossy exchange may omit only information an applicable
rule permits to be omitted for that exchange operation. It reports each loss
by original artifact and location, affected information, reason, and governing
permission before producing output. All remaining content, identities, versions,
owners, references, and provenance must be preserved without reinterpretation.
An output that drops a covered mandatory fact fails output validation. If
required or preservable unknown content cannot be retained and no omission
permission applies, refuse the exchange and issue a loss report; issuing the
report alone does not authorize output.

The source validation result, exchange result, loss report, and any output
validation result are separate. Exact exchange of a known invalid artifact may
succeed as preservation, while its structural verdict remains failed. Lossy
exchange cannot claim exact preservation. No exchange result establishes
behavioral equivalence. The representation needed to demonstrate exact
preservation remains to be selected before implementation claims.

## Results, coverage, and candidate verdict rules

Each report identifies the processor and version, operation, exact inputs,
rule edition, phase when applicable, fixed validation scope, extension support,
checks performed, and exclusions. It associates each finding with the artifact,
location or scoped subject, relation when applicable, rule, evidence, and
outcome. It lists permitted deferrals and checks not performed separately.
A textual finding is sufficient for this proposal; no stable code is minted.

The following aggregation is a candidate for this scope only, not a replacement
for proposal 0003's unresolved global aggregation rules:

1. A known violation of any applicable covered rule makes the scope verdict
   fail. Preserve all known findings, including unsupported or unobserved checks.
2. With no known violation, an unsupported required interpretation or check
   makes the verdict unsupported. Missing evidence or undetermined rule
   applicability makes it inconclusive if no required check is unsupported.
3. A positive scope verdict requires every applicable covered check to succeed
   or be an expressly permitted deferral meeting every declaration condition.
   A deferred obligation remains unsatisfied for later graph validation.
4. An operation not requested has no verdict. An interrupted or incomplete
   check contributes no positive evidence. Successful inventory production
   proves only production of the stated inventory.

For exchange, success means all required preservation and dependency-accounting
checks succeeded and each permitted loss was reported. Otherwise refuse the
requested exchange; retain its findings even when a partial inspection report
can be returned. This operation result never changes a source validation
failure to a pass. Unsupported and inconclusive outcomes both prevent a
positive validation or exchange claim; their distinction explains the cause.

## Conceptual acceptance and refusal witnesses

These witnesses assume adoption of the candidate choices above. Today they are
review questions, not executable fixtures or evidence of AgSDL conformance.

| Supplied case and requested operation | Expected candidate result |
| --- | --- |
| Fragment owns an Agent with all covered facts and exports it; local references resolve uniquely. | Scope validation passes. Deeper behavior and target-kind invariants remain unchecked. |
| That Agent lacks only its Interface relation and carries the complete permitted declaration. | Scope validation passes with the obligation listed as deferred; no resolved-graph verdict. |
| The same missing Interface belongs to a System root document, or the Fragment declaration lacks the affected Agent identity. | Scope validation fails; no applicable allowance or valid declaration. |
| The Agent has a dangling local Interface reference and labels it unresolved. | Scope validation fails. The missing-minimum exception does not excuse an invalid supplied reference. |
| The Agent has a valid immutable external Interface reference; no target is fetched. | Local declaration checks may pass; target content and availability remain unchecked. No claim of a resolved graph. |
| Two local definitions have the same scoped identifier, or one local Agent has two lifecycle owners. | Scope validation fails even if both records are marked unresolved. |
| An imported Agent retains its package owner and is the System's only participant. | No failure for absence of a locally owned Agent. System completeness remains outside this verdict. |
| One Agent definition identifier, one Principal relation, and two scoped Principal identities. | The Agent Identity check passes under the recommended interpretation; no acting identity or authority is inferred. |
| A materialized import creates a local Agent lacking its Principal relation but records the missing fact. | Scope validation fails; inspection and exact preservation may succeed with that failure retained. |
| An optional unknown annotation has a supplied governing rule allowing it to be ignored for validation, and is preserved in context. | It does not prevent scope validation; exchange makes no interpretation claim. |
| An unknown required extension changes identifier equality. | Positive validation is unavailable, with unsupported interpretation reported; exact preservation can still be considered separately. |
| A version constraint has no shared compatibility rule, or extension requiredness is indeterminate. | With no known failure or unsupported required check, validation is inconclusive. |
| Exchange would drop an unknown required policy payload without an omission permission. | Refuse exchange and report the prospective loss. Existing structural results remain separate. |
| Requested lossy exchange omits a presentation note under an explicit permission. | Exchange may succeed with a separate loss report; exact preservation is not claimed. |
| A receiver is told a required dependency is included but the delivered material lacks it. | Dependency-accounting check fails. Do not claim complete exchange or full validation. |
| Supplied immutable dependency content fails its declared integrity check. | Covered integrity check fails, regardless of an earlier valid reference declaration. |

## Traceability and consequences

REQ-001, REQ-002, and REQ-005 motivate the declaration inventory and identity
checks. REQ-006 through REQ-009 require bounded validation and inspectable
claims. REQ-011 through REQ-020 govern dependencies, versions, references, and
unknown extensions. REQ-037 and REQ-038 motivate provenance and preservation
accounting. This scope implements no blanket claim to satisfy those entire
requirements; excluded operations and checks remain visible.

A reader can implement the inventory and selected reference checks without
implementing every Tool, Policy, or runtime construct. The cost is a deliberately
limited positive verdict. Even a fully preserved System can have unchecked
behavioral or structural defects outside this scope. The single deferral keeps
the first Fragment witness testable without making every incomplete import
eligible for positive validation.

## Alternatives considered

Full-model validation would offer a broader guarantee but require many unsettled
contracts and make basic reading depend on runtime and binding semantics.
Opaque copying alone would preserve bytes but give reviewers no agreed
inventory or account of missing dependencies. Arbitrary caller-selected check
subsets would make positive results incomparable; the proposed scope is fixed.
Allowing all declared missing relations to pass would contradict the explicit
permission boundary approved in Decision 0004. Refusing every incomplete
artifact would unnecessarily prevent useful inspection and preservation.

## Choices required before adoption

The maintainer must review the exact scope, single Interface deferral, excluded
root cases, non-deferrable obligations, Agent Identity interpretation, and
operation-specific verdict rules above. None follows automatically from D5.

Two independent readers still need the following settled before they can
reliably produce the same results:

- A shared input representation, payload boundaries, locations, and exact
  preservation comparison. Recommend selecting these after scope approval;
  this proposal supplies no parser contract or serialization.
- Exact scope and identifier equality, including version identities and
  duplicate declarations. Recommend explicit scopes and exact comparison with
  no implicit merging, alias inference, or version ordering.
- A complete normative inventory of the covered checks, permitted target kinds,
  declaration constraints, and phase applicability. Recommend adopting only
  the bounded scope above first, with excluded target invariants explicit.
- A rule for establishing that an unknown payload cannot alter covered meaning
  and may be ignored or omitted for a given operation. Recommend relying on
  an identified, supported governing rule, never the author's optional label
  alone. Until that evidence exists, the relevant check cannot pass.
- A preservation and loss result representation, with the candidate precedence
  of failure, unsupported checks, missing evidence, and success made normative.
  Findings must survive aggregation. General AgSDL verdicts remain separate.
- Shared positive, negative, and inconclusive fixtures for every covered check
  and the witnesses above, after the representation is chosen. Repository
  maintenance checks do not substitute for this evidence.

The first review approves, revises, or rejects these candidate choices. A later
adoption step would place the agreed requirements in `spec/`, then define
representation and executable evidence. This proposal alone establishes no
language compatibility or implementation support.
