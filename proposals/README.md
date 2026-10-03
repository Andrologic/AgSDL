# Proposals

Proposals describe material changes before they become normative.

Use a filename such as `0001-system-identity.md`. Include the problem, proposed
semantics, consequences, alternatives, security considerations, compatibility
impact, and unresolved questions.

Proposal acceptance does not update the specification by itself. The normative
change must be applied separately and reviewed against the accepted proposal.

For the next model, start with the [0.2 preparation index](../docs/0.2/README.md).
It distinguishes accepted directions, the [canonical candidate requirements](../spec/0.2/README.md),
the proposed block contract and historical experiments.

## Current 0.2 preparation

| Proposals | Disposition |
| --- | --- |
| [0019](0019-agent-prompt-and-resources.md) | 0.2 design directions accepted under [Decision 0011](../docs/decisions/0011-message-based-agent-model.md): persistent Agents, multimodal Messages, distinct prompt/resources, optional initial prompt and output constraints and workspace access through configuration. Concrete grammar is specified in the [candidate specification](../spec/0.2/README.md), pending adoption; the [bounded c1 tooling](../experimental/agent-flow-0.2/README.md) checks its stated static subset. No normative adoption or execution evidence. |
| [0020](0020-blueprint-flow-0.2.md) | 0.2 flow directions accepted under [Decision 0012](../docs/decisions/0012-blueprint-flow-directions.md): visible response transfer, terminal routing decisions, deterministic conditions, configuration before initialization, recovery, loops, parallel output connections, queueing/steering and explicit joins. Concrete grammar is specified in the [candidate specification](../spec/0.2/README.md), pending adoption; the [bounded c1 tooling](../experimental/agent-flow-0.2/README.md) checks its stated static subset. No normative adoption or execution evidence. |
| [0021](0021-logic-block-contract-0.2.md) | Proposed common contract for Condition, Join, Prepare, Call, local compositions and custom implementations. Builds on 0019/0020; the [candidate specification](../spec/0.2/README.md) defines its bounded concrete form under `agsdl-exp-flow-0.2-c1`. No final grammar adoption or execution evidence; remaining release scope stays explicit. |

## Adopted sources for 0.1.0

[Decision 0007](../docs/decisions/0007-adopt-0.1.0-contract.md), dated 2026-09-07,
records the selected contract. The [specification](../spec/README.md) is the
normative source, not these snapshots.

| Proposals | Disposition |
| --- | --- |
| [0012](0012-minimal-0.1.0-contract.md) | Limited adoption of candidate-2 rules expressly inherited by 0013; replaced G/R rules, alternatives and experiment instructions are excluded. File remains the byte-identical historical snapshot at `009a51eb301688f06d29bb7e2f1784e3c4a4cc98`. |
| [0013](0013-modular-mvp-contract.md) | Selected modular contract adopted with its retained Principal restriction, applied in spec with official marker `agsdl-0.1.0`. File remains the byte-identical historical snapshot at `280347eec4e2e051d296f9271bfccc86c98d4d40`. |

The proposed-status statements inside 0012/0013 describe their historical
preparation dates. This register records the later limited adoption without
changing pinned source bytes or relabelling experimental corpus evidence.
[Section and rule traceability](../docs/reviews/0007-0.1.0-contract-traceability.md)
identifies every inheritance, replacement and exclusion. Adoption does not
state publication or implementation conformance.

## Earlier 0.2 design inputs and experiments

These texts retain their recorded status and bytes. They are not the current
Agent/Message contract and have not been collectively adopted or rejected.

| Proposals | Disposition |
| --- | --- |
| [0014](0014-minimal-core-0.2.md) | Proposed smaller core and composable format for 0.2, with [candidate examples](../docs/research/0.2-design-examples.md); not adopted or implemented. The current contract remains `agsdl-0.1.0`. |
| [0015](0015-validation-reports-0.2.md) | Proposed lightweight validation reports and diagnostic agreement for 0.2; not adopted or implemented. The current contract remains `agsdl-0.1.0`. |
| [0016](0016-kiss-experiment-0.2.md) | Historical bounded candidate under [Decision 0008](../docs/decisions/0008-0.2-experiment-directions.md). Its c2 readers, examples and 38-case assessment remain in Git at `f2a20f28f8d03baa1f7cb1bb4f477ea4dd3706b0`. Not normatively adopted or published; superseded for the active experiment by 0017. |
| [0017](0017-agent-only-kiss-0.2.md) | Frozen agent-only experiment under [Decision 0009](../docs/decisions/0009-agent-only-experiment.md), removing Principal and approval recipient lists. The [42-case comparison](../experimental/kiss-0.2/ASSESSMENT.md) covers the updated static readers. Not normative adoption, publication or execution support. |
| [0018](0018-human-and-software-agents.md) | Accepted 0.2 design direction under [Decision 0010](../docs/decisions/0010-human-and-software-agents.md): common Agent definition for software and human work, with [static feasibility examples](../experimental/kiss-0.2/human-participation/README.md). Its definition-oriented framing is superseded for the next model by 0019 under Decision 0011. No new grammar, candidate edition, normative adoption or execution support. |

Proposal 0016's relative artifact links now open the later 0017 files. Read its
original guide and witness from the recorded historical revision instead:

```sh
git show f2a20f28f8d03baa1f7cb1bb4f477ea4dd3706b0:experimental/kiss-0.2/README.md
git show f2a20f28f8d03baa1f7cb1bb4f477ea4dd3706b0:experimental/kiss-0.2/examples/duplicate-step-assign.json
```

| Proposals | Disposition |
| --- | --- |
| 0022 | Withdrawn notation draft, retained in Git at `c90321f`. No grammar or candidate adopted. The accepted default delivery direction is recorded in 0020 and Decision 0012; the other notation choices remain unaccepted. |

## Earlier conceptual and binding proposals

These proposals precede the current 0.2 model. Their original scope and open
questions are historical inputs, not additional release commitments.

| Proposals | Disposition |
| --- | --- |
| 0001 and 0004 through 0010 | Proposed; no normative adoption in Decision 0007. |
| 0002, 0003 and 0011 | Remain conceptual proposals. Only the concrete bounded contract selected through 0012/0013 is adopted, not their full model or conformance rules. |

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
