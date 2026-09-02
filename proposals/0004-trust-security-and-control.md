# Proposal 0004: trust, security, and human control

- Status: proposed
- Date: 2026-09-02

## Summary

An AgSDL definition should describe the security intent for an agentic system in
a form that reviewers and runtimes can inspect. It should also state what the
runtime must prove or record. The definition does not enforce its own policy. A
runtime, deployment, operator, or external service may ignore, misinterpret, or
fail to implement a declaration.

This proposal separates three kinds of security evidence:

1. **Declared policy** states the intended permissions, restrictions, human
   controls, and evidence requirements.
2. **Attested capability** states what an identified implementation claims it
   can enforce, with the issuer, subject, scope, validity, and evidence needed to
   evaluate that claim.
3. **Observed execution** records what happened during a particular execution,
   including decisions, approvals, resource use, policy violations, and
   termination.

None of these is a substitute for another. A declared restriction without an
enforcing runtime is an unmet requirement. An attestation is a scoped claim, not
proof that every execution complied. An execution record supports audit but
cannot recover events that were never recorded or whose evidence was altered.

## Problem

Agentic systems combine instructions and executable authority. They may load
remote packages, call tools, retain data, delegate work, and act across network
and organizational boundaries. The same definition can be interpreted by
runtimes with different isolation, identity, approval, and audit mechanisms.

A portable definition needs enough information to answer these questions:

- Who or what is trusted, for which action, and on what evidence?
- Which permissions are necessary, and where must they be enforced?
- Which data and authority may cross each trust boundary?
- Which actions require a person's consent or approval?
- How can an operator limit, suspend, terminate, investigate, and revoke a
  running system?
- Which claims can validation establish, and which require implementation or
  execution evidence?

Without a shared model, broad ambient authority and unverifiable security claims
look portable even when they depend on one runtime.

## Scope

This proposal defines the security concepts and requirements that the future
AgSDL system model should represent. It covers document authors, packages and
references, agents, models, tools, skills, memories, transports, runtimes,
operators, and users.

It does not:

- define serialization syntax;
- define an authorization protocol, identity provider, secret store, sandbox,
  transport, or audit backend;
- claim that structural validation enforces runtime behavior;
- make a runtime trustworthy because it can parse a definition;
- standardize provider-specific security features;
- require sensitive values, credentials, or secret material in a definition.

## Terms

**Principal** is a human or machine identity that may receive authority or be
held accountable for an action.

**Resource** is data, a service, a capability, or an execution facility to which
access can be controlled.

**Capability** is bounded authority to perform an operation on a resource.

**Trust boundary** is a point where data, control, identity, or authority moves
between parties or protection domains with different security assumptions.

**Declared policy** is security intent expressed by an AgSDL definition.

**Attested capability** is a verifiable, scoped claim that an implementation can
provide a security property.

**Observed execution** is evidence about events and outcomes from one execution.

**Consent** is a user's informed and revocable agreement to a stated use of
their data or authority.

**Approval** is an accountable decision that permits a specific pending action.
Consent does not imply approval of every action, and approval does not create
consent for another purpose.

**Revocation** withdraws authority, trust, consent, or approval before its
previously expected end.

**Emergency stop** is an operator control intended to prevent new work and
terminate or contain work already in progress.

## Security evidence model

### Declared policy

The system model should be able to declare:

- principals, owners, accountable operators, and intended users;
- trust boundaries and the resources that cross them;
- allow rules, deny rules, and the default when no rule matches;
- the subject, resource, operation, purpose, conditions, and duration of each
  permission;
- isolation and confidentiality requirements;
- accepted provenance and integrity evidence;
- consent and approval requirements;
- resource budgets, rate limits, deadlines, and failure behavior;
- logging, disclosure, retention, and deletion requirements;
- delegation depth, scope, recipients, and revocation behavior;
- emergency-stop behavior and the authority allowed to invoke it;
- evidence that a deployment must produce before and during execution.

Policy should be deny by default whenever the definition does not grant an
operation. Implementations may support broader ambient authority, but such
authority does not satisfy the declared policy and must not be reported as
conforming enforcement.

### Attested capability

The model should let a deployment associate an implementation capability claim
with:

- the issuer and the subject implementation;
- the property claimed and its exact scope;
- the implementation version and relevant configuration identity;
- the validity period and revocation status;
- the verification method and supporting evidence;
- qualifications, dependencies, and known limitations.

