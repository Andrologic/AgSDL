# Independent JavaScript 0.2.0 reader

This standard-library Node.js reader checks 0.2.0 document declarations.
Its semantic source is [spec/0.2/](../../../spec/0.2/README.md), published as `v0.2.0`. It preserves the `agsdl-0.2.0` marker and reports execution
support as `not-assessed`.

```sh
node tooling/0.2/javascript/reader.mjs tooling/0.2/examples/test-loop.json
node --test tooling/0.2/javascript/reader.test.mjs
```

The CLI consumes one file, emits one JSON report, and exits 0 for a valid checked
document, 1 for parse/shape/declaration failure, or 2 for usage/file-access failure.
`read(bytes)` is the same API. It never runs Python, fetches content or executes a
graph. It shares the schema as data and the official JavaScript lossless JSON
scanner/serializer only. Exact decimal comparison and all 0.2.0 semantic
rules are implemented locally. Integer constraints have no implicit JavaScript
safe-integer cap: mathematical integers beyond 2^53 remain exact number tokens.
Parser resource exhaustion is a rejected input, not a success observation.

The [independent corpus guide](../conformance/README.md) defines report comparison,
invalid diagnostic projections, retained evidence and implementation independence.
Supplied-record checks remain separately scoped Python tooling.
