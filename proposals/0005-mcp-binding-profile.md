# Proposal 0005: Model Context Protocol binding profile

- Status: proposed
- Date: 2026-09-02
- Target: post-0.0.1 binding model
- Depends on: Proposals 0002, 0003, and 0004
- External contract: MCP `2026-07-28`

## Summary

This proposal defines how a future AgSDL description should reference and
assess a Model Context Protocol binding without copying MCP or presenting an
external protocol contract as portable AgSDL meaning. It covers tools,
resources, prompts, capabilities, extensions, authorization, and multi-turn
exchanges.

The proposal does not add normative syntax. AgSDL is still a conceptual
pre-draft, so no MCP conformance or interoperability claim follows from this
document.

## Problem

An endpoint and a protocol label are not enough to describe an MCP dependency.
MCP behavior depends on its dated revision, protocol era, transport,
directional capabilities, selected server entries, extension contracts,
authorization flow, and handling of multi round-trip requests. Several MCP
terms also overlap with broader AgSDL terms while carrying different meanings.

Treating MCP discovery as an AgSDL system definition would erase Action,
Effect, ownership, trust, policy, and failure semantics. Copying MCP schemas
into AgSDL would create a second, stale protocol definition. Treating a
successful request as proof of authorization or interoperability would exceed
the evidence.

## Scope

This proposal covers:

- an MCP binding requirement and its resolved binding;
- references to MCP core and extension contracts;
- mappings for MCP tools, resources, prompts, and client features;
- protocol-version and capability negotiation;
- authorization and credential-reference boundaries;
- MRTR, elicitation, sampling, roots, subscriptions, and Tasks; and
- failure, degradation, and conformance evidence.

It does not define an MCP client or server, reproduce MCP message schemas,
choose an AgSDL serialization, standardize OAuth, assign trust to an MCP server,
or claim behavioral equivalence with any MCP SDK.

## Terms

An **MCP binding requirement** is a protocol-qualified binding requirement. It
states the MCP contracts, endpoint role, capabilities, named entries, security
conditions, and failure behavior an implementation must satisfy.

An **MCP resolved binding** is a deployment-specific Resolved binding that
selects an MCP client, server endpoint, transport, credentials references, and
verified contract versions for one MCP binding requirement.

An **MCP contract reference** identifies the external MCP core specification or
an MCP extension by publisher, owner-qualified identity, exact edition or
immutable content identity, and authoritative location.

An **MCP entry mapping** relates one MCP-advertised tool name, resource URI or
URI template, or prompt name to one or more AgSDL definitions. It states which
party controls the external entry and which MCP operation resolves or invokes
it.

An **MCP capability requirement** identifies a directional MCP capability and
settings constraints. It is not an AgSDL Implementation feature, Authority
grant, or Security capability claim.

An **MCP degradation case** names an unmet or changed external condition, the
affected AgSDL operation, the permitted fallback if any, and the observable
result. Omission does not authorize a fallback.

## Proposed semantics

### Contract identity and protocol era

Every MCP binding requirement should identify:

- the MCP core contract by exact dated revision;
- the protocol era, either modern per-request metadata or legacy
  initialization;
- every extension through a separate MCP contract reference;
- the client or server role AgSDL expects the bound implementation to perform;
- the standard or custom transport contract; and
- any earlier MCP revisions that may be selected, each as a separate binding
  variant with an explicit compatibility and degradation policy.

For the current stable contract, the core identity is MCP `2026-07-28` and the
era is modern. A range such as "MCP 2026 or later" is insufficient because MCP
date ordering does not prove semantic compatibility. An SDK package version
cannot substitute for the MCP contract revision.

A required MCP extension should identify its owner-qualified capability key and
its independently versioned or content-addressed specification. The settings
object should remain governed by that external contract. Official and
experimental status should be recorded without treating either status as
evidence of implementation quality.

### Binding contents

An MCP binding requirement should contain or reference these facts:

| Fact | Meaning in AgSDL |
| --- | --- |
| Core contract | Exact external MCP revision and authoritative schema |
| Endpoint role | MCP client or MCP server role required from the bound component |
| Transport | `stdio`, Streamable HTTP, or an identified custom binding |
| Server selection | External endpoint or process selection constraints, without embedded secrets |
| Required server capabilities | Capabilities and settings that discovery must report |
| Required client capabilities | Capabilities and settings that the client must send on each applicable request |
| Entry mappings | MCP names or URIs related to AgSDL definitions |
| Extensions | Independent MCP extension contract references and capability settings |
| Authorization | Applicable external authorization contract, credential references, and AgSDL policy application points |
| Interaction | Required MCP message patterns, subscription behavior, and MRTR limits |
| Degradation | Predeclared outcomes for every optional or unavailable dependency |
| Evidence | Structural, resolution, and execution checks needed for the claim |

