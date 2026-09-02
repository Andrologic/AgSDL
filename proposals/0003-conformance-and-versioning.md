# Proposal 0003: conformance and versioning

- Status: proposed
- Target: pre-draft conformance model
- Depends on: Decision 0001

## Problem

AgSDL needs testable conformance claims before it selects a serialization. A
single claim that a product "supports AgSDL" would hide which documents it can
inspect, which meanings it preserves, and which behavior it can execute.

Versioning has the same risk. The specification, a document, an extension, a
referenced component, and an adapter can change independently. Treating them as
one version would make compatibility claims ambiguous and upgrades unsafe.

This proposal defines the subjects of conformance, the evidence each claim
requires, and the compatibility rules that later normative text should express.
It does not define field names, a serialization, or a wire protocol.

## Scope

This proposal covers:

- conformance contracts for documents, producers, consumers, validators,
  runtimes, and adapters;
- the boundary between structural evidence and execution evidence;
- implementation-feature claims and conformance profiles;
- version identities and compatibility relations;
- unknown information, implementation-feature negotiation, deprecation, and
  test suites.

It does not certify implementation quality, security, performance, or fitness
for a particular deployment. Those properties need separate requirements and
evidence.

## Terms

The following terms are used consistently throughout this proposal.

- **Specification version** identifies one published set of AgSDL normative
  semantics.
- **Document version claim** identifies the specification version whose rules
  govern a document.
- **Extension** adds semantics outside the AgSDL core under an independently
  governed identity and version.
- **Referenced component** is a separately identified artifact used by a
  document and resolved outside that document.
- **Implementation feature** is a named normative contract for one testable
  unit of implementation behavior. Its contract cites the normative
  requirements that define its inputs, results, constraints, and applicable
  subject types. Tests and documented inspection procedures provide evidence
  for that contract; they do not define its semantics. This term does not mean
  an authority granted over a resource or a security assurance claim.
- **Conformance profile** is a named, versioned set of mandatory implementation
  features, normative requirements, and constraints used to make comparable
  conformance claims. It is distinct from a **configuration profile**, which
  constrains choices in a conceptual-model definition. Neither profile kind is
  interchangeable with the other. Whether one may reference the other remains
  an open question.
- **Preservation** means retaining information and identity without claiming to
  understand or execute its semantics.
- **Structural evidence** comes from inspecting artifacts without executing the
  described agentic system.
- **Execution evidence** comes from observed runs in a declared test
  environment.

## Proposed conformance model

Conformance is a claim about one identified subject, one specification version,
and one set of implementation features or one conformance profile. The claim
cites the applicable normative requirements and identifies the test-suite
version or documented inspection procedure used as evidence. A bare claim of
"AgSDL conformant" is incomplete.

Each report records the subject identity and version, the applicable
specification version, the claimed implementation features or conformance
profile, the test-suite identity and version or inspection procedure, the test
environment when execution occurred, the result of every applicable check, and
any unsupported or untested optional implementation feature.

No universal conformance level is proposed. Implementation-feature claims are
preferable because the subjects have different responsibilities. A conformance
profile is justified only when independent implementations need the same
interoperable subset and the normative scope of each included implementation
feature is stable. Each feature must have an executable test, a deterministic
structural test, or a documented inspection procedure when execution would be
unsafe or cannot be deterministic. Conformance profiles are not quality grades,
and their names must not imply that one conformance profile is universally
better than another. The project must not publish an implementation-feature
identity before its normative scope is stable.

### Document conformance

A document conforms to a specification version and, when claimed, to a
conformance profile. Unresolved-document validation examines the document as
supplied without fetching referenced components. It must:

- identify the governing specification version unambiguously;
- satisfy every applicable structural requirement;
- contain only core constructs, declared extensions, and references permitted
  by that specification version and conformance profile;
- meet all local cross-reference and reference-declaration constraints that can
  be checked without resolving external components;
- avoid claiming execution behavior as a property proven by document
  validation.

An unresolved-document conformance verdict proves that the artifact is
well-formed under the stated rules. It does not prove that a runtime can execute
it, that referenced components are available, or that executions satisfy the
declared goals.

Resolved-graph validation evaluates the graph produced by an identified
resolver environment. It checks resolved identities and versions, integrity
evidence, graph-wide constraints, and requirements that apply across component
boundaries. An unavailable required reference, an invalid resolved component,
an integrity failure, or an incompatible resolved version fails the
resolved-graph verdict. An unavailable optional reference does not invalidate
the unresolved document, but it prevents a positive resolved-graph verdict for
any implementation feature or operation that depends on that reference. The
report records the unaffected checks separately. A mutable reference may pass
unresolved-document validation, but a reproducible resolved-graph verdict must
record the exact resolved component and integrity evidence. An invalid reference
declaration fails unresolved-document validation; invalid resolved content fails
resolved-graph validation.

