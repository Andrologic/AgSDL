# Independent implementation-readiness review

- Status: non-normative review; no proposal or decision is accepted here.
- Date: 2026-09-04
- Base commit: `3fac3138764102705099e4166268b08838c737a1`
- Scope: proposals 0001 through 0004 and dependent passages in 0005 through
  0010. Existing review conclusions were not used as evidence.

## Result and limits

The proposals support conceptual inspection, but do not yet close a contract
that two independent third-party processors could implement and claim as AgSDL
conformance. This is consistent with [Decision 0001](../decisions/0001-specification-before-syntax.md),
[Decision 0002](../decisions/0002-version-0.0.1.md), and the empty normative
specification described in [spec/README.md](../../spec/README.md).
[Decision 0003](../decisions/0003-repository-boundary.md) permits reference
tooling without accepting the proposed semantics.

This review tests the proposed rules together. A conflict between proposals is
not a defect in an adopted language. The witnesses below are descriptions of
small conceptual graphs, not syntax, fixtures, or runtime tests. Binding
findings concern what the repository proposes, not independent verification of
the external protocols or claims that an adapter exists.

| Question | Finding | Classification |
| --- | --- | --- |
| Complete system using exclusively imported Agent definitions | The System ownership minimum rejects it. | Demonstrated restriction; intent needs confirmation. |
| One Action occurrence with distinct authorization requirements at several points | The occurrence cannot directly retain all corresponding decisions under the current relation limit. | Demonstrated representation conflict; no general impossibility of multi-point execution is proved. |
| Coherent Principal and Identity | The core permits distinct actor and identifier records; proposal 0004 defines Principal as an identity. | Terminological conflict, with a separate underspecified Identity relation. |
| Earlier conformance levels alongside implementation features | The mandatory level claim has no defined interpretation in the feature model. | Unreconciled requirement, not proof that features and all possible levels are logically incompatible. |
| Incomplete fragment before resolution | The intent and binding procedure exist; applicability of mandatory core relations by phase remains incomplete. | Missing common validation rule, not missing fragment support. |
| Third-party reading, validation, and exchange | Useful obligations exist, but their normative input and result contracts do not. | Deliberate pre-draft incompleteness and remaining semantic decisions. |

## Minimal witnesses

### 1. A system whose only Agent belongs to a package

Let a Package version own and export one fully described Agent. A System uses
that definition and exposes its interface. Give the System a local control-flow
definition so that the generic minimum of one owned Definition is satisfied.
There is no locally created Agent and no missing dependency.

