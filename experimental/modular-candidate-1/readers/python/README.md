# Independent Python modular candidate reader

This directory implements the seven static operations from
[proposal 0013](../../../../proposals/0013-modular-mvp-contract.md) for edition
`proposal-0013-candidate-1`. It is experimental reference tooling, not an
adopted specification, runtime, readiness verdict or interoperability claim.

The implementation started from this repository's independent candidate-2
Python reader because proposal 0013 inherits its strict JSON and UTF-8 parser,
lossless number handling, D rules, report format, direct annex boundary and
exact exchange rules. The files here are a separate reader path. They emit only
the modular marker and never rewrite candidate-2 input bytes or reports.

Run the CLI from the repository root:

```sh
python3 experimental/modular-candidate-1/readers/python/cli.py < request.json
```

The request is one JSON object with `operation`, base64 `primary`, an `annexes`
object mapping dependency ids to base64 bytes, and optional `losses` for
`lossyExchange`. The response contains exactly `report` and `artifacts`.
Envelope and host failures use stderr and exit status 2. Document findings use
the report with exit status 0.

Run its tests with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s experimental/modular-candidate-1/readers/python -v
```

The tests exercise all 22 modular corpus oracles with this reader alone and add
cases for structural validation outside the selected configuration, duplicate
claims, content closure, operation selection and approval chains. That result
does not compare independent readers.

All inputs come from the caller. The reader performs no fetching, engine or
adapter execution, approval intake, authentication, evidence retrieval, state
migration or fallback selection. Compatibility findings compare declarations
by exact Edition only. Deep inputs remain subject to Python's recursion and
memory limits; a host resource failure is not an AgSDL verdict.
