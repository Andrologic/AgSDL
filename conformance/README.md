# AgSDL 0.1.0 conformance corpus

This directory contains the official corpus and the neutral report comparator
for the seven operations defined by [AgSDL 0.1.0](../spec/README.md). The
normative specification is the only source of oracle meaning. Fixtures,
schemas, this corpus and reader output do not add semantics.

The corpus does not bundle reader outputs or comparison evidence. A successful
corpus check proves that the checked-in inputs, hashes, schema expectations,
oracle records and coverage index are internally consistent. It does not prove
that any reader implements the specification.

## Contents

- `fixtures/manifest.json` pins 137 cases and every input byte hash.
- `fixtures/candidate2/` has 111 new official inputs derived from historical
  D, inspect, exchange, lossyExchange and still-applicable G mutations.
- `fixtures/modular/` has 26 new official inputs derived from the modular cases.
- `build-corpus.py` performs the recorded mechanical derivation without invoking
  a reader. Run it with an already installed Draft 2020-12 `jsonschema` package.
- `check-corpus.py` checks provenance, hashes, normative citations, oracle
  structure and the rule matrix using the standard library. Its optional
  `--jsonschema` mode checks every recorded shape expectation.
- `compare-readers.py` validates official report structure, exact source
  locations and slices, inventory states, output artifacts, corpus assertions
  and complete normalized agreement between two or more readers.
- [Coverage](COVERAGE.md) states the rule variants and historical exclusions.

## Corpus checks

Run the checks that require no third-party package:

```sh
python3 conformance/check-corpus.py
python3 -m unittest conformance/test_check_corpus.py conformance/test_compare_readers.py -v
```

An optional project-local environment can also check the official Draft 2020-12
assertions:

```sh
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install jsonschema
python3 conformance/check-corpus.py --jsonschema
```

The package is supplementary and is not a project dependency. `scripts/check.sh`
runs the standard-library corpus check and focused test modules. Syntax-error
cases have no schema assertion because schema validation starts after parsing.
`interpreted-number-exact` also has no schema assertion: a normal host JSON
parser rounds its deliberately non-integral large number before a schema library
sees it. Its P-SHAPE oracle follows the specification's mathematical check and
stays in the report corpus.

## Reader comparison

Each reader command must consume one JSON request on standard input and emit one
JSON response on standard output. The request contains `operation`, base64
`primary`, a base64 `annexes` map and, for lossyExchange cases that declare one,
`losses`. The response is exactly `report` plus an `artifacts` map whose values
are base64 bytes. The Report marker is `agsdl-0.1.0`; a historical report is
rejected rather than converted.

Use a new empty evidence directory. Reader labels and case names accept ASCII
letters, digits, underscore and hyphen.

```sh
agsdl_reports=$(mktemp -d)
python3 conformance/compare-readers.py \
  --reader '["python","python3","tooling/readers/python/cli.py"]' \
  --reader '["javascript","node","tooling/readers/javascript/cli.mjs"]' \
  --reports "$agsdl_reports"
```

The comparator stores stdout and stderr for every reader/case plus
`summary.json`. It returns nonzero for blocked cases, invalid reports, oracle
differences, timeouts or any cross-reader mismatch. It compares Result
unit/phase/verdict, Finding tuples, Check sets and locations, State sets including
the specified R assessment details, exact Slice byte ranges and bytes, Loss
records, OutputRecord hashes and delivered artifact bytes.

The final local delivery comparison covers all 137 cases with no blocked case,
failure or mismatch. Its 274 reports also satisfy `schemas/report.schema.json`.
The comparator never chooses the correct semantic result. The manifest supplies
the normative oracle, and full cross-reader agreement can still preserve a
shared implementation mistake outside covered combinations. Keep raw reports,
the summary digest and the exact tested revision when retaining evidence.

## Derivation boundary

The builder creates distinct official files and recalculates their hashes. It
changes an interpreted historical contract marker only at the Document root.
For candidate-2 G cases it wraps the old single Interface contract in an
explicit inbound `default` Operation, assigns `invoke.operation`, and assigns
the old immediate approved target to `approval.call`. This is the explicit
mechanical mapping recorded by the adoption traceability. Modular G/R records
already have the adopted form and retain their operation ids, call ids and
runtime declarations.

When a direct annex changed, the builder updates a dependency hash only if the
historical hash exactly matched that historical annex. Intentional mismatches
and null hashes remain test mutations. Syntax-invalid and non-Document inputs
retain their intended bytes. Some therefore have the same content hash as their
historical source, but the manifest recomputes and pins that hash rather than
assuming it.

Candidate-2 validateR cases are excluded. Their Requirement/Selection grammar,
R-REQUIREMENT rule and old runtime inventory do not exist in 0.1.0. No fixture,
oracle or reader output under `experimental/` is changed or relabelled.
