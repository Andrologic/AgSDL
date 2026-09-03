# Conceptual A2UI declarative-interface example

Status: exploratory example, non-normative
External basis: A2UI `v0.9.1` as reviewed in `docs/research/a2ui.md`

## Intent

An expense-review agent asks a renderer to present one interactive expense
surface. The user can correct fields and request submission. The example shows
how proposal 0008 keeps A2UI presentation, runtime state, user interaction,
approval, and protected effects separate.

This is an AgSDL conceptual example, not A2UI JSON or AgSDL syntax. It does not
claim that an adapter or renderer implements the mapping.

## Conceptual entities

- **Expense review system**, the System definition and lifecycle owner of the
  local definitions below.
- **Expense review agent**, an Agent definition acting through an identified
  service Principal and Principal Identity.
- **Employee**, a human Principal with an authenticated employee Identity.
- **Expense renderer requirement**, a Runtime binding requirement for an
  identified renderer runtime instance. Its resolved binding must support the
  pinned A2UI `v0.9.1` format binding and the selected catalog implementation.
- **Expense surface state**, a State definition for the component graph and data
  model of each active expense surface. Progressive updates produce successive
  State occurrences. The renderer runtime instance is the declared authority
  for resolving concurrent writes and identifies the current occurrence. The
  active state ends when the surface is deleted or the execution ends,
  whichever comes first. Retained history follows the separate trace and State
  retention rules.
- **Expense surface**, one runtime Resource identified for the current
  execution. Its A2UI surface identifier is correlation data, not a global
  AgSDL definition identity.
- **Reviewed expense catalog**, a Referenced component governed by the client
  application owner. Its A2UI catalog identifier, content digest, renderer
  implementation version, and allowed components and functions remain
  distinct evidence.
- **Generated expense interface**, a bidirectional Interface. Its outbound
  operations carry A2UI surface lifecycle messages. Its inbound operation
  carries A2UI user-action messages and renderer errors.
- **Expense surface lifecycle**, a Protocol with absent, active-incomplete,
  renderable, invalid, and deleted states. User submission is disabled outside
  the renderable state.
- **Request expense submission**, an unprotected Action that records the user's
  request for review against **Expense review queue**, an internal Resource.
  It may produce a **submission requested** Effect. The A2UI `submit_expense`
  event requests this Action but is not itself proof of identity, approval, or
  execution.
- **Submit approved expense**, a protected Action that can produce an
  **expense recorded** Effect against the external expense service Resource.
- **Expense approval requirement**, which requires a separate, matching human
  Approval decision for the final amount, currency, merchant, date, and receipt
  identity.
- **Renderer boundary**, a Trust boundary between the agent service and the
  employee-side renderer. It governs generated components and updates flowing
  toward the renderer, and action context or synchronized data flowing back.
- **Expense service boundary**, a Trust boundary governing the protected
  submission and external Effect.

The A2UI data model is execution State. It does not become Memory merely because
the renderer can return it to the agent. This example disables full data-model
synchronization. The action context carries only the final fields required by
Request expense submission.

## Binding requirements

The Expense renderer requirement selects the current production release
`v0.9.1` in the stable A2UI `v0.9` protocol family. It pins the reviewed
upstream schemas and catalog by immutable identity. The selected format binding
disables inline catalogs: the agent does not advertise acceptance, and the
renderer supplies none. The binding also rejects `v1.0` candidate envelopes,
unknown components, and unknown renderer functions.

The selected transport binding must provide ordered and framed outbound
messages, a correlated return path, endpoint authentication, confidentiality,
integrity, freshness, replay handling, and explicit delivery failure. A
transport product name alone does not satisfy the requirement.

The renderer must:

- reject updates before surface creation and duplicate creation while the
  surface remains active;
- maintain component graph and data model as separate parts of Expense surface
  state;
- display placeholders without enabling submission while required references
  or bindings remain unresolved;
- validate every envelope against the pinned protocol and catalog schemas;
- enforce catalog and URL policy independently of agent output;
- record applied and rejected updates in the required execution trace;
- correlate an action to the current surface occurrence and authenticated
  employee session;
- end the active surface state on deletion, release values under the declared
  retention rules, and keep any retained history separate from a later reuse
  of the same A2UI identifier.

These are binding requirements. Only a resolved renderer binding plus suitable
test and execution evidence can show that an implementation satisfies them.

## Narrative path

1. Expense review agent sends a surface creation message for a new expense
   surface using Reviewed expense catalog. Expense surface lifecycle moves from
   absent to active-incomplete.
2. The agent sends progressive component and data updates. The renderer applies
   each valid update in order. Missing child references keep the surface in
   active-incomplete, and the employee cannot submit it.
3. Once the root, required fields, component references, validation rules, and
   policy controls resolve, the renderer moves the surface to renderable. The
   employee corrects the amount. This changes Expense surface state locally.
4. The employee activates the submit component. The renderer emits an A2UI
   `submit_expense` action message with the current surface correlation,
   component source, timestamp, and minimized context. The message crosses
   Renderer boundary as untrusted input.
5. Generated expense interface maps the message to Request expense submission
   after verifying the authenticated employee session, current surface
   occurrence, expected component, freshness, and non-replay conditions.
6. The system presents a separate Approval request containing the final
   material context. A matching human Approval decision may contribute to the
   Authorization decision for Submit approved expense. The earlier A2UI action
   does not satisfy that requirement.
7. A permitted Authorization decision lets the service Principal invoke Submit
   approved expense across Expense service boundary. Expense recorded remains
   a distinct Effect occurrence. A denied or indeterminate decision produces no
   permitted submission.
8. The agent requests surface deletion. The renderer produces the terminal
   State occurrence, ends the active surface state, and records deletion. State
   history and trace records remain subject to their declared retention rules.
   A later `v0.9.1` surface may reuse the external identifier, but it receives a
   new Resource identity and a separate State history.

## Version-candidate variation

If the system later selects an A2UI `v1.0` binding, it needs a new binding
identity and review. The candidate can put initial components and data in
surface creation, mix catalogs, attach extensions, and exchange remote function
calls. It also changes deletion semantics and surface identifier lifetime.

The stable binding in this example must not approximate those features. A
candidate function that submits the expense would be a protected AgSDL Action,
not harmless renderer logic. Catalog caller metadata would still not replace
Expense approval requirement or the Authorization decision.

## Counterexamples

- The renderer shows a submit button before later component updates provide the
  final amount and warning text, then accepts a click. This treats partial
  progressive state as a complete interface and breaks the declared lifecycle.
- The renderer sends an inline catalog in its client capabilities, and the agent
  accepts it despite this binding's policy. A familiar identifier is not
  integrity evidence, and this example forbids client-supplied inline catalogs.
- The system treats `sourceComponentId: submit_button` and the message timestamp
  as proof that the employee approved the final expense. Both are payload
  claims. Neither authenticates the employee or satisfies the Approval
  requirement.
- Full data-model synchronization sends receipt notes and internal accounting
  fields to the agent even though only amount, currency, merchant, date, and
  receipt identity are required. This violates the example's minimization and
  synchronization policy.
- A reused `v0.9.1` surface identifier inherits the deleted surface's Approval
  decision. Identifier reuse creates a new occurrence and cannot transfer
  approval or authorization.
- A runtime advertises Reviewed expense catalog and is treated as authorized to
  open URLs or submit expenses. Catalog support is an implementation feature,
  not an Authority grant.
