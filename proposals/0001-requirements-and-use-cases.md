# Proposal 0001: requirements and use cases

- Status: proposed
- Date: 2026-09-02

## Summary

AgSDL needs a requirements baseline before it defines a conceptual model or a
serialization. This proposal identifies the people and software that use an
AgSDL description, the operations they need to perform, and the boundary
between portable description and runtime behavior.

The proposal covers systems with one agent and systems with several agents. It
defines stable identifiers for requirements, quality goals, non-goals, use
cases, and constraints. These identifiers are local to this proposal. An
accepted proposal would guide later normative text, schemas, examples, and
conformance tests, but would not make this document normative by itself.

## Problem

Framework-specific code often mixes system intent, portable structure, runtime
configuration, and implementation details. Readers cannot reliably tell which
parts another implementation can preserve. Tools also lack a shared basis for
validation, comparison, migration, governance, and evaluation.

A syntax-first design would hide this problem behind field names. AgSDL instead
needs a testable account of what a description must express and what conforming
software must be able to do with it.

## Scope

This proposal defines requirements for the AgSDL model and for future
conforming processors. It does not define a file format, concrete grammar,
runtime API, transport, or framework adapter.

The same model must describe:

- a single agent with its resources, controls, and runtime requirements;
- a multi-agent system with topology, routing, delegation, handoffs, and shared
  or isolated resources;
- a complete system and a reusable fragment intended for composition;
- portable concepts and explicitly identified implementation-specific
  extensions.

## Proposed semantics

AgSDL defines the portable meaning of declared system facts and relationships.
It also defines how processors expose missing information, unsupported
concepts, extensions, and target bindings. An AgSDL description states intent,
requirements, and evidence. A runtime or adapter remains responsible for
implementing those declarations and proving its own conformance.

Later normative work should derive the conceptual model from the mandatory
requirements below. It may split capabilities into profiles or conformance
levels, but any split must keep unsupported information and loss visible.

## Terms used in this proposal

An **AgSDL description** is a representation of an agentic system or reusable
fragment according to the future AgSDL specification.

An **AgSDL processor** is software that reads an AgSDL description for an
operation such as validation, comparison, composition, exchange, import, or
deployment planning.

A **portable meaning** is the meaning that conforming processors are expected
to preserve independently of a framework, provider, transport, or runtime.

An **external reference** identifies material outside the containing
description. The referenced material may be another AgSDL description or a
resource governed by another specification.

An **extension** adds information outside the portable model while remaining
identifiable as an extension.

A **runtime binding** maps a described concept to an implementation, service,
artifact, credential source, endpoint, or deployment facility.

## Users and required operations

### System authors and maintainers

Authors describe a system boundary, its agents, resources, relationships,
controls, and lifecycle. Maintainers compare revisions, replace components,
compose reusable fragments, and assess whether a change preserves portable
meaning.

### Reviewers, operators, and governors

Human reviewers inspect ownership, permissions, trust boundaries, approval
points, failure policies, and deployment requirements. Operators resolve
runtime bindings and compare declared observability or evaluation needs with
what a target environment provides. Governance and security teams identify
unresolved risks without executing the system.

### Tool and runtime implementers

Tool implementers parse, validate, index, compare, compose, package, and
exchange descriptions. Runtime and adapter implementers map portable concepts
to target capabilities, report unsupported concepts or information loss, and
keep target-specific behavior separate from portable claims.

### Evaluators and auditors

Evaluators associate tests, datasets, metrics, thresholds, and evidence with a
system or component. Auditors connect observed events and evaluation results to
stable described identities and versions.

## Information inventory

The model must be able to carry or reference the following information when it
is relevant to the described system:

- system identity, purpose, boundary, owners, lifecycle state, inputs, outputs,
  and interfaces;
- agent identity, role, instructions, model requirements, tools, skills,
  knowledge, memory, and state;
- topology, communication, routing, delegation, handoffs, coordination, and
  failure handling;
- permissions, credential references, policies, guardrails, trust boundaries,
  human decisions, and escalation paths;
- runtime capabilities, deployment targets, resource needs, placement,
  availability, and lifecycle hooks;
- events, traces, logs, metrics, evaluation definitions, test evidence, and
  conformance claims;
