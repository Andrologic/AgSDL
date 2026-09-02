# Proposal 0005: Agent Payments Protocol binding extension model

- Status: proposed
- Date: 2026-09-02
- Target: post-0.0.1 binding model
- Depends on: Proposals 0002, 0003, and 0004
- External contract: AP2 `v0.2.0`

## Summary

This proposal defines how a future AgSDL description should reference, map,
and assess an Agent Payments Protocol binding. It covers AP2 roles, mandate
chains, trusted user decisions, constraints, receipts, deterministic
verification, and accountability evidence.

The binding keeps checkout and payment semantics in a candidate AgSDL
Extension. The portable AgSDL core continues to express delegation, approval,
authorization, policy, evidence, and responsibility without depending on AP2
or any credential format.

This proposal adds no normative syntax. AgSDL is a conceptual pre-draft, so it
does not create an AP2 adapter, payment capability, conformance result, or
interoperability claim.

## Problem

A protocol label and a signed mandate do not describe an agent payment system.
AP2 behavior depends on occupied roles, distinct trust models, exact mandate
types, a credential format, deterministic verification, open-to-closed
constraints, commerce and payment contracts, stateful replay controls, and
receipt evidence.

Several AP2 terms also overlap with AgSDL concepts. An AP2 role may be occupied
by a non-agentic principal, so it is not always an AgSDL Role. AP2 calls its
user authorization operation Mandate Delegation, but the signed credential is
not itself an AgSDL Delegation, Approval decision, or Authorization decision.
A receipt can prove a verifier's signed result without proving every external
effect or assigning legal liability.

Copying AP2 schemas into AgSDL would create a stale protocol fork. Treating AP2
as a general authorization model would make unrelated systems depend on a
payment-specific binding extension and on unfinished external credential work.

## Scope

This proposal covers:

- AP2 Binding requirements and an AP2 binding resolution;
- external contract identity for AP2 and its dependencies;
- role occupancy, role combination, and delegated verification work;
- direct and autonomous mandate authorization;
- Checkout and Payment Mandate mappings;
- consent and approval separation;
- constraint, budget, recurrence, replay, and revocation requirements;
- signed receipts, dispute evidence, trace correlation, and accountability;
- deterministic verification and failure behavior; and
- structural, resolution, deployment, and execution evidence.

It does not define payment rails, settlement, a commerce API, transport,
discovery, AP2 credential schemas, cryptographic algorithms, consent law,
dispute adjudication, or liability rules. It does not add support for the AP2
v0.1.0 Intent Mandate or Cart Mandate vocabulary to the v0.2.0 binding.

## Terms

An **AP2 binding extension** is the candidate extension contract defined by
this proposal. A future published instance has an owner-qualified identity,
independent version, compatibility policy, validation rules, portability
effect, and one portable System or Fragment definition that declares an AP2
integration as its target. Its payload references the external AP2 contract,
portable AgSDL definitions, and Binding requirements. It does not target or
contain a Resolved binding. When optional, it also defines or references the
portable meaning and allowed operations that remain without AP2 semantics.

This proposal does not publish the extension identity or version. Those values
must wait until AgSDL has normative extension syntax and stable target rules.
"AP2 binding extension" is neither a Configuration profile nor a Conformance
profile. A future Conformance profile may select tested AP2 implementation
features without changing this extension's document semantics.

An **AP2 binding requirement** is a portable binding requirement under the AP2
binding extension. It identifies the AP2 contract, required roles, mandate
types, credential and trust contracts, mapped AgSDL definitions and binding
requirements, verification duties, evidence requirements, and failure
behavior. It does not select a runtime instance, endpoint, key, or deployment
identity.

An **AP2 binding resolution** is a deployment assessment over the ordinary
Resolved bindings that satisfy the extension's Binding requirements. It is not
a new kind of Resolved binding. It records resolved external contracts,
Principal identities, trust roots, credential and key references, accounting
services, commerce and payment bindings, and known gaps.

An **AP2 role requirement mapping** relates one required AP2 protocol role to
portable Principal, Agent, Runtime, Environment, Interface, and binding
requirements. It preserves the role's duties without selecting a deployment
actor.

An **AP2 participant requirement mapping** applies the same separation to an
AP2 participant that is not one of the five roles, including a User, Network,
Issuer, payment initiation service provider, or Agent Provider.

