# Cross-proposal review 0001

- Status: completed
- Review date: 2026-09-02
- Reviewed branches: `feature/prior-art-research`,
  `feature/requirements-and-use-cases`, `feature/core-conceptual-model`,
  `feature/conformance-and-versioning`, and
  `feature/trust-security-and-control`

## Review basis

This review compares the five deliverables with the repository scope, Decision
0001, and each other. It treats every proposal as non-normative and does not
assume a serialization. Findings are ordered by severity. A blocking finding
would make two accepted proposals require incompatible implementations or would
prematurely settle a core semantic boundary. An important finding can be fixed
without redesigning the whole proposal. An improvement strengthens precision or
maintainability but need not delay integration on its own.

The prior-art version claims for MCP 2026-07-28, OpenAPI 3.2.0, OpenTelemetry
1.60.0, and OpenTelemetry Semantic Conventions 1.44.0 were checked against their
official project pages on the review date.

## Blocking findings

### B-01: one-agent systems are forced to have a topology

- Files and sections: `proposals/0001-requirements-and-use-cases.md`,
  "Comprehension and identity", REQ-003; and
  `proposals/0002-core-conceptual-model.md`, "Relationship model".
- Conflict: REQ-003 requires a complete one-agent system without a synthetic
  multi-agent topology. The relationship table requires every `System` to use
  exactly one `Topology`. The topology definition also requires at least one
  addressable node, so the requirement is substantive rather than an optional
  empty aggregate.
- Required correction: change `System --uses--> Topology` to `0..1`, or define a
  topology as a general system interaction graph and explain why the one-agent
  case has portable topology semantics. The first option matches REQ-003 and
  imposes less authoring burden.

### B-02: portable definitions require deployment bindings

- Files and sections: `proposals/0001-requirements-and-use-cases.md`, "Deployment,
  portability, and import", REQ-032 and REQ-034; and
  `proposals/0002-core-conceptual-model.md`, "Tool", "Memory", "State", and
  "Relationship model".
- Conflict: the requirements separate portable meaning from runtime bindings.
  The conceptual cardinalities nevertheless require every tool and memory to be
  implemented or backed by at least one runtime or environment element, and
  every state definition to be managed by at least one runtime. A portable
  reusable package therefore cannot resolve without selecting implementation
  objects.
- Required correction: make these binding relations optional in the conceptual
  graph. Put the `1..*` obligation on a resolved deployment that claims the
  corresponding component is executable. Define a distinct validation result
  for a portable definition and for a deployment resolution.

### B-03: `profile` has two incompatible meanings

- Files and sections: `proposals/0002-core-conceptual-model.md`, "Profile"; and
  `proposals/0003-conformance-and-versioning.md`, "Terms" and "Proposed
  conformance model".
- Conflict: proposal 0002 defines a profile as constrained choices applied to
  exactly one base definition or profile. Proposal 0003 defines it as a named,
  versioned set of mandatory capabilities and constraints used across
  conformance subjects. The latter has no base-definition requirement and may
  describe processor behavior rather than customize a definition. One exact
  term cannot support both identity, composition, and conformance rules.
- Required correction: reserve `profile` for one concept. A practical split is
  `configuration profile` for proposal 0002 and `conformance profile` for
  proposal 0003. Define whether either can reference the other, but do not make
  them interchangeable.

### B-04: `capability` changes meaning across conformance and security

- Files and sections: `docs/research/prior-art.md`, "Gaps in current prior art"
  and "Decisions AgSDL will need to make";
  `proposals/0003-conformance-and-versioning.md`, "Terms" and "Capability
  negotiation"; and `proposals/0004-trust-security-and-control.md`, "Terms" and
  "Attested capability".
- Conflict: the research explicitly leaves `capability` for definition. Proposal
  0003 then makes it a testable unit of implementation behavior. Proposal 0004
  first defines it as bounded authority over a resource, then uses "attested
  capability" for an implementation's claimed security property. Negotiating
  these values could consequently confuse supported behavior, granted authority,
  and evidence of enforcement.
