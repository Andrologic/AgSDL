# Conceptual examples for AgSDL

The first two examples originated in the AgSDL 0.0.1 conceptual release. The
versions below follow the current proposed model, including the composition
and authorization directions in [Decision
0004](../docs/decisions/0004-approved-design-directions.md). The `v0.0.1` tag
preserves the released versions. These examples remain non-normative and
independent of serialization syntax, frameworks, providers, transports, and
runtimes.

The [imported-Agent composition and authorization
example](conceptual/composition-and-authorization.md) illustrates the revised
participation and decision-accounting rules, including refusal and missing
evidence. It is not part of the tagged 0.0.1 release.

An additional [A2A 1.0 external binding example](a2a-1.0-external-binding.md)
illustrates proposal 0006. It is not part of the AgSDL 0.0.1 conceptual model
and does not establish binding syntax or interoperability.

The separate [A2UI declarative-interface
example](a2ui-declarative-interface.md) explores proposal 0008 against an
external format. It remains non-normative, pins the reviewed A2UI version, and
does not claim an implemented adapter or interoperability.

## 1. Single-agent document assistant

### Intent

An employee asks one agent to answer a question from a company handbook. The
example shows the smallest useful system boundary without inventing a topology
or protocol.

### Conceptual entities

- **Handbook assistant system**, a System definition. Its boundary contains the
  assistant and the locally defined components below. The employee and the
  handbook store remain outside that boundary.
- **Employee**, a human Principal definition, and **employee account**, its
  Identity. The Principal is the accountable actor. The Identity names that
  actor within the company account scope and does not by itself prove control
  of the account or grant authority.
- **Handbook assistant**, an Agent definition, and **assistant service
  principal**, the Principal definition under which the agent acts. The agent's
  definition identity and its Principal Identity remain distinct.
- **Answer from the handbook**, an ordered Instructions definition that directs
  the agent to answer only from retrieved handbook passages and to state when
  the available passages do not answer the question.
- **Text inference capability**, a Model definition used by the agent.
- **Question interface**, an Interface definition exposed by the System. It
  contains one inbound **ask question** Interface operation. The operation is a
  complete single-message interaction and makes the **answer handbook
  question** Action available.
- **Handbook lookup**, a Tool definition used by the agent. It makes the
  **retrieve handbook passages** Action available and declares its required
  lookup binding. The Tool declares that retrieval has no effect outside the
  current execution state.
- **Company handbook**, a Resource governed by the company records authority
  and reached through the Tool.
- **Employee-to-assistant boundary**, a Trust boundary separating the employee
  trust domain from the assistant trust domain. It governs the inbound question
  crossing through the ask question operation. The crossing treats the
  question as untrusted content and does not transfer the employee's authority
  to the agent.

Every definition local to this complete document has exactly one lifecycle
owner, the Handbook assistant system. The external Company handbook Resource
keeps its external governing authority. Containment and use do not transfer
that authority or ownership.

### Directed relations and useful cardinalities

- Handbook assistant system `owns` local definitions, one or more in total.
  Each local definition has exactly one lifecycle owner.
- Handbook assistant system `owns` Handbook assistant, exactly one in this
  example, `uses` that Agent as its participant, and `exposes` Question
  interface, exactly one.
- Handbook assistant `acts as` Assistant service principal, exactly one, and is
  `represented by` one agent Identity distinct from that Principal's Identity.
- Employee `identified by` Employee account, one of one or more possible
  identities for that Principal.
- Handbook assistant `directed by` Answer from the handbook, exactly one here,
  and `uses` Text inference capability and Handbook lookup, one of each here.
- Question interface `contains` Ask question, exactly one here. Ask question
  `makes available` Answer handbook question, exactly one Action.
- Handbook lookup `makes available` Retrieve handbook passages, exactly one
  Action here. That Action `targets` Company handbook, exactly one Resource in
  each occurrence.