An **AP2 resolved participant assignment** is part of an AP2 binding resolution.
It relates one role or non-role participant requirement mapping to the concrete
Principal identity, Runtime instance, or external endpoint selected by the
applicable Resolved bindings.

An **AP2 artifact mapping** relates an AP2 mandate, disclosure set, checkout
JWT, payment credential reference, or receipt to the AgSDL definitions and
occurrences it may support as evidence. It does not collapse the artifact into
those subjects.

An **AP2 constraint mapping** relates one exact AP2 constraint type and schema
version to an AgSDL Policy or Delegation condition, its evaluation inputs,
state dependencies, failure result, and evidence.

An **AP2 verification requirement** identifies the deterministic capability and
binding conditions, accepted external contracts, verification rules and inputs,
trust and time-source requirements, state dependencies, result contract,
failure behavior, and evidence required at one AP2 verification point. The
resolved binding selects the component that satisfies it.

## Proposed semantics

### Core and extension boundary

The AgSDL core should remain independent of AP2. It should express these facts
for payment and non-payment systems alike:

- Principal definitions and identity requirements for every user, agent,
  runtime, external system, approver, verifier, and accountable provider;
- Delegation definitions and occurrences for bounded delegated authority;
- Approval requirements, requests, and decisions for bounded human decisions;
- Policies, application points, Authority grants, Authorization requirements,
  and Authorization decisions for protected Actions;
- Resources, Actions, Effects, trust boundaries, credential references, and
  failure policies;
- immutable evidence artifacts, execution occurrences, causal relations, trace
  requirements, and evidence gaps; and
- Handoffs for responsibility transfer that does not grant authority.

The AP2 binding extension should target one portable System or Fragment
definition that declares an AP2 integration. Its payload adds payment-specific
contract references, role and participant mappings, mandate and receipt
mappings, constraint mappings, and verification requirements. The payload may
reference other portable definitions and Binding requirements without changing
their core kind.

A published extension instance declares its owner, version, required or
optional status, compatibility identity, validation rules, and portability
effect. An optional instance must define or reference a portable fallback that
states which non-AP2 meaning and operations remain valid when the extension is
not interpreted. A generic AgSDL processor may preserve that unrecognized
optional instance and continue only within the declared fallback. If no safe
portable fallback exists for an operation, the extension must be required for
that operation. A processor that does not understand a required instance must
report it and stop before the affected operation. A payment-aware processor
must also reject an AP2-required operation when it cannot interpret the whole
selected AP2 binding extension.

AgSDL should not define a generic Mandate entity. A signed external artifact
can support a Delegation occurrence, Approval decision, Authorization decision,
or observed Action result. Those subjects keep separate identities, rules, and
evidence scopes.

### External contract identity

An AP2 binding requirement should identify:

| Contract fact | Required identity |
| --- | --- |
| AP2 protocol | Exact release and immutable source identity, initially `v0.2.0` at commit `b4587ac1d055888a73b4b21750973cffba961793` |
| Mandate types | Exact `vct` strings and schema suffixes used by every open and closed mandate |
| Credential format | Exact SD-JWT VC, key-binding, selective-disclosure, and delegation contracts |
| User authorization | Exact OpenID4VP or other approved presentation contract and selected trust model |
| Commerce protocol | Separately versioned UCP or another contract that supplies checkout and role-to-role operations |
| Transport or agent protocol | Separately versioned binding such as HTTP, A2A, or MCP when used |
| Payment instrument and rail | External payment contract and identity rules required by the selected instrument |
| Constraint extensions | Owner-qualified type, schema, selective-disclosure rules, and deterministic evaluation algorithm |
| Receipt and dispute handling | AP2 receipt schemas plus external retention, retrieval, adjudication, and settlement evidence contracts where required |

The binding should treat the Delegate SD-JWT dependency and SD-JWT VC base
profile as unresolved until each has an immutable content identity. A mutable
repository URL or an unnamed credential profile may support authoring but
cannot support a reproducible resolved-graph verdict.

AP2 `v0.1.0` is a separate binding variant. Its Intent Mandate, Cart Mandate,
and A2A extension must not be accepted under a v0.2.0 claim. A future FIDO
edition is also a separate contract until an explicit compatibility assessment
and adapter suite establish a mapping.

The release SDK is another separate implementation identity. Its documented
Delegate SD-JWT deviation and arbitrary-depth chain support do not amend AP2
v0.2.0 or enable agent-to-agent mandate redelegation in this extension.