- Required correction: use three terms with disjoint definitions, for example
  `implementation feature`, `authority grant`, and `security capability claim`.
  Update negotiation, profiles, and attestations to name the relevant kind. Keep
  the final vocabulary open until one terminology proposal reconciles all five
  documents.

### B-05: the occurrence model classifies durable artifacts inconsistently

- Files and sections: `proposals/0002-core-conceptual-model.md`, "Definitions and
  occurrences", "Knowledge", "State", "Trace", and "Deployment".
- Conflict: an occurrence is defined as data created or observed during an
  execution, yet package artifacts are neither definitions nor occurrences,
  embedded knowledge can be a package artifact, and a deployed instance is
  called a runtime occurrence. A deployed instance is not data created during an
  execution, and an artifact generated by an execution may outlive it. Evidence
  and versioning cannot reliably target this partition.
- Required correction: distinguish at least definitions, runtime instances,
  execution occurrences, and immutable artifacts. State which identities and
  version links each category carries. Then revise the `Evaluation`, `Trace`,
  `Package`, and `Deployment` relations to target those categories explicitly.

## Important findings

### I-01: several mandatory requirements are not bounded by a claim or operation

- File and section: `proposals/0001-requirements-and-use-cases.md`, "Mandatory
  requirements", especially REQ-001, REQ-006, REQ-015, REQ-023, REQ-033,
  REQ-036, and REQ-038.
- Problem: phrases such as "a person must be able", "each detected violation",
  and "identify changes in portable meaning" do not define a finite input domain,
  supported operation, or completeness criterion. REQ-036 appears to require an
  importer to report every omitted behavior, including behavior it cannot
  observe. These are valuable goals but cannot all support repeatable
  conformance tests as written.
- Required correction: bind processor obligations to declared capabilities,
  source boundaries, validation phases, and known findings. Replace exhaustive
  claims about hidden source behavior with a required coverage statement and an
  explicit unknown category. Move human readability to a quality goal with a
  documented review rubric.

### I-02: conformance depends on a test suite before defining the normative unit

- File and section: `proposals/0003-conformance-and-versioning.md`, "Terms",
  "Proposed conformance model", and "Conformance suites".
- Problem: every capability is defined by a conformance test and every claim must
  name a test-suite version, but normative requirements and capability
  aggregation remain open. This reverses the dependency: tests should trace to
  settled normative behavior rather than create the capability boundary.
- Required correction: define a capability as a named normative contract first.
  Require a claim to cite the applicable normative items and the suite used as
  evidence. Permit documented inspection procedures where execution would be
  unsafe or cannot be deterministic. Do not publish capability identities until
  their normative scope is stable.

### I-03: runtime conformance promises more than executions can establish

- File and section: `proposals/0003-conformance-and-versioning.md`, "Runtime
  conformance" and "Evidence boundaries".
- Problem: a runtime must "execute supported portable semantics as specified"
  and enforce all covered lifecycle and failure behavior. Later text correctly
  limits execution evidence to fixtures, inputs, observations, and tolerances.
  The unqualified obligation can be read as proof over all executions, which is
  impossible for nondeterministic agents and uncontrolled dependencies.
- Required correction: define runtime conformance as passing the required suite
  for an identified runtime configuration and evidence boundary. Keep an
  independent implementation obligation to follow the specification, but state
  that the verdict does not prove universal behavioral compliance.

### I-04: document conformance and reference availability are not cleanly split

- File and section: `proposals/0003-conformance-and-versioning.md`, "Document
  conformance", "Evidence boundaries", and "Referenced component versions".
- Problem: document conformance requires all checkable cross-reference and
  integrity constraints, yet it expressly does not prove referenced components
  are available. No result distinguishes an unresolved but structurally valid
  reference from a failed resolved-document claim. This also conflicts with the
  requirements proposal's incomplete-package and offline-validation cases.