### Producer conformance

A producer conforms for each specification version and conformance profile it
claims. For every supported output mode, it must:

- emit conforming documents;
- declare every extension and external dependency it emits;
- emit version claims that match the semantics actually produced;
- avoid emitting a claimed implementation feature unless its required
  information is present;
- preserve required identity and version information during transformations.

Producer tests inspect a representative output corpus, including boundary cases
defined by the test suite. Passing examples alone cannot establish producer
conformance.

### Consumer conformance

A consumer conforms for each implementation feature it claims. It must:

- accept every conforming document within the claimed specification version and
  implementation-feature set;
- reject, preserve, or report unsupported information according to the unknown
  information rules below;
- interpret supported core semantics consistently with the specification;
- expose unsupported required implementation features before relying on the
  document;
- avoid silently changing semantics while reading or transforming a document.

A consumer that only reads metadata can conform for metadata implementation
features without claiming runtime or full-document support.

### Validator conformance

A validator conforms for a specification version, conformance profile, and
declared validation phase. It must:

- accept every structurally conforming artifact in its declared domain;
- reject every test-suite artifact that violates an applicable structural rule;
- identify the violated normative rule through a stable diagnostic category;
- distinguish invalid input from valid input that uses an unsupported extension
  or implementation feature;
- report checks that were skipped because they require resolution or execution.

The two document validation phases are unresolved-document validation and
resolved-graph validation. A validator must state which phase it performed and
must not collapse their results into one ambiguous document verdict. It cannot
issue an execution verdict without execution evidence.

### Runtime conformance

A runtime conforms only for explicitly claimed execution implementation
features and a declared specification version or conformance profile. A runtime
verdict is bounded to an identified runtime configuration, conformance-suite
version, fixture and input set, required observations, and test environment. The
implementation remains obligated to follow every normative requirement in its
claim, but a passing verdict does not prove compliance for untested inputs,
unobserved behavior, or other environments. Within that boundary, it must:

- reject a system before execution when a required implementation feature is
  unsupported;
- execute supported portable semantics as specified;
- enforce applicable lifecycle, policy, and failure behavior covered by the
  claimed implementation-feature set;
- produce the observations required by the conformance suite;
- identify adapter-dependent or implementation-specific behavior in its report.

Runtime conformance requires execution tests. Parsing and validation results are
necessary inputs but are not sufficient evidence.

### Adapter conformance

An adapter conforms for a declared source contract, target system and version,
AgSDL specification version, direction, and implementation-feature set. It must:

- define the mapping for every claimed implementation feature;
- preserve the portable meaning of mapped constructs;
- report every dropped, approximated, synthesized, or target-specific behavior;
- reject required semantics that it cannot preserve unless an explicit,
  testable degradation policy permits the mapping;
- pass round-trip tests when it claims reversible conversion;
- pass target execution tests when it claims behavioral equivalence.

Structural comparison can prove representation preservation. Only execution in
the target system can support a behavioral-equivalence claim. Even then, the
claim is bounded by the tested inputs, observations, target version, adapter
version, and environment.

## Evidence boundaries

Structural tests can verify:

- artifact shape, value domains, required information, and uniqueness;
- declared identities and versions;
- reference syntax, integrity metadata, and resolvability in a controlled
  resolver environment;
- graph constraints such as missing nodes, forbidden cycles, and incompatible
  declared requirements;
- extension declarations, implementation-feature declarations, and
  conformance-profile membership;
- deterministic transformations and loss reports;
- whether two normalized artifacts preserve the same declared information.

Structural tests cannot prove that tools are reachable, credentials authorize
an operation, models follow instructions, policies hold during a run, failures
recover as declared, or two runtimes behave equivalently.

Execution tests can verify observed behavior for specified fixtures, inputs,
dependencies, seeds where available, observation points, and acceptance
criteria. They cannot prove behavior for all future inputs or uncontrolled
external systems. A test report must label nondeterministic outcomes and state
the repetition and tolerance policy. Unsupported observations yield
"inconclusive," not "pass."

Security properties require their own threat model and evidence. Neither a
structural verdict nor a successful execution implies that a system is secure.
Security evidence must attach to an existing conformance subject or to a named
evidence scope that maps to one. Definition evidence maps to document or
validator claims. Producer and consumer security behavior maps to those subject
types. Deployment evidence records the resolved configuration and environment
used by a runtime claim. Execution evidence records the observations from a
bounded runtime test. Adapter-specific security behavior maps to an adapter
claim. A security assurance claim must identify its threat model, normative
requirements, subject, evidence scope, and evidence source. It is not an
implementation feature and does not grant authority.

