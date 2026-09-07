# AgSDL 0.1.0 example

[`general-purpose-system.json`](general-purpose-system.json) is an official,
non-normative example of the locally adopted 0.1.0 contract. It was adapted
from an existing conforming modular-candidate fixture instead of inventing a
second model. The example illustrates the specification; it cannot override it.

The document contains all three declaration layers:

- **Definition**: one System owns two Agents, their Principals, a multi-operation
  Interface, Actions, a Resource, a ControlFlow, a Tool and reusable content.
  Typed relations connect each Agent to its Principal, Interface, Tool and
  direction.
- **Graph**: one closed flow invokes the two Agents in sequence and routes every
  failure to a failure terminal. The selected Interface operation, Action,
  Principal, resources, ports and bindings are explicit at each invocation.
- **Runtime declaration**: `portable` and `alternate` configure the same graph
  and Agents with different explicit engine assignments. `portable` is selected.
  Neither array order nor a single available choice acts as a default.

The `example/*` engine, adapter, implementation and capability Editions are
illustrative custom identities. Their names carry no built-in meaning or trust.
The included claims describe declared support and use placeholder evidence
hashes; they are not verified evidence that an engine or Tool works.

No part of the example launches an engine, invokes a Tool, requests approval or
executes the graph. An actual Execution would be an external occurrence pinned
to the exact document bytes and one configuration id. The 0.1.0 contract defines
no launch API, default engine or execution-readiness verdict.

Use the [tooling guide](../../tooling/README.md) to prepare base64 requests and
run both integrated readers.