- Required correction: name separate unresolved-document and resolved-graph
  validation phases. Specify which phase can claim document conformance and how
  unavailable optional, unavailable required, mutable, and integrity-failing
  references affect each verdict.

### I-05: security conformance introduces four subjects that do not map to the
main conformance model

- Files and sections: `proposals/0003-conformance-and-versioning.md`, "Proposed
  conformance model"; and `proposals/0004-trust-security-and-control.md`,
  "Conformance implications".
- Problem: proposal 0003 defines document, producer, consumer, validator,
  runtime, and adapter conformance. Proposal 0004 defines definition, capability,
  deployment, and execution conformance. Only runtime has an evident partial
  match. Reports could issue similarly named verdicts with different subjects
  and evidence.
- Required correction: express the security claims as capability-specific claims
  of the proposal 0003 subjects, or add deployment and execution evidence as
  explicit evidence scopes rather than new conformance subjects. Provide a
  mapping table before either proposal is accepted.

### I-06: deny by default is promoted from a security profile choice to a core
policy rule

- Files and sections: `proposals/0004-trust-security-and-control.md`, "Declared
  policy" and "Least privilege and authority"; and
  `proposals/0002-core-conceptual-model.md`, "Policy".
- Problem: proposal 0004 says policy should deny by default when no grant exists.
  Proposal 0002 deliberately leaves deny and conflict behavior explicit for each
  applicable policy set. A universal default would be a material semantic
  decision and could invalidate descriptive imports of systems with another
  default.
- Required correction: keep the core free of an implicit decision. Require every
  effective policy set to declare its default. A security profile may require
  deny by default and may reject deployments that cannot enforce it.

### I-07: the security proposal mixes portable requirements with legal and
product obligations

- File and section: `proposals/0004-trust-security-and-control.md`, "Consent and
  approvals", "Actor and asset model", and "Threat and control matrix".
- Problem: informed and non-coercive consent, accessibility, legal basis, data
  rights, and affected-person testing depend on jurisdiction, product context,
  and user interface evidence. Making their complete vocabulary part of the core
  would exceed a portable system description and cannot be tested by AgSDL
  alone.
- Required correction: keep `approval` as a portable control-flow and
  authorization concept. Model `consent requirement` as an externally governed
  policy obligation with issuer, jurisdiction or policy profile, subject,
  purpose, and evidence reference. Move detailed legal and human-factors
  controls to optional profiles.

### I-08: the prior-art conclusion turns mappings into recommendations too early

- File and section: `docs/research/prior-art.md`, "Overall conclusion".
- Problem: the note says AgSDL can use A2A, MCP, AsyncAPI, OpenTelemetry, OPA,
  SPDX, SLSA, and OCI for named responsibilities. The repository rules treat
  these as external systems until integrations are implemented and tested. No
  mapping or round-trip evidence exists yet, and OPA-compatible policy decision
  points are only one enforcement architecture.
- Required correction: recast the paragraph as candidate mapping hypotheses.
  State that each needs a separate proposal, semantic mapping, loss analysis,
  and executable tests before AgSDL can claim integration or compatibility.

### I-09: the prior-art source policy does not preserve reproducibility

- File and section: `docs/research/prior-art.md`, "Purpose and method", "Open
  Policy Agent and Rego", and "OCI Image and Distribution specifications".
- Problem: the note records an access date but several citations point to
  unversioned documentation or the `main` branch. Future readers cannot recover
  the exact text reviewed. The matrix also gives evaluative ratings such as
  `Strong` without criteria, which makes independent review difficult.
- Required correction: cite immutable release editions or commit identifiers
  where available. For living documentation, record the retrieved revision or
  archived snapshot. Define what `Strong`, `Partial`, and adjacent coverage mean,
  then cite the supporting section for disputed matrix entries.

### I-10: the conceptual model overstates control-flow determinism