The binding should identify the MCP endpoint as an external endpoint or
Environment element and place an Interface at the relevant AgSDL boundary. It
should reference MCP as the external Protocol contract. It should not duplicate
MCP JSON-RPC methods as AgSDL operations unless an AgSDL Interface operation
needs a stable local identity for policy, tracing, or composition.

### Capability negotiation

MCP capability requirements are directional and operation-specific.

- Server capabilities such as `tools`, `resources`, and `prompts` are assessed
  from a `server/discover` result or from equivalent execution evidence allowed
  by the exact MCP revision.
- Client capabilities such as `elicitation`, `sampling`, and `roots` are
  requirements on the metadata sent with each applicable request in modern
  MCP. A prior request does not satisfy them.
- Nested settings, including `listChanged`, resource `subscribe`, elicitation
  modes, sampling tool support, and extension settings, are part of the
  requirement when portable behavior depends on them.
- Discovery is evidence of advertised support. It does not prove correct
  execution, enforcement, authority, or availability at a later time.

A resolved binding is satisfied only if every required capability has a
compatible directional match. Optional capabilities may be absent only when an
MCP degradation case defines the remaining portable behavior. A runtime should
reassess request-specific client capabilities before every request and should
invalidate or refresh cached server discovery according to the applicable MCP
cache contract.

Modern negotiation should use `server/discover` or handle the MCP
`UnsupportedProtocolVersionError`. A recognized modern error should lead only
to selection of a predeclared mutually supported modern version. It should not
trigger legacy fallback. A binding that supports both eras should follow the
transport-specific MCP probe rules and keep separate resolved evidence for the
selected era.

### Tools

An AgSDL Tool may use an MCP entry mapping to identify the MCP tool name and
`tools/call` as its invocation operation. The mapping should preserve the MCP
input and output contracts by reference. It should also relate the Tool to the
AgSDL Actions it makes available and the Resources those Actions can affect.

MCP tool descriptions, annotations, input schemas, output schemas, and result
content remain MCP-governed data. An AgSDL author may add stricter local input
constraints, effects, policy, or approval requirements. The author should not
weaken or silently rewrite the referenced MCP contract. A mismatch should make
the mapping unsatisfied or require a new adapter with a declared transformation
and evidence.

An MCP tool's presence does not grant authority to call it. A successful
`tools/call` result does not prove that every AgSDL Authorization requirement or
Effect declaration was enforced. Tool-level errors, JSON-RPC errors,
authorization failures, and transport failures should remain distinguishable
in failure and trace records.

### Resources

An MCP resource mapping should identify an exact URI, a URI-template constraint,
or an explicit dynamic-discovery policy. It may realize access to an AgSDL
Resource or Knowledge definition. The AgSDL definition should still identify
the governing authority, provenance and freshness expectations, access method,
and relevant policy.

An MCP URI is the protocol identity of an advertised item. It does not establish
AgSDL ownership or truth. A resource link returned from a tool should be treated
as a newly observed external reference unless a resolved mapping already covers
it. Dynamic URI-template expansion should remain within declared scheme, host,
path, size, and content-type constraints where those facts affect policy.

### Prompts

An MCP prompt mapping should identify the prompt name, its argument contract,
and the AgSDL Instructions or Interface operation that may consume its returned
messages. The server controls the returned content. The binding should state
its trust classification, instruction precedence, allowed consumers, and the
policy applied before that content can influence an Action.

MCP's user-controlled interaction convention does not prove AgSDL consent or
approval. Selecting or retrieving a prompt neither grants authority nor changes
the precedence of its instructions.

### Extensions

Every required MCP extension should have:

- an MCP contract reference independent from the core revision;
- the exact capability identifier and compatible settings constraints;
- required support on the client, server, or both;
- a status such as official or experimental as source metadata;
- fallback behavior from the extension contract and any stricter AgSDL
  degradation case; and
- conformance evidence scoped to that extension edition.

An MCP extension is external protocol behavior. It is not automatically an
AgSDL Extension. An AgSDL Extension is needed only when the AgSDL document adds
non-core meaning that cannot be expressed through the MCP binding requirement
and existing AgSDL definitions.