- versions, dependencies, external references, packages, profiles, runtime
  bindings, and extensions.

This inventory identifies subject matter. It does not imply that every
description must contain every category or that the listed categories are the
final entities of the conceptual model.

## Requirement conventions

`REQ-*` identifies a proposed mandatory capability. A later specification must
make each applicable requirement enforceable through normative text and a
conformance test or documented inspection procedure.

`QUAL-*` identifies a quality goal. Quality goals guide design choices but need
measurable acceptance criteria before they can support conformance claims.

`NG-*` identifies a non-goal. `UC-*` identifies a use case. `CON-*` identifies
an explicit constraint. The traceability table links every requirement and
quality goal to at least one use case or constraint.

## Mandatory requirements

### Comprehension and identity

- **REQ-001 Human-readable meaning.** A person must be able to inspect an AgSDL
  description and determine its declared system purpose, boundary, principal
  components, relationships, ownership, and controls without executing it.
  Conformance evidence must include an inspection procedure for those facts.
- **REQ-002 Stable identity.** The model must support stable identities for a
  system and for components that other parts of a description, external
  descriptions, observations, or evaluation evidence need to address.
  Validation must reject an ambiguous reference within its declared scope.
- **REQ-003 Single-agent completeness.** The model must represent a system with
  one agent, including the agent's interfaces, resources, controls, runtime
  requirements, observability, and evaluation needs, without introducing a
  synthetic multi-agent topology.
- **REQ-004 Multi-agent completeness.** The model must represent several agents
  and their topology, routing, delegation, handoffs, communication constraints,
  shared resources, isolated resources, and system-level controls.
- **REQ-005 Declared and absent information.** The model must distinguish a
  value declared by the author, a value inherited or resolved from a reference,
  an explicitly unspecified value, and information that the model does not
  express. A processor must not silently invent portable meaning for absent
  information.

### Validation and conformance

- **REQ-006 Structural validation.** A processor must be able to report whether
  a description satisfies the structural rules of its declared AgSDL version
  and must identify each detected violation by location and rule.
- **REQ-007 Semantic validation.** The specification must define checkable
  cross-component constraints, including reference integrity, identity
  uniqueness, required relationships, and incompatible declarations. A
  processor must report every violation it detects without treating runtime
  success as proof of validity.
- **REQ-008 Validation profiles.** Validation must distinguish the portable
  core from optional profiles, extensions, and target-specific checks. A report
  must identify which rule sets it applied.
- **REQ-009 Conformance claims.** A description and processor must be able to
  state the AgSDL version, profiles, extension support, and conformance level
  they claim. Claims must be inspectable and must not imply runtime guarantees
  outside the tested level.

### Composition, exchange, and lifecycle

- **REQ-010 Composition.** The model must support assembling a system from
  reusable descriptions or fragments. Composition rules must define identity
  scope, reference resolution, conflict detection, and the resulting portable
  meaning. Unresolved conflicts must produce diagnostics rather than implicit
  precedence.
- **REQ-011 Dependency boundaries.** A composed description must identify each
  dependency and whether it is embedded, externally resolved, optional, or
  supplied by a deployment environment.
- **REQ-012 Exchange completeness.** A processor that exports or packages a
  description must report which dependencies are included, omitted, externally
  referenced, or unavailable. A receiver must be able to detect an incomplete
  package before claiming full validation.
- **REQ-013 Version identity.** The model must identify the AgSDL language
  version and support distinct versions of systems, components, dependencies,
  and extensions where those distinctions affect resolution or meaning.
- **REQ-014 Compatibility assessment.** The specification must define how a
  processor reports compatible, incompatible, and indeterminate version
  relationships. It must not equate successful parsing with semantic
  compatibility.
- **REQ-015 Change comparison.** A processor must be able to compare two
  descriptions and identify changes in portable meaning separately from
  changes confined to extensions, runtime bindings, or presentation.

### References and extensions

- **REQ-016 External references.** External references must identify the target,
  the expected kind of target, and the resolution or integrity information
  needed by the applicable profile. Processors must report unresolved,
  mismatched, or integrity-failing references.
- **REQ-017 Controlled resolution.** Reference resolution must be explicit about
  its base, resolver, and permitted sources. Validation must be possible in a
  mode that performs no network access or other external retrieval.