Examples include claims that a runtime can isolate tool processes, bind
approvals to immutable action parameters, redact configured fields from logs, or
interrupt delegated work. These examples describe concepts, not AgSDL syntax.

Self-attestation may be useful operational evidence, but policy must be able to
require an independent issuer or a particular assurance level. A stale,
unverifiable, out-of-scope, or revoked attestation does not satisfy a deployment
requirement.

### Observed execution

The model should let policy require execution evidence that identifies:

- the definition, resolved dependencies, runtime, configuration, and policy
  versions used;
- authenticated principals and delegated identities;
- policy decisions and their inputs;
- consent, approval, denial, timeout, override, and revocation events;
- model, tool, skill, memory, transport, and external-resource interactions;
- resource consumption and budget decisions;
- data classification changes, disclosures, and retention actions;
- integrity failures, containment actions, emergency stops, and termination;
- gaps caused by sampling, unavailable collectors, redaction, or loss.

Evidence must carry enough integrity, ordering, and identity information for the
declared verification method. Policy should state whether missing evidence
causes refusal, degraded operation, or a recorded non-conformance.

## Actor and asset model

Every identified actor is a principal, a resource controller, a source of
untrusted input, or more than one of these. A definition should not treat an
actor as trusted without stating the scope and basis of that trust.

| Actor class | Assets and authority at risk | Representative threats | Required policy questions |
| --- | --- | --- | --- |
| Document authors and publishers | System intent, identities, dependency choices, requested authority | Malicious policy, accidental overbreadth, misleading claims, unauthorized publication, downgrade | Who may author, review, sign, publish, replace, or withdraw a definition? Which changes require independent review? |
| Packages and references | Imported definitions, prompts, code, policies, profiles, evidence | Dependency confusion, substitution, tampering, mutable references, compromised maintainer, stale or revoked content | Which sources, identities, versions, digests, signatures, freshness windows, and transitive dependencies are accepted? |
| Agents | Delegated identity, goals, context, tool authority, data | Prompt injection, goal drift, confused deputy behavior, privilege aggregation, unauthorized delegation, evasion of stops | What may each agent read, decide, invoke, disclose, delegate, and retain? Which limits survive handoff? |
| Models and model providers | Prompts, retrieved data, outputs, provider credentials, usage metadata | Data disclosure, untrusted output, model substitution, training or retention beyond consent, adversarial content, nondeterministic policy bypass | Which provider, model identity, data-use terms, locations, filters, and output handling are acceptable? |
| Tools and tool providers | External side effects, credentials, files, networks, accounts | Excessive permissions, command or argument injection, compromised tool, hidden side effects, replay, stale authorization | Which exact operations and resources are allowed? How are parameters validated, effects previewed, results authenticated, and calls made idempotent? |
| Skills and instruction sources | Reusable instructions, workflows, referenced assets or code | Instruction injection, hidden policy conflict, provenance loss, authority smuggling, unsafe update | Who published the skill? Which version and content identity were reviewed? Which permissions does its use require? |
| Memories and knowledge sources | Personal data, confidential data, learned state, retrieved content | Poisoning, cross-user leakage, unauthorized inference, excessive retention, deletion failure, stale data | Who may write, read, correct, export, and delete data? What are its purpose, classification, provenance, and retention limits? |
| Transports and intermediaries | Messages, identities, routing metadata, approvals, results | Eavesdropping, tampering, replay, rerouting, impersonation, traffic analysis, delivery ambiguity | What peer authentication, confidentiality, integrity, freshness, ordering, and delivery properties are required? |
| Runtimes and deployment operators | Enforcement, isolation, secrets, scheduling, logs, stop controls | Policy ignored or misinterpreted, breakout, secret exposure, evidence suppression, unsafe fallback, compromised host | Which controls must the runtime enforce? What evidence demonstrates support and use? What happens when enforcement is unavailable? |
| Human operators and administrators | Deployment, overrides, approvals, logs, revocation, emergency control | Insider abuse, account compromise, approval fatigue, unreviewed override, failure to stop or revoke | Which duties are separated? Which actions require strong authentication, dual control, reason capture, and audit? |
| End users and affected people | Inputs, personal data, accounts, decisions, consent | Deception, coercive consent, unauthorized action, unsafe reliance, impersonation, inability to contest or delete | What notice, consent, confirmation, recourse, accessibility, and data rights apply? Who is affected without being an active user? |

