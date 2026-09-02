# AP2 v0.2.0 binding research

Status: research note, non-normative
Last reviewed: 2026-09-02

## Purpose and source boundary

This note examines the current public Agent Payments Protocol release as input
to an AgSDL binding proposal. It does not define AgSDL syntax, reproduce AP2,
make either project conformant, or assert that an AP2 payment integration works.

The latest public release found on 2026-09-02 is
[`v0.2.0`](https://github.com/google-agentic-commerce/AP2/releases/tag/v0.2.0),
published on 2026-04-28 from commit
[`b4587ac1d055888a73b4b21750973cffba961793`](https://github.com/google-agentic-commerce/AP2/tree/b4587ac1d055888a73b4b21750973cffba961793).
The default branch contains later repository-maintenance commits but no newer
protocol release. This review therefore uses the release tag, not `main`.

The AP2 repository and FIDO Alliance call the project "Agent Payments
Protocol". The v0.2 specification heading says "Agentic Payment Protocol".
This note uses the public project name and records the heading difference
rather than treating it as another protocol.

The phrase "Agent Payments ProtocolContent Protocol" does not identify a
contract in the reviewed AP2 sources. It appears to concatenate names. This
review does not infer a second Content Protocol or confuse AP2 with Model
Context Protocol.

Google contributed AP2 to the FIDO Alliance in April 2026. The
[FIDO announcement](https://fidoalliance.org/fido-alliance-to-develop-standards-for-trusted-ai-agent-interactions/)
says its Payments Technical Working Group will develop agent-initiated commerce
specifications from AP2 and Mastercard Verifiable Intent contributions. No
separately versioned FIDO AP2 specification was publicly available at review
time. FIDO stewardship does not change the identity of the reviewed Google
release.

The primary protocol sources are the release-pinned
[AP2 specification](https://github.com/google-agentic-commerce/AP2/blob/v0.2.0/docs/ap2/specification.md),
[Agent Authorization model](https://github.com/google-agentic-commerce/AP2/blob/v0.2.0/docs/ap2/agent_authorization.md),
[Checkout Mandate](https://github.com/google-agentic-commerce/AP2/blob/v0.2.0/docs/ap2/checkout_mandate.md),
[Payment Mandate](https://github.com/google-agentic-commerce/AP2/blob/v0.2.0/docs/ap2/payment_mandate.md),
[flows](https://github.com/google-agentic-commerce/AP2/blob/v0.2.0/docs/ap2/flows.md),
and [security and privacy
considerations](https://github.com/google-agentic-commerce/AP2/blob/v0.2.0/docs/ap2/security_and_privacy_considerations.md).
The release-pinned
[JSON Schemas](https://github.com/google-agentic-commerce/AP2/tree/v0.2.0/code/sdk/schemas/ap2)
are the machine-readable source for mandate content and receipts.

Source facts below summarize those materials. AgSDL assessments are project
conclusions and do not add requirements to AP2. Later official tracker reports
are labeled separately and do not amend the release contract.

## Version and contract boundaries

### Source facts

AP2 v0.2.0 replaces the v0.1.0 vocabulary of Intent Mandate, Cart Mandate, and
Payment Mandate with open and closed forms of Checkout Mandate and Payment
Mandate. Open mandates carry constraints and bind a future presentation to an
agent key. Closed mandates authorize a particular checkout or payment. The
exact `vct` values include independent schema suffixes:

- `mandate.checkout.open.1` and `mandate.checkout.1`;
- `mandate.payment.open.1` and `mandate.payment.1`.

An implementation must match the whole `vct` value. The AP2 release number and
each mandate schema suffix are therefore separate version domains.

AP2 is a security feature inside a commerce protocol. Catalog operations,
checkout mutation, role-to-role APIs, transport, and most discovery are outside
its scope. The v0.2 specification is designed for Universal Commerce Protocol
compatibility, but an AP2 implementation need not use UCP, A2A, MCP, ADK, or
Gemini. The separately published
[UCP AP2 Mandates extension](https://ucp.dev/2026-01-23/specification/ap2-mandates/)
is an integration contract with its own dated version and activation rules.

The Agent Authorization model normatively references OpenID4VP 1.0, RFC 9901
SD-JWT, RFC 7800 confirmation keys, and an individual Delegate SD-JWT draft.
The Delegate SD-JWT reference points to a mutable repository with no release
tag. The normative list does not identify an exact SD-JWT VC base-profile
edition even though AP2 uses SD-JWT VC terminology, the `dc+sd-jwt` format, and
the `vct` claim. AP2 mentions other verifiable digital credential formats as
possible extensions, but v0.2 specifies SD-JWT for Checkout and Payment
Mandates.

The release SDK documents a deliberate wire-shape deviation from
`draft-gco-oauth-delegate-sd-jwt-00`. It terminates AP2 chains with a
`typ=kb+sd-jwt` token carrying `aud`, `nonce`, and `sd_hash`, and rejects the
draft's alternative trailing plain KB-JWT form. The SDK also implements
arbitrary-depth delegation chains even though the AP2 specification places
agent-to-agent mandate delegation outside v0.2.0.

### AgSDL assessment

An AgSDL binding must identify AP2 `v0.2.0`, the exact mandate `vct` values, the
credential format, and every external authorization, commerce, transport, and
payment contract independently. A label such as "AP2 compatible" or an SDK
package version cannot supply those identities.

The unversioned Delegate SD-JWT dependency and unidentified SD-JWT VC profile
prevent a reproducible positive resolved-graph verdict unless a binding pins
both reviewed contracts by immutable identities. A future FIDO specification
is a new candidate contract, not an implicit update to AP2 v0.2.0.

## Roles and responsibility

### Source facts

AP2 defines five logical roles:

| AP2 role | Main protocol responsibility |
| --- | --- |
| Shopping Agent | Discovers products, builds the checkout, assembles mandate content, obtains signatures, presents mandates, and manages receipts |
| Credential Provider | Supplies payment credentials and verifies that the agent may access a credential scoped to the checkout |
| Merchant | Supplies and completes the checkout, signs its checkout JWT, verifies Checkout Mandates, and protects inventory and pricing integrity |
| Merchant Payment Processor | Processes payment and verifies that the payment credential is scoped to the checkout |
| Trusted Surface | Deterministically presents mandate content, obtains user authorization and consent, and causes the mandate to be signed |

One entity may occupy several roles. The Merchant, Merchant Payment Processor,
and Credential Provider may be agentic or non-agentic. The Shopping Agent is
expected to be agentic. The Trusted Surface must be non-agentic.

Every AP2 validation or processing duty assigned to a role must run in
deterministic code, even when that role also uses an LLM. A role may delegate
its responsibilities to a provider. The provider then follows the verification
rules for that role.

AP2 separately says that agent-to-agent delegation of mandates is outside
v0.2.0. This differs from delegating a role's verification work to a service.

### AgSDL assessment

AP2 roles are protocol responsibilities, not automatically AgSDL Role
definitions. An AgSDL Role is assigned to an Agent, while several AP2 roles may
belong to non-agentic principals or external systems. A portable binding
requirement should map each required AP2 role to Principal, Agent, Runtime, or
Environment definitions and binding requirements. Deployment resolution should
then assign concrete Principal identities, Runtime instances, and endpoints.
Co-located roles remain separate mappings so reviewers can inspect each duty
and trust boundary.

The current AgSDL Protocol model also assigns protocol positions through
agent-only Roles. Representing AP2 as an ordinary Protocol definition would
therefore require synthetic Agents for non-agentic participants. The candidate
extension should instead target the integrating System or Fragment and preserve
AP2 role labels in extension-specific requirement mappings until the core has a
non-agentic protocol-participant concept.

Delegated verification work maps to a Handoff when only responsibility moves.
It also needs an AgSDL Delegation when the provider receives authority to take
a protected Action. Neither mapping authorizes agent-to-agent mandate
redelegation, which the AP2 release does not specify.

## General mandate authorization model

### Source facts

The Agent Authorization model separates two operations:

1. Mandate Delegation. A user reviews mandate content on a Trusted Surface,
   authorizes it, and delegates the signed mandate to an agent.
2. Action Authorization. A verifier challenges the agent, receives a mandate
   presentation, verifies its integrity and scope, then returns a signed
   receipt for acceptance or rejection.

Two trust models create user-authorized mandates. In the User Credential model,
the verifier trusts a credential issuer to vouch for the holder's Trusted
Surface. AP2 profiles OpenID4VP `transaction_data` and Delegate SD-JWT for this
operation. In the Trusted Agent Provider model, the verifier directly trusts
the agent provider to obtain authorization and consent on a deterministic
surface and protect its signing key from the agent.

An open mandate has constraints and a `cnf` confirmation key for the agent. An
agent later creates the transaction-bound closed mandate using proof of
possession of that key. A direct flow instead obtains a user-authorized closed
mandate for the final transaction. Selective disclosure reveals only claims
needed by the verifier.

AP2 allows new mandate and constraint types with collision-resistant names. Its
general authorization text says the model could apply beyond payments, but
v0.2.0 only defines payment-specific Checkout and Payment Mandates and their
constraints.

### AgSDL assessment

The general ideas already fit the proposed AgSDL core:

- Delegation defines bounded authority independently of its credential format.
- An Approval decision records a person's bounded decision at a Trusted
  Surface.
- An Authorization decision records a verifier's result for one principal,
  Action, Resource, Policy, context, and time.
- Authentication evidence establishes control of user, provider, verifier, or
  agent identities without creating authority.
- An immutable artifact preserves the signed mandate or receipt bytes, while
  occurrences record approval, delegation, authorization, Action, and Effect.

Mandate Delegation applies to both AP2 modes when a Shopping Agent receives and
later presents the mandate. A user-authorized closed mandate in direct mode
therefore supports a transaction-bounded Delegation occurrence as well as an
Approval decision. When a Trusted Surface communicates directly with a
non-agentic Merchant and no Shopping Agent acts for the user, that separate
flow has no agent delegation.

AgSDL should not add a generic Mandate entity. A mandate is one external
credential representation that can support several distinct AgSDL facts. The
signature proves integrity and signer control under stated trust assumptions.
It does not, by itself, prove informed consent, valid authority, policy
enforcement, action execution, or an external effect.

Non-payment systems should express verifiable delegation through the existing
core concepts and a credential-format binding when needed. They should not
depend on AP2 or reuse AP2 payment `vct` values.

## Checkout and payment authorization

### Source facts

A closed Checkout Mandate contains the merchant-signed `checkout_jwt` and its
`checkout_hash`. The Merchant verifies the credential chain, checks the hash
against the checkout it supplied, evaluates every disclosed open Checkout
constraint, and returns a signed Checkout Receipt.

A closed Payment Mandate identifies the transaction, payee, amount, payment
instrument, and optional payment initiation service provider or execution date.
Its `transaction_id` is the hash of the checkout JWT. Credential Providers and
Networks verify the Payment Mandate before releasing a payment credential. The
Merchant Payment Processor verifies that credential is scoped to the checkout
before processing payment and returns a signed Payment Receipt.

The release defines these open mandate constraints:

| Mandate | Constraint types |
| --- | --- |
| Checkout | `checkout.allowed_merchants`, `checkout.line_items` |
| Payment | `payment.agent_recurrence`, `payment.allowed_payees`, `payment.allowed_payment_instruments`, `payment.allowed_pisps`, `payment.amount_range`, `payment.budget`, `payment.reference`, `payment.execution_date` |

The line-item constraint defines the required matching outcome and presents a
maximum-flow formulation as one implementation method. Unknown or unevaluable
constraints fail. Recurrence and budget depend on previous presentations and
accumulated amounts. AP2 says a Shopping Agent must not present a subsequent
open Payment or Checkout Mandate without a rejection receipt from the previous
one. Its stated rationale is to prevent several checkouts under one open
mandate. The wording does not fully define the identifier or state scope needed
to enforce that rule across verifiers.

### AgSDL assessment

The binding must separate the Shopping Agent's mandate presentation and request
from the action performed in response. Checkout request, Merchant order
commitment, payment-authority request, credential release, payment submission,
and payment processing have different acting and initiating Principals,
Resources, evidence, and failure outcomes. One authorization result cannot
substitute for another. The payment credential is a secret or opaque credential
reference, not an Authority grant and not a copy of payment card data in the
description.

Every AP2 constraint maps to an AgSDL Policy or Delegation condition, but AP2
owns its exact evaluation. AgSDL should reference the constraint contract and
record the evaluated inputs and result. Amount units, currency, time source,
merchant and instrument identity comparison, disclosed set, and checkout bytes
must be explicit enough to reproduce the result.

Recurrence, budget, and overlapping-use checks are stateful. A static document
or isolated mandate presentation cannot prove them. A resolved deployment must
identify the authoritative accounting scope, serialization or atomicity rule,
receipt update behavior, and fail-closed response when state is unavailable.

## Consent, approval, and trusted surfaces

### Source facts

AP2 requires the Trusted Surface to obtain user authorization and consent after
displaying mandate content. The Trusted Surface is part of each defined trust
model. The AP2 release does not define notice language, comprehension,
accessibility, coercion safeguards, legal basis, withdrawal, or a general
consent record. Mandate management and external revocation remain largely
outside its scope.

The direct mode shows and signs the final closed mandates. The autonomous mode
shows and signs constrained open mandates, then allows the bound agent key to
create closed mandates later. The release recommends the shortest practical
expiry for open mandates but does not define a universal duration.

### AgSDL assessment

The Trusted Surface interaction can support an Approval decision only when the
binding preserves the exact presented content, user Principal identity,
surface and signer identities, decision, time, expiry, and definition or policy
versions. In an autonomous flow, the later agent-signed closed mandate is a use
of delegated authority, not another human approval.

Under the Trusted Agent Provider model, the provider's signature supports the
provider's claim that it obtained authorization and consent. The mandate alone
does not identify every fact required for an AgSDL Approval decision. Missing
human identity, display, decision, time, or version evidence remains an evidence
gap rather than an inferred Approval occurrence.

Where law or policy requires consent, an AgSDL consent requirement and consent
record remain separate. A valid AP2 signature cannot prove that a user
understood the notice or that the consent was legally sufficient. Revocation,
withdrawal, notification, and recourse need separate policy or profile
requirements.

## Receipts, evidence, and liability

### Source facts

The general Mandate Receipt is a verifier-signed JWT with issuer, success or
error result, and a hash reference to the final mandate in the chain. AP2 adds
Checkout and Payment Receipt schemas. A Payment Receipt also identifies a
payment and, on success, payment service provider and network confirmations.

For dispute verification, AP2 joins the Checkout Mandate and Receipt with the
Payment Mandate and Receipt, recomputes checkout and mandate hashes, and applies
the role verification rules. The specification says the resulting information
can be evidence of what the user and roles saw. Retention, retrieval, dispute
procedure, and legal treatment are outside AP2.

The AP2 FAQ says the evidence helps payment networks establish accountability
and liability principles. It does not assign liability to a party.

### AgSDL assessment

A receipt is signed external evidence with a declared issuer and observation
boundary. A general Mandate Receipt supports an Authorization decision result.
A Checkout Receipt can also support the observed outcome of checkout
completion. A Payment Receipt can support a payment Action or Effect occurrence
within the issuer's declared observation boundary. None proves product
delivery, final settlement, irreversibility, absence of another attempt, or the
completeness of the trace without extra evidence.

AgSDL accountability requires the user, agent, agent provider, verifier,
merchant, credential provider, payment processor, and any delegated provider to
retain distinct Principal identities and causal relations. Evidence can support
attribution. Legal or scheme liability remains an external adjudication result
and must not be inferred from a valid chain.

## Deterministic verification

### Source facts

AP2 requires deterministic validation even inside an agentic role. For an
autonomous presentation, verification combines Delegate SD-JWT processing,
signature and trust checks, agent proof of possession, unchanged-claim checks,
constraint evaluation, transaction binding, and receipt handling. AP2 also
requires privacy-preserving selective disclosure and rejects unknown
constraints.

The release includes JSON Schemas and Python unit tests for schema-derived
models, SD-JWT helpers, mandate chains, constraint algorithms, disclosures, and
receipts. Its GitHub workflows do not run the Python tests as a protocol
conformance suite. No AP2 implementation conformance program, cross-vendor test
suite, or published test-vector contract was found in the reviewed release.

An [open community proposal in the AP2
tracker](https://github.com/google-agentic-commerce/AP2/issues/265) offers
canonicalization vectors for an `open_mandate_hash` not defined by v0.2.0. The
issue has no linked merge or milestone at review time. A related
[implementation discussion](https://github.com/google-agentic-commerce/AP2/discussions/262)
treats consume-once behavior as an extra runtime state layer and asks which
canonical mandate representation should identify it. These discussions show
active interoperability work. Their proposed algorithms and external libraries
are not part of the AP2 v0.2.0 contract.

Later open reports in the official tracker identify three additional release
gaps. Issue
[#297](https://github.com/google-agentic-commerce/AP2/issues/297) reports that
`payment.agent_recurrence` lacks interoperable period semantics and that the
SDK evaluator does not enforce its frequency. Issue
[#298](https://github.com/google-agentic-commerce/AP2/issues/298) reports that
the SDK treats empty or undisclosed line-item alternatives as a wildcard and
does not enforce required quantity as the documentation describes. Issue
[#299](https://github.com/google-agentic-commerce/AP2/issues/299) reports that
the SDK drops Payment Instrument extension fields and compares allowed
instruments only by `id`. Inspection of the tagged SDK confirms the cited code
paths. The reports remain open and are not normative amendments, but they
identify cases where the release SDK cannot supply conformance evidence.

### AgSDL assessment

A binding can declare deterministic checks, but a positive interoperability
claim needs executable tests against identified implementations. At minimum,
future AP2 adapter tests need positive and negative cases for:

1. exact AP2 and mandate versions, schema validation, and unsupported types;
2. signer, trust-root, time, audience, nonce, revocation, and proof-of-possession
   checks under the selected credential format;
3. `sd_hash`, `checkout_hash`, `transaction_id`, open-to-closed chain, and
   receipt-reference recomputation from preserved compact bytes;
4. unchanged claims, every supported constraint algorithm, selective
   disclosures, decoys, fail-closed unknown constraints, empty line-item
   alternatives, required quantities, qualified item identities, and Payment
   Instrument extension preservation and comparison;
5. direct and autonomous flows, including altered content after approval;
6. recurrence counts and every frequency boundary, timezone and daylight-saving
   transition, budget, replay, concurrent presentation, rejected candidate,
   expiry, revocation, and unavailable accounting state;
7. separated Checkout and Payment decisions, payment credential scope, receipt
   status, and dispute-chain assembly;
8. delegated verification responsibility, combined roles, and preservation of
   each accountable Principal identity; and
9. loss reports for unsupported constraints, trust models, credential formats,
   commerce bindings, payment instruments, and evidence fields.

Passing AP2's unit tests would show behavior of that SDK revision. It would not
prove that an AgSDL adapter preserves the model or that two independent payment
participants interoperate.

## Release limitations relevant to AgSDL

The following limits are explicit in AP2 or observable in its released
artifacts:

- AP2 does not define the surrounding commerce API or transport.
- Agent-to-agent mandate redelegation is outside v0.2.0.
- Mandate selection and disclosure selection are Shopping Agent implementation
  details.
- Receipt retrieval, retention, dispute process, and liability assignment are
  outside the protocol.
- Consent quality and legal sufficiency are not verifiable from mandate shape.
- Stateful recurrence, budget, and overlap enforcement need shared execution
  state that the wire artifacts do not supply.
- `payment.agent_recurrence` does not define interoperable rolling or calendar
  periods, reference events, timezones, daylight-saving behavior, or boundary
  rules for its frequency values.
- The tagged SDK diverges from the documented `checkout.line_items` behavior
  for empty or undisclosed alternatives and required quantities. AP2 also leaves
  the item-identifier namespace underspecified.
- The tagged SDK drops type-specific Payment Instrument fields and compares
  allowed instruments only by `id`, while AP2 permits instrument extensions and
  does not define the identity namespace.
- Delegate SD-JWT is a mutable individual draft in the AP2 normative reference
  set.
- AP2 uses SD-JWT VC fields and format identifiers without naming an exact
  normative SD-JWT VC base-profile edition.
- The released SDK deliberately differs from the Delegate SD-JWT draft and
  supports arbitrary delegation depth beyond AP2's specified agent-to-agent
  scope. SDK behavior cannot silently fill either protocol gap.
- The Payment Mandate prose uses integer minor units for transaction amounts,
  while some non-normative amount-range and budget examples show decimal
  amounts and the budget schema allows a JSON number. A binding must not invent
  a conversion rule.
- The main specification requires a nondeterministic checkout JWT signature to
  resist guessing, while the security considerations allow a deterministic
  signature when the checkout adds sufficient entropy. A strict binding must
  report this rule as unresolved instead of choosing one interpretation.
- The release's package metadata still reports version `0.1`, so package
  version cannot identify the v0.2 protocol contract.
- The repository supplies samples and SDK unit tests, not an AP2 conformance
  suite or proof of cross-implementation interoperability.
- Proposed canonicalization vectors and consume-once layers remain unmerged,
  non-normative community work.

These limits support a candidate AgSDL binding extension with explicit gaps.
They do not support normative syntax, imported AP2 schemas, or an
interoperability claim at AgSDL's current pre-draft stage.
