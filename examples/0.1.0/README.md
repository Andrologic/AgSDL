# Progressive AgSDL examples

These complete JSON documents illustrate the published `agsdl-0.1.0` contract.
They are non-normative. The smaller documents introduce one layer at a time;
the existing full example supplies explicit configuration alternatives without
copying its large runtime declaration into another file.

| Step | Document | Relevant validation and expected Results |
| --- | --- | --- |
| 1 | [minimal-document.json](minimal-document.json) | `validateD`: D pass. A System root and required empty arrays; no Agent minimum applies. |
| 2 | [single-agent.json](single-agent.json) | `validateD`: D pass. One Agent with actsAs Principal, directedBy Role and exposes Interface relations. Payloads remain opaque. |
| 3 | [two-agent-sequence.json](two-agent-sequence.json) | `validateD`: D pass. `validateG`: D/G pass, unresolved-document. `resolveG`: D pass, G pass in resolved-graph, with no annexes. |
| 4 | [general-purpose-system.json](general-purpose-system.json) | `validateD`: D pass. `validateG` and `resolveG`: D/G pass in their respective phases. `validateR`: D/R pass, unresolved-document. |

For every document, `inspect` passes inventory production, `exchange` passes and
returns the identical primary bytes, and `lossyExchange` fails with no artifacts.
Request annexes are `{}`. D Results always use `unresolved-document`; inventory
and exchange Results use phase null. Requesting G or R on an absent container
also passes with the container checks excluded. This supplies no graph or runtime.
R is absent in steps 1–3; G is absent in steps 1–2.

The sequence passes `call-a.y` into `call-b.x` after `call-a` succeeds. Both
invocations have explicit operation, Action, Principal, resources, ports and
bindings; failures reach a failure terminal. Its Role payload supplies no
portable executable instructions.

The full example preserves the existing two-Agent Document, sequence and reusable
Tool/Instructions/Skill content. Unlike the smaller sequence, both calls receive
the graph input `x`. It declares `portable` and `alternate` configurations for
the same graph and Agents; `portable` is explicitly selected. Neither array order
nor a single choice supplies a default. The `example/*` Editions and evidence
hashes are illustrative assertions, not verified support. R pass excludes
readiness and evidence assessment. The example does not execute anything.

## Verify the examples

From the repository root, run the lightweight check with Python 3 and Node.js:

```sh
python3 scripts/check-examples.py
```

It runs both existing reader CLIs on all seven operations for all four documents,
checks Result units/phases/verdicts and exact exchanged bytes, and fails on a
mismatched expectation. It is an example regression check, not a full-report
comparison or semantic oracle. To also validate D, present G/R containers,
interpreted payload shapes and emitted Reports, use an environment with
Draft 2020-12 `jsonschema` installed:

```sh
python3 scripts/check-examples.py --jsonschema
```

No package is needed for the default check. Schemas add shape evidence only.
The [implementation walkthrough](../../docs/implementation-guide.md) explains
byte preservation, operation selection and diagnostics. The
[tooling guide](../../tooling/README.md#prepare-a-request-without-installation)
shows individual requests; replace its example path and operation as needed.
