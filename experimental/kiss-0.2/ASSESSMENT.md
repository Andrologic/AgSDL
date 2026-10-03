# Agent-only KISS assessment

Status: experimental findings and recommendations, not normative adoption.
The [candidate](../../proposals/0017-agent-only-kiss-0.2.md) is
`agsdl-exp-0017-c1`; the published contract remains `agsdl-0.1.0` in release 0.1.1.

## Observed facts

The [42-case corpus](corpus/README.md) passes for the updated Python and
JavaScript readers: 42/42 cases, 84 valid reports, zero oracle mismatches and
zero reader mismatches. This includes negative and incomplete results whose
exact observations are expected. The comparison checks all six results and all
diagnostic/gap tuples, including cause sets. Reader outputs did not supply the
expectations. The focused suites pass 25 Python tests, 72 JavaScript tests and
9 comparator tests.

The implementations were developed separately for c2. This revision updates both
in one change; their agreement is useful evidence but is not a claim of two
independently authored implementations of the Principal removal. Each run retains
its actual Git SHA, dirty state, runtime versions and candidate/input/source
hashes outside the checkout. Reproduce with the command in the corpus guide.

The previous c2 assessment, 38-case corpus and readers remain available in Git
at `f2a20f28f8d03baa1f7cb1bb4f477ea4dd3706b0`. Proposal 0016 and Decision 0008
are unchanged. Their evidence describes that earlier candidate only.

[measure.py](measure.py) counts every object member recursively, top-level fields
and compact UTF-8 bytes, with source hashes. Run
`python3 experimental/kiss-0.2/measure.py` from the repository root.
Whitespace is excluded; string content and authored names still affect size.

| Declaration | Object members | Compact bytes | Root fields |
| --- | ---: | ---: | ---: |
| 0.1.0 single Agent | 83 | 1,230 | 8 |
| 0014 single-Agent sketch | 40 | 703 | 4 |
| 0017 named Agent | 28 | 489 | 4 |
| 0017 embedded Agent | 24 | 431 | 2 |
| 0.1.0 two-Agent sequence | 288 | 4,216 | 9 |
| 0014 two-Agent sketch | 105 | 1,763 | 4 |
| 0017 two-Agent sequence | 81 | 1,354 | 5 |
| 0017 sequence with two configurations | 235 | 4,832 | 7 |
| Historical c2 governed call | 132 | 2,522 | 6 |
| 0017 governed call | 121 | 2,316 | 5 |

The governed-call change removes 11 members and 206 compact bytes: its Principal
catalog, Agent reference and two approval recipient lists. These were actor data,
not empty placeholders. A consumer must handle any needed assignments separately.
The other examples retain their previous size because the edition markers have
the same length and those examples already omitted Principal.

Original [0.1.0 examples](../../examples/0.1.0/README.md) and
[0014 sketches](../../docs/research/0.2-design-examples.md) are unchanged. Similar
use cases have different information and obligations; these are not lossless
conversions. Named and embedded Agents share content and operation here, saving
four members and 58 bytes by embedding, at the cost of Definition identity.
Two complete configurations still add 154 members and 3,478 bytes to the sequence.

## Inferences

Removing Principal removes one catalog and all actor/recipient lookups from this
candidate. Scope and approval data checks remain useful because they describe
which call and data a decision concerns. The format now leaves human identity,
authentication and authorization to its consumer. Structural pass cannot prove
that those responsibilities were fulfilled.

The change simplifies the model without merging Agents, engines or configurations.
It does not reduce the remaining cost of Applications, claims, evidence hashes,
complete settings or graph checks. Those need separate decisions, with explicit
accounting for any capability or static guarantee removed.

## Recommendations and limits

Retain explicit instruction order, call interfaces, Tool contracts separate from
implementations, and alternative engine configurations. Further simplification
should target repeated declarations and single-valued fields before removing
useful modularity. Assess configuration and compatibility complexity next.

Normative adoption and the intended 0.2 scope remain undecided. Skills, imports,
packages, assemblies, conditions, parallelism, dynamic delegation and migration
are outside this experiment, not permanently excluded. The corpus is finite;
no runtime, adapter, authentication or external capability evidence was exercised.
Agreement does not establish execution support, universal correctness, lossless
migration or readiness to replace the published contract.