### Role mapping and separation

The current AgSDL Protocol model assigns sender and receiver positions to
AgSDL Roles, and an AgSDL Role is assigned only to an Agent. AP2 roles may be
occupied by non-agentic services or external systems. This extension therefore
keeps AP2 protocol-role labels in its own requirement mappings rather than
creating synthetic Agents or weakening the core Role invariant. A future core
model for non-agentic protocol participants may replace this extension-specific
mapping only through an explicit compatibility change.

Each required AP2 role should have one AP2 role requirement mapping. At the
portable level, the mapping should identify:

- the accountable Principal definition or constraints on that Principal;
- the Agent, Runtime, Environment, Interface, and binding requirements for the
  role;
- whether the role permits LLM participation in inbound communication,
  outbound communication, or processing;
- every deterministic verification capability required by the role;
- its protected Actions, Resources, trust boundaries, Policies, and Authority
  requirements;
- delegated work requirements; and
- required trace and evidence outputs.

The AP2 binding resolution should contain a corresponding resolved participant
assignment derived from ordinary Resolved bindings. It identifies the concrete
Principal identity, Runtime instance or external endpoint, verifier component,
key and credential references, and delegated provider. A portable mapping
cannot contain those deployment selections.

The Shopping Agent requirement may map to an Agent definition assigned an
AgSDL Role for shopping responsibilities. The Trusted Surface requirement maps
to a non-agentic Runtime binding requirement and human Interface, plus
constraints on the Principal that controls its signing operation. Merchant,
Credential Provider, and Merchant Payment Processor requirements may permit an
Agent or deterministic service. The applicable Resolved bindings select one
permitted form and report it rather than inferring it from the AP2 role name.

Network is an AP2 verification and receipt participant but is not one of the
five AP2 roles. A binding that uses a Network should include an AP2 participant
requirement mapping and resolved participant assignment for it. The same rule
applies to a User, Issuer, payment initiation service provider, or Agent
Provider whenever the selected flow depends on that participant.

When one resolved Principal occupies several AP2 roles, the AP2 binding
resolution should retain the separate assignments, duties, policy application
points, keys, and evidence. It should report whether the deployment preserves
or weakens intended separation of duties.

AP2 permission to delegate a role's responsibilities maps to a Handoff for the
work and, when protected Actions are involved, a separate Delegation and
Authorization requirement. The delegate assumes the AP2 verification duties of
that role. This does not enable mandate redelegation between Shopping Agents.

### Mandate and occurrence mapping

An AP2 artifact mapping should preserve the compact signed bytes and disclosed
claims used by the verifier. A decoded or normalized JSON object alone is
insufficient when AP2 hashes the encoded credential or checkout JWT.

The following mappings apply:

| AP2 subject | AgSDL mapping |
| --- | --- |
| User-authorized open mandate | Immutable artifact supporting an Approval decision and a Delegation occurrence that establishes bounded authority |
| Agent key in open mandate `cnf` | Proof-of-possession evidence for a separately mapped delegate Principal identity, not an Authority grant |
| Agent-signed closed mandate | Immutable artifact supporting a Delegation use occurrence and an Authorization decision for the exact closed Action |
| User-authorized closed mandate | Immutable artifact supporting an Approval decision and a transaction-bounded Delegation occurrence to the Shopping Agent; its later presentation supports a verifier's Authorization decision |
| Merchant-signed checkout JWT | External integrity evidence for the offered checkout Resource state |
| Checkout or Payment Mandate presentation | Message or protocol occurrence carrying the artifact, disclosures, verifier challenge context, and correlation identity |
| Payment credential or token | Protected opaque credential reference scoped to a payment Action and checkout, never an embedded secret or standalone Authority grant |
| Checkout Receipt | Signed immutable artifact supporting the Merchant's authorization result and observed checkout outcome within its evidence scope |
| Payment Receipt | Signed immutable artifact supporting the processor's payment result and any Effect occurrence only within its declared observation boundary |

Every mapped approval should identify what the Trusted Surface displayed, the
human Principal identity, decision, mandate content digest, time, expiry,
surface identity, signer identity, and applicable definition and policy
versions. The signature is evidence for that occurrence. It does not replace
the occurrence or prove the quality of the human decision.

