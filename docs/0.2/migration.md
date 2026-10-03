# Migrating from 0.1 and the 0017 experiment

This guide helps readers carry system intent from the published `agsdl-0.1.0`
contract or the frozen `agsdl-exp-0017-c1` experiment into the persistent-Agent
and Message model being prepared for 0.2. It describes the accepted directions
in [Decision 0011](../decisions/0011-message-based-agent-model.md) and
[Decision 0012](../decisions/0012-blueprint-flow-directions.md), and the current
proposals [0019](../../proposals/0019-agent-prompt-and-resources.md),
[0020](../../proposals/0020-blueprint-flow-0.2.md), and
[0021](../../proposals/0021-logic-block-contract-0.2.md). It is a migration aid,
not a normative contract or an automatic conversion recipe. The [0.2
preparation index](README.md) records what is accepted, proposed, and still
unsettled.

## Keep editions and evidence distinct

The published 0.1 contract remains `agsdl-0.1.0`. The frozen 0017 experiment
uses `agsdl-exp-0017-c1`; its readers and comparison evidence apply to that
candidate. The persistent-Agent flow c1 is another bounded experiment,
`agsdl-exp-flow-0.2-c1`. None of these markers can be relabelled as another.
There is no automatic upgrade or format converter. Preserve each source
artifact and its reports, then author a separate target description against the
eventual adopted 0.2 contract. Static checks do not establish execution support.
The official 0.1 reader contract names seven operations: `inspect`,
`validateD`, `validateG`, `resolveG`, `validateR`, `exchange`, and
`lossyExchange`. Experimental candidates have their own static checks and
report scopes; those checks do not replace the seven official operation
contracts or produce comparable official results.

## Re-map the model before the flow

The 0.1 model centers on a versioned Document boundary, Root, owned Definitions,
typed Relations, exports, dependencies, and optional Graph and
RuntimeDeclaration records. The next model centers on persistent Agents,
Messages, content, configuration, and, when needed, a flow. Do not assume that
one old record becomes one new record.

For each old Root and Definition, decide which system boundary and reusable
content still matter. Carry their human meaning into the target description,
but retain the old Keys, owners, package boundaries, exports, dependency
identities, hashes, and provenance in the source record or an explicit migration
cross-reference if the target model does not represent them. In particular,
0.1's `System`, `Fragment`, and `PackageVersion` roots and Definition ownership
do not map directly to named Agent and content entries. Do not silently discard
package identity or treat a content URI as a versioned AgSDL Definition.

Make a loss list for the old D relations (`actsAs`, `exposes`, `directedBy`,
`uses`, and `contains`), exports, dependencies, and deferrals. The next model
does not carry these as equivalent typed relation records. Re-express their
intent in Agent, content, configuration, or flow declarations where the target
contract provides a corresponding concept; retain the original tuple and
target identity alongside the migration record when it does not.

For each Agent, separate instructions from information made available to it.
0.1 `Instructions` and `directedBy` relationships can inform the target prompt;
documents, reports, and other supporting material belong with resources. A
resource does not become an instruction merely because the old format stored
both as Definitions. Keep declared accessibility and actual authorization
separate: a URI does not establish that content is available or permitted.
The target directions allow multiple media types and optional output
constraints, subject to the selected Engine and integration.

Do not treat content applied before every old invocation as only the persistent
Agent's initial prompt. Distinguish initial instructions from instructions or
information that must accompany later Messages. Retain or explicitly remap
application adapters, parameters, order, and 0017 instruction-slot identities;
repeated applications must not be silently deduplicated. The next contract may
not preserve each application mechanism.

0.1 requires each Agent Definition to refer through `actsAs` to a Principal,
and each invoke to agree with that Principal. The 0017 experiment removed the
Principal catalog and approval-recipient lists. The next model uses one Agent
concept for human and software participation and does not define Principal as
its actor record. Preserve any needed identity, responsibility, or audit facts
outside that removed relation. Authentication and authority remain external.
A human Message or Agent opinion does not authorize a protected action; keep
approval intent attached to the action in the target design.

## Re-map work, state, and configuration

A 0.1 Graph schedules explicit `invoke` operations against an Agent Interface
and Operation. Each invoke carries action, resource, principal, context and
typed port references. The 0017 grammar also describes calls and explicit
operations. In the next model, an Agent is a continuing participant across
Messages. A flow step addresses work to that Agent; revisiting it does not
create a new Agent or reset its context. A fresh context therefore needs a
separate Agent. Preserve invocation-specific action/resource scope and typed
input/output obligations when they remain important, since they do not
automatically follow from naming an Agent.

Record the old graph's intended order, branches, terminal outcomes, and failure
paths before rewriting it. The next flow directions support deterministic
conditions, routing decisions, parallel connections, explicit joins, loops,
and recovery. All connections from the selected output activate their
destinations; other outputs remain inactive. Direct inputs to an Agent remain
separate Messages unless a Join groups results. By
default, transfer includes all user-visible text for the completed work,
including progress text, and excludes reasoning and raw Tool exchanges. If the
old graph relied on selected outputs, typed port bindings, success-edge-only
output availability, or a narrower transfer, state that intent explicitly in the new
flow design. Do not infer an implicit Join or iteration limit.

0.1 `RuntimeDeclaration` binds configurations to graphs and assigns Engines,
Tools, implementations, reusable-content Applications, parameters, and
capability claims. 0017 has its own explicit per-Agent configuration and
Application grammar. The next model selects each Agent's configuration before
initialization; that selection remains fixed for the Agent instance. There is
no default provider or Engine. Re-map Engine and Tool choices, settings, access,
prompt/resource content, and output requirements deliberately. Preserve old
compatibility claims and their evidence as source assertions when needed; the
new directions do not make an Engine or Model name proof of support.

## Manual migration sequence

1. Keep an unchanged copy of the 0.1 or 0017 artifact, its marker, and any
   associated report or comparison evidence.
2. Inventory the system boundary, reusable identities, ownership, external
   dependencies, Agent roles, principals, interfaces, action/resource scope,
   graph outcomes, and configuration evidence in the source.
3. For each item, record whether the target keeps it, expresses it through a
   different concept, or leaves it outside the target model. Carry forward
   security, authorization, and provenance obligations explicitly.
4. Author the target description against the adopted 0.2 serialization when it
   exists. The current c1 schema and static reader can illustrate and check
   their bounded candidate only; c1 does not settle all accepted directions.
5. Validate with tools for the target edition and retain their edition marker
   and evidence scope. Do not compare a c1 result as if it were an official
   0.1 result, or claim runtime behavior from static validation.

Before using a new edition, consult the preparation index for pending decisions
about block contracts, protected actions, capability support, lifecycle,
delivery, and migration scope. [Decision 0010](../decisions/0010-human-and-software-agents.md)
and [Decision 0011](../decisions/0011-message-based-agent-model.md) retain the
shared Agent model and separate approval controls. [Proposal 0019](../../proposals/0019-agent-prompt-and-resources.md)
records support declarations; [Proposal 0021](../../proposals/0021-logic-block-contract-0.2.md)
retains protected-action and support requirements. Their concrete syntax and
integration contracts remain pending for the next contract. Condition, Join,
Prepare, Call, and composition forms remain proposed, not adopted 0.2 syntax.
