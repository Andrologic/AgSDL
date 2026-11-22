# Tooling

The reference validator and a Mermaid renderer for AgSDL 0.4.0. They need
Python 3.9 or newer and its standard library only. They read documents; they
never run agents, calls or flows.

Run the commands from this directory, or add it to `PYTHONPATH`.

## Validate

```sh
python3 -m agsdl ../examples/write-and-review.json
```

```text
../examples/write-and-review.json: valid (0 errors, 0 warnings)
```

| Option | Effect |
| --- | --- |
| `--json` | Print the [JSON report](../spec/validation.md#report). |
| `--modules DIR` | Use the harness modules in `DIR` instead of [`../harnesses`](../harnesses/README.md). |

Exit status: `0` when every document is valid, `1` when one is invalid, `2`
when a file or a module cannot be read.

The checks and diagnostic codes are listed in
[Validation](../spec/validation.md). Join reports give the origin and branches
the validator deduced for each join.

## Project folders

Pass the project directory or its `agsdl.json` to either command.

```sh
python3 -m agsdl ../examples/review-project
python3 -m agsdl.mermaid ../examples/review-project
```

In Python, `load_project(path)` returns the assembled `document`, its base
directory `root`, the MCP `secrets` requirements and the local `mcp_files`
by server ID. Use `validate_path(path, modules)` for a validation report
with source locations. See [project folders](../spec/project.md).

## Draw

```sh
python3 -m agsdl.mermaid ../examples/parallel-review.json
python3 -m agsdl.mermaid ../examples/reusable-review.json --composition triple-review
```

The output is a Mermaid flowchart of the authored steps and routes. Joins are
drawn as stadiums, compositions as subroutine boxes, error routes as dotted
lines, and choices and outcomes as edge labels. The flow's `onError` is a
dotted line from the start. A choice or outcome with an empty route leads to
an end node.

## Use from Python

```python
from agsdl import load_modules, validate_bytes

report = validate_bytes(open("document.json", "rb").read(), load_modules())
print(report.valid, report.as_json()["diagnostics"])
```

## Tests

```sh
python3 -m unittest discover -s tests
```

The tests run every [conformance case](../conformance/README.md), check that
every run scenario is well formed and names existing steps, and check that
every [example](../examples/README.md) is valid.

## Layout

| File | Role |
| --- | --- |
| `agsdl/jsoninput.py` | Strict JSON input. |
| `agsdl/schemacheck.py` | The subset of JSON Schema the AgSDL schemas use. |
| `agsdl/valueschema.py` | Value schemas: consistency, validation, path checks. |
| `agsdl/permissions.py` | Permission presets, rules and pattern matching. |
| `agsdl/graph.py` | Composition expansion, scope graphs, dominators and join analysis. |
| `agsdl/validator.py` | All checks, harness modules and the report. |
| `agsdl/mermaid.py` | The Mermaid renderer. |

## Portable archives

The archive commands run from `tooling/`. Create a snapshot, inspect its
inventory and declared MCP prerequisites, then restore it to a new folder:

```sh
python3 -m agsdl.archive pack ../examples/review-project review.agsdl
python3 -m agsdl.archive inspect review.agsdl
python3 -m agsdl review.agsdl
python3 -m agsdl.mermaid review.agsdl
python3 -m agsdl.archive unpack review.agsdl restored
python3 -m agsdl restored
```

To keep versions, use a dedicated bundle outside the project, or use the
reserved filename `.agsdl-history.bundle` at its root. The first command creates it.
Run `version` again after editing the project to append a commit. Each call
prints the commit ID. The export checks the snapshot against the recorded tip.

```sh
python3 -m agsdl.archive version restored versions.bundle -m "First review"
python3 -m agsdl.archive pack restored shared.agsdl --history versions.bundle
python3 -m agsdl.archive unpack shared.agsdl received --with-history
git clone -b versions received/.agsdl-history.bundle editable
git -C editable log --oneline
```

To work from an older version, check out that commit in `editable`, edit the
files, then run the following command with its full commit ID. This creates
`alternative.bundle` alongside the original history.

```sh
python3 -m agsdl.archive version editable versions.bundle -m "Alternative review" \
  --parent FULL_COMMIT_ID --fork alternative.bundle
```

Snapshot commands require only Python. Recording, including or restoring Git
history also requires Git. The default `unpack` restores the current project
even when Git is unavailable. The [archive format](../spec/archive.md) defines
the portable files and the checks performed during import.

The inspect report includes a content fingerprint. It hashes the UTF-8 JSON
encoding of the files inventory with sorted keys, integer sizes, literal
Unicode, and no formatting whitespace. The fingerprint stays the same when an
author adds history to an otherwise identical snapshot.