- Employee-to-assistant boundary `separates` exactly two trust domains and
  `governs crossing through` Ask question, exactly one crossing operation here.
- Each question Message occurrence is `sent by` exactly one Principal Identity,
  is `addressed to` at least one Principal Identity, and `conforms to` exactly
  one Interface operation.

No Topology is declared because there is no participant graph to constrain. No
Protocol is declared because the interface operation defines a complete
single-message interaction.

### Narrative path

1. The Employee sends a question through Ask question using the Employee
   account Identity. Authentication evidence may establish control of that
   Identity, but it remains separate from the Principal and from any authority.
2. The question crosses the Employee-to-assistant boundary as untrusted
   content. The Handbook assistant receives it through its declared Interface
   operation.
3. Acting as the Assistant service principal, the agent follows Answer from the
   handbook and invokes Handbook lookup to request Retrieve handbook passages
   against the Company handbook Resource.
4. The agent supplies the retrieved passages and question to the Text inference
   capability, then returns an answer or the declared no-answer response. Model
   output does not become a new definition and does not alter the Tool contract.

### Counterexamples

- The document uses the Employee account Identity as if it were the Employee
  Principal and treats successful authentication as permission to read the
  handbook. This violates the separation of Principal, Identity, authentication
  evidence, and authority.
- Handbook lookup reaches the external handbook without identifying the
  Resource or its governing authority. This violates the requirement that an
  external Resource identify the authority source that governs it.

## 2. Human-approved supplier payment

### Intent

Two agents prepare and execute one supplier payment. A handoff transfers
responsibility to the payment agent, while authorization and human approval
remain separate controls before the external effect.

### Conceptual entities

- **Supplier payment system**, the System definition and lifecycle owner of all
  local definitions in this example.
- **Invoice review agent** and **Payment agent**, two Agent definitions. Each
  acts as its own Principal definition and has its own Principal Identity.
- **Finance approver**, a human Principal definition with a distinct corporate
  Identity.
- **Invoice intake interface**, exposed by the Invoice review agent and by the
  System, with one inbound **submit invoice** operation. **Payment execution
  interface**, exposed by the Payment agent, contains the inbound **offer
  payment work item** operation used between the agents.
- **Payment participant topology**, a Topology that permits the directed path
  from Invoice review agent to Payment agent through the two declared
  interfaces.
- **Supplier payment flow**, a Control flow with a prepare step, a handoff step,
  an approval wait, an authorization step, and one of two terminal outcomes:
  payment recorded or payment refused. Every branch ends at one of those
  terminals, so the flow is closed and has no unbounded cycle.
- **Execute approved payment**, a Handoff definition that transfers
  responsibility for one payment work item from Invoice review agent to Payment
  agent after the receiving agent accepts it. The Handoff grants no authority.
- **Payment submission**, a Tool definition used by Payment agent. It makes the
  protected **submit supplier payment** Action available and declares that the
  Action may produce the **funds transferred** Effect outside the System.
- **Company bank account**, the protected Resource targeted by the Action, and
  **bank service**, an external environment element that performs the payment.
- **System-to-bank boundary**, a Trust boundary governing the outbound Action
  crossing and the resulting Effect between the system and bank trust domains.
- **Supplier payment policy**, a Policy that denies unmatched requests and
  permits submission only for the accepted payment work item, within its amount
  and supplier constraints, after matching human approval.
- **Payment gate**, the Policy application point that mediates Submit supplier
  payment before Funds transferred can occur. It applies Supplier payment
  policy and requires **Payment authorization requirement**.
- **Payment authorization requirement**, which requires the Payment agent's
  valid authentication evidence, a scoped Authority grant for the Company bank
  account, the Policy result, and **Finance approval requirement**.
- **Finance approval requirement**, which accepts a decision only from the
  Finance approver for the exact supplier, bank account, amount, currency, and
  expiry presented in one Approval request.

### Directed relations and useful cardinalities