- **REQ-018 Identifiable extensions.** Every extension must have an unambiguous
  owner or namespace and a version or compatibility identity. A processor must
  distinguish recognized, unrecognized, required, and optional extensions.
- **REQ-019 Extension preservation.** A processor that rewrites or exchanges a
  description must either preserve unrecognized extensions without claiming to
  understand them or report their loss. It must not silently reinterpret an
  extension as portable meaning.
- **REQ-020 Portable fallback.** When an extension is optional, the description
  must define or reference the portable meaning that remains without it. When
  no such meaning exists, the extension must be marked as required for the
  relevant operation.

### Security and human control

- **REQ-021 Security boundaries.** The model must represent principals, trust
  boundaries, permissions, protected resources, credential references, policy
  points, and the operations to which controls apply.
- **REQ-022 Secret separation.** AgSDL must support references to secrets and
  credential sources without requiring secret values in a description. A
  processor must be able to inspect and validate a description without
  resolving secret values.
- **REQ-023 Least-authority analysis.** The model must expose enough information
  for a processor or reviewer to compare declared component operations with
  granted permissions and report excessive, missing, or indeterminate access.
- **REQ-024 Human supervision.** The model must represent human approval,
  review, override, interruption, and escalation points, including the actor,
  triggering condition, permitted decision, timeout or absence policy, and
  effect on system flow.
- **REQ-025 Failure and safety policy.** The model must represent the required
  response to denied actions, unavailable dependencies, invalid outputs,
  control failures, and exhausted limits. It must allow a reviewer to
  distinguish fail-closed, fail-open, retry, degrade, and escalate policies.
- **REQ-026 Untrusted content boundary.** The model must identify inputs,
  instructions, tool results, retrieved knowledge, and messages that cross a
  trust boundary, together with the controls expected at that boundary.

### Observability and evaluation

- **REQ-027 Observable identity.** The model must associate declared events,
  traces, logs, metrics, and evaluation evidence with stable system, component,
  operation, and version identities.
- **REQ-028 Observability requirements.** A description must be able to declare
  required event classes, correlation relationships, redaction rules, retention
  constraints, and metric definitions without prescribing a telemetry vendor.
- **REQ-029 Evaluation definition.** The model must represent evaluation scope,
  inputs or dataset references, procedure, metrics, thresholds, expected
  evidence, environment assumptions, and the system version under evaluation.
- **REQ-030 Result separation.** Evaluation definitions, recorded results, and
  conformance claims must remain distinct. A declared evaluation or threshold
  must not imply that a system passed it.
- **REQ-031 Behavioral uncertainty.** The model must let authors state expected
  or prohibited outcomes and probabilistic quality targets while preserving the
  distinction between a declaration, an observed result, and a runtime
  guarantee.

### Deployment, portability, and import

- **REQ-032 Runtime requirements.** The model must describe required runtime
  capabilities, resource constraints, supported environments, placement,
  lifecycle, and availability needs without naming a specific implementation
  unless the declaration is explicitly a runtime binding or extension.
- **REQ-033 Deployment planning.** A processor must be able to compare declared
  requirements with a target environment and report satisfied, unsatisfied, and
  indeterminate requirements before deployment.
- **REQ-034 Binding separation.** Runtime bindings must remain distinguishable
  from portable meaning. Replacing a binding must not appear to change portable
  meaning unless the replacement also changes a portable declaration.
- **REQ-035 Capability gaps.** An adapter or deployment processor must report
  unsupported concepts, approximations, substitutions, and information loss.
  It must not claim portable equivalence when a gap remains.
- **REQ-036 Framework import.** An importer must identify the source framework
  and version, the source artifacts examined, each mapped portable concept,
  each generated extension, each unresolved value, and each omitted or
  unsupported behavior.
- **REQ-037 Import provenance.** Imported descriptions must retain enough
  provenance to repeat or audit the import and to distinguish imported facts
  from author-supplied corrections or later edits.
- **REQ-038 Round-trip accounting.** Import and export tools must be able to
  report which information can round-trip to a target framework and which
  information will change or be lost. Round-trip success must not by itself
  establish behavioral equivalence.

## Quality goals

