# Official corpus coverage

The authoritative case index is `fixtures/manifest.json`. Its `coverage` map is
checked in both directions: every listed case declares the same association,
and each association has a Result, Finding, Check or State oracle that supports
the stated variant. A positive validation Result also witnesses every mandatory
rule executed by that unit when the case names that rule.

The matrix covers rule families and report states. It is not exhaustive across
all combinations of malformed prerequisites, duplicate records, extension
modes, graph shapes and configuration choices.

| Rule | Covered variants |
| --- | --- |
| P-SYNTAX | positive, negative |
| P-SHAPE | positive, negative, excluded |
| D-IDENTITY | positive, negative |
| D-OWNER | positive, negative |
| D-REFERENCE | positive, negative, external target unchecked |
| D-RELATION | positive, negative |
| D-CYCLE | positive, negative |
| D-EXPORT | positive, negative |
| D-AGENT | positive, negative |
| D-DEFERRAL | positive, negative, deferred |
| D-DEPENDENCY | positive, negative |
| D-INTEGRITY | positive, negative, inconclusive, unknown |
| X-MODE | positive, negative, unsupported, inconclusive |
| G-TARGET | positive, negative, blocked, excluded |
| G-PATH | positive, negative, excluded |
| G-DATA | positive, negative, excluded |
| G-APPROVAL | positive, negative, excluded |
| G-RESOLVE | positive, negative, unsupported, inconclusive, excluded |
| R-SELECTION | positive, negative |
| R-BINDING | positive, negative |
| R-TOOL | positive, negative |
| R-CONTENT | positive, negative, blocked, excluded |
| R-COMPATIBILITY | positive, negative, inconclusive, unknown, blocked, excluded |
| E-PRESERVE | positive, negative, inconclusive |
| E-LOSS | mandatory failure and prospective Loss records |
| P-PREREQUISITE | blocked only, as required by the report contract |
| X-EXECUTION | excluded only |
| X-FULL-MODEL | excluded only |
| X-READINESS | excluded only in primary R Results |
| X-EVIDENCE-ASSESSMENT | excluded only in primary R Results |

## Operation distribution

| Operation | Cases |
| --- | ---: |
| inspect | 24 |
| validateD | 42 |
| validateG | 24 |
| resolveG | 15 |
| validateR | 14 |
| exchange | 12 |
| lossyExchange | 6 |
| Total | 137 |

The 26 modular cases retain all previously exercised 0.1.0 R families,
Interface Operation selection, two sequential approval gates and direct annex
Operation resolution. The 111 candidate-2-derived cases retain the broader JSON,
D, inspection, preservation, loss refusal, graph path/data, extension and direct
resolution families whose normative rules survived adoption.

The historical `D-DEFERRAL:excluded` label is deliberately absent. The official
resolved-deferral case records a deferred D finding and a failing G-TARGET; G
does not execute D-DEFERRAL, so an excluded D-DEFERRAL Check would be false.

No candidate-2 R case is carried forward. No official case covers the removed
R-REQUIREMENT rule, old subjectless Selection, EvidenceClaim, model/provider or
hosting inventory. The corpus also makes no execution, authentication,
authorization enforcement, readiness, interoperability or publication claim.