## Trust boundaries

A definition should identify every applicable boundary below, both endpoints,
the resources crossing it, the policy enforcement point, and the failure policy.
Nested systems may introduce more boundaries.

| Boundary | What crosses it | Main concern |
| --- | --- | --- |
| Authoring to publication | Definition content, signatures, review decisions | Unauthorized or misleading definitions entering distribution |
| Definition to package or reference resolver | Identifiers, constraints, fetched content, provenance evidence | Substitution, mutable resolution, and transitive dependency risk |
| Definition to runtime | Declared policy and deployment requirements | Semantic mismatch or unsupported policy treated as enforced |
| Control plane to execution plane | Configuration, credentials references, approvals, stop and revoke commands | Privileged command spoofing, stale state, or enforcement delay |
| Runtime to execution host or sandbox | Code, context, environment access, results | Isolation failure and ambient host authority |
| Agent to agent | Goals, context, identity, capability, results | Authority laundering, context leakage, and loss of accountability |
| Agent to model | Instructions, sensitive context, model output | Provider disclosure and untrusted output controlling actions |
| Agent to tool or skill | Arguments, delegated credentials, instructions, results | Excessive authority, injection, and hidden effects |
| Agent to memory or knowledge | Queries, records, embeddings, retrieved content | Poisoning, unauthorized disclosure, and retention beyond purpose |
| Runtime to transport or intermediary | Messages, metadata, acknowledgements | Impersonation, replay, tampering, and ambiguous delivery |
| System to external service or organization | Data, requests, side effects, contractual commitments | Different ownership, policy, jurisdiction, and incident response |
| User to system | Input, identity, consent, approvals, output | Misunderstood authority, manipulation, and unsafe reliance |
| Operator to system | Deployment, override, investigation, revocation, emergency stop | Concentrated privilege and insufficient accountability |
| Execution to observability systems | Traces, logs, metrics, content, identifiers | Sensitive-data duplication, tampering, and excessive retention |
| Persistent state to backup, export, or deletion process | Stored data and derived copies | Incomplete deletion, uncontrolled copies, and recovery exposure |

An implementation must not infer that two named components share a trust domain
only because one runtime hosts them. Conversely, a boundary declaration cannot
create isolation. The deployment needs an enforcement mechanism and evidence
that the mechanism covered the execution.

## Proposed policy semantics

### Least privilege and authority

Permissions should identify the principal, resource, operation, purpose,
conditions, and lifetime. Broad categories should be refinable by deployment
policy. Authority should be limited by default and should not expand through
composition, retries, fallback, delegation, or handoff.

A component that needs several authorities should receive them separately when
the implementation can enforce that separation. Unused, expired, denied, or
revoked authority must not remain available through cached credentials or an
already running delegate.

### Provenance and integrity

Definitions, packages, references, skills, models, tools, policies, and
attestations should have stable identities. Policy should be able to constrain
publisher identity, source, version, content digest, signature, review state,
freshness, and revocation.

A human-readable name is not an integrity identity. A mutable location alone is
not sufficient evidence that reviewed content is the content used. Resolution
evidence should cover transitive references and record the result used for each
execution.

### Secrets by reference

Definitions must not contain secret values. They may identify a secret by an
opaque reference and declare the intended consumer, purpose, allowed operation,
scope, and lifetime. The reference must not be assumed harmless. It may reveal
metadata or act as a bearer token in some systems, so policy should classify and
protect it.

The runtime or secret provider is responsible for authentication, retrieval,
injection, rotation, revocation, redaction, and disposal. An implementation
should avoid exposing a secret to the model, agent context, logs, child
processes, or delegates when a narrower credential broker can perform the
authorized operation.

### Isolation and confidentiality

Policy should identify required separation between principals, users, tenants,
components, data classes, executions, and environments. It should state allowed
communication paths and whether data may leave a host, region, organization, or
provider boundary.

Isolation requirements may cover process, filesystem, network, account,
credential, memory, accelerator, storage, and observability domains. The model
should express the required property without claiming that a named sandbox or
deployment technology provides it.

### Consent and approvals