- **QUAL-001 Determinism.** Given the same description, declared dependencies,
  resolver inputs, version, profiles, and extension support, conforming
  processors should produce the same portable interpretation and structural
  validation outcome.
- **QUAL-002 Diagnostic precision.** Diagnostics should identify the affected
  component or relationship, the violated rule, and a correction path without
  exposing secret values.
- **QUAL-003 Minimal description burden.** A complete single-agent description
  should not require multi-agent, deployment, or extension declarations that do
  not apply to it.
- **QUAL-004 Reviewability.** Security, human-control, deployment, and
  portability declarations should be discoverable without reconstructing them
  from unrelated fragments.
- **QUAL-005 Loss visibility.** Every transformation should make dropped,
  approximated, unresolved, or target-specific information visible in its
  result or report.
- **QUAL-006 Offline inspectability.** A reviewer should be able to inspect the
  system boundary, declared controls, dependency inventory, and unresolved
  references without network access, secret access, or system execution.
- **QUAL-007 Scale tolerance.** Identity, references, composition, and
  diagnostics should remain usable for both a small one-agent description and a
  system composed from many agents and reusable packages. Concrete performance
  targets remain profile-specific.
- **QUAL-008 Evolvability.** New optional concepts should be introducible through
  versioned profiles or extensions while older processors can still identify
  what they do not understand.

## Non-goals

- **NG-001 Runtime implementation.** AgSDL does not execute agents, schedule
  work, host models, or provide a universal runtime.
- **NG-002 Transport definition.** AgSDL does not define a new message transport
  or replace protocols such as those used by external agent systems.
- **NG-003 Provider API.** AgSDL does not standardize a model-provider, tool,
  storage, identity-provider, or telemetry API.
- **NG-004 Behavioral determinism.** A valid description does not guarantee that
  an agent will follow instructions, produce a correct answer, complete a task,
  or behave identically across runs.
- **NG-005 Security certification.** Structural or semantic validity does not
  prove that a system is secure, safe, compliant, or free from prompt injection
  and other attacks.
- **NG-006 Deployment success.** A positive static deployment assessment does
  not guarantee capacity, availability, performance, provider behavior, or
  successful deployment.
- **NG-007 Lossless universal import.** AgSDL does not promise a lossless mapping
  from every framework or arbitrary source code.
- **NG-008 Hidden semantics.** Framework behavior that an importer cannot
  observe or map remains an explicit gap rather than inferred portable meaning.
- **NG-009 Serialization choice.** This proposal does not choose YAML, JSON, or
  any other grammar, canonical form, or authoring notation.
- **NG-010 Interoperability by assertion.** Shared field names, successful
  parsing, or conformance claims without executable tests do not establish
  interoperability.

## Explicit constraints

- **CON-001 Pre-syntax constraint.** Requirements and conceptual meaning precede
  serialization design. No example in this phase establishes syntax.
- **CON-002 Implementation independence.** Portable meaning cannot depend on a
  named framework, provider, transport, deployment service, or runtime.
- **CON-003 Verifiable interoperability.** An interoperability claim requires
  executable conformance evidence for the claimed operations and profiles.
- **CON-004 External-system boundary.** Framework adapters, MCP, A2A, runtimes,
  providers, and transports remain external systems until an integration is
  implemented and tested.
- **CON-005 Explicit uncertainty.** Missing knowledge, unresolved references,
  unsupported concepts, and nondeterministic outcomes remain explicit. A tool
  cannot convert them into a positive conformance or equivalence claim.
- **CON-006 Secret safety.** Core inspection and validation cannot require secret
  material to be embedded in or disclosed through an AgSDL description.

## Use cases

### UC-001 Review a single-agent assistant

An author describes one support agent, its inputs and outputs, model
requirements, approved tools, knowledge sources, memory boundary, permissions,
human escalation, failure policy, telemetry, evaluation suite, and deployment
needs. A reviewer validates the description offline and identifies an excessive
tool permission. No multi-agent topology is added merely to satisfy the model.

### UC-002 Review delegation in a multi-agent system

An architect describes a coordinator, specialist agents, routing conditions,
delegation limits, handoff payloads, shared and isolated state, trust boundaries,
approval points, and failure paths. A reviewer follows a delegated operation
from entry to completion or escalation and detects a message path that lacks a
declared authorization check.

