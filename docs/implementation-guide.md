# Implementation walkthrough for 0.1.1 preparation

This non-normative guide uses the published `agsdl-0.1.0` contract. Version
0.1.1 is local maintenance work. See [release status](../README.md#release-status-and-history)
and the [specification](../spec/README.md) for their separate roles.

## 1. Load bytes and preserve opaque content

Read the primary artifact as bytes. Supply direct annex bytes yourself, keyed
by the declared dependency id. A dependency location is a hint, not a retrieval
instruction. Keep the original bytes for hashes, diagnostic byte locations,
opaque slices and exchange. Parsing and reserializing JSON can change whitespace,
number lexemes and therefore artifact identity.

`inspect` returns an inventory without validating Document semantics. Keep its
opaque slices with the source bytes. A known Kind name does not mean its payload
has implemented semantics. D interprets Document records, identities, relations
and minima; definition payloads and entire graphs/runtime values remain opaque.
G interprets graphs and selected Interface/ApprovalRequirement payloads. R
interprets runtime and reached Tool/Instructions/Skill payloads. Action,
Principal, Resource, Role and ControlFlow payloads remain opaque, as do the
payloads of other known Kinds for which no interpretation is defined. See
[Document boundaries](../spec/document.md) and [model](../spec/model.md).

## 2. Choose the question

| Operation | Question |
| --- | --- |
| `validateD` | Do the Document declarations satisfy D? |
| `validateG` | Do graphs satisfy local G checks, with external target checks excluded? |
| `resolveG` | Do graphs satisfy G using directly supplied required annexes? |
| `validateR` | Do configurations satisfy R, and what support is declared for an explicit selection? |

G and R report their D prerequisite separately. R does not replace G validation.
Absent graphs/runtime containers yield exclusions, not evidence of a graph or
an engine. Start with the [complete progressive JSON examples](../examples/0.1.0/README.md).
Use the existing [request preparation commands](../tooling/README.md#prepare-a-request-without-installation)
with the chosen example path and operation. They encode bytes into the existing
CLI request and invoke both readers. No SDK or runtime setup is required.
Reader-specific host behavior is documented in the [Python guide](../tooling/readers/python/README.md)
and [JavaScript guide](../tooling/readers/javascript/README.md).

## 3. Read the response

Each response contains `report` and base64 `artifacts`. Process exit 0 means a
response was produced. Read each Result's `input`, `unit`, `phase` and `verdict`.
`pass` covers that scope; `fail` records a violation; `unsupported` records
unavailable required interpretation; `inconclusive` records insufficient evidence
or blocked checks. Findings name rules and locations. Checks distinguish
completed, blocked and excluded work. Inventory distinguishes absence, explicit
unknowns, declarations and unchecked content. A deferred obligation remains
visible even when D passes.

Keep reports with the exact input bytes and tested reader revision. The
[diagnostic dossier](reviews/0009-0.1.1-diagnostic-expectations.md) records unresolved
choices for some malformed records and Unicode ordering. Agreement on the
release corpus or the examples is bounded evidence, not universal agreement.
Schemas check shapes only; they do not establish semantic validity or correct
report diagnostics.

## 4. Exchange the original bytes

Request `exchange` separately and inspect its Result before consuming artifacts.
On success, decode `artifacts.primary` and compare it to the original bytes;
do the same for each supplied annex. Exchange enforces its dependency accounting
and integrity rules, but may preserve semantically invalid or non-JSON bytes.
An exchange pass does not imply a validation pass. `lossyExchange` always refuses
output in this edition and reports prospective losses. The
[example check](../examples/0.1.0/README.md#verify-the-examples) exercises both paths.

## Reusable Agents and sub-agents

An Agent is a reusable Definition. `uses` and `contains` describe relations;
a graph can chain invocations, including repeated invocations of one Agent.
Repeated invocations share that Agent's binding within a Configuration.
These declarations define no dynamic creation, fork/join, context or permission
inheritance, nested graphs or delegated execution. There is no `SubAgent` Kind.
An engine may have internal sub-agents, but their behavior is external to the
portable AgSDL contract. Neither a relation nor a static validation report
establishes that behavior.