[Proposal 0002, Ownership, use, and containment](../../proposals/0002-core-conceptual-model.md#ownership-use-and-containment)
preserves the imported Agent's original lifecycle owner. Its
[Relationship model](../../proposals/0002-core-conceptual-model.md#relationship-model)
requires `System owns Agent` with `1..*` targets. The System owns zero Agents,
so this graph fails that row. Transferring ownership would violate the reuse
rule. Creating a wrapper Agent changes the supplied system and cannot be
assumed to be an editorial repair.

This proves a restriction, not a universally inconsistent model. Systems with
a locally owned Agent remain possible. [Proposal 0001, REQ-010 and UC-003](../../proposals/0001-requirements-and-use-cases.md#mandatory-requirements)
motivate package composition but do not explicitly promise that every System
may have zero locally owned Agents. The restriction might be intentional.

An external A2A endpoint is a different case.
[Proposal 0006, Agent Card boundary](../../proposals/0006-a2a-1.0-external-binding.md#agent-card-boundary)
explicitly forbids inferring an internal Agent definition or complete System
from a card. An Agent Card does not supply the imported Agent in this witness.
[Proposal 0010, Materialized import boundary](../../proposals/0010-open-agent-specification-binding.md#materialized-import-boundary)
does supply a relevant composition case: a generated Fragment owns locally
mapped Agents, and external AgSDL definitions retain their source owner.

### 2. Two authorization points for one occurrence

Let one protected Action have two Policy application points. Each has a
different Authorization requirement. One acting Principal attempts the Action
once on one Resource. Both points permit it before the same governed Effect.

[Proposal 0002, Action and effect](../../proposals/0002-core-conceptual-model.md#action-and-effect)
allows multiple application points, and
[Cross-cutting invariant 6](../../proposals/0002-core-conceptual-model.md#cross-cutting-invariants)
requires each point to obtain its required decision. In the
[Relationship model](../../proposals/0002-core-conceptual-model.md#relationship-model),
each Authorization decision satisfies exactly one Authorization requirement.
The witness therefore needs two decisions. Yet one Action occurrence has at
most one `authorized by` target.

The direct representation of both decisions as authorization of this occurrence
is impossible under those cardinalities. One decision applying several Policies
does not solve the witness: its two Authorization requirements are distinct.
Splitting the attempted operation into two Action occurrences changes the
witness. An aggregate decision or an indirect evidence association could solve
the representation problem only with additional meaning that is not defined.

There is a narrower reading: both points run, but the occurrence links only one
decision and an execution trace records the other. The present prose does not
explicitly require every decision to be an `authorized by` edge. Consequently,
this is not proof that execution through several points is impossible or that
every such graph is inconsistent. It proves that complete per-occurrence
authorization accounting is not closed by the stated relations.

[Proposal 0009, Checkout and payment separation](../../proposals/0009-agent-payments-protocol-binding.md#checkout-and-payment-separation)
distinguishes mandate presentation, checkout, credential release, submission,
and payment processing. Different decisions for these different Actions are
not the witness above. The binding also permits reuse at another point only
under the same Authorization requirement and the external contract's rules.
Its payment flow is not, by itself, evidence of this conflict.

[Proposal 0005, Multi-turn exchanges](../../proposals/0005-mcp-binding-profile.md#multi-turn-exchanges)
requires reconsideration near the effect and correlates retry messages. It
does not settle the core relation between several decisions and one Action
occurrence. [Proposal 0007, Interface roles and operations](../../proposals/0007-agent-user-interaction-protocol-binding.md#interface-roles-and-operations)
defines attempts and denied pre-attempt checks in its own context. Those rules
must not be replaced by an assumption that every protocol request is the same
Action occurrence.

### 3. One actor, two scoped identities

Let an Agent definition have a definition identifier. Let its Principal have
two scoped identities, with one chosen as the acting identity for a particular
Action occurrence. [Proposal 0002, Principals, identities, and authentication
evidence](../../proposals/0002-core-conceptual-model.md#principals-identities-and-authentication-evidence)
allows this: a Principal has one or more identities, and an occurrence has
exactly one acting Principal identity. The definition identity remains
distinct. Multiple identities are therefore not inherently contradictory.

The same section defines Principal as an actor and Identity as an identifier.
[Proposal 0004, Terms](../../proposals/0004-trust-security-and-control.md#terms)
instead defines Principal as a human or machine identity. Taken as exact common
definitions, these disagree. Aligning the latter wording with the actor
distinction is a safe terminological correction, provided it adds no ownership,
authentication, or authority rule.

There is a separate uncertainty in proposal 0002's `Agent represented by
Identity` row, which has exactly one target and exactly one inverse source.
The row does not say whether this is the Agent's definition identity or a
Principal identity. Reading it as a definition identifier allows the witness.
Reading it as the complete set of acting identities would impose another
restriction. That interpretation cannot be settled by capitalization alone.
Changing the row's meaning or cardinality requires review.

Bindings preserve rather than eliminate this distinction:

- [Proposal 0005, Authorization](../../proposals/0005-mcp-binding-profile.md#authorization)
  separates Principal, Identity, credentials, authentication, and authority.
- [Proposal 0006, Messages](../../proposals/0006-a2a-1.0-external-binding.md#messages)
  rejects inference of a Principal from a protocol-side label.
- [Proposal 0007, Interface roles and operations](../../proposals/0007-agent-user-interaction-protocol-binding.md#interface-roles-and-operations)
  allows an event without endpoint identities to remain external data or a
  Trace record, while refusing the Message occurrence mapping.
- [Proposal 0008, Role mapping](../../proposals/0008-a2ui-format-binding.md#role-mapping)
  permits an external endpoint Principal without inventing an Agent.
- [Proposal 0009, Role mapping and separation](../../proposals/0009-agent-payments-protocol-binding.md#role-mapping-and-separation)
  keeps non-agentic protocol-role mappings in the extension. Absence of such
  roles in the core table does not prove absence in this binding.
- [Proposal 0010, Component dispatch and Agent mapping](../../proposals/0010-open-agent-specification-binding.md#component-dispatch)
  preserves source component identifiers without promoting them to Principal
  identities, and records unresolved mandatory Agent relations.

### 4. A consumer claiming one reading feature

Consider a consumer that only reads metadata and claims an implementation
feature for that operation, with a version and bounded evidence.
[Proposal 0003, Consumer conformance](../../proposals/0003-conformance-and-versioning.md#consumer-conformance)
explicitly permits this. Its [Proposed conformance model](../../proposals/0003-conformance-and-versioning.md#proposed-conformance-model)
proposes no universal level and forbids publishing feature identities before
their normative scope is stable.

[Proposal 0001, REQ-009](../../proposals/0001-requirements-and-use-cases.md#validation-and-conformance)
still requires descriptions and processors to state a claimed conformance
level, and its traceability entry refers to a tested level. No rule identifies
the level for this consumer or equates a level with a feature set. The proposals
cannot supply a determinate combined claim contract as written. This is not
proof that all possible level systems contradict feature sets: an explicit
translation could allow both. It would be a substantive reconciliation of a
mandatory requirement, not merely a word substitution.

### 5. A fragment with one missing mandatory relation

Let a Fragment own and export an Agent with all other mandatory facts,
including behavioral direction, definition identity, and Principal relations,
but no Interface relation. It declares an Unresolved requirement
identifying that Agent, the missing relation, expected target kind, and the
condition for satisfying it. Nothing is fetched.

[Proposal 0002, Document roots](../../proposals/0002-core-conceptual-model.md#document-roots)
allows unresolved requirements in fragments without a synthetic System.
[Proposal 0003, Document conformance](../../proposals/0003-conformance-and-versioning.md#document-conformance)
separates unresolved-document validation from resolved-graph validation.
[Proposal 0010, Materialized import boundary and Agent mapping](../../proposals/0010-open-agent-specification-binding.md#materialized-import-boundary)
specifically proposes the missing-relation procedure in this witness and
requires failure if the binding cannot represent it.

The core Agent invariant and relation table nevertheless require at least one
Interface without explicitly assigning that minimum to a validation phase.
Proposal 0003 requires all applicable structural requirements at the unresolved
phase, but does not define which relation minima can be deferred by an
Unresolved requirement. A binding mapping report alone is explicitly
insufficient under proposal 0010.

The desired unresolved fragment is supported in intent; a common rule for its
positive initial verdict remains undefined. This differs from a valid external
reference declaration whose target has not been fetched. Proposal 0003 already
explains that distinction and requires a failed resolved-graph verdict for an
unavailable required reference. It does not follow that every incomplete
fragment is invalid, nor that every missing relation may be deferred.

### 6. Two independent readers exchanging a fragment

One processor reads the previous fragment offline and preserves an optional
unknown extension. Another receives the exported artifact, checks its declared
dependencies, and asks for an unresolved-document verdict only.

[Proposal 0001, REQ-006 through REQ-020](../../proposals/0001-requirements-and-use-cases.md#mandatory-requirements)
supplies coverage, dependency accounting, resolution, preservation, and loss
obligations. [Proposal 0003, Unknown information](../../proposals/0003-conformance-and-versioning.md#unknown-information)
requires operation-specific classification and preservation or a loss report.
Its [Conformance suites](../../proposals/0003-conformance-and-versioning.md#conformance-suites)
requires normative traceability. These are useful proposed contracts, so saying
that third-party processors have no guidance would be a false positive.

They still cannot derive one implementable AgSDL contract. There is no adopted
input language, stable normative feature scope, complete phase applicability
rule, or exact aggregate-verdict rule. Proposal 0003 explicitly leaves verdict
aggregation and normalization open. For example, reporting preservation loss
does not by itself determine an overall pass or fail; the loss report and
verdict remain separate. This review does not fill those gaps with an API,
serialization, diagnostic code set, or new aggregate status.

## Five decisions for maintainer review

These are alternatives for later work, not accepted decisions. Identity wording
can be corrected separately; resolving the meaning of the Agent Identity row
is a dependency of the fifth decision rather than an assumed correction.

| Decision | Minimal alternatives and recommendation | Work that depends on it | Work that can proceed |
| --- | --- | --- | --- |
| D1. Must a complete System own an Agent locally? | Retain the restriction and document it, or permit all-imported Agent composition while preserving source ownership. Recommend permitting that composition; the exact participation relation still needs review. | System minimum requirements, package composition verdicts, complete imports under 0010. | Provenance review and examples of fragments that retain source ownership. |
| D2. How does one occurrence account for every required authorization point? | Permit multiple directly associated decisions, or define an explicit aggregate or indirect accounting contract. Recommend direct accounting for distinct requirements; do not assume that a shared Policy implies a shared decision. | Complete authorization evidence, multi-point validation, related trace requirements. | Review of distinct Actions and their individual decisions in AP2 and other bindings. |
| D3. What replaces or interprets the mandatory level claim? | Revise REQ-009 around feature and profile claims, or retain levels with an explicit mapping and scope. Recommend the feature model already developed in 0003. | Claim completeness, requirement traceability, comparable processor evidence. | Inventory of operation-specific obligations, without minting feature identifiers. |
| D4. Which missing relations can remain valid before resolution? | Define phase-specific deferral through explicit unresolved requirements, or require structurally complete definitions and keep incomplete material outside a positive document verdict. Recommend explicit deferral consistent with 0010, with the permitted cases reviewed. | Incomplete fragment verdicts, import completion, composition and resolver checks. | Inspection of declarations and separate reporting of missing facts without a positive conformance claim. |
| D5. What is the first normative third-party operation contract? | Select a bounded reading, validation, and exchange scope, or postpone conformance claims until a broader model is adopted. Recommend scoping that contract before implementation claims, without selecting syntax here. | Stable feature contracts, phase rules, preservation and loss semantics, agreement on verdicts. D3 and D4 and the Identity-row interpretation affect the selected scope; D1 and D2 apply when their constructs are included. | A non-normative requirements inventory and reference-tooling reports that identify inputs, covered checks, and unknowns. |

## Safe wording changes and semantic changes

Safe editorial work can align proposal 0004's Principal definition with the
actor/identifier distinction in proposal 0002, use `Principal identity`
consistently when that meaning is already explicit, and replace ambiguous
references to a profile with its already established configuration or
conformance qualifier. No source edits are made by this report.

Changing ownership or authorization cardinalities, giving the Agent Identity
row a previously unspecified interpretation, retiring mandatory level claims,
allowing missing relations to satisfy an initial validation phase, or defining
aggregate verdicts changes meaning. These require proposal review and maintainer
validation. Binding-specific support and existing safeguards should survive
that work; table omissions alone are not grounds to redesign the core.

The next reviewable artifact can be a list of the exact requirements affected
by D1 through D5, with the witnesses above retained as acceptance questions.
That work does not require a new language design or a claim of implementation
readiness.
