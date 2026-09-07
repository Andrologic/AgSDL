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
| D-EXPORT | positive, negative, blocked |
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
| R-SELECTION | positive, negative, blocked |
| R-BINDING | positive, negative, blocked |
| R-TOOL | positive, negative, blocked |
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
| validateD | 45 |
| validateG | 25 |
| resolveG | 15 |
| validateR | 21 |
| exchange | 12 |
| lossyExchange | 6 |
| Total | 148 |

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

## Native maintenance coverage

`official-empty-system-validateD` witnesses D-AGENT positive with no local
Agents. Its oracle follows the Document Agent minima and the rule execution
requirement that a rule with no subjects completes. The 137 historical-derived
cases and their coverage remain unchanged. Native additions are indexed alongside
them without claiming historical provenance.

Ten cases in `official/diagnostic-dependencies.cases.json` isolate determined
partial-diagnostic obligations. Inputs reuse the empty System shape or a compact
single-call System with one Agent, Instructions and Tool. They do not duplicate
the general-purpose example. Their exact Finding oracles come from mandatory
field shape and the absence of independent semantic violations, not reader votes.

| Cause | Native witness and normative basis |
| --- | --- |
| Root identity versus form | Missing root key completes empty exports; missing root kind also blocks form. Document exports and Reports known empty domains. |
| Unreadable enumeration | Missing configurations blocks at runtime; missing selected agents blocks assessment at Configuration. Reports Runtime rule execution. |
| Missing configuration identity | Selection lookup and id checks block while graph checks complete. Runtime Configuration selection and assignments. |
| Missing mandatory engine | Shape fails and binding assessment blocks; supplied Tool assessment remains declared-supported. Runtime Declared compatibility. |
| Missing invoke resources | Resource enumeration blocks G-TARGET while independent targets complete. Graph Targets, data and paths. |
| Missing Instructions body | Shape fails without blocking readable content requirements or declared compatibility. Runtime Content composition and Declared compatibility. |
| Missing Tool action or inputs | Absent action blocks typed lookup; absent ports do not block independent Tool capability assessment. Runtime Tool requirements and Reports R-TOOL. |

The focused reader tests retain exhaustive determined deletion and combination
checks. No complete oracle is added for dossier 0009 groups E/G/I's open choices
or Unicode collation. Check assertions in the manifest require the listed states
and locations; they are not exhaustive Check-set oracles. Exact Finding sets and
selected assessment States additionally guard against invented assessments.