In the Trusted Agent Provider trust model, a provider signature establishes the
provider's signed claim that it obtained user authorization. It does not, by
itself, establish an Approval decision by an identified human Principal. The
mapping records an evidence gap unless separate evidence identifies the human,
presented content, decision, time, and applicable versions.

Every mapped Delegation should identify the user or other delegating Principal,
Shopping Agent delegate, Actions, Resources, purpose, conditions, lifetime,
revocation, and redelegation rule. The authority cannot exceed the delegator's
own delegable Authority grant. AP2 mandate bytes do not establish that upstream
authority by themselves.

### Direct and autonomous modes

In direct mode, the final Checkout and Payment Mandates should each map to a
human Approval decision and a transaction-bounded Delegation occurrence to the
Shopping Agent for the exact Action and material context only when the evidence
requirements above are satisfied. A provider-signed mandate without that human
evidence records the provider claim and an Approval evidence gap instead. The
corresponding verifier still produces a separate Authorization decision. When
a Trusted Surface instead communicates directly with a non-agentic Merchant
and no Shopping Agent acts for the user, the description selects a separate
flow and does not invent a Delegation occurrence.

In autonomous mode, the user-authorized open Checkout and Payment Mandates map
to bounded Delegation occurrences. The later closed mandates map to use of
those delegations. The agent signature and key binding prove control of the
endorsed key and bind the presentation. They do not create a later human
Approval decision.

As an additional AgSDL safeguard, the binding should fail closed when it omits
an expiry Policy for an open mandate, the required agent binding, a constraint
needed for the mapped AgSDL Action, or revocation and state behavior required
by the effective Policy. AP2 recommends a short expiry but does not require a
portable duration or define the other lifecycle controls.

### Checkout and payment separation

The AP2 binding extension should model each request separately from the action
that fulfills it. Every mapping identifies the initiating Principal, acting
Principal, target Resource, policy application point, Authorization decision,
and possible Effects.

| AP2 interaction | Acting Principal and Action | Required separation |
| --- | --- | --- |
| Present Checkout Mandate | Shopping Agent presents authorization evidence and requests the purchase | The Merchant decides whether that Shopping Agent may request this checkout under the mandate |
| Complete checkout | Merchant commits or rejects the order | The Merchant acts under its own authority and Policy; the Shopping Agent request is the initiating occurrence |
| Present Payment Mandate | Shopping Agent presents authorization evidence and requests credential access or payment initiation | The Credential Provider or Network decides whether that Shopping Agent may use the payment authority for this checkout |
| Release payment credential | Credential Provider or Network releases a credential scoped to the checkout | The provider or Network is the acting Principal; the authorized Shopping Agent request is the initiating occurrence |
| Submit payment | Merchant or payment initiation service provider submits the scoped payment instruction or credential | This is distinct from the Shopping Agent's mandate presentation and from processing by the MPP |
| Process payment | Merchant Payment Processor accepts or rejects the scoped payment request | The MPP is the acting Principal; authorization, funds movement, and settlement remain distinct results |

The Checkout and Payment Mandates are cryptographically linked but support
different Delegations and Authorization decisions at different policy
application points. A permitted decision for one Principal, Action, or Resource
cannot satisfy another point unless the description identifies the same
Authorization requirement and AP2 permits that use.

The checkout, company or user account, payment instrument, merchant obligation,
and funds should remain separate Resources. Order commitment, credential
release, payment authorization, funds movement, settlement, fulfillment,
refund, and dispute outcome should remain separate Effects or observed states.
No AP2 success result should silently collapse them.

### Constraint mapping and state

Each AP2 constraint mapping should identify the exact mandate `vct`, constraint
type, schema, normative evaluation rules, mapped Policy or Delegation
condition, closed mandate fields, disclosed claims, comparison rules, and
result. A resolved implementation also identifies its evaluation algorithm and
evidence that the algorithm produces the required result. Unknown, undisclosed,
malformed, ambiguous, or unevaluable required constraints fail.

For v0.2.0, the AP2 binding extension may map only these built-in constraint
types:

- `checkout.allowed_merchants`;
- `checkout.line_items`;
- `payment.agent_recurrence`;
- `payment.allowed_payees`;
- `payment.allowed_payment_instruments`;
- `payment.allowed_pisps`;
- `payment.amount_range`;
- `payment.budget`;
- `payment.reference`; and
- `payment.execution_date`.

