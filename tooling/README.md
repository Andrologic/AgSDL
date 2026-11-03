# Tooling

The reference validator and a Mermaid renderer for AgSDL 0.3.0. They need
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

The tests run every [conformance case](../conformance/README.md) and check
that every [example](../examples/README.md) is valid.

## Layout

| File | Role |
| --- | --- |
| `agsdl/jsoninput.py` | Strict JSON input. |
| `agsdl/schemacheck.py` | The subset of JSON Schema the AgSDL schemas use. |
| `agsdl/valueschema.py` | Value schemas: consistency, validation, path checks. |
| `agsdl/permissions.py` | Permission presets, rules and pattern matching. |
| `agsdl/graph.py` | Composition expansion, dominators and join analysis. |
| `agsdl/validator.py` | All checks, harness modules and the report. |
| `agsdl/mermaid.py` | The Mermaid renderer. |
