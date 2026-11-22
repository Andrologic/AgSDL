# Declared run input (prototype)

The venue flow asks for quotes for the city supplied at launch. A reviewer can
choose an offer in a different city. The final call records both cities. The
reviewer only needs to return the choice. See the [flow](../../examples/prototypes/venue-input.json)
and the [sample inputs and expected arguments](../../conformance/prototypes/venue-input.json).

## Try it

Run these commands from the repository root. The preview resolves the arguments
locally. You supply the reviewer's sample output, so neither an agent nor an
MCP server is needed.

```sh
export PYTHONPATH=tooling
doc=examples/prototypes/venue-input.json
python3 -m agsdl.input_prototype check "$doc"
python3 -m agsdl.input_prototype preview "$doc" --input '{"city":"Paris"}' --call lookup
python3 -m agsdl.input_prototype preview "$doc" --input '{"city":"Paris"}' \
  --call record --previous '{"results":{"city":"Lyon"}}'
```

| Call | Arguments the host would send |
| --- | --- |
| `lookup` | `{"city":"Paris"}` |
| `record` | `{"requestedCity":"Paris","chosenCity":"Lyon"}` |

Try replacing the launch value with `{"city":42}`. The preview reports
`launch: rejected` and `INPUT_INVALID` at `/city`. Now restore Paris and
pass `{"results":{}}` to `--previous` for `record`. The launch succeeds, but
`record` reports `OPERAND` at `/results/city` when binding `chosenCity`.
Both cases exit with status 1. The command exits with status 2 if you omit a
required `--previous` sample or supply malformed JSON on the command line.

## Launch

The experimental contract marker is `agsdl-prototype-run-input`. A standalone
document can declare an optional `flow.input` using the same value schema as an
agent result. For the venue flow, the schema requires an object with a string
property named `city`.

The host validates the supplied JSON value before starting the entry step.
If a schema is declared, omission or a schema violation rejects the launch
with `INPUT_INVALID`. No step starts and no error route runs. JSON `null` is
a supplied value and follows the usual type check. If the flow omits the
declaration, the host can still supply its ordinary entry message. Supplying a
separate typed value in that case is a launch error.

The accepted value belongs to one run. Every visit, parallel branch and
resumed activation reads the same snapshot. A host that supports resumption
must retain that snapshot with the run. Agents receive selected values through
explicit message resources.

## Read the value

| Where | Example | Reads |
| --- | --- | --- |
| MCP argument | `{"input":["city"]}` | The original city, including in an entry call |
| MCP argument | `{"path":["results","city"]}` | The preceding step's chosen city |
| Route message resource | `{"input":["city"]}` | The original city as an inline resource |

An empty input path selects the whole value. Strings select object properties
and nonnegative integer indices select array elements. Input resources default
to `application/json` and may specify a `mediaType`. Selecting a resource on a
route makes it available to the target under the name chosen by the author.

The prototype validator reports `MESSAGE_PATH` for an input read without a
declaration or a path the schema rules out. When a flow with declared input
starts at a call, that call has no preceding output. A `path` operand there
also produces `MESSAGE_PATH`. A path through an optional property can pass
validation. If the property is absent when read, the receiving step fails
with `OPERAND`.

Input reads are scoped to the top-level flow. An author can pass a resource
into a composition through its incoming message. Direct reads inside a
composition, input-driven `each`, form widgets and defaults are outside this
experiment. Project folders and portable archives keep their published formats.

## Try it in a host

Validate the document with `validate_prototype` before using the flow.
Set `snapshot = RunInput.accept(flow, supplied_value)` before scheduling work.
Use `snapshot.resolve_arguments` at MCP calls. On a route,
`bind_resources` materializes input selections and leaves ordinary resource
declarations for the host to resolve.

For a resumable run, persist the accepted `snapshot.value` alongside the
flow revision and the run state. On restart, load that same revision and
pass the saved JSON value to `RunInput.accept` again. For a flow without a
declared input, omit the value on both calls. The Python helper uses integers
and `Decimal` for JSON numbers, as returned by `agsdl.jsoninput`.

A host trial can reuse the [venue fixture](../../conformance/prototypes/venue-input.json).
Check the arguments sent to `lookup`, pause after the review, then resume and
check what `record` receives. For the rejected launch, verify that the host
scheduled zero steps. This is the host evidence sought in
[issue 23](https://github.com/Andrologic/AgSDL/issues/23).
