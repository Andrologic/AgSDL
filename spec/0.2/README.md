# AgSDL 0.2.0

Status: **published bounded draft under `v0.2.0`.** [Decision 0013](../../docs/decisions/0013-adopt-0.2.0-contract.md)
records the bounded adoption under delegated maintainer authority. The document
and report marker is `agsdl-0.2.0`. The [0.1.0 specification](../README.md)
retains its meaning and bytes. Publication history is maintained in the
[release-status reference](../../README.md#release-status-and-history).

This index and its three chapters define the normative 0.2.0 contract.
Requirements apply within their stated scopes. Schemas derive from this text;
examples, historical proposals and readers do not add semantics. The concrete
contract was reviewed at `bc441c0a894d286c4585eee261b07f8f03f9d6a7` before its
mechanical edition promotion. The old candidate marker is a distinct edition
and is rejected by 0.2.0 readers; its reports cannot be relabelled as 0.2.0 evidence.

| Chapter | Scope |
| --- | --- |
| [Content, configuration and declarations](content.md) | Closed document shapes, Messages, persistent Agents, configuration selection, Interfaces, structured results, URI origins and exact support declarations. |
| [Flow, lifecycle and protected admission](flow.md) | Data and delivery profiles, queueing and steering, response attribution, blocks, joins, failure inputs, local composition and approval gates. |
| [Static validation and supplied-record checks](validation.md) | Static rule codes and report limits; completion, delivery, admission and preparation record checks. |

## Requirement and evidence scopes

Requirements describe declarations and consuming-integration behavior. The
graphless `ExternalDeliveryRequest` is a declarative delivery profile, not a
transport or live endpoint. Flow result fields describe selector inputs, not a
mandatory wire envelope. The lifecycle and admission obligations apply at their
stated boundaries; passing a static or supplied-record check does not demonstrate
them in a running system.

The validation chapter defines each check's scope. Reports retain
`executionSupport: not-assessed`. The [independent declaration-reader corpus](../../tooling/0.2/conformance/README.md)
has 112 cases, including rejection of the pre-adoption candidate marker. Its
report interchange conventions are non-normative. Schema comparison checks
shapes only. Supplied-record checkers have separate tests and are not independently
reimplemented by the JavaScript reader. This edition defines no additional
operation-feature catalog or whole-system conformance profile.

## Bounded scope

Composition is non-nested and serial or conditional internally. Joins use the
specified direct-fork structure. Unknown syntax is rejected. Gate chains,
invocation capture and admission freshness are specified; supplied records
establish internal consistency only. URI payloads, core execution paths and
external support evidence remain unassessed by static readers.

Execution evidence is required for the implementation support claimed, not for
every possible Engine or Tool before publishing a language draft. The
[tooling guide](../../tooling/0.2/README.md) provides commands and examples;
[release notes](../../docs/releases/0.2.0.md) record verification and limits.
