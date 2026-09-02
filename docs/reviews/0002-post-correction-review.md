# Post-correction review 0002

- Status: completed
- Review date: 2026-09-02
- Review basis: corrected foundation integrated on
  `feature/integrate-foundation`

## Scope and method

This review rechecks findings B-01 through B-05 and I-01 through I-10 from
`docs/reviews/0001-cross-proposal-review.md`. It compares the corrected research
note and proposals with `docs/scope.md`, Decision 0001, and each other. The
proposals remain non-normative and pre-syntax.

`Resolved` means the cited correction removes the conflict or precision gap
identified by review 0001. `Partially resolved` means the correction narrows the
problem but leaves part of the original finding in force. `Open` means the
original finding still applies.

## Blocking findings

| Finding | Status | Corrected section and evidence |
| --- | --- | --- |
| B-01 | resolved | Proposal 0002, "System", "Topology", and "Relationship model". A one-agent system needs no topology, omitting topology declares no static participant graph, and `System uses Topology` now has cardinality `0..1`. This matches REQ-003 in proposal 0001. |
| B-02 | resolved | Proposal 0002, "Portable requirements and resolved bindings", "Relationship model", and "Deployment". Portable tool, memory, and state definitions declare binding requirements without selecting implementations. Resolved bindings belong to deployment resolution, and only a deployment claiming readiness must resolve every required binding. |
| B-03 | resolved | Proposal 0002, "Configuration profile", and proposal 0003, "Terms". The texts now distinguish `configuration profile`, which constrains one base definition or configuration profile, from `conformance profile`, which groups implementation features, normative requirements, and constraints. Neither can substitute for the other, and cross-reference between them remains an explicit open question. |
| B-04 | resolved | Proposal 0002, "Authorization requirement and decision"; proposal 0003, "Terms" and "Implementation-feature negotiation"; and proposal 0004, "Terms" and "Attested security capability claim". `Implementation feature`, `authority grant`, and `security capability claim` now have disjoint meanings. Negotiation concerns implementation features only, authority grants bound permitted actions, and security capability claims carry scoped assurance evidence. |
| B-05 | resolved | Proposal 0002, "Definitions, runtime instances, execution occurrences, and immutable artifacts", "Evaluation definition and result", "Trace requirement, execution trace, trace record, and trace artifact", "Deployment", "Package", and "Relationship model". The four subject categories are disjoint, have separate identity and version links, and the revised relations target each category explicitly. |

## Important findings

| Finding | Status | Corrected section and evidence |
| --- | --- | --- |
| I-01 | resolved | Proposal 0001, "Requirement conventions", "Mandatory requirements", and "Counter-cases and prohibited claims". Processor duties now apply only to a declared operation, validation phase, observed input boundary, and coverage statement. REQ-001, REQ-006, REQ-015, REQ-023, REQ-033, REQ-036, and REQ-038 use known findings or an explicit `unknown` result. Human reviewability is QUAL-009 with a documented review procedure. |
| I-02 | resolved | Proposal 0003, "Terms", "Proposed conformance model", and "Conformance suites". An implementation feature is first a named normative contract. Tests and inspection procedures provide evidence and trace to normative requirements; they do not define semantics. Feature identities cannot be published before their normative scope is stable. |
| I-03 | resolved | Proposal 0003, "Runtime conformance" and "Evidence boundaries". A runtime verdict is bounded to an identified configuration, suite version, fixtures, inputs, observations, and environment. The text keeps the implementation obligation but states that a passing verdict proves nothing about untested inputs, unobserved behavior, or other environments. |
| I-04 | resolved | Proposal 0003, "Document conformance" and "Validator conformance". The proposal separates unresolved-document validation from resolved-graph validation and assigns unavailable required, unavailable optional, mutable, invalid, and integrity-failing references to explicit verdict behavior. Validators must name the phase and cannot collapse the results. |
| I-05 | resolved | Proposal 0003, "Evidence boundaries", and proposal 0004, "Conformance implications". Security claims now use the six existing conformance subjects. Deployment and execution are evidence scopes, not new subjects, and the mapping table defines the permitted evidence for each subject. |
| I-06 | resolved | Proposal 0002, "Policy", and proposal 0004, "Declared policy" and "Least privilege and authority". Every effective policy set declares its unmatched-rule decision. The core supplies no implicit allow or deny default; a named security profile may require deny by default. |
| I-07 | resolved | Proposal 0004, "Terms", "Approvals and externally governed consent", and "Threat and control matrix". Approval remains a portable control-flow and authorization concept. Consent is an externally governed obligation, while legal sufficiency, accessibility, interface design, and related product duties belong to optional profiles, external policy systems, or external assurance. |
| I-08 | resolved | Prior-art note, "Decisions AgSDL will need to make" and "Overall conclusion". External standards are candidate mapping hypotheses. Each requires a separate proposal, semantic mapping, loss analysis, and executable tests before any integration, compatibility, or round-trip claim. |
| I-09 | resolved | Prior-art note, "Purpose and method" and the coverage-matrix rating definitions immediately before the matrix. Citations use published editions, tags, or commits when available. Living documentation records the reviewed commit, all sources share a retrieval date, and `Strong`, `Partial`, adjacent labels, and blank cells now have stated criteria. |
| I-10 | resolved | Proposal 0002, "Control flow", "Model-selected transition", and "Relationship model". Model-assisted choice now uses a closed allowed-successor set, declared selection authority, required observation, and failure policy without claiming a deterministic predicate or repeatable choice. |

## Vocabulary consistency check

The corrected foundation uses the required vocabulary consistently:

- `profile` is not left unqualified where the distinction matters.
  `Configuration profile` customizes a definition; `conformance profile` groups
  conformance contracts. A `security profile` is a named policy specialization,
  not a third interchangeable base concept.
- `implementation feature` denotes supported implementation behavior and a
  named normative conformance contract. It neither grants authority nor asserts
  a security property.
- `authority grant` denotes bounded permission for a principal, operation, and
  resource. It does not imply implementation support or enforcement evidence.
- `security capability claim` denotes a scoped assertion that an implementation
  can provide a security property. Attestation adds issuer, subject, validity,
  and verification evidence; the claim grants no authority.
- `definition` is a versioned description of intended structure or behavior.
- `runtime instance` is an addressable deployed realization with deployment and
  realized-definition identity. It is not an execution occurrence.
- `execution occurrence` is data created or observed during an execution and
  records applicable definition versions when known.
- `immutable artifact` is fixed content with a content identity or integrity
  reference. Sealing preserves it independently from the occurrence that
  created it.

The separation is also preserved in the relationship tables: definitions carry
portable relations, deployments establish runtime instances, execution and
evidence relations target occurrences, and package versions or trace artifacts
carry immutable content.

## Verdict

All blocking findings B-01 through B-05 are resolved. All important findings
I-01 through I-10 are resolved. The remaining questions are labelled as open
design questions and do not reintroduce the reviewed conflicts through a
cardinality, default, or positive conformance claim.

**Verdict: ready to integrate into `develop` as the AgSDL foundation.** This
verdict approves the corrected pre-draft research and proposals for integration.
It does not accept their proposed semantics as normative specification text and
does not authorize syntax or schema work ahead of Decision 0001.
