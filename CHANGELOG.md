# Changelog

Harness modules keep their own changelogs, in `harnesses/<name>/CHANGELOG.md`.

## 0.3.0 (unreleased)

A redesign. Documents written for 0.2 must be rewritten. See
[decision 0014](docs/decisions/0014-agsdl-0.3-model.md) for the reasons.

### Added

- Harness modules: `harness` on each agent, with modules for Codex, Claude
  Code, opencode and pi, and a diagnostic policy for unsupported,
  approximate and unverified support.
- Standard agent properties: `model`, `skills`, `mcpServers`, `permissions`,
  `results`, `plan`, `planFirst`, `completionCheck`, `maxCorrections`,
  `harnessSettings`.
- Permissions with actions, effects and presets, required on every agent; a
  zone made of the workspace and added `directories`, with reads outside it
  denied by default; home-relative and absolute paths in rules; and
  `reviewer` to choose whether a person or a model answers `ask` actions.
  Harness rules count for reads, writes and network access only when the
  agent cannot run shell commands.
- The `agsdl_submit_result` tool and automatic corrections, bounded by
  `maxCorrections` and `completionCheck.maxFailures`.
- Instances: shared, named and `new`.
- Delivery modes `queue` and `steer`.
- Messages carried by routes, with `from` selections.
- Results typed by media type: JSON values for `application/json` and
  `+json` types, strings for `text/*`, file URIs otherwise.
- Agents that instruct: `instructs`, an `instructions` field in the result
  tool, and a default `prompt` on agent steps.
- Joins deduced from the graph, quorum joins, branch exits, and all-mode
  joins that keep failed branches (`failures`, `maxFailures`, outcome
  `incomplete`).
- Fan-out: `each` on a route target starts it once per element of a list,
  and a join gathers the paths as one list, with each element. An empty list
  completes the join's group at once. `concurrency` caps the paths running
  at once, and `max` the elements, with the `FANOUT_LIMIT` failure.
  Selections read the element with `item`; an instructing agent gives each
  path its own mission by submitting its instructions as a list.
- `minItems` and `maxItems` in value schemas.
- Calls to commands and MCP tools. A command can read its standard output
  as lines or as JSON with `parse`, giving `data.value`.
- `timeoutMs` on agent and call steps, counting machine time only, with the
  `TIMEOUT` failure; `answerTimeoutMs` on agents for requests to a person.
- A flow-level `onError`, and a failed run when a failure is not handled.
- Nested compositions with joins and parallel routes.

### Changed

- Routing after an agent always uses its choice; the choices are the keys of
  `next`.
- Approvals offer a person the choices of their `next` map and pass on the
  person's comment.
- Calls route on their outcome, `passed` or `failed`. The condition step is
  removed.
- A single validator with JSON reports, and a Mermaid renderer.

### Removed

- `bindings`, `configurations`, `claims` and configuration selection.
- The `prepare` step, `decision` declarations, `steers` and acknowledgement
  states.
- Join `after`, `members`, `mode`, the join-level `accept` (now inside
  `quorum`) and the `NO_ACCEPTABLE_RESULT` error.
- Protected approval chains.
- The 0.1 specification, experimental prototypes and earlier reader corpora
  from the tree. They remain in the tags below.

## Earlier editions

| Edition | Tag | Date |
| --- | --- | --- |
| 0.2.0 | [`v0.2.0`](https://github.com/Andrologic/AgSDL/tree/v0.2.0) | 2026-10-03 |
| 0.1.1 | [`v0.1.1`](https://github.com/Andrologic/AgSDL/tree/v0.1.1) | 2026-09-08 |
| 0.1.0 | [`v0.1.0`](https://github.com/Andrologic/AgSDL/tree/v0.1.0) | 2026-09-07 |
| 0.0.2 | [`v0.0.2`](https://github.com/Andrologic/AgSDL/tree/v0.0.2) | 2026-09-05 |
| 0.0.1 | [`v0.0.1`](https://github.com/Andrologic/AgSDL/tree/v0.0.1) | 2026-09-02 |