## Version identities

### Specification versions

Each published specification has an immutable identity. Corrections that change
normative meaning require a new specification version. Editorial corrections
may update presentation metadata but must leave the immutable normative edition
available.

The first draft should delay choosing a version number format. Whatever format
is selected must support exact equality and an explicit compatibility relation;
ordering alone is insufficient.

### Document version claims

A document claims exactly one governing specification version. It may declare
additional compatibility claims only when a normative transformation or a
conformance test establishes them. A document revision is separate from its
document version claim, so editing a document does not imply a new specification
version.

### Extension versions

Every extension has a globally unambiguous owner-qualified identity, an
independent version, and a compatibility policy. Extension compatibility does
not inherit from the core specification. A conforming report lists the exact
extension versions used or the resolved versions when a permitted constraint is
declared.

### Referenced component versions

A referenced component has an identity, a version or immutable content identity,
and a resolution policy. Reproducible claims record the resolved component and
its integrity evidence. A mutable reference may be useful during authoring, but
it cannot support a reproducible conformance result unless the report captures
what was resolved.

### Adapter versions

An adapter version is independent of the specification and target-system
versions. Conformance reports identify all three. Updating a target framework
or provider invalidates behavioral evidence until the adapter suite passes
against the new target version.

## Compatibility rules

Compatibility is directional and implementation-feature-specific.

- A newer consumer is **backward compatible** with an older specification
  version only if it accepts all conforming documents in the claimed older
  implementation-feature set and preserves their portable meaning.
- An older consumer is **forward compatible** with a newer specification
  version only if it can process documents in the claimed newer
  implementation-feature set without rejecting or changing the meaning of
  required information it does not understand.
- A producer is backward-targeting only when it emits documents conforming to
  the older specification, rather than merely relabeling newer semantics.
- An adapter is compatible only for the intersection of implementation features
  proven for its source, mapping, and target contracts.

Adding an optional construct can be compatible for consumers that implement the
specified unknown-information policy. Adding a required construct, changing an
existing meaning, broadening an allowed value in a way closed consumers cannot
handle, or changing default behavior is incompatible unless an implementation
feature or conformance-profile boundary prevents affected implementations from
receiving it.

A conformance statement must say "backward" or "forward," name both versions,
and state the implementation-feature set. "Compatible" by itself has no
conformance meaning.

## Unknown information

Unknown core information and unknown extension information have different
failure modes.

A consumer encountering unknown information must classify it as required for
the requested operation, optional and safely ignorable under the governing
rules, or preservable but uninterpreted. It must stop before the requested
operation when required semantics are unknown. It may continue past optional
unknown information only when the specification or extension contract defines
that information as ignorable for that operation.

A transforming consumer must preserve preservable unknown information exactly
or issue a loss report before output. It must not move unknown information into
a context where its meaning could change. Validators report a declared but
unsupported extension separately from an undeclared extension and from invalid
core information.

These rules establish behavior without choosing how a future serialization
encodes fields or extension namespaces.

## Implementation-feature negotiation

Negotiation compares declared implementation-feature identities and versions
before an operation begins. The requesting side supplies required and optional
implementation features. The responding side returns the supported
intersection and any constraints. Execution proceeds only when every required
implementation feature has a compatible match.

Negotiation results are evidence of agreement, not proof of correct
implementation. Each side still needs conformance evidence for the
implementation features it advertises. Negotiation must fail explicitly on
ambiguous identities,
incompatible versions, or unmet required constraints. A fallback is allowed
only when the requester declared it in advance and the fallback has testable
semantics.

This proposal defines the negotiation semantics, not a transport or message
format.

## Deprecation

Deprecation warns of a planned compatibility change; it does not change current
semantics. A deprecation record identifies the affected normative item, the
first specification version carrying the notice, the replacement or migration
path when one exists, and the earliest version in which removal may occur.

Conforming implementations continue to support deprecated required behavior for
every specification version they claim. Producers should emit a diagnostic when
they create newly deprecated content. Consumers and validators should report
use without rejecting content that remains valid. Removal requires a new,
incompatible specification version and migration fixtures in the test suite.

Extensions and conformance profiles publish their own deprecation schedules.
Deprecation in one version domain does not silently deprecate another.

## Conformance suites

The project should publish a versioned suite for each specification version.
The suite should contain:

- positive and negative structural fixtures;
- expected diagnostic categories for invalid fixtures;
- implementation-feature-specific producer and consumer cases;
- resolver fixtures and resolved-graph cases;
- execution scenarios with observable acceptance criteria;
- adapter mapping, loss, round-trip, and target-execution cases;
- compatibility fixtures spanning supported version pairs;
- extension and unknown-information cases;
- machine-readable result metadata independent of any one test runner.

