# Modular candidate-1 shapes

These Draft 2020-12 shapes derive from [proposal 0013](../../../proposals/0013-modular-mvp-contract.md),
marker `proposal-0013-candidate-1`. They are experimental, not adopted AgSDL
schemas. Candidate-2 files and their evidence remain unchanged.

[modular.schema.json](modular.schema.json) is one schema resource with explicit
entry points. It reuses unchanged primitive/envelope and condition/end-step
shapes from candidate-2 through relative file references. Resolve those local
references against the schema file; no network retrieval is needed.

| Requested scope | JSON Pointer into modular.schema.json |
| --- | --- |
| D Document, default entry point | /$defs/Document |
| G graphs array | /$defs/Graphs |
| R runtime value | /$defs/RuntimeDeclaration |
| Selected Interface payload | /$defs/InterfacePayload |
| Selected ApprovalRequirement payload | /$defs/ApprovalRequirementPayload |
| Observed Tool payload | /$defs/ToolPayload |
| Observed Instructions payload | /$defs/InstructionsPayload |
| Observed Skill payload | /$defs/SkillPayload |

Choose the schema entry point for the exact value in scope; validating a D
Document alone leaves graphs, runtime and definition payloads opaque. Semantic
selection of a payload and attribution of its errors belong to the proposal's
rules. Schema traversal does not imply that every definition payload is selected.

Records are closed. Requirements, reference uniqueness, operation ids, exact
Agent coverage, content prerequisite order, finite graphs, approval-chain links,
capability assessment and report aggregation need semantic checks outside JSON
Schema. JSON Schema host numeric handling also cannot replace the inherited
lossless JSON parser and mathematical uint/positive check.

This lot checks schema JSON and reference integrity, without deriving or running
a new corpus. Lot B must prepare independent examples and oracles from the exact
proposal revision before either reader is adapted. Existing readers and the
candidate-2 comparator do not claim support for this marker.
