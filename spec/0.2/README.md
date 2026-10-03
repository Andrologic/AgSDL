# AgSDL 0.2 candidate specification

Status: **candidate requirements pending maintainer adoption. Unreleased.**
The document marker remains `agsdl-exp-flow-0.2-c1` pending final edition
allocation. Moving these rules into `spec/0.2/` neither adopts them nor replaces
the [normative 0.1.0 specification](../README.md). Published versions are recorded
in the [release status](../../README.md#release-status-and-history).

This index and its three chapters are the canonical candidate contract, moved
from the persistent-Agent experiment. The schema derives from these rules;
examples and readers do not add semantics. The accepted design directions are
recorded in [0019](../../proposals/0019-agent-prompt-and-resources.md) and
[0020](../../proposals/0020-blueprint-flow-0.2.md), with the proposed common block
contract in [0021](../../proposals/0021-logic-block-contract-0.2.md). Those proposals
retain their status; the concrete candidate requirements here await final review
and an explicit maintainer adoption decision.

| Chapter | Scope |
| --- | --- |
| [Content, configuration and declarations](content.md) | Closed document shapes, Messages, persistent Agents, configuration selection, Interfaces, structured results, URI origins and exact support declarations. |
| [Flow, lifecycle and protected admission](flow.md) | Data and delivery profiles, queueing and steering, response attribution, blocks, joins, failure inputs, local composition and approval gates. |
| [Static validation and supplied-record checks](validation.md) | Static rule codes and report limits; completion, delivery, admission and preparation record checks. |

## Requirement and evidence scopes

Candidate requirements describe declarations and consuming-integration behavior.
The graphless `ExternalDeliveryRequest` is a declarative delivery profile, not a
transport or live endpoint. Flow result fields describe selector inputs, not a
mandatory wire envelope. The lifecycle and admission obligations apply at their
stated boundaries; passing a static or supplied-record check does not demonstrate
them in a running system.

The validation chapter defines each available check's scope. Reports retain
`executionSupport: not-assessed`. Schema comparison checks shapes only. The
[independent declaration-reader comparison](../../experimental/agent-flow-0.2/conformance/README.md)
covers 107 cases; existing 0.1 and frozen
0017 evidence cannot be relabelled as evidence for this candidate. The
[experiment guide](../../experimental/agent-flow-0.2/README.md) contains the
examples, implementation commands and evidence references.

## Remaining release scope

This candidate is a testable foundation, not a proposal to silently remove
accepted features from 0.2. Unknown syntax is rejected rather than ignored. The
[preparation index](../../docs/0.2/README.md#before-a-02-release) tracks completion.
The following boundaries remain explicit for final review and adoption.

| Area | State and remaining work |
| --- | --- |
| Composition | Non-nested serial/conditional expansion, explicit Agent parameters and diagnostic origins are specified and checked. Review the bounded form before adoption. |
| Protected actions | Gate chains, invocation capture and admission deadlines are specified; static structure and supplied record consistency are checked. Authority/enforcement needs consuming implementation evidence. |
| Interfaces and support | Bounded value constraints, URI origins and scoped exact claims are specified and checked. URI payloads and core execution paths remain explicitly unassessed. |
| Lifecycle integration evidence | Queue and steering obligations, text assembly, source selection and error inputs are defined. Static record checks do not prove attribution, delivery, correction or cancellation in an implementation. |
| Validation and release | Independent declaration comparison is available. Final review of graph and check coverage, migration guidance review, final edition allocation and explicit maintainer adoption remain pending. Publication requires a separate decision. |

Execution evidence is required for the implementation support claimed, not for
every possible Engine or Tool before publishing a language draft. No release
tag, official contract replacement or publication follows from this preparation.
The [draft release notes](../../docs/releases/0.2.0.md) describe the proposed scope.