If one party lacks a required MCP extension, the runtime should stop before the
affected operation. If the extension is optional, it may revert to core MCP
behavior only when both the external extension contract and the AgSDL
degradation case permit the same fallback.

The official `io.modelcontextprotocol/tasks` extension should be referenced as
an extension contract, not treated as core MCP `2026-07-28`. Its task handle and
status are execution occurrences. A mapping to AgSDL Control flow, Work item,
State, cancellation, or approval concepts should be explicit and should account
for durable identity, terminal states, cooperative cancellation, polling,
mid-flight input, and expiry. The `2026-07-28` extension applies task-augmented
results to `tools/call`; the binding should not infer task support for another
MCP operation.

### Authorization

An HTTP MCP binding may reference the MCP `2026-07-28` authorization contract.
A stdio binding should instead declare the Environment and credential-reference
requirements that supply credentials to the process. A custom transport should
identify its own authentication and authorization contract.

The binding should keep these AgSDL facts separate:

- the Principal and Identity on whose behalf the MCP client acts;
- credential references and the component allowed to resolve them;
- authentication evidence established by the authorization flow;
- OAuth resource, issuer, audience, and scope constraints;
- the AgSDL Authority grants and Policies considered for each Action;
- the Policy application point that mediates the call; and
- the resulting Authorization decision and execution evidence.

An OAuth token, accepted scope, successful discovery response, or successful
MCP call cannot create an AgSDL Authority grant. A binding should never embed a
token, client secret, authorization code, or refresh token. It should require
audience-bound tokens for the selected MCP resource and forbid token passthrough
where the external contract does.

Step-up authorization after `401` or `403` should be a declared branch with a
bounded retry and cancellation policy. It must not widen the AgSDL Action or
Resource scope silently. If authorization cannot be obtained, protected
operations fail or follow a predeclared non-protected fallback whose portable
meaning is different and visible.

### Multi-turn exchanges

For MCP `2026-07-28`, server-required client input uses MRTR. A binding that
permits `InputRequiredResult` should declare:

- the originating methods among `tools/call`, `resources/read`, and
  `prompts/get`;
- allowed input request kinds and their required client capabilities;
- which principal or component answers each kind;
- maximum retries or another termination condition;
- timeout, decline, cancellation, invalid-response, and replay behavior;
- whether the operation may be retried safely and how occurrences correlate;
- handling of opaque `requestState`; and
- trace requirements across the original request, input processing, and retry.

Each retry is a new MCP JSON-RPC request but may continue one AgSDL protocol
occurrence. The binding should not assume that authorization or approval from
the first request remains valid. A protected Action should receive an
Authorization decision close enough to its eventual effect to account for
changed arguments, input responses, policies, credentials, and time.

Elicitation supplies user input. An AgSDL Approval decision requires a separate
mapping that binds the exact Action, Resources, principal scope, and material
parameters. URL elicitation may carry a separate authentication flow, but the
returned continuation is not itself Authentication evidence until the declared
verifier establishes that evidence.

Sampling and roots are deprecated in MCP `2026-07-28`. A new binding should not
require them. A compatibility binding may require them while recording their
deprecated status and a migration target. Sampling requests and nested tool
loops should map model use, tools, authority, data disclosure, budgets,
termination, and observations explicitly. Roots remain informational and cannot
satisfy an AgSDL trust boundary, sandbox, or file-access policy.

### Subscriptions and catalog freshness

A binding that relies on list-change or resource-update notifications should
require `subscriptions/listen` and the relevant capability settings. It should
define reconnection, relisting, cache invalidation, maximum staleness, and the
behavior while the subscription is unavailable. The transport connection is
not the subscription identity.

A binding may omit subscriptions and use bounded relisting when that produces
the same declared portable behavior. Silent indefinite use of a stale catalog
is not a fallback.

## Degradation matrix

Each applicable row should become an explicit MCP degradation case. `Fail`
means the affected operation cannot support a positive readiness or execution
claim.