The line-item mapping should cite AP2's normative matching conditions and record
the resolved item identities and quantities. A resolved verifier may use the
illustrative maximum-flow formulation or another algorithm that produces the
same required result. Its implementation feature and tests should identify the
chosen algorithm. Equality-based mappings should record the compared canonical
identities. Range and budget mappings should state currency, units,
inclusivity, and the exact AP2 representation. Because the v0.2.0 examples and
schemas are inconsistent about integer minor units and decimal numbers, a
binding must report the case as unresolved instead of inventing a conversion.

AP2 v0.2.0 does not define interoperable calendar semantics for
`payment.agent_recurrence`. Until a separately identified contract defines the
reference event, rolling or calendar interpretation, timezone, daylight-saving
behavior, boundaries, and every frequency value, that constraint remains
unresolved and cannot receive a positive readiness verdict.

The portable requirement for recurrence, budget, and overlap checks should
identify an authoritative State definition, accounting scope, consistency and
atomicity requirements, recorded facts, and fail-closed behavior. The State
definition should cover all verifiers and delegates that may accept the same
open mandate. It should require prior presentations, pending candidates,
receipts, accumulated amounts, expiry, and revocation to remain distinguishable.

The AP2 binding resolution should identify the Runtime instance and state store
that satisfy those requirements, including the component that serializes or
atomically reserves uses. Unavailable, partitioned, or stale state produces an
indeterminate result and follows the declared fail-closed Policy.

