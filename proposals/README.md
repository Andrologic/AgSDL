# Proposals

Proposals describe material changes before they become normative.

Use a filename such as `0001-system-identity.md`. Include the problem, proposed
semantics, consequences, alternatives, security considerations, compatibility
impact, and unresolved questions.

Proposal acceptance does not update the specification by itself. The normative
change must be applied separately and reviewed against the accepted proposal.

## Status register after the 0.1.0 adoption decision

[Decision 0007](../docs/decisions/0007-adopt-0.1.0-contract.md), dated 2026-09-07,
records the maintainer delegation and the precise contract selected under it.
The [specification](../spec/README.md) is the normative source, not these files.

| Proposals | Current disposition |
| --- | --- |
| 0001 and 0004 through 0010 | Proposed; no normative adoption in Decision 0007. |
| 0002, 0003 and 0011 | Remain conceptual proposals. Only the concrete bounded contract selected through 0012/0013 is adopted, not their full model or conformance rules. |
| 0012 | Limited adoption of candidate-2 rules expressly inherited by 0013; replaced G/R rules, alternatives and experiment instructions are excluded. File remains the byte-identical historical snapshot at `009a51eb301688f06d29bb7e2f1784e3c4a4cc98`. |
| 0013 | Selected modular contract adopted with its retained Principal restriction, applied in spec with official marker `agsdl-0.1.0`. File remains the byte-identical historical snapshot at `280347eec4e2e051d296f9271bfccc86c98d4d40`. |

The proposed-status statements inside 0012/0013 describe their historical
preparation dates. This register records the later limited adoption without
changing pinned source bytes or relabelling experimental corpus evidence.
[Section and rule traceability](../docs/reviews/0007-0.1.0-contract-traceability.md)
identifies every inheritance, replacement and exclusion. Adoption does not
state publication or implementation conformance.

## Proposal files

- [`0001: requirements and use cases`](0001-requirements-and-use-cases.md)
- [`0002: core conceptual model`](0002-core-conceptual-model.md)
- [`0003: conformance and versioning`](0003-conformance-and-versioning.md)
- [`0004: trust, security, and human control`](0004-trust-security-and-control.md)
- [`0005: Model Context Protocol binding profile`](0005-mcp-binding-profile.md)
- [`0006: A2A 1.0 external binding`](0006-a2a-1.0-external-binding.md)
- [`0007: Agent User Interaction Protocol binding`](0007-agent-user-interaction-protocol-binding.md)
- [`0008: external A2UI format binding`](0008-a2ui-format-binding.md)
- [`0009: Agent Payments Protocol binding extension model`](0009-agent-payments-protocol-binding.md)
- [`0010: Open Agent Specification binding`](0010-open-agent-specification-binding.md)
- [`0011: first reading, inspection, and exchange contract`](0011-first-exchange-contract.md)
- [`0012: minimal candidate contract for 0.1.0`](0012-minimal-0.1.0-contract.md)
- [`0013: modular MVP contract`](0013-modular-mvp-contract.md)