Consent should identify the person or represented party, purpose, data or
authority covered, notice presented, collection method, validity period, and
withdrawal path. Consent must be collected before the covered use unless an
explicit policy basis permits another sequence.

An approval should bind the approver, pending action, target, material
parameters, expected effects, expiry, and the definition and policy versions in
force. A material change after approval requires a new approval. Policy should
support separation of requester and approver, multiple approvers, denial,
timeout, and non-delegable decisions.

Interfaces and repeated prompts can manipulate users into approval. A
declaration can require an informed approval flow, but only interface review and
execution evidence can show whether the person received accurate information
and made an uncoerced choice.

### Budgets and failure containment

Policy should bound resources that can amplify harm or cost. Relevant budgets
include time, money, tokens, tool calls, network requests, data volume, storage,
parallel work, delegation depth, retries, and externally visible side effects.

The policy should identify the accounting scope, unit, authority allowed to
raise the budget, behavior near exhaustion, and behavior at exhaustion. Nested
budgets should not silently reset during delegation, retries, restarts, or
handoffs. An unavailable meter should trigger the declared failure policy.

### Emergency stops and safe states

Policy should define who may initiate an emergency stop, the scope of the stop,
the expected maximum response time, and the safe state. It should distinguish:

- refusal of new work;
- cancellation of queued work;
- interruption of active model and tool calls where supported;
- revocation of delegated authority and credentials;
- containment of work that cannot be interrupted;
- preservation of evidence needed for investigation;
- recovery and the authority required to resume.

No portable definition can guarantee immediate termination. External services
may already have committed an effect, transports may be partitioned, and a
runtime or host may be compromised. Deployments must verify interruption and
containment behavior under realistic failure conditions.

### Logging, retention, and confidentiality

Logging policy should identify required events, fields, integrity protection,
access, disclosure, retention, deletion, and evidence-loss behavior. It should
also identify data that must not be recorded, including secrets and unnecessary
sensitive content.

Audit completeness and data minimization can conflict. Policy should resolve
that conflict by requiring identifiers, hashes, redacted summaries, or access-
controlled payloads only where they support a stated verification purpose.
Logs, traces, embeddings, caches, backups, and derived evaluation data all need
retention treatment. Deleting a primary record does not establish deletion of
its copies or derived data.

### Delegation and revocation

Delegation should preserve the identity of the delegator and delegate. It should
also carry purpose, authority, constraints, budget, approval state, expiry,
delegation depth, redelegation permission, and accountability. A delegate must
not receive authority greater than the intersection of the delegator's
delegable authority and the delegation grant.

Revocation policy should identify the revocable object, issuer, propagation
targets, expected response time, cached-state behavior, in-flight action
behavior, and evidence of completion. Revocation is not established by changing
a definition after deployment. The control plane, runtime, credential systems,
delegates, transports, and external services must receive and enforce it.

## Threat and control matrix

The declarative column states what AgSDL should be able to require. The
implementation column states what a conforming deployment would need to do. The
verification column describes evidence, not a guarantee that AgSDL validation
can provide.

