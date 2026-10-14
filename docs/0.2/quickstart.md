# AgSDL 0.2.0 quickstart

This page shows how to write, check and view a first `agsdl-0.2.0` document.
It is non-normative. The [0.2.0 specification](../../spec/0.2/README.md) controls.
The commands check declarations only; they never start an Agent or call a Tool.

## Requirements

Python 3.9 or newer, from the repository root. No package is installed.
Node.js is optional and only needed for the independent JavaScript reader.

## 1. Describe one Agent

Save this document as `first.json` in a working directory of your choice,
outside the checkout:

```json
{
  "contract": "agsdl-0.2.0",
  "id": "first",
  "bindings": {
    "assistant-engine": {
      "contract": { "identity": "example/agent-engine", "version": "1" },
      "implementation": { "identity": "example/local-engine", "version": "1" }
    }
  },
  "configurations": {
    "default": { "engine": "assistant-engine" }
  },
  "agents": {
    "writer": {
      "configuration": "default",
      "prompt": [{ "value": "Draft the requested text." }]
    }
  }
}
```

`bindings` names the external contract each Engine must satisfy and the
implementation you select. Identities here are fictional. `configurations`
selects that Engine explicitly; there is no default Engine. `agents` declares
one persistent Agent with an initial prompt.

## 2. Check it

```sh
python3 tooling/0.2/reader.py path/to/first.json
```

The command prints one JSON report and exits with 0. Read these fields first:

- `valid` is `true` when every static rule passed.
- `findings` lists each failed rule as a `code` and a JSON Pointer `path`.
- `executionSupport` is always `not-assessed`.
- `coreNeeds` and `unassessed` list what an integration still has to provide.

A valid report covers the declarations only. It does not show that an Engine
exists, that access is granted or that the Agent can run.

## 3. Read a finding

Change the Agent's `configuration` to `"missing"` and check again. The command
exits with 1 and the report contains:

```json
"findings":[{"code":"REFERENCE","path":"/agents/writer/configuration"}]
```

The [validation chapter](../../spec/0.2/validation.md#static-checks-and-evidence-limits)
defines every rule code. Exit code 2 means a usage or file-access failure.

## 4. Add a flow

Save this document as `write-and-review.json`:

```json
{
  "contract": "agsdl-0.2.0",
  "id": "write-and-review",
  "bindings": {
    "assistant-engine": {
      "contract": { "identity": "example/agent-engine", "version": "1" },
      "implementation": { "identity": "example/local-engine", "version": "1" }
    },
    "review-choice": {
      "contract": { "identity": "example/review-decision", "version": "1" },
      "implementation": { "identity": "example/explicit-final-choice", "version": "1" }
    }
  },
  "configurations": {
    "default": { "engine": "assistant-engine" }
  },
  "agents": {
    "writer": {
      "configuration": "default",
      "prompt": [{ "value": "Draft the requested text and address review feedback." }]
    },
    "reviewer": {
      "configuration": "default",
      "prompt": [{ "value": "Review the draft. Choose accepted or changes_needed when finished." }]
    }
  },
  "flow": {
    "entry": "write",
    "steps": {
      "write": { "type": "agent", "agent": "writer", "next": ["review"] },
      "review": {
        "type": "agent",
        "agent": "reviewer",
        "decision": { "binding": "review-choice", "choices": ["accepted", "changes_needed"] },
        "next": { "accepted": [], "changes_needed": ["write"] }
      }
    }
  }
}
```

The writer works first; its visible output goes to the reviewer. The reviewer's
final decision selects a route. `changes_needed` returns to the same persistent
writer. `accepted` lists no destination, so no further step is activated.
The `review-choice` binding names the contract that reports the decision.

Check it as before, then view its declared connections:

```sh
python3 tooling/0.2/render_mermaid.py path/to/write-and-review.json
```

The output is a [Mermaid](https://mermaid.js.org/) flowchart of the top-level
flow. Paste it into any Mermaid viewer. The view is static: it does not expand
compositions or evaluate conditions.

## 5. Compare both readers

```sh
node tooling/0.2/javascript/reader.mjs path/to/write-and-review.json
```

The independent JavaScript reader prints an equivalent report for the same input
within the [corpus limits](../../tooling/0.2/conformance/README.md#limits).

## Next steps

- Read the [worked scenarios](worked-scenarios.md) and the
  [maintained examples](../../tooling/0.2/README.md#read-or-check-an-example).
- Read the [flow chapter](../../spec/0.2/flow.md) before using Joins,
  steering, compositions or approval gates.
- Use the [supplied-record commands](../../tooling/0.2/README.md#supplied-record-commands)
  to check recorded outputs, deliveries and admissions.
