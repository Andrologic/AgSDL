# Decision 0013: named outcomes with configurable transmission

- Status: accepted 0.2 design directions; no normative adoption or publication.
- Date: 2026-10-01.
- Starting revision: `7c096fe72f4ab46707a8419dc4bd17af0bcb83e9`.

The maintainer accepted named outcomes for step choices, with their transmission
configured through the selected Engine integration, and authorized recording
this model for 0.2. It refines the flow directions in
[Decision 0012](0012-blueprint-flow-directions.md).

The accepted semantics, illustrative mappings and adverse cases are maintained
in [Proposal 0020](../../proposals/0020-blueprint-flow-0.2.md#named-outcomes-independent-of-the-engine).
An ordinary sequence needs no choice. At a declared choice, the Agent selects
one authored continuation while its report follows the existing content and
transfer rules. The integration can obtain that selection through text,
structured data, a Tool, a human interface or another explicit mechanism.
Routing waits for completion, a valid selection and valid required results.
Missing, unknown or ambiguous choices use recovery or a diagnostic stop.

This direction imposes no universal verdict names, mandatory structured report,
Tool, MCP dependency or separate human Agent type. It does not introduce a
runtime, editor contract or hot configuration changes. Compatibility depends
on the configured integration and evidence for it, not the Engine's name.

Concrete serialization, validation rules and integration mappings remain
candidate work. The official specification, frozen 0017 candidate, readers and
their evidence keep their existing meaning. This decision does not claim that
any harness already implements these semantics.