| Threat | Actors or boundary | Declarative controls | Implementation controls | Verification method |
| --- | --- | --- | --- | --- |
| Unauthorized or deceptive definition publication | Authors; authoring to publication | Authorized publishers, required reviewers, content identity, signature and withdrawal policy | Protected signing keys, review workflow, authenticated registry, revocation distribution | Verify signature chain and review records; attempt unauthorized publication; confirm withdrawal propagation |
| Dependency substitution, confusion, or downgrade | Packages, references, skills; resolver boundary | Allowed sources and publishers, immutable content identity, version constraints, transitive policy, freshness and revocation rules | Authenticated resolver, digest and signature checks, lock or resolution record, fail-closed downgrade handling | Reproduce resolution; compare all digests; inject a conflicting or revoked package and confirm refusal |
| Malicious or compromised imported instructions | Packages, skills, knowledge | Provenance, review state, requested permissions, policy precedence, isolation requirement | Content scanning, permission mediation, instruction and data separation, sandboxing | Review dependency graph; test adversarial imports; compare requested with granted authority; inspect execution trace |
| Runtime silently ignores declared policy | Definition to runtime | Required capabilities, evidence, unsupported-policy behavior, fail-closed requirement | Capability negotiation, policy compiler, enforcement points, refusal on unsupported requirements | Negative conformance tests; signed capability evidence; policy-decision and denial records |
| Excessive or ambient authority | Agents, tools, runtimes | Deny by default, scoped and time-bound grants, purpose restriction, no implicit inheritance | Reference monitor, short-lived credentials, account and network isolation, syscall or API mediation | Enumerate effective permissions; attempt out-of-scope operations; inspect credential lifetime and denial logs |
| Prompt or content injection changes authority | Users, knowledge, tools, models, skills | Trusted instruction sources, untrusted-data labels, non-overridable policy, approval gates | Separate instruction and data channels, policy enforcement outside model output, argument validation | Adversarial injection suite; confirm unchanged effective policy and blocked unauthorized calls |
| Confused deputy or authority laundering | Agents, tools, delegates | Caller identity propagation, purpose-bound grants, delegation intersection and depth | End-to-end identity binding, per-call authorization, non-transferable tokens | Trace authority lineage; test cross-principal requests and redelegation beyond scope |
| Model or provider substitution | Models; agent to model | Accepted provider and model identity, version policy, capabilities, data-use and location limits | Authenticated endpoint, deployment identity checks, controlled fallback | Compare request records with accepted identities; force fallback and confirm declared behavior |
| Sensitive data disclosed to a model or provider | Models, users, memories | Data classification, purpose, provider, region, retention, training-use, consent and redaction policy | Data-loss prevention, field filtering, regional routing, provider configuration, credential broker | Synthetic canary tests; provider configuration evidence; sampled redacted traces; consent records |
| Untrusted model output triggers a side effect | Models, agents, tools | Output trust classification, schema or constraint requirements, approval and tool policy | Parse and validate output, authorize tool calls independently, preview consequential effects | Fuzz malformed output; adversarial model tests; confirm approval binding and independent policy decisions |
| Tool argument injection or hidden side effect | Tools; agent to tool | Allowed operation, target and parameters, effect class, idempotency and approval requirements | Typed API boundary, allowlists, escaping, dry run or preview, transaction and replay protection | Fuzz arguments; compare preview to committed effect; replay calls; inspect external audit records |
| Compromised tool or external service | Tools, external organizations | Provider identity, integrity and attestation requirements, data and network limits, failure behavior | Service authentication, egress control, sandbox, response validation, circuit breaker | Substitute endpoint or certificate; simulate malicious responses; review egress and containment records |
| Secret exposure or credential reuse | Runtime, tools, models, logs | Secret by reference, intended consumer, purpose, scope, lifetime, redaction and revocation | Secret broker, scoped ephemeral credentials, isolated injection, rotation, zeroization, log filtering | Secret scanning; canary credential; inspect process exposure; rotate and revoke during execution |
| Memory poisoning or unauthorized modification | Memories, knowledge, users, agents | Writer permissions, provenance, integrity, review, correction and conflict policy | Authenticated writes, versioning, validation, quarantine, integrity checks | Attempt unauthorized write; trace retrieved claims to sources; restore and compare versions |
| Cross-user, cross-tenant, or cross-run leakage | Memories, runtime, observability | Isolation domains, read and write scopes, lifecycle, export and deletion policy | Separate namespaces and keys, access control, cache partitioning, tenant-aware logging | Isolation penetration tests; seeded canaries; access-log review; deletion and cache-eviction tests |
| Retention beyond purpose or incomplete deletion | Memories, logs, backups, providers | Purpose, retention period, deletion trigger, derived-copy and backup policy, verification evidence | Lifecycle jobs, deletion propagation, tombstones, backup expiry, provider deletion API | Inventory copies and derivatives; run deletion exercise; verify expiry and record exceptions |
| Message interception, tampering, replay, or impersonation | Transports, agents, control plane | Peer identity, confidentiality, integrity, freshness, ordering, replay and delivery requirements | Mutual authentication, encryption, signed or authenticated messages, nonce or sequence checks | Protocol tests; replay and reorder messages; inspect key and peer identity evidence |
| Ambiguous delivery causes duplicate or missing effects | Transports, tools | Delivery semantics, idempotency, acknowledgement, retry and reconciliation policy | Stable operation identifiers, deduplication, transactional outbox or equivalent, reconciliation | Inject loss and timeout; repeat messages; compare intended and external effects |
| Sandbox escape or host compromise | Runtime; runtime to execution host | Required isolation properties, host trust assumptions, network and filesystem policy, containment behavior | Hardened isolation, patching, minimal host services, egress filtering, detection and shutdown | Escape tests, configuration audit, vulnerability evidence, incident exercise; independent assessment where required |
| Operator or administrator abuse | Operators; operator to system | Role separation, least privilege, strong authentication, dual approval, override limits and audit | Privileged access management, separate accounts, immutable audit trail, alerting | Access review; attempt self-approval; inspect override records; periodic insider-threat exercise |
| Approval is stale, vague, replayed, or manipulated | Users, operators, agents | Immutable action binding, material parameters, approver role, expiry, single-use rule, reason and user notice | Authenticated approval service, nonce, transaction binding, accessible and accurate interface | Modify parameters after approval; replay or expire approval; usability and interface review; inspect audit chain |
| Consent is absent, coerced, or used for another purpose | Users and affected people | Notice, purpose, data, basis, validity, withdrawal, affected-party and recourse requirements | Consent service, purpose enforcement, preference propagation, non-coercive interface | Consent-record audit; withdraw during execution; product and legal review; affected-person testing |
| Budget bypass through retries, restart, or delegation | Agents, runtime, delegates | Shared accounting scope, units, nested limits, reset rules, exhaustion behavior | Central or consistent metering, atomic reservations, inherited budgets, rate limiting | Fault injection across restart and delegation; reconcile meter with provider and tool records |
| Runaway or harmful work cannot be stopped | Agents, tools, runtime, operators | Emergency-stop authority, scope, response target, safe state, propagation, recovery rule | Independent control path, cancellation, credential revocation, queue purge, network containment | Timed stop drills with nested delegates, partitions, hung tools, and external side effects; document residual work |
| Revoked authority remains usable | Delegates, tools, secrets, transports | Revocation target, propagation and response requirements, cache and in-flight policy | Short-lived tokens, online status checks, push invalidation, cancellation and reconciliation | Revoke during active and partitioned runs; test cached credentials; inspect completion evidence |
| Audit evidence is altered, suppressed, or leaks data | Runtime, operators, observability | Required events, integrity, access, redaction, retention, missing-evidence behavior | Append-only or tamper-evident storage, separate audit authority, encryption, filtering, health monitoring | Tamper and collector-loss tests; verify chain or signature; access review; sensitive-data scanning |
| False or stale capability attestation | Runtime, provider, attestation issuer | Trusted issuers, subject and configuration binding, scope, validity, revocation, assurance level | Protected attestation process, evidence collection, revocation publication | Validate issuer and subject; change configuration; expire or revoke claim and confirm deployment refusal |
| Unsafe fallback after control failure | Runtime, model, tool, transport | Explicit failure policy, forbidden fallback, degraded-mode authority and disclosure | Fail closed for protected actions, circuit breakers, isolated degraded mode | Disable policy, approval, secret, meter, or audit dependency and observe behavior |
| User relies on fabricated or unsafe output | Models, agents, users | Output status, source and uncertainty requirements, human review, contest and correction path | Grounding, validation, calibrated user interface, review workflow, incident handling | Task-specific evaluations; source checks; user testing; review correction and appeal records |

