# Examples

Complete AgSDL 0.3.0 documents. Each one is valid. Validate them all from
`tooling/`:

```sh
python3 -m agsdl ../examples/*.json
```

| Example | Shows | Harnesses |
| --- | --- | --- |
| [write-and-review](write-and-review.json) | A loop by choice; a fresh reviewer each time; a completion check. | Codex, Claude Code |
| [parallel-review](parallel-review.json) | Three parallel reviews, a quorum vote, a result schema, branch results sent back. | Claude Code, opencode |
| [fix-until-green](fix-until-green.json) | A command call routed on its outcome, the test output sent to the same developer. | pi |
| [ci-watcher](ci-watcher.json) | A watcher that steers a working developer; a join; an MCP permission. | Claude Code, Codex |
| [release-approval](release-approval.json) | A selected result in a message, an approval, an MCP call. | Codex |
| [reusable-review](reusable-review.json) | A composition with a join, bound to an agent. | Claude Code, opencode |
| [plan-and-build](plan-and-build.json) | An agent that instructs another; a default prompt for routes that bring none. | Claude Code, Codex |
| [assistant](assistant.json) | One fully configured agent without a flow: skills, MCP, permission rules, plan, plan first, completion check. | Claude Code |

Draw any flow with:

```sh
python3 -m agsdl.mermaid ../examples/ci-watcher.json
```

Model names such as `example/large`, skill paths and the MCP server URLs are
fictional.