Every test identifies the normative requirement it exercises and the subject
types to which it applies. Tests that depend on external services declare those
dependencies and cannot be part of a deterministic core verdict. The suite
publishes its coverage gaps. A passing result establishes only the claims in the
suite version used.

Implementations may run additional tests, but those results remain separate
from the standard suite verdict. Certification, trademarks, and who may publish
official results are governance questions outside this proposal.

## Abstract verdict examples

These examples illustrate report meaning without establishing syntax.

1. A document receives `pass` for core structural conformance to specification
   version A and `unsupported` for extension E version 2. The document is not
   invalid solely because this validator lacks E.
2. A validator receives `fail` because it accepted a negative fixture with a
   dangling required reference. The report names the graph-integrity diagnostic
   category.
3. A consumer receives `pass` for preservation and `not claimed` for execution.
   It round-tripped an unknown optional extension but did not interpret it.
4. A runtime receives `inconclusive` for a recovery implementation feature
   because the test environment could not observe whether a remote tool call
   was duplicated.
5. An adapter receives `pass` for structural mapping, emits a separate loss
   report for an optional target-only annotation, and receives `not tested` for
   behavioral equivalence. It cannot claim equivalent execution.
6. A producer receives `fail` for backward targeting because its output carries
   the older version claim while relying on newer default behavior.

The standard verdict vocabulary should distinguish at least `pass`, `fail`,
`unsupported`, `not claimed`, `not tested`, and `inconclusive`. A later proposal
must define exact aggregation rules before these labels become normative.
`Pass with declared loss` is not an aggregate verdict. Introducing it remains
an open decision until normative rules define required and optional loss and
their effect on each conformance subject. Until then, a verdict and a loss
report remain separate.

## Consequences

This model makes conformance claims longer but auditable. Implementers can ship
partial support without pretending to support the whole language. Users can
compare products by implementation feature and evidence. The cost is a
maintained registry of implementation features, conformance profiles,
diagnostics, compatibility relations, and tests.

The model also blocks several shortcuts. Schema validation cannot stand in for
semantic validation, runtime execution, or adapter equivalence. Version order
cannot stand in for compatibility. Negotiated support cannot stand in for
tested support.

## Alternatives considered

### One conformance badge

A single badge is easy to communicate but cannot distinguish parsing,
validation, execution, and adaptation. It would reward vague claims and make
failures hard to diagnose.

### Ordered conformance levels

Levels such as basic, intermediate, and complete suggest a universal progression
that does not exist across subject types. Implementation-feature sets and
conformance profiles produce claims that tests can verify directly.

### Semantic versioning for every version domain

Mandating one numbering convention now would confuse numbering with a defined
compatibility relation. The project can select a notation after it knows what
changes are compatible in each domain.

### Ignore all unknown information

This improves forward acceptance at the cost of silent semantic loss. The
required, ignorable, and preservable classification gives consumers a safe and
testable choice.

## Security considerations

False conformance claims can cause a runtime to execute unsupported policy or
permission semantics. Required implementation features therefore fail closed
before execution. Test reports identify the implementation, environment,
dependencies, and versions so results cannot be transferred silently to a
different setup.

Resolvers and extensions cross trust boundaries. Structural validity does not
authorize retrieval or execution. Conformance suites must use controlled
fixtures and must not require implementations to fetch untrusted resources.

## Compatibility impact

The project has no published syntax or compatibility promise, so adopting this
proposal breaks no existing AgSDL contract. It constrains later designs by
requiring explicit version identities, directional compatibility claims,
unknown-information behavior, and testable implementation-feature boundaries.

## Decisions to avoid in the first draft

The first draft should leave these choices reversible until implementation
experience and conformance fixtures exist:

- a universal numeric version scheme for every version domain;
- an assumption that version ordering implies compatibility;
- a closed list of implementation features or conformance profiles;
- a single global conformance badge or linear maturity scale;
- one mandated negotiation transport;
- a serialization-specific rule for unknown fields or extension namespaces;
- permanent diagnostic codes before the normative requirements stabilize;
- a promise that round-trip preservation implies behavioral equivalence;
- a certification authority, trademark policy, or paid compliance program;
- a fixed support lifetime or deprecation interval without release experience.

## Unresolved questions

1. Which core implementation features are small enough to test independently
   but useful enough to advertise?
2. Does the first public draft need any named conformance profile, or are
   implementation-feature claims sufficient?
3. Which compatibility relations should the project publish, and for how many
   prior specification versions?
4. What artifact normalization, if any, is needed for preservation and
   round-trip tests after a serialization is chosen?
5. Which observations form the deterministic minimum for runtime tests?
6. How should test-suite errata affect previously published verdicts?
7. Which party signs or attests conformance reports, if any?
