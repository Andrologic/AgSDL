# AgSDL 0.1.0

This is the adopted normative AgSDL 0.1.0 contract, with document and report
marker `agsdl-0.1.0`. Adoption is recorded in
[Decision 0007](../docs/decisions/0007-adopt-0.1.0-contract.md). Adoption does not
state that a release has been published or that any implementation conforms.

The normative specification consists of this index and the following chapters.
Requirements stated in declarative form are binding within their named scope.
Examples illustrate those requirements. Historical proposals, schemas, fixtures
and implementations do not add requirements or resolve contradictions in them.
A schema mismatch is a defect; the normative text controls.

| Chapter | Scope |
| --- | --- |
| [Model and vocabulary](model.md) | Definition identity, ownership, actors and fixed configurations. |
| [Serialization and operations](serialization.md) | Shared closed notation, JSON, host requests, phases and prerequisites. |
| [D: document declarations](document.md) | Envelope, relations, minima, dependencies, deferrals and extensions. |
| [G: simple graphs](graph.md) | Explicit Interface operations, data flow and sequential human gates. |
| [R: configurations](runtime.md) | Per-Agent engines, tools, content and declared compatibility. |
| [Reports](reports.md) | Closed report grammar, diagnostics, inventory, rule execution and preservation. |

## Edition and feature identities

The official specification Edition is `{"identity":"agsdl/spec","version":"0.1.0"}`.
The report contract Edition is `{"identity":"agsdl/report","version":"0.1.0"}`.
Both are denoted by `contract:"agsdl-0.1.0"` in their respective closed records;
neither requires an extra field. Rule identifiers in Reports are scoped to this
report contract. Processor Edition identifies the reporting implementation.

An implementation feature is one named operation contract below. Each feature
has version `0.1.0`, and includes its full input, inventory, output, diagnostic,
prerequisite and exclusion rules from these chapters. There is no selectable
subset of rules within a feature. Features may be implemented separately.

| Feature identity | Operation | Validation unit and phase |
| --- | --- | --- |
| `agsdl/inspect` | inspect | Inventory only, phase null. |
| `agsdl/validateD` | validateD | D, unresolved-document. |
| `agsdl/validateG` | validateG | G with D prerequisite, unresolved-document. |
| `agsdl/resolveG` | resolveG | G with primary/required-annex D prerequisites, resolved-graph. |
| `agsdl/validateR` | validateR | R with D prerequisite, unresolved-document. |
| `agsdl/exchange` | exchange | Exact preservation, phase null. |
| `agsdl/lossyExchange` | lossyExchange | Mandatory refusal and prospective loss inventory, phase null. |

A feature claim identifies its processor Edition, these exact feature Editions
and the evidence inputs/procedure used. A Report identifies one operation and
its input hashes; it is an observation, not a certificate of every implementation
behavior. A positive D/G/R Result covers only the unit and phase in that Result.
No general conformance profile, execution feature, runtime readiness feature or
whole-model conformance claim is defined by this edition. Inspection success
and byte-preserving exchange are independent of document validity.

There is no version ordering, automatic upgrade or compatibility inference from
these identities. Documents validated together by resolveG use this exact
marker. Other markers fail validation shape; exact exchange may preserve their
bytes without relabelling them. Experimental reports remain historical evidence
for their own editions and cannot be relabelled as official results.