### UC-003 Compose a reusable subsystem

A maintainer combines an agent package, an organization policy profile, and a
deployment-neutral knowledge component. A processor resolves identities and
versions, reports an incompatible policy dependency, and refuses to choose an
implicit winner. After correction, it records which dependencies remain
external.

### UC-004 Exchange a self-contained review package

A vendor sends a customer a system description with embedded reusable
components, integrity-bound external references, declared extensions, and a
dependency manifest. The customer's offline processor reports one unavailable
optional reference and one unsupported required extension before making a
conformance claim.

### UC-005 Compare revisions

A maintainer compares two versions of a system. The report separates a changed
approval policy and a new agent relationship from a telemetry vendor binding
change and editorial reordering. The maintainer uses the portable changes to
select the required security and evaluation reviews.

### UC-006 Plan deployment to two environments

An operator compares one portable description with a managed cloud environment
and an isolated on-premises environment. The cloud target lacks a required data
residency control. The on-premises target cannot resolve one model capability.
The processor reports the first as unsatisfied and the second as indeterminate.
It predicts neither deployment success nor runtime performance.

### UC-007 Import a framework application

An adapter inspects framework configuration and source artifacts. It maps
agents, tools, and explicit routing to portable concepts, records a
framework-specific callback as an extension, and marks dynamically constructed
prompts as unresolved. The resulting provenance report distinguishes imported
facts from a maintainer's later corrections.

### UC-008 Audit execution evidence

An auditor receives traces and evaluation results from a deployed system. Stable
identities connect the evidence to a system version, agent, operation, and
evaluation definition. Redaction and retention declarations are inspectable.
The audit records a failed threshold without changing the evaluation definition
or the description's structural conformance status.

### UC-009 Replace a runtime binding

An operator changes the model service and telemetry backend while preserving
the declared model capabilities, data controls, event classes, and metrics. A
comparison reports binding changes but no portable semantic change. A target
assessment still checks whether the replacements meet the declarations.

### UC-010 Extend without silent degradation

A framework adds a versioned scheduling extension. One processor recognizes it.
Another does not, preserves the extension during a rewrite, and reports that it
cannot perform deployment planning because the extension is required for that
operation. Neither processor treats the scheduling behavior as portable core
meaning.

## Counter-cases and prohibited claims

### CC-001 Valid description, incorrect answer

A processor validates an assistant description. At runtime the model returns an
incorrect answer. AgSDL validation established that the description was
well-formed and semantically consistent under the applied rules. It did not
guarantee answer correctness.

### CC-002 Declared approval, bypassed control

A description requires human approval before a payment. A defective runtime
skips the approval. The description supports review, implementation checks, and
audit correlation, but cannot by itself enforce runtime behavior or certify the
runtime.

### CC-003 Equivalent structure, different behavior

Two runtimes consume the same portable description and expose the same declared
capabilities. They use different model versions, scheduling, retry timing, or
hidden defaults and produce different outcomes. Structural agreement does not
establish behavioral equivalence.

### CC-004 Successful import with an omitted callback

An importer parses a framework project but cannot observe a callback registered
dynamically at runtime. The importer must report the source boundary and the
unknown behavior. A generated description cannot claim complete or lossless
coverage.

### CC-005 Passing evaluation outside its assumptions

A system passes an evaluation in one environment. A later deployment changes
the model, tools, data, or policy. The recorded result remains evidence for the
tested version and assumptions, not a guarantee for the later deployment.

### CC-006 Complete deployment plan, failed deployment

A target assessment finds all declared requirements satisfied. Deployment later
fails because a provider is unavailable. AgSDL supported preflight comparison,
not availability or successful execution.

## Traceability

The following table is exhaustive for the requirements and quality goals in
this proposal.