The v0.2.0 Python SDK is not the constraint contract. Open upstream reports
identify divergent behavior for
[`payment.agent_recurrence`](https://github.com/google-agentic-commerce/AP2/issues/297),
[`checkout.line_items`](https://github.com/google-agentic-commerce/AP2/issues/298),
and [Payment Instrument extension fields and identity
comparison](https://github.com/google-agentic-commerce/AP2/issues/299). A
resolved binding that selects that SDK must report the affected checks as
unproven until versioned regression tests establish the required behavior.

An AP2 constraint extension should remain an external contract with an
owner-qualified type, immutable schema identity, selective-disclosure rules,
deterministic evaluation algorithm, compatibility rules, and test vectors. A
processor that does not support it should not approximate it.

### Consent and human control

AP2 user authorization maps to Approval. Consent remains a separate externally
governed requirement. When consent applies, the description should identify its
subject, purpose, covered data or authority, governing policy or jurisdiction,
record, withdrawal, expiry, and failure behavior.

An AP2 mandate or Trusted Surface claim may be evidence considered by a consent
system. Structural or cryptographic validation cannot establish notice quality,
comprehension, accessibility, freedom of choice, legal basis, or recourse.

As an additional AgSDL safeguard, the extension should require an external
management path when users need to inspect, revoke, or narrow active autonomous
authority. It should also identify revocation propagation, cached-state
behavior, in-flight action behavior, and evidence of completion. Editing an
AgSDL definition or deleting a local mandate copy does not revoke authority
already accepted elsewhere.

### Deterministic verification requirements

Every AP2 verifier should resolve to a deterministic component outside any LLM
decision path. The component may belong to an agentic role, but model output
must not decide whether a mandate passes.

An AP2 verification requirement should cover, where applicable:

1. exact AP2 release, mandate `vct`, schema, constraint types, and external
   credential contracts;
2. compact artifact preservation and schema validation;
3. signer identity, issuer trust, accepted algorithm, key status, validity
   interval, audience, nonce, and verifier challenge;
4. SD-JWT chain, disclosure digest, decoy, key binding, proof of possession,
   and `sd_hash` checks;
5. open claims preserved unchanged in the closed mandate;
6. deterministic evaluation of every constraint with unknown constraints
   failing;
7. checkout JWT signature, current checkout identity, `checkout_hash`,
   `transaction_id`, `payment.reference`, and receipt-reference linkage;
8. recurrence, budget, overlap, replay, expiry, and revocation state;
9. payment credential scope before release or processing;
10. applicable signed success or error receipt issuance, plus any additional
    AgSDL requirement for atomic state update; and
11. trace output that records inputs, algorithms, contract identities,
    decisions, errors, and evidence gaps without exposing secrets or
    undisclosed claims.

A verifier may use a delegated technology provider. The role requirement
mapping and resolved participant assignment still name the AP2 role responsible
for the result, the provider Principal that ran the check, and the evidence
returned. The description should not present the provider as the original user,
agent, merchant, or payment processor.

### Receipts and accountability

An AP2 receipt mapping should identify the issuer Principal, signature and key
contract, referenced mandate bytes, status vocabulary, creation time,
correlation identifiers, observation boundary, storage policy, and verification
result. Error receipts are evidence and should remain in the trace.

The following claims remain distinct:

- the verifier accepted or rejected a mandate;
- checkout completion was observed;
- a payment was authorized, initiated, cleared, settled, reversed, or refunded;
- goods or services were fulfilled;
- a party was attributable to a signed statement; and
- an adjudicator assigned legal or scheme liability.

AP2 mandates and receipts can support the first claims within declared evidence
boundaries. External payment, fulfillment, dispute, and legal systems supply the
rest. The extension must not label a cryptographically valid chain as proof of
liability.

The execution trace should preserve distinct identities for the user,
Shopping Agent, Agent Provider or credential issuer, Trusted Surface, Merchant,
Credential Provider, Network, Merchant Payment Processor, delegated verifier,
and adjudicator. It should link Approval, Delegation, mandate presentations,
Authorization decisions, Actions, Effects, receipts, revocations, and disputes
without merging their actors or outcomes.

## Resolution and conformance

Unresolved-document validation can inspect whether a binding names exact
contracts, roles, mandate types, mappings, required constraints, credential
references, failure policies, and evidence requirements. It can also reject
embedded secrets and claims that use v0.1 mandate names under v0.2.0.

Resolved-graph validation can resolve immutable external contracts, mapped
Principals and Resources, verifier components, trust and key references,
commerce and payment bindings, constraint algorithms, accounting state, and
trace requirements. It should fail when a required dependency is mutable,
missing, incompatible, or ambiguous.

Deployment checks can establish that identified deterministic components,
protected keys, credential brokers, state stores, clocks, trust roots,
revocation sources, and evidence stores are present with claimed configuration.
They cannot prove that a future execution will use them correctly.

Execution tests are required for an AP2 runtime or adapter claim. A future
suite should cover all positive and negative cases listed in the accompanying
research note, including altered content, unknown constraints, replay,
concurrent use, unavailable state, delegated verification, combined roles, and
evidence loss.

AgSDL currently has no normative syntax, AP2 adapter, payment fixture, or
executable AP2 conformance suite. This proposal therefore supports only
conceptual review. It must not be cited as an implemented payment or
interoperability feature.

## Failure matrix

The origin column prevents an AgSDL safeguard from being misreported as an AP2
requirement. "AP2" means the result derives from v0.2.0. "AgSDL" means this
proposal adds the result to preserve core invariants or fail safely. "External"
means another declared Policy or contract governs the result.

| Condition | Origin | Proposed result |
| --- | --- | --- |
| AP2 release or mandate `vct` differs from the declared contract | AP2 and AgSDL | Reject the affected AP2 operation or select a separate predeclared binding variant |
| Credential, delegation, commerce, transport, or payment contract is unresolved | AgSDL | No positive resolved-graph or readiness verdict |
| Required AP2 role has no accountable Principal or deterministic verifier | AP2 and AgSDL | Fail readiness for that role's operations |
| Signer, trust, time, audience, nonce, key binding, digest, or chain check fails | AP2 and external credential or delegation contracts | Deny and issue or preserve the applicable AP2 error receipt |
| Required constraint is unknown, hidden, malformed, ambiguous, or unevaluable | AP2 and AgSDL | Deny with `unresolved_constraint` where AP2 permits it; otherwise follow the declared fail-closed Policy |
| Checkout or payment linkage does not recompute from preserved bytes | AP2 | Deny as invalid mandate or credential |
| Amount unit, recurrence period, identity comparison, or other rule is ambiguous | AgSDL | Indeterminate, then fail closed for the protected Action |
| Recurrence, budget, overlap, replay, or revocation state is unavailable or stale | AgSDL | Indeterminate, then fail closed for the protected Action |
| Shopping Agent attempts a subsequent presentation without the AP2-required rejection receipt | AP2 Shopping Agent duty; optional AgSDL verifier Policy | Report the Shopping Agent violation; verifier refusal applies only when the AgSDL Policy declares it |
| Payment credential is broader than or unbound to the checkout | AP2 | Do not release or process it |
| Trusted Surface or provider signing key is exposed to an agentic component | AP2 trust assumption and AgSDL containment | Fail the affected trust-model requirement and revoke or contain according to Policy |
| Provider-signed mandate lacks evidence of the human decision it claims | AgSDL | Record an Approval evidence gap and do not infer an identified human Approval decision |
| User approval exists but a separate consent obligation is unsatisfied | External | Deny the operation governed by that consent requirement |
| Receipt is missing, invalid, or outside its observation boundary | AP2 receipt duties and AgSDL evidence model | Report the applicable AP2 duty or verification failure, record an evidence gap, and never infer the missing result |
| A role delegates verification without preserving provider identity and authority | AgSDL | Fail the delegated role requirement mapping or resolved participant assignment |
| Transport or commerce flow proposes an unprotected fallback after AP2 activation | AgSDL | Refuse unless a separate binding and explicit human decision authorize a semantically different flow |

## Requirements traceability

| Existing requirement | Contribution of this proposal |
| --- | --- |
| REQ-002, REQ-013, REQ-014, and REQ-016 | Separates AP2 release, mandate schema, credential, commerce, transport, payment, adapter, and dependency identities |
| REQ-008, REQ-009, REQ-018, REQ-019, and REQ-020 | Keeps AP2 and constraint semantics in the AP2 binding extension with exact support and failure reporting |
| REQ-021 through REQ-026 | Maps roles, principals, trust boundaries, credentials, delegation, approval, consent, policy, authorization, and fail-closed behavior |
| REQ-027, REQ-028, and REQ-030 | Preserves causal evidence and separates definitions, signed artifacts, observed results, and claims |
| REQ-032 through REQ-035 | Defines portable requirements, deployment resolution, deterministic verifier needs, and visible gaps without prescribing an implementation |
| REQ-009 and CON-003 | Requires structural and execution evidence scoped to the AP2 binding extension before interoperability claims |

This table identifies conceptual coverage. It is not conformance evidence and
does not close the unresolved implementation work in those requirements.

## Conceptual example

This example illustrates information, not syntax.

A procurement System definition carries the candidate AP2 binding extension
and portable participant requirements. Its AP2 binding resolution maps a
Shopping Agent, corporate card Credential Provider, Merchant, Merchant Payment
Processor, and non-agentic corporate approval surface to distinct Principal
identities. It references AP2 v0.2.0, SD-JWT, an immutable Delegate SD-JWT
draft, OpenID4VP, a dated commerce binding, and the corporate card payment
contract separately.

The employee approves open Checkout and Payment Mandates for one approved
merchant, one item set, at most 20,000 integer minor currency units, before a
fixed expiry. The signed artifacts support one Approval decision and two
Delegation occurrences to the Shopping Agent. They do not prove legal consent
for marketing or data reuse.

Later, the Shopping Agent assembles a checkout. Deterministic code verifies the
merchant-signed checkout JWT before using the agent key to create closed
mandates. The Credential Provider verifies the Payment Mandate and releases a
credential scoped to its checkout. The Merchant independently verifies the
Checkout Mandate. The Merchant Payment Processor checks the credential scope
before payment.

Each verifier produces a distinct Authorization decision. Signed receipts and
the compact mandate bytes enter the trace. If the budget state is unavailable,
an amount unit is ambiguous, or any constraint is unknown, the relevant Action
is denied. A Payment Receipt supports the processor's observed payment result.
It does not prove settlement, delivery, or which party would bear liability in
a later dispute.

## Consequences

### Benefits

- General delegation and verifiable authorization remain usable without AP2.
- Payment-specific meanings stay governed by the exact AP2 contract.
- Role responsibility, user approval, delegated authority, verifier decisions,
  actions, effects, receipts, and liability remain distinct.
- Deterministic verification duties and state dependencies become inspectable.
- Version changes and unsupported constraints fail visibly.

### Costs and limitations

- Authors must map several roles, resources, trust contracts, and evidence
  subjects instead of attaching one mandate to a payment tool.
- Autonomous flows need protected keys, authoritative shared state, revocation,
  and receipt management outside the LLM path.
- Reproducible resolution requires an immutable identity for AP2's mutable
  Delegate SD-JWT dependency.
- AP2 and AgSDL both lack the executable cross-implementation suite needed for
  an interoperability claim at this stage.
- Consent sufficiency, dispute outcome, settlement, fulfillment, and legal
  liability remain external concerns.

## Alternatives considered

### Add Mandate to the AgSDL core

This would bind the core to one credential pattern and obscure the difference
between a definition, human decision, delegated authority, verifier decision,
signed artifact, and receipt. Existing AgSDL concepts express the portable
meaning more precisely.

### Copy AP2 schemas into AgSDL

This would fork AP2's contract and still omit trust roots, role occupancy,
commerce operations, payment rails, state, and evidence boundaries. Exact
external references plus adapter tests are smaller and safer.

### Treat AP2 as a transport or commerce protocol

AP2 does not define the surrounding role-to-role APIs, checkout lifecycle, or
transport. A binding still needs a separate UCP, A2A, MCP, HTTP, or other
contract where those behaviors matter.

### Treat every signed mandate as a valid authorization

Signature validity establishes only part of the evidence chain. The verifier
must also resolve trust, identity, time, key binding, unchanged claims,
constraints, transaction linkage, state, policy, and revocation.

### Import AP2 v0.1 terminology into the current extension

Intent Mandate and Cart Mandate belong to v0.1.0. Accepting them under v0.2.0
would hide a material contract change. A legacy adapter needs its own mapping,
loss report, and tests.

## Security considerations

Every LLM and agent remains a potential attacker under the AP2 threat model.
Mandate creation, signature release, verification, constraint evaluation,
state update, credential release, and receipt protection should run in
deterministic components whose keys and state are inaccessible to model
context.

Selective disclosure limits what one verifier receives. It does not make
disclosed values trustworthy or prevent correlation through hashes, merchant
identities, payment instruments, timing, or receipts. The description should
declare disclosure purpose, recipient, retention, and audit requirements while
keeping undisclosed claims out of logs.

Long-lived open mandates concentrate authority. Expiry, revocation,
notification, recurrence, budget, atomic use, and in-flight behavior need
explicit Policies. A local Shopping Agent promise not to double spend is not a
sufficient control against a compromised agent or concurrent verifier paths.

Role combination can remove independent checks. An AP2 binding resolution
should report combined user surface, agent provider, credential provider,
merchant, and payment processor roles as a trust concentration. It should never
infer independence from separate AP2 role labels.

Signed receipts may contain payment and correlation identifiers. Their
integrity, confidentiality, retention, deletion, and controlled disclosure need
policy. Missing or unverifiable evidence should remain an evidence gap, not a
successful result.

## Compatibility impact

AgSDL has no normative syntax or published AP2 binding contract, so this
proposal breaks no conforming document. It constrains future syntax and adapter
work to represent exact external contracts, role and artifact mappings,
deterministic verification, stateful controls, evidence boundaries, and
fail-closed gaps.

AP2 v0.1.0, AP2 v0.2.0, the UCP AP2 Mandates extension, and any future FIDO
specification remain separate compatibility subjects. Ordering or shared names
do not prove compatibility.

## Unresolved questions

1. Which future AgSDL artifact type should preserve signed mandate and receipt
   bytes without turning AgSDL into an evidence store?
2. How should one portable state model describe atomic recurrence and budget
   enforcement across independent verifiers and payment networks?
3. What immutable edition of Delegate SD-JWT should an AP2 v0.2.0 binding use?
4. Which amount representation should a strict adapter accept where AP2 v0.2.0
   prose, examples, and schemas differ?
5. What exact temporal contract defines every `payment.agent_recurrence`
   frequency, reference event, timezone, and period boundary?
6. Are `checkout.line_items` quantities exact, minimum, or maximum requirements,
   and what qualified identifier namespace applies to acceptable items?
7. Which Payment Instrument fields and identity comparison rules must a strict
   adapter preserve for every instrument type?
8. How should a strict adapter handle AP2's conflicting checkout entropy rules
   for deterministic signatures?
9. What minimum trust metadata identifies a Trusted Surface and proves that its
   signing path is isolated from the Shopping Agent?
10. How should revocation and in-flight cancellation work when a verifier has
   already issued a scoped payment credential?
11. Which receipt statuses can support an AgSDL Effect occurrence, and what
   external settlement evidence is required for each payment rail?
12. Can one adapter suite cover both User Credential and Trusted Agent Provider
   trust models without hiding their different issuers and failure modes?
13. What loss report is required when translating AP2 v0.1 Intent and Cart
   Mandates to v0.2 open and closed Checkout Mandates?
14. When FIDO publishes a successor, which organization and contract identity
    should govern the AgSDL extension name and compatibility policy?
15. Which canonical bytes should identify an open mandate for shared
    consume-once state if a later AP2 edition standardizes that operation?
