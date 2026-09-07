# Candidate-2 shape schemas

These experimental JSON Schemas derive from
[proposal 0012](../../../proposals/0012-minimal-0.1.0-contract.md).
The proposal remains unadopted. The schemas use
[JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12/json-schema-core).

| Schema entry | Input |
| --- | --- |
| [D.schema.json](D.schema.json) | A complete parsed Document. Definition payloads, graphs, runtime and other JSON fields stay opaque. |
| [G.schema.json](G.schema.json) | The present `graphs` value, an array of Graph records. |
| `G.schema.json#/$defs/Graph` | One Graph. |
| `G.schema.json#/$defs/InterfacePayload` | One selected Interface payload. |
| `G.schema.json#/$defs/ApprovalRequirementPayload` | One selected ApprovalRequirement payload. |
| [R.schema.json](R.schema.json) | The present `runtime` value, a RuntimeDeclaration. |

All references are local to their schema. To validate a named `$defs` entry,
retain the containing schema as the reference-resolution root. Apply selected
payload schemas only when G observes those targets. An absent graphs or runtime
container needs no G or R schema call; null is a present value and fails these
entries. G and R operations still require D validation separately.

These schemas cover record shape, required fields, primitive domains, enums and
explicit grammar array minima. Records are closed; Ports and Binding maps allow
any nonempty member name. Identity and hash patterns reject trailing newlines.
Integer constraints apply mathematically, so a JSON number such as `1.0` can
satisfy an integer constraint.

Schema acceptance is not a D, G or R pass. Readers separately check uniqueness,
identity, ownership, references, exports, deferrals, extension classification,
graph paths, data availability, approval constraints, runtime relationships,
annex accounting and hashes. Those semantic rules are deliberately absent here,
including uniqueness rules that JSON Schema could partly express.

A strict byte parser must first enforce UTF-8, Unicode scalar validity, duplicate
member rejection and the remaining P-SYNTAX rules. Use exact numeric parsing for
interpreted numbers; preserve opaque numeric lexemes and source bytes separately.
A validator receiving rounded floating-point values cannot recover lost precision.
The schemas produce no candidate findings, inventory slices, exclusions or
exchange outputs. No schema result establishes execution support or readiness.
