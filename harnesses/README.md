# Harness modules

A harness module says how one harness supports each standard AgSDL property,
and how it enforces permissions. The format is defined in
[Harnesses](../spec/harnesses.md) and checked by the
[module schema](../schema/harness-module.schema.json). Modules are data: the
validator reads them and never runs anything.

## Modules

| Harness | Module version | Harness versions covered |
| --- | --- | --- |
| Codex | 1.0.0 | `>=0.152.0` |
| Claude Code | 1.0.0 | `>=2.1.111` |
| opencode | 1.0.0 | `>=2.0.28 <3.0.0` |
| pi | 1.0.0 | `>=1.2.0 <2.0.0` |
| Macro | 1.0.0 | `0.1.8` |

Each module lists, in `sources`, the code and documentation its claims rest
on, and explains every approximation in a `note`. Each has its own
`CHANGELOG.md`.

## Support at a glance

| Property | [Codex](codex/module.json) | [Claude Code](claude-code/module.json) | [opencode](opencode/module.json) | [pi](pi/module.json) | [Macro](macro/module.json) |
| --- | --- | --- | --- | --- | --- |
| Resources | approx. | approx. | approx. | approx. | approx. |
| Model name | native | native | native | native | native |
| Effort | native | native | native | native | approx. |
| Skills | native | native | native | native | — |
| MCP servers | native | native | native | native | — |
| Plan | native | native | — | — | — |
| Plan first, auto | approx. | native | approx. | — | — |
| Plan first, ask | — | native | — | — | — |
| Reviewer, person | native | native | native | — | — |
| Reviewer, model | native | approx. | — | — | — |
| Added directories | native | native | native | native | — |
| New instance per work | native | native | native | native | — |
| Steer | native | native | native | native | — |

"approx." means the harness does something close; the validator warns and
shows the module's note. "—" means absent: using the property is an error.

| Permission `deny` | Codex | Claude Code | opencode | pi | Macro |
| --- | --- | --- | --- | --- | --- |
| `read` | sandbox | sandbox | harness | — | — |
| `write` | sandbox | sandbox | harness | — | — |
| `shell` | harness | harness | harness | — | harness |
| `network` | sandbox | sandbox | harness | harness | harness |
| `mcp` | harness | harness | harness | harness | harness |
| `delegate` | harness | harness | harness | harness | harness |
| `read` outside the zone | sandbox | sandbox | harness | — | harness |

Permissions are enforced or they are not. A `deny` that a harness cannot
enforce makes the agent invalid; `full` requests no `deny` at all. For `read`,
`write`, `network` and reads outside the zone, `harness` holds only when the
agent cannot run shell commands. The module files give `allow` and `ask` too.

The table is a summary. The module files are the reference.

## Updating a module

1. Check the harness's code or documentation for the version you cover.
2. Change `module.json`, with a source for each claim.
3. Bump the module version: minor when documents valid before stay valid,
   major otherwise.
4. Add an entry to the module's `CHANGELOG.md`.
5. Run `./scripts/check.sh`.

A module describes what the harness does today. It never describes plans, and
AgSDL never invents a feature a harness lacks.
