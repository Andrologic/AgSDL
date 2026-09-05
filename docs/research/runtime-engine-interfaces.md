# Runtime engine interfaces

Status: non-normative research, consulted 2026-09-05. This study prepares the
runtime-interface questions in parts 22–31 of the local 0.1.0 work plan. It
adopts no proposal, syntax, schema, identity rule, or graph behavior. All eleven
proposals remain proposed. No agent CLI, SDK, server, or integration was run,
installed, or downloaded for this study. Macro was neither inspected nor changed.

## Evidence and version boundary

The table identifies documentation snapshots, not tested implementation versions.
The web pages are rolling documentation; their consultation date does not pin a
release. Version thresholds below apply only to the stated behavior.

| Key | Interface and primary source | Version evidence and consultation |
| --- | --- | --- |
| C1 | Codex app-server, local `codex-rs/app-server/README.md`, sections Protocol, Lifecycle Overview, API Overview, Approvals, Experimental API Opt-in | Repository `/Users/oscarlahaie/github/codex`, HEAD `00a7b888b23715989db19b74f6cb623ca46be620`; this file had no working-tree changes. Read first on 2026-09-05. This local source snapshot is not an installed binary version. |
| C2 | [Codex App Server](https://learn.chatgpt.com/docs/app-server), sections Protocol, Message schema, Getting started, and turn configuration | Verified 2026-09-05; rolling documentation. Generated protocol schemas are specific to the generating Codex version; none generated here. |
| H | [Run Claude Code programmatically](https://code.claude.com/docs/en/headless), structured output, streaming, session metadata, and continuing conversations | Verified 2026-09-05; rolling CLI documentation. Streaming drain behavior changes at v2.1.214; cross-project resume lookup changes at v2.1.223. No installed version checked. |
| S | [Agent SDK overview](https://code.claude.com/docs/en/agent-sdk/overview), capabilities and interface comparison | Verified 2026-09-05; Python and TypeScript libraries, no package version pinned. The SDK exposes the Claude Code agent loop; the direct model Client SDK and hosted Managed Agents are separate interfaces/products. |
| P | [Python SDK reference](https://code.claude.com/docs/en/agent-sdk/python), query versus ClaudeSDKClient, ClaudeAgentOptions, message types | Verified 2026-09-05; rolling reference. The TypeScript reference returned a retrieval error, so detailed method claims below use Python only. |
| A | [SDK permissions](https://code.claude.com/docs/en/agent-sdk/permissions), evaluation flow and allow/deny rules; [CLI permissions](https://code.claude.com/docs/en/permissions), permission rules | Both verified 2026-09-05; rolling documentation. Rules and callbacks have ordering and exceptions, not a universal approval interception guarantee. |
| F | [SDK configuration loading](https://code.claude.com/docs/en/agent-sdk/claude-code-features), settingSources and inputs outside its control; [CLI reference](https://code.claude.com/docs/en/cli-reference), flags | Both verified 2026-09-05; rolling documentation. Configuration defaults need rechecking for the selected SDK and CLI versions. |

C1 is reproducible only where that source snapshot is available. C2 independently
confirms the public protocol outline. C1 calls WebSocket experimental and
unsupported; C2 also warns that the app-server command is experimental and not
supported for production workloads. Neither is evidence of an AgSDL integration.

## Documented capability matrix

Cells name external API elements, not proposed AgSDL fields. Codex app-server
and Claude Code are engine interfaces; a model provider supplies model inference,
a protocol carries interactions, and hosting places processes. These roles do
not identify one another. The engines below are research examples, with no
selection, default engine, or closed catalogue implied.

| Concern | Codex app-server | Claude Code CLI and Agent SDK |
| --- | --- | --- |
| Interface | Bidirectional JSON-RPC-style messages without the `jsonrpc` header; JSONL over stdio, plus documented socket transports. Initialization precedes requests. C1/C2. | CLI subprocess with `-p`; Python and TypeScript SDKs expose the agent loop. H/S. |
| Configuration and model | Thread/turn options include model, working directory, sandbox and approval settings. `config/read` reports effective layered configuration. Resume can recover persisted model/effort or use explicit overrides. C1. | CLI `--model`, `--settings`, `--setting-sources` and system-prompt flags; Python `ClaudeAgentOptions` exposes model, working directory, environment and prompt options. F/P. |
| Sessions and resume | `thread/start`, `thread/resume`, `thread/fork`; Thread contains Turns and Items. Ephemeral threads can be memory-only. These are Codex session concepts. C1. | CLI `--continue` or `--resume` with session ID. Python `query()` starts fresh unless continuation/resume is requested; `ClaudeSDKClient` supports multiple exchanges. H/P. |
| Streaming and results | Item start/completion and text-delta notifications; `turn/completed` supplies terminal turn state. A response to `turn/start` is not completion. C1. | CLI text, JSON, or JSONL events; final `result` includes response and session metadata. Partial messages require the documented streaming flags. Python returns an asynchronous message iterator. H/P. |
| Approvals | Server-initiated command and file-change approval requests carry thread/turn/item correlation. Policy and managed requirements affect whether prompting occurs. Experimental permission requests and dynamic tools require capability opt-in. C1. | SDK hooks, rules and permission mode precede unresolved `canUseTool` decisions. `allowedTools` auto-approves listed tools; it does not remove other tools. Bare deny entries can remove tools. A callback alone does not mediate every action. A. |
| Tools | Built-in tool events and MCP management are documented. `dynamicTools` and `item/tool/call` are experimental client-tool interfaces, distinct from MCP. C1. | Built-in tools, MCP, hooks and subagents are documented. Python supports custom SDK MCP tools. Availability and authorization are separate controls. S/P/A. |
| Cancellation | `turn/interrupt` ends an active turn with terminal notification. This establishes a control request, not rollback of prior side effects. C1. | Python `ClaudeSDKClient.interrupt()` is documented; Python `query()` does not support interrupts. CLI print-mode cancellation and external side-effect cleanup guarantees are not established by H. P. |
| Ambient context | Effective configuration layering, managed requirements, working directory and persisted session state affect behavior. C1 documents skill discovery through `skills/list`. This study does not establish a complete inventory or suppression contract for instruction files, memory, hooks and host inputs. C1. | Omitting `settingSources` loads user/project/local settings and project instructions. An empty list does not suppress managed policy, global configuration or auto memory. Working directory affects discovery; child instructions can load on demand. F. |
| Unproven limits | No tested disconnect/replay, event-loss recovery, cancellation cleanup, policy coverage, session portability or AgSDL mapping. Experimental opt-in does not provide compatibility guarantees. | No tested cross-language SDK parity, crash recovery, complete approval coverage, session portability, cancellation cleanup or AgSDL mapping. CLI behavior cannot be inferred for every SDK version. |

## Implications for the proposed model

[Proposal 0002](../../proposals/0002-core-conceptual-model.md#runtime) describes
Runtime as execution capabilities, a binding requirement as portable constraints,
and a resolved binding as a deployment-specific selection. The following are
recommendations for later proposal work, not adopted requirements:

- Describe needed capabilities separately from the chosen engine, interface,
  model provider and hosting environment. For example, resumable conversation
  and mediated file writes are separate needs; a model name proves neither.
- Record candidate evidence at interface and version granularity. Documentation
  establishes a candidate capability, while a later integration test would need
  to establish its actual coverage. Keep unsupported and indeterminate outcomes
  visible rather than interpreting missing evidence as support.
- Assess approval application points against actual interception paths. An
  approval callback or sandbox setting alone does not prove enforcement of every
  proposed Policy application point.
- Investigate configuration provenance and ambient context before describing
  reproducible bindings. Record what can be observed, overridden or suppressed,
  and what remains controlled by the host or organization.
- Keep session IDs and streamed results as engine-specific evidence until an
  occurrence mapping has been reviewed. Neither conversation resume nor fork
  proves portable state identity, graph semantics or execution equivalence.

A future resolved-binding study could compare each requirement with a pinned
candidate and a coverage report. This document supplies no binding serialization,
`engineRef`, feature identity, default engine or compatibility claim.

## Questions for a future Macro implementation

Macro has no defined engine contract for this study. Request the following from
its implementer before making any capability claim:

- Published interface entry points, transport, lifecycle handshake, versioning
  and experimental-feature policy.
- Separation of engine configuration, model/provider choice, credentials
  references and hosting constraints.
- Session creation, persistence, resume and fork contracts, including storage
  scope, retention and behavior after failures.
- Event/result schemas, correlation, ordering, terminal states, errors,
  backpressure and reconnect behavior.
- Tool registration/discovery, MCP boundaries, permission evaluation order,
  approval callbacks and the exact actions those controls mediate.
- Cancellation scope, acknowledgement and terminal evidence, including tools
  already running and irreversible external effects.
- Ambient inputs, discovery timing, precedence, effective-configuration reporting
  and isolation controls for instructions, settings, skills, hooks and memory.
- Unsupported-capability reporting and version-pinned integration evidence for
  each claimed requirement, including explicit unknowns.

These questions also apply to other candidate engines. Answers would inform
later research and proposals; they would not adopt an AgSDL runtime contract.
