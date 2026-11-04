# AgSDL

AgSDL, the Agentic Systems Definition Language, describes **agents** and the
**flows** that connect them, in JSON that people and software can read,
validate and version.

A document says what each agent is, what it may do, which harness runs it,
and how work moves between agents. A harness is the program that runs an
agent: Codex, Claude Code, opencode, pi, Macro and others. One flow can mix
harnesses.

## Status

| Edition | Status |
| --- | --- |
| **0.3.0** | Draft. Not published. Not compatible with earlier editions. |
| 0.2.0 | Last published edition, tag [`v0.2.0`](https://github.com/Andrologic/AgSDL/tree/v0.2.0). |

AgSDL is not stable. Expect breaking changes until 1.0.

## A first document

A developer on Codex writes a change; a reviewer on Claude Code sends it back
until it is ready.

```json
{
  "contract": "agsdl-0.3.0",
  "id": "write-and-review",
  "title": "Write and review",
  "agents": {
    "developer": {
      "harness": "codex",
      "instructions": "Implement the request, then run the tests.",
      "permissions": "workspace",
      "completionCheck": { "command": "npm test" }
    },
    "reviewer": {
      "harness": "claude-code",
      "instructions": "Review the change. Choose ready or revise.",
      "permissions": "read-only"
    }
  },
  "flow": {
    "entry": "develop",
    "steps": {
      "develop": { "type": "agent", "agent": "developer", "next": "review" },
      "review": {
        "type": "agent",
        "agent": "reviewer",
        "instance": "new",
        "next": { "revise": "develop", "ready": [] }
      }
    }
  }
}
```

It is [`examples/write-and-review.json`](examples/write-and-review.json).
Validate it with Python 3.9 or newer, without any package to install:

```sh
cd tooling
python3 -m agsdl ../examples/write-and-review.json
```

The validator checks the document and compares each agent with its
[harness module](harnesses/README.md). It never runs anything.

## Where to go next

| You want to | Read |
| --- | --- |
| Write a first document | [Quickstart](docs/quickstart.md) |
| Understand the language | [Specification](spec/README.md) |
| See complete documents | [Examples](examples/README.md) |
| Know what a harness supports | [Harness modules](harnesses/README.md) |
| Validate or draw a document | [Tooling](tooling/README.md) |
| Test another implementation | [Conformance cases and run scenarios](conformance/README.md) |
| Know what is still open | [Open questions](spec/open-questions.md) and [roadmap](ROADMAP.md) |
| Contribute | [Contributing](CONTRIBUTING.md) |

## Repository

| Directory | Content |
| --- | --- |
| `spec/` | The specification of the current edition. |
| `schema/` | JSON Schemas for documents and harness modules. |
| `harnesses/` | One module per supported harness. |
| `examples/` | Complete, valid documents. |
| `tooling/` | The reference validator and a Mermaid renderer. |
| `conformance/` | Test documents with their expected diagnostics, and run scenarios for hosts. |
| `docs/` | Scope, quickstart and design decisions. |

Earlier editions, their reports and their history are available from their
Git tags.

## License

See [LICENSE](LICENSE).