- Files and sections: `docs/research/prior-art.md`, "Gaps in current prior art";
  and `proposals/0002-core-conceptual-model.md`, "Protocol", "Control flow", and
  "Cycle rules".
- Problem: the research leaves the boundary between deterministic and
  model-selected orchestration open. The conceptual model requires every
  nonterminal step and protocol state to enumerate successors or waits and every
  branch condition to have portable meaning. It does not model a bounded
  model-selected transition whose choice is intentionally nondeterministic.
- Required correction: add an explicit unresolved transition-selection concept
  or mark model-selected choice as an open question. Require the definition to
  declare the allowed successor set, selection authority, observation, and
  failure boundary without claiming a deterministic branch predicate.

## Improvements

### A-01: separate protocol, interface, topology, and control-flow examples

- File and section: `proposals/0002-core-conceptual-model.md`, "Interface",
  "Protocol", "Topology", and "Control flow".
- Improvement: add one syntax-free example that shows an interface operation, a
  multi-message protocol, a permitted topology edge, and an invocation step as
  four separate facts. Include a one-agent example in which only the applicable
  facts exist. This will expose accidental duplication before cardinalities
  become normative.

### A-02: name the tool, skill, and advertised service boundaries explicitly

- Files and sections: `docs/research/prior-art.md`, "Agent Skills" and "Gaps in
  current prior art"; and `proposals/0002-core-conceptual-model.md`, "Tool" and
  "Skill".
- Improvement: retain the proposed tool operation contract and packaged
  behavioral skill, but add a separate open term for an externally advertised
  service such as an A2A skill. State that tool availability, skill assignment,
  advertised service, authority grant, and runtime support are independent.

### A-03: reduce the core security inventory before acceptance

- File and section: `proposals/0004-trust-security-and-control.md`, "Threat and
  control matrix" and "Unresolved questions".
- Improvement: tag each matrix row as a candidate core requirement, profile
  requirement, deployment check, or external assurance concern. The existing
  matrix is useful, but accepting all rows as one core obligation would make a
  minimal single-agent description disproportionately large.

### A-04: preserve verdict composition as an open decision

- File and section: `proposals/0003-conformance-and-versioning.md`, "Abstract
  verdict examples".
- Improvement: keep the proposed verdict words illustrative and add a rule that
  `pass with declared loss` cannot be introduced as an aggregate verdict until
  the required versus optional loss boundary is defined. A plain `pass` plus a
  separate loss report is easier to compare across subjects.

## Decisions that can remain open

The following questions need not block integration of corrected proposals:

- the eventual serialization, field names, and concrete identity notation;
- the numeric version format and the number of prior versions supported;
- the initial registry of conformance capabilities and named profiles;
- whether credentials become a top-level entity;
- the exact telemetry protocol and minimum trace event set;
- resolver technology, package transport, signature format, and attestation
  issuer;
- a portable vocabulary for side-effect severity;
- certification, trademarks, and publication governance.

They must stay labelled as open questions. None should leak into cardinalities,
default behavior, or a positive conformance verdict before a proposal and tests
settle it.

## Branch verdicts

| Branch | Verdict | Conditions |
| --- | --- | --- |
| `feature/prior-art-research` | Prête avec correction mineure | Recast integration recommendations as hypotheses, make citations reproducible, and define matrix ratings. |
| `feature/requirements-and-use-cases` | Prête avec correction mineure | Bound processor obligations to declared operations and observable source coverage; move subjective human readability out of mandatory conformance. |
| `feature/core-conceptual-model` | À reprendre | Resolve B-01, B-02, B-03, and B-05, then reconcile model-selected transitions and the tool, skill, capability boundary. |
| `feature/conformance-and-versioning` | À reprendre | Resolve the profile and capability collisions, align security evidence subjects, and separate unresolved-document from resolved-graph verdicts. |
| `feature/trust-security-and-control` | À reprendre | Separate authority from implementation capability, map security evidence to the main conformance model, and move legal or product-specific controls into profiles. |