## Static validation and runtime verification

Structural validation should be able to establish only facts present in, or
cryptographically bound to, the definition and its resolved inputs. Depending on
the future model, validation may establish that:

- required security declarations exist and use recognized terms;
- referenced principals, resources, boundaries, permissions, budgets, and
  policies resolve consistently;
- no secret value appears where only a secret reference is allowed;
- a permission is narrower than a declared enclosing limit;
- delegation and approval declarations contain required constraints;
- an imported artifact matches a declared content identity or signature;
- an attestation is well formed, in scope, current, and issued by an accepted
  identity, assuming the verifier trusts its roots and revocation information.

Static validation cannot establish that:

- the author, runtime, operator, provider, or attestation issuer is honest;
- an implementation enforces a declared permission or isolation boundary;
- a model will follow instructions, resist injection, or produce safe output;
- a tool has no hidden side effects or vulnerabilities;
- a secret was never exposed outside its intended consumer;
- a user understood or freely gave consent or approval;
- an emergency stop will reach every component within a stated time;
- revocation reached a disconnected delegate or undid an external effect;
- logs are complete, accurate, confidential, or undeleted elsewhere;
- deleted information has no backup, cache, embedding, inference, or provider
  copy;
- a future execution will behave like a tested execution;
- the complete system is secure.