| Condition | Default outcome | Permitted declared alternative |
| --- | --- | --- |
| No mutually supported MCP revision | Fail | Select another predeclared binding variant |
| Modern server returns a supported-version error | Retry once under a mutually supported declared revision | Surface an actionable failure |
| Server is legacy | Fail for a modern-only binding | Select a separately declared legacy variant after the MCP probe |
| Required server capability or setting absent | Fail | None for the affected operation |
| Required client capability absent on a request | Fail | Use a predeclared flow that does not require it |
| Required MCP extension absent or incompatible | Fail | None for the affected operation |
| Optional MCP extension absent | Follow the extension contract and declared degradation case | Use core behavior only when both explicitly permit it |
| Mapped tool, resource, template, or prompt absent | Mark the mapping unsatisfied | Use a named alternative with equivalent behavior proven by adapter tests |
| Catalog-change subscription unavailable | Mark freshness requirement unsatisfied | Bounded relisting under the declared staleness limit |
| Authorization missing or invalid | Refuse the protected operation | Start the declared authorization branch |
| Scope insufficient | Refuse the protected operation | Bounded step-up authorization without expanding AgSDL authority |
| MRTR input kind unsupported | Fail the originating operation | Use a predeclared non-MRTR operation |
| Elicitation declined or cancelled | Follow the declared refusal or cancellation branch | None implicit |
| Sampling or roots required by a new binding | Report deprecated dependency | Use the declared migration binding |
| Task extension unavailable | Do not accept task results | Use a declared synchronous core result only if its behavior and limits match |
| Discovery, transport, or endpoint unavailable | Readiness indeterminate or failed according to the check boundary | Use a separately resolved endpoint |

## Resolution and conformance

Unresolved-document validation can check that the binding names an exact MCP
revision, protocol era, transport, directional capabilities, contract
references, entry mappings, authorization mode, degradation cases, and no
secret values. It cannot prove that the endpoint exists or supports them.

Resolved-graph validation can resolve immutable MCP and extension contract
references, check compatible identities and editions, select the endpoint and
credential references, and detect missing mappings. Network discovery produces
runtime or deployment evidence, not unresolved-document evidence.

A future MCP binding adapter should claim conformance only for named
implementation features. At minimum, executable suites should cover:

1. modern discovery and direct version-error negotiation;
2. rejection of an undeclared revision and separation of legacy fallback;
3. per-request client capability emission, missing-capability errors, and HTTP
   header-to-body mismatch rejection;
4. positive and negative tool, resource, prompt, and catalog-change mappings;
5. required and optional extension negotiation, including Tasks if claimed;
6. HTTP authorization discovery, audience checks, insufficient-scope recovery,
   token isolation, and refusal paths;
7. stdio credential injection without applying the HTTP authorization flow;
8. MRTR success, decline, cancellation, timeout, unsupported input, changed
   authorization, bounded retry, and opaque `requestState` handling; and
9. loss reports and trace correlation across every declared degradation case.

Passing structural checks would support only a mapping or readiness claim.
Behavioral interoperability requires execution against identified MCP client
and server implementations, exact contract and adapter versions, controlled
fixtures, and observable acceptance criteria. No such suite exists in AgSDL at
the time of this proposal.

## Requirements traceability

| Existing requirement | Contribution of this proposal |
| --- | --- |
| REQ-013 and REQ-014 | Separates the AgSDL, MCP core, MCP extension, adapter, and SDK version domains and makes compatibility directional |
| REQ-016 and REQ-017 | Defines exact external contract references and separates offline validation from endpoint discovery |
| REQ-018 through REQ-020 | Preserves extension identity, independent versioning, required support, and explicit fallback |
| REQ-021 through REQ-026 | Maps trust crossings, secret references, authority, approval, failure, and untrusted MCP content without assigning them to MCP capabilities |
| REQ-027 and REQ-028 | Requires observable correlation across discovery, authorization, calls, MRTR retries, subscriptions, and degradation |
| REQ-032 through REQ-035 | Defines a portable MCP binding requirement, deployment-specific resolution, and visible capability gaps |

This traceability identifies conceptual coverage. It is not conformance
evidence and does not close the unresolved implementation work in those
requirements.

## Conceptual example

This example illustrates information, not syntax.

A handbook assistant declares an MCP binding requirement for MCP `2026-07-28`
over Streamable HTTP. It requires the server `tools` and `resources`
capabilities, maps MCP tool `search_handbook` to the AgSDL Handbook lookup Tool
and Read handbook Action, and maps resource template
`handbook://pages/{page}` to Company handbook Knowledge. The binding does not
require prompts, sampling, roots, or extensions.

The HTTP authorization contract uses a credential reference resolved by the
deployment. A Policy application point still requires an AgSDL Authorization
decision for the employee Principal, Read handbook Action, and requested page.
An OAuth scope is evidence supplied to that decision, not the Authority grant.