| ID | Primary use case or constraint | Acceptance focus |
| --- | --- | --- |
| REQ-001 | UC-001, UC-002 | Offline human inspection exposes purpose, boundary, components, relationships, ownership, and controls. |
| REQ-002 | UC-003, UC-008 | References and evidence resolve to unambiguous stable identities. |
| REQ-003 | UC-001 | A complete one-agent system validates without synthetic topology. |
| REQ-004 | UC-002 | Multi-agent relationships and resource boundaries are representable and reviewable. |
| REQ-005 | UC-006, UC-007, CON-005 | Reports preserve declared, resolved, unspecified, unsupported, and absent states. |
| REQ-006 | UC-001, UC-004 | Validation reports each structural violation with a rule and location. |
| REQ-007 | UC-002, UC-003 | Cross-component violations are detected independently of execution. |
| REQ-008 | UC-004 | Reports list the core, profiles, extensions, and target checks applied. |
| REQ-009 | UC-004, CON-003 | Claims name their version, scope, profiles, extensions, and tested level. |
| REQ-010 | UC-003 | Composition resolves scope and conflicts without implicit precedence. |
| REQ-011 | UC-003, UC-004 | Every dependency has a declared delivery or resolution status. |
| REQ-012 | UC-004 | Sender and receiver can detect incomplete exchange packages. |
| REQ-013 | UC-003, UC-005 | Meaningful language, system, component, dependency, and extension versions remain distinguishable. |
| REQ-014 | UC-003, UC-004 | Compatibility reports separate compatible, incompatible, and indeterminate results. |
| REQ-015 | UC-005, UC-009 | Comparison separates portable, extension, binding, and presentation changes. |
| REQ-016 | UC-004 | Bad targets, kinds, resolution, and integrity are diagnosed. |
| REQ-017 | UC-001, UC-004 | Resolution inputs and sources are explicit, and offline validation is available. |
| REQ-018 | UC-004, UC-010 | Extension identity, version, support, and necessity are reportable. |
| REQ-019 | UC-010 | Unknown extensions survive rewriting or their loss is reported. |
| REQ-020 | UC-010 | Optional extensions have portable fallback; required extensions block unsupported operations. |
| REQ-021 | UC-001, UC-002 | Principals, resources, operations, trust boundaries, and controls can be inspected. |
| REQ-022 | UC-001, CON-006 | Inspection and validation use secret references rather than secret values. |
| REQ-023 | UC-001, UC-002 | Granted permissions can be compared with declared operations. |
| REQ-024 | UC-001, UC-002 | Human decision points include actor, trigger, choices, absence policy, and flow effect. |
| REQ-025 | UC-001, UC-002 | Failure responses are explicit and distinguishable. |
| REQ-026 | UC-001, UC-002 | Cross-boundary content and its expected controls are identifiable. |
| REQ-027 | UC-008 | Evidence correlates to system, component, operation, and version. |
| REQ-028 | UC-008, UC-009 | Telemetry requirements remain vendor-neutral and include privacy controls. |
| REQ-029 | UC-008 | Evaluation scope, procedure, metrics, evidence, assumptions, and target version are present. |
| REQ-030 | UC-008 | Definitions, results, and claims cannot be mistaken for one another. |
| REQ-031 | UC-008, CC-001 | Expected outcomes remain distinct from observations and guarantees. |
| REQ-032 | UC-006 | Runtime needs are portable unless explicitly bound or extended. |
| REQ-033 | UC-006 | Target assessment reports satisfied, unsatisfied, and indeterminate requirements. |
| REQ-034 | UC-009 | Binding replacement remains separate from portable semantic change. |
| REQ-035 | UC-006, UC-010 | Gaps, approximations, substitutions, and loss prevent false equivalence claims. |
| REQ-036 | UC-007 | Import reports source scope and every mapping, extension, unknown, omission, and unsupported behavior. |
| REQ-037 | UC-007 | Provenance supports repeatable audit and distinguishes later edits. |
| REQ-038 | UC-007, CC-003 | Round-trip reports loss without claiming behavioral equivalence. |
| QUAL-001 | UC-003, CON-003 | Equivalent declared inputs produce the same portable interpretation and structural result. |
| QUAL-002 | UC-001, UC-003 | Diagnostics identify subject, rule, and correction path without secrets. |
| QUAL-003 | UC-001 | Single-agent descriptions omit inapplicable multi-agent and deployment structure. |
| QUAL-004 | UC-001, UC-006 | Reviewers can find controls and requirements without reconstructing scattered meaning. |
| QUAL-005 | UC-005, UC-007, UC-010 | Transformations expose every known loss, approximation, and unresolved item. |
| QUAL-006 | UC-001, UC-004 | Core review works offline, without secrets or execution. |
| QUAL-007 | UC-001, UC-002, UC-003 | The same identity, reference, composition, and diagnostic model works at both scales. |
| QUAL-008 | UC-010 | Older processors identify unsupported optional additions without silent reinterpretation. |