These properties require implementation inspection, conformance and adversarial
testing, deployment evidence, operational exercises, provider evidence, human-
factors review, or observation of the specific execution. Some remain
unprovable. A conformance report should say which method it used and identify
residual uncertainty.

## Conformance implications

Future conformance work should distinguish at least these claims:

- **Definition conformance** means the document expresses a structurally valid
  security model. It says nothing about enforcement.
- **Capability conformance** means an implementation presents acceptable
  evidence for the security capabilities required by a definition.
- **Deployment conformance** means a specific deployment resolves every
  requirement to an enforcement or evidence mechanism and reports gaps.
- **Execution conformance** means observed evidence for a specific execution
  satisfies the declared verification rules, subject to stated evidence gaps.

An implementation must not collapse these claims into a generic "secure" or
"compliant" status. Unsupported requirements, weaker substitutions, overrides,
missing evidence, and unverifiable external dependencies must remain visible.

## Consequences

### Benefits

- Reviewers can distinguish intended policy from claimed enforcement and actual
  execution.
- Portable definitions can state security requirements without standardizing a
  runtime or vendor mechanism.
- Least privilege, delegation, human approval, revocation, and audit become
  system relationships instead of framework-specific comments.
- Conformance tests can target explicit security claims and failure behavior.

### Costs and limitations

- Authors must model principals, resources, boundaries, and evidence instead of
  using a single trust flag.
- Runtimes need capability reporting and must expose unsupported requirements.
- Strong verification may need external identity, signature, attestation,
  policy, audit, and test systems.
- Detailed execution evidence creates storage, confidentiality, and retention
  risks of its own.
- Some providers cannot expose enough evidence to satisfy a strict policy.

## Alternatives considered

### Treat security as runtime-specific configuration

This avoids a large portable model, but prevents reviewers from comparing the
intended authority and controls of equivalent systems. It also hides security
requirements during migration.

### Define a fixed list of security levels

Labels such as "high security" conceal different threat assumptions and
mechanisms. They cannot express which actor, resource, boundary, or failure mode
the level covers. Profiles may later bundle reviewed requirements, but their
contents and limits must remain inspectable.

### Require one enforcement technology

Mandating a sandbox, identity system, transport, or policy engine would conflict
with AgSDL's implementation-independent scope. The model should state properties
and evidence requirements, then let profiles or deployments select mechanisms.

### Record only execution traces

Traces describe observed events, but they do not define allowed behavior or
prove that omitted events did not occur. Policy and capability evidence remain
necessary.

## Security considerations

This entire proposal concerns security, but its own misuse deserves attention.
A detailed declaration can reveal system topology, privileged identities,
control paths, provider choices, and defensive limits. Definitions and
attestations need access, disclosure, retention, and integrity controls. Public
packages should avoid operational identifiers that help an attacker target a
deployment.

A policy can also create a false sense of control. Tooling should present
unresolved requirements, self-attested claims, evidence gaps, overrides, and
unverified external behavior prominently. A green structural validation result
must never be presented as a security certification.

## Compatibility impact

The project has no published syntax or compatibility promise. This proposal
adds concepts for later terminology and requirements work. Accepting it would
not update the normative specification by itself.

## Unresolved questions

1. Which minimum evidence fields belong in the portable model, and which should
   remain profile-specific?
2. Should assurance levels be standardized, or should AgSDL only identify the
   issuer and verification method?
3. How should nested definitions combine deny rules, approvals, budgets, data
   classifications, and retention requirements without creating implicit
   authority?
4. Which policy conflicts must make a definition invalid, and which may remain
   deployment-time errors?
5. How should a definition identify affected people who are not authenticated
   users of the system?
6. What common vocabulary can describe side-effect severity without assuming a
   particular industry or legal regime?
7. How should execution evidence express partial ordering across transports and
   providers without prescribing one trace format?
8. What evidence is sufficient to claim that emergency-stop and revocation
   requirements cover external services that offer no cancellation mechanism?
9. How should confidential policy and topology details be disclosed to a
   verifier without publishing them to every package consumer?
10. Which threat-model and verification requirements belong in the base
    specification, and which belong in optional security profiles?