- Supplier payment system `owns` both Agents and every other local definition.
  It `uses` both Agents as participants. Each local definition has exactly one
  lifecycle owner.
- Each Agent `acts as` exactly one Principal definition and is `represented by`
  exactly one agent Identity. Finance approver is `identified by` one of one or
  more human identities.
- Payment participant topology `contains node for` both Agents and `contains
  directed edge through` Payment execution interface for the permitted handoff
  path from Invoice review agent to Payment agent.
- Supplier payment system `exposes` Invoice intake interface, exactly one
  system Interface here. Each Agent `exposes` at least one Interface.
- Supplier payment flow `contains` six steps here, four nonterminal steps and
  two terminal steps. Each nonterminal step
  `transitions to` at least one successor, and each branch reaches exactly one
  of the two terminal outcomes.
- Execute approved payment `transfers responsibility for` exactly one payment
  work item. Each Handoff occurrence `transfers from and to` exactly two
  Principal Identities and is `governed by` exactly one Handoff definition.
- Payment agent `uses` Payment submission, one Tool here. Payment submission
  `makes available` Submit supplier payment, one protected Action here.
- Submit supplier payment `targets` Company bank account, one Resource for each
  Action occurrence, and `may produce` Funds transferred, one Effect definition
  here.
- Submit supplier payment is `mediated by` Payment gate, exactly one policy
  application point here. Payment gate `applies` Supplier payment policy and
  `requires` Payment authorization requirement.
- Payment authorization requirement `applies` Supplier payment policy,
  `considers` the scoped Authority grant, and `may require` Finance approval
  requirement. All three are required in this example.
- Each Approval request `satisfies` exactly one Approval requirement and is
  `requested by` exactly one Principal Identity. At most one Approval decision
  `responds to` that request; the decision is `supplied by` exactly one human
  Principal Identity and may `contribute to` one Authorization decision.
- Each Authorization decision `evaluates for` exactly one Principal Identity,
  is `evaluated against` exactly one Authorization requirement, and is `made
  at` Payment gate. It binds the Action, Resource, context, Policy version,
  result, and decision time. When a Submit supplier payment Action occurrence
  exists, it `has authorization decision` for the decision used at Payment
  gate. A refusal before an attempt does not create an Action occurrence.
- Each Funds transferred occurrence is `caused by` exactly one Submit supplier
  payment Action occurrence. A permitted Authorization decision does not prove
  that either occurrence happened.

### Narrative path

1. Invoice review agent prepares a bounded payment work item containing the
   supplier, bank account, amount, currency, and invoice reference.
2. Execute approved payment offers that work item to Payment agent. The agent
   accepts it, so responsibility moves to Payment agent. Its authority does not
   change, and the trace keeps both Principal Identities in the handoff chain.
3. The flow creates an Approval request for the exact proposed Action and
   material context, then waits. A denial, expiry, or missing response follows
   the fail-closed branch to Payment refused.
4. Finance approver supplies a matching, unexpired Approval decision. Payment
   gate evaluates Payment authorization requirement for Payment agent against
   its authentication evidence, scoped Authority grant, Supplier payment
   policy, and that Approval decision.
5. Only a permitted Authorization decision lets Payment agent invoke Submit
   supplier payment. The Action crosses the System-to-bank boundary and may
   produce Funds transferred against the Company bank account. The flow then
   reaches Payment recorded. A denied or indeterminate decision reaches Payment
   refused without invoking the Tool.

### Counterexamples

- Payment agent treats the accepted Handoff as authority to submit the payment.
  This violates the rule that Handoff transfers responsibility but grants no
  authority. The protected Action still needs an applicable permitted
  Authorization decision.
- Finance approver approves 900 euros, but Payment agent changes the amount to
  9,000 euros before submission and reuses the decision. The Approval decision
  no longer matches the Action's material context, so it cannot satisfy Payment
  authorization requirement. Payment gate must deny or follow its declared
  indeterminate failure behavior before any Funds transferred Effect.
