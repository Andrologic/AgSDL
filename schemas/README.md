# AgSDL 0.1.0 schemas

These JSON Schema Draft 2020-12 shapes derive from the adopted
[specification](../spec/README.md). The normative text controls. Schemas do not
create semantics and a schema pass is not a D/G/R verdict.

| Entry point | Input and normative source |
| --- | --- |
| [D.schema.json](D.schema.json) | Document, [D](../spec/document.md); payloads, graphs and runtime stay opaque. |
| [G.schema.json](G.schema.json) | Graphs array, [G](../spec/graph.md); apply only when G interprets it. |
| [R.schema.json](R.schema.json) | RuntimeDeclaration, [R](../spec/runtime.md); apply only when R interprets it. |
| [report.schema.json](report.schema.json) | Report, [report grammar](../spec/reports.md). |
| [agsdl.schema.json](agsdl.schema.json) | All shared record definitions; default entry is Document. |

Selected payload entry points in `agsdl.schema.json#/$defs/` are
`InterfacePayload`, `ApprovalRequirementPayload`, `ToolPayload`,
`InstructionsPayload` and `SkillPayload`. The operation's interpretation closure
in the text decides whether to apply them. An absent optional container is not
validated as null. References are local and complete; no proposal or experimental
schema is needed. The `$schema` URI identifies the standard metaschema, not an
AgSDL network resolver.

The schema checks closed members, required fields, primitive domains and array
minima. It deliberately leaves identity/Edition uniqueness, Ref kinds and
resolution, cycles, Agent minima, content prerequisites, compatibility findings,
checks and report ordering to the normative semantic rules. JSON parsing must
first preserve arbitrary numeric lexemes and reject duplicate names and invalid
Unicode; a host JSON parser or schema library may not provide those guarantees.
Numbers in uint/positive fields must be checked mathematically. Schema errors
are not a substitute for the normative diagnostic locations or partial checks.

The report schema enforces record shapes only. Its unit/phase assignments,
operation/result inventory, input hashes, verdict aggregation, allowed rule ids,
State details, Slice bounds and copied bytes must also satisfy the text.