## Proposed consequences

Later conceptual-model work must account for each `REQ-*` item or explicitly
revise this proposal. Serialization candidates must be evaluated against the
requirements rather than defining them through syntax. Conformance design must
separate document validity, processor behavior, profile support, adapter
coverage, and runtime evidence.

The breadth of the information inventory may produce profiles or conformance
levels rather than one mandatory all-purpose document shape. That decision
remains open. Whatever split is chosen must preserve traceability and must not
weaken visibility of unsupported information.

## Alternatives considered

### Define a minimal agent manifest first

A manifest centered on one agent would be easier to draft, but it would defer
system topology, shared controls, human supervision, observability, and
deployment boundaries. Later additions would likely conflict with identities
and composition rules established too narrowly.

### Standardize a serialization first

A concrete serialization would make examples and tooling appear sooner. It
would also turn provisional field names and nesting into accidental semantics.
Decision 0001 rejects that order.

### Treat framework configuration as the common model

Using one framework as the baseline would simplify its adapter while making
hidden defaults and framework-specific behavior look portable. It would fail
the implementation-independence constraint.

### Limit AgSDL to static structure

Static structure alone would help inventory components, but it would omit the
policies, human decisions, evidence, evaluation assumptions, and portability
gaps needed for review and governance. AgSDL can describe these declarations
without claiming to execute or enforce them.

## Security considerations

Descriptions can expose system topology, tool capabilities, trust boundaries,
deployment details, and references that help an attacker. Exchange and storage
profiles will need confidentiality, integrity, access-control, provenance, and
redaction requirements.

Reference resolution and import inspect external material. Future processors
must treat that material as untrusted, support offline operation, constrain
resolvers, and avoid executing imported code merely to discover configuration.
The exact resolver and sandbox requirements remain future design work.

Extensions can conceal security-relevant behavior from processors that do not
recognize them. Required-extension markers and loss reporting reduce silent
degradation, but they do not prove that an extension is safe. Conformance claims
must name extension support.

Secret references may still reveal metadata about credential providers,
accounts, or protected resources. Profiles need rules for minimizing and
redacting that metadata while retaining enough information for authorization
review.

## Compatibility impact

No published AgSDL syntax or normative specification exists, so this proposal
breaks no existing compatibility promise. If accepted, its identifiers provide
a review baseline for conceptual-model and serialization proposals. They do not
guarantee that identifiers will become public API names in the future
specification.

## Unresolved questions

1. Which requirement subsets belong to the portable core, optional profiles,
   processor conformance levels, or operation-specific capabilities?
2. What minimum information makes an AgSDL description complete rather than a
   reusable fragment or an intentionally partial description?
3. Which stable identity forms and scopes support composition, versioning,
   evidence correlation, and offline exchange without imposing a
   serialization?
4. Which semantic constraints must all processors evaluate, and which may be
   reported as indeterminate because they require external knowledge?
5. What compatibility relation applies to language versions, system versions,
   component versions, profiles, dependencies, and extensions?
6. What integrity and reproducibility guarantees must external references
   support in each profile?
7. How should composition express author intent when two fragments address the
   same component without relying on implicit precedence?
8. What preservation contract can processors offer for unrecognized extensions
   before a canonical serialization exists?
9. Which observability declarations belong to portable meaning, and which
   depend on runtime or telemetry profiles?
10. How should evaluation evidence be signed, versioned, retained, and linked
    without turning AgSDL into an evidence-storage format?
11. What static analysis is sufficient for a deployment or least-authority
    assessment to return "satisfied" rather than "indeterminate"?
12. How should importers measure and report coverage when framework behavior is
    created dynamically or hidden behind runtime defaults?
13. Which executable tests are required before an implementation may claim
    parsing, validation, transformation, adapter, or runtime conformance?
14. Which security metadata must remain available for offline review, and which
    metadata should be withheld or redacted during exchange?
