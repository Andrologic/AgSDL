# KISS c2 assessment

Status: experimental findings and recommendations, not normative adoption.
The [candidate](../../proposals/0016-kiss-experiment-0.2.md) remains
`agsdl-exp-0016-c2`; the published contract remains `agsdl-0.1.0` in release 0.1.1.

## Observed facts

The [38-case corpus](corpus/README.md) passes for both independent readers:
38/38 cases, 76 valid reports, zero oracle mismatches and zero reader mismatches.
This includes negative and incomplete findings whose exact observations are
expected. No oracle expectation was changed to obtain agreement. The comparison
checks all six results and all diagnostic/gap tuples, including cause sets;
it does not reduce agreement to the highest outcome.

The reader baselines reviewed before integration were Python
`04bd276dd75470a05761496b5dc45932e3437873` and JavaScript
`ffc81611a76284dd3fcce05496de3671dc04a197`, integrated at
`970183fbda6fe98fbcf58bf77e99a7077f6b027c`. These identify the reader versions
assessed, not the commit of every future comparison. Each run's external metadata
records its actual checkout SHA, dirty state and source hashes, including reused
lexical parsers. Reproduce with the dedicated command in the corpus guide.

[measure.py](measure.py) counts every object member recursively, counts top-level
fields and serializes these examples with compact separators and unescaped
Unicode to count UTF-8 bytes. It reports source hashes and top-level field names.
Whitespace is excluded; string content and authored names still affect size.
Run `python3 experimental/kiss-0.2/measure.py` from the repository root.

| Declaration | Object members | Compact bytes | Root fields |
| --- | ---: | ---: | ---: |
| 0.1.0 single Agent | 83 | 1,230 | 8 |
| 0014 single-Agent sketch | 40 | 703 | 4 |
| c2 named Agent | 28 | 489 | 4 |
| c2 embedded Agent | 24 | 431 | 2 |
| 0.1.0 two-Agent sequence | 288 | 4,216 | 9 |
| 0014 two-Agent sketch | 105 | 1,763 | 4 |
| c2 two-Agent sequence | 81 | 1,354 | 5 |
| c2 sequence with two configurations | 235 | 4,832 | 7 |
| c2 governed call | 132 | 2,522 | 6 |

The original [0.1.0 examples](../../examples/0.1.0/README.md) and
[0014 sketches](../../docs/research/0.2-design-examples.md) are unchanged.
These are similar use cases with different information and obligations, not
lossless conversions. The official single Agent has four Definitions and three
relations, with empty payloads; c2 supplies actual Instructions and an operation,
and omits an actor. The named and embedded c2 Agent share that content and
operation. Embedding removes two catalogs and their references, saving four
members and 58 bytes here, but changes Definition identities to value addresses.

The official sequence carries scoped/versioned keys, separate relations and
Action/Resource/context declarations. The c2 sequence uses typed catalogs and
four graph steps, with ports on the Interface and Agent selection at each invoke.
It omits actor and scope for pure text processing. The 0014 sequence also omits
governed effects but retains Definition versions, module declarations, an actor
and an Interface reference at each invoke. C2 instead permits one Interface per
Agent and adds named instruction slots and explicit effects. Its higher root
field count comes from separate typed catalogs, despite fewer total members.

Configurations remain substantial: the same c2 Agent/graph declarations plus
two complete configurations add 154 members and 3,478 compact bytes. Engine
choices, claims, Applications and repeated complete settings remain explicit.
The governed-call row is a different scenario with two approval gates, actor,
scope and configuration; it is not a size delta for the plain sequence.

## Inferences and implementation cost

The examples support removing repeated local key/owner information, keeping
call ports at their Interface, and allowing single-use content inline. Optional
Principal removes a placeholder for descriptive Agents but also removes actor
information. Neither this result nor smaller JSON proves that making it optional
is appropriate for every future use case.

Fewer author fields do not eliminate validation work. Named and embedded choices
need equivalent checks. Stable instruction slots and Applications retain ordering
and coverage rules. The readers must separate readable identity/field projections
from whole-record shape, preserve independent failures and union causes. Graph
availability and approval-chain checks remain necessary for these declarations.

Concrete c2 work corrected dependencies around duplicate step ids and empty
requirements. Additional witnesses cover malformed scopes, a missing call beside
unreadable approvers, and duplicate slots beside an unreadable slot. They show
why a detailed report needs more than rejecting the first malformed record.
The comparison found no further reader discrepancy on this corpus. It does not
measure engineering time, prove minimal implementation complexity or use source
line counts as a quality score.

## Recommendations and remaining decisions

Retain the demonstrated local-reference simplification, one declaration of port
types, whole named/embedded content choices and the separation of structural
findings from declared compatibility. Keep explicit content order and coverage;
the negative cases show that omitted or reordered content remains detectable.
The fixed six-unit report suffices for this bounded validation experiment without
an inventory, success trace, byte slices or rewritten output. This supports a
small read-only operation, not a preservation or exchange contract.

Before normative adoption, decide whether the reduced scope is the intended
minimum: one Interface per Agent, optional actor for descriptive cases, literal
rather than identified action/resource scopes, artifact-wide identity and no
per-Definition versions. The cost of complete configuration repetition versus
shared settings/bindings also remains an authoring decision. The corpus does not
select a general module system or settle these tradeoffs.

Skills, imports, packages, assemblies, conditions, parallelism, dynamic delegation
and migration are outside this experiment, not permanently removed. No runtime,
engine, adapter, authentication or external capability evidence was exercised.
Agreement on 38 static inputs establishes neither exhaustive candidate correctness
nor execution support, interoperability, round-trip preservation or readiness to
replace the published contract. Broader scope and normative adoption remain
separate maintainer decisions.