The tool may return form elicitation through MRTR to disambiguate a search. The
example binding permits at most two retries. Decline ends with the declared
no-answer outcome.
The elicited text is untrusted input and cannot approve another Action. If the
server lacks `resources`, the system may still call `search_handbook` only when
the Tool result contract supplies the complete answer path; otherwise readiness
fails. This difference is declared before deployment.

## Consequences

The binding remains small because MCP owns its wire schemas. AgSDL adds only the
facts MCP does not own: system meaning, mappings, trust, authority, policy,
failure, and evidence. Exact revisions and explicit degradation make upgrades
more work, but they prevent a change in an external protocol from silently
changing portable behavior.

The proposal also prevents common category errors. MCP capability support is
not authority. An MCP resource is not automatically an AgSDL Resource. An MCP
prompt is not trusted Instructions. Elicitation is not approval. Roots are not
a sandbox. An MCP Task is not automatically an AgSDL Work item. A transport
session is not a conversation, and the current MCP revision has no protocol
session at all.

## Alternatives considered

### Copy the MCP schema into AgSDL

This would enable local shape checks but fork the authoritative external
contract and still omit AgSDL Actions, Effects, policy, and authority. A pinned
contract reference plus adapter tests is smaller and more accurate.

### Discover everything at runtime

Pure discovery cannot state which capabilities and entries the system needs,
whether their absence is safe, or which external changes alter portable
behavior. Discovery should resolve a declared requirement rather than create
one.

### Treat MCP as a generic tool transport

This loses resources, prompts, client capabilities, extensions, authorization,
subscriptions, MRTR, and version-era behavior. It also hides the difference
between transport delivery and protocol semantics.

### Define one binding for every MCP revision

The change from `2025-11-25` to `2026-07-28` removed initialization and sessions,
changed subscriptions and server-to-client interaction, and moved Tasks. One
binding with implicit fallback would make incompatible behavior look portable.

## Security considerations

MCP endpoints, catalogs, prompt content, tool metadata, resource content,
extension data, and continuation state cross trust boundaries. The binding
should identify those crossings and the controls applied to each. Discovery
identity is self-reported. Tool annotations are untrusted hints. Remote JSON
Schema references should not be fetched merely because an MCP entry contains
them.

Formal MCP extensions belong in the `extensions` capability map. Entries in an
`experimental` capability map should remain implementation-specific unless a
separate identified contract defines them. A binding should not treat an
experimental entry as stable MCP core behavior.

Authorization should preserve issuer and audience validation, resource
indicators, exact redirect handling, least-privilege scope selection, protected
token storage, and the MCP prohibition on token passthrough. URL elicitation
needs visible target identity and user control. Form elicitation should not
collect secrets. Sampling and nested tool loops need disclosure, authority,
budget, and termination controls.

Opaque `requestState`, task handles, cursors, subscription identifiers, and
resource URIs are untrusted external values. Implementations should bound their
size and lifetime, avoid logging secrets, and keep them scoped to the endpoint,
contract revision, principal, and operation that produced them.
When `requestState` affects authorization, resource access, or business logic,
the MCP server should meet the exact MCP integrity, expiry, principal-binding,
request-binding, and replay requirements. An AgSDL declaration cannot supply
those controls by itself.
When `requestState` affects authorization, resource access, or business logic,
the MCP server should meet the exact MCP integrity, expiry, principal-binding,
request-binding, and replay requirements. An AgSDL declaration cannot supply
those controls by itself.

## Compatibility impact

AgSDL has no normative syntax or published binding contract, so this proposal
breaks no conforming document. It constrains future syntax and adapter work to
represent exact external contracts, directional capability requirements,
explicit mappings, authorization separation, MRTR, and visible degradation.

MCP `2025-11-25` and earlier remain possible targets through separate legacy
binding variants. This proposal does not assert that a modern binding can be
translated to a legacy binding without loss.

## Unresolved questions

1. Should the first AgSDL syntax make protocol bindings a general reusable
   entity or a profile-specific subordinate record?
2. Which MCP entry mappings need stable AgSDL identities when catalogs are
   intentionally dynamic?
3. What minimum execution suite can test MRTR authorization re-evaluation
   without depending on a production OAuth service?
4. Should an MCP extension contract reference require an immutable content
   digest when the extension publishes no numbered edition?
5. Can one generic subscription freshness model cover MCP, event protocols, and
   framework-specific catalogs without losing their different guarantees?
6. Which AgSDL occurrence should correlate retries of one MRTR interaction while
   keeping each Action and Authorization decision independently auditable?
