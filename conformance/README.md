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

- `fixtures/manifest.json` pins 148 cases: 137 historical derivations and 11
  native official cases, with every input byte hash.
- `fixtures/candidate2/` has 111 new official inputs derived from historical
  D, inspect, exchange, lossyExchange and still-applicable G mutations.
- `fixtures/modular/` has 26 new official inputs derived from the modular cases.
- `build-corpus.py` performs the recorded mechanical derivation without invoking
  a reader. It uses the Python standard library.
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

The initial 0.1.0 local delivery comparison covered all 137 historical-derived
cases with no blocked case,
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

## Native official cases and regeneration

Add a case to a new `fixtures/official/<topic>.cases.json` file containing a JSON
array of case records. Store its primary and annex bytes under
`fixtures/official/`. Use a unique `official-` case name and
`"derivation":{"family":"official","method":"normative-oracle"}`.
There is no `historicalCase` for a native case. Paths remain relative to
`fixtures/`; record their SHA-256 hashes explicitly.

Write `expected`, `source`, `schemaAssertions` and `coverage` from the normative
text before running readers. `source` names existing specification sections;
coverage associations need corresponding oracle evidence. The minimal case in
`fixtures/official/minimal.cases.json` illustrates this format: a System may
have no Agent, so Agent minima have no subjects and D passes. It does not test
partial diagnostics or Unicode ordering.

Run `PYTHONDONTWRITEBYTECODE=1 python3 conformance/build-corpus.py`, then
`./scripts/check.sh`. The builder derives the original 111 candidate-2 and 26
modular cases, appends the native case files in filename order, rebuilds coverage
and checks the resulting manifest. It copies native records unchanged and never
rewrites native input bytes or derives an oracle from reader output. Invalid
native hashes fail generation; they are not repaired automatically. Keep each
new group in its own case file to allow independent additions.

## Distribution integrity and historical Git evidence

`check-corpus.py` checks distributed files without Git: complete current spec
and schema hash inventories, fixture hashes, provenance structure, native case
records, normative citations, oracle structure and coverage. Regeneration updates
`normativeSources` and `schemas` to current file hashes, so reviewed changes can
be verified before committing. Inspect these hash changes with the source diff.
Hashes establish internal integrity, not authenticity against an outside trust
anchor.

`normativeBase` and `historicalNormativeSources` retain the initial normative
revision and its original hashes. Regeneration preserves them even when current
files change. Run `python3 conformance/check-corpus.py --git-provenance` to also
verify those historical bytes with Git. An unavailable revision, including in a
shallow clone, fails this explicitly requested check; fetch the history separately
or run the distribution check without this option.

`./scripts/check.sh` requests Git provenance when run in a Git checkout. In an
archive, it explicitly reports the omitted Git checks and still runs distribution
integrity and structural checks and regression suites. The modular historical
checker is unchanged: `check-historical-distribution.py` supplies its three
historical source reads from distributed files through a module-local adapter.
Every original hash assertion still runs, but these reads provide no evidence
about a Git revision. The adapter rejects unrecognized reads. The repository
check exports `PYTHONDONTWRITEBYTECODE=1` for all Python commands.

The official comparator and builder use the local `report_support.py` helpers.
These were extracted unchanged from candidate-2; the current comparator does
not load an experimental comparator. Comparison rules, including existing sort
behavior, are unchanged.

## Current maintenance verification

The 0.1.1 candidate adds ten representative diagnostic cases to the existing
native empty-System case. [Coverage](COVERAGE.md#native-maintenance-coverage)
explains their normative basis. Historical cases and their identities remain
unchanged. Current results and blockers belong to the [0.1.1 release
notes](../docs/releases/0.1.1.md), separate from the historical 0.1.0 results above.

The [full verification command](../CONTRIBUTING.md#full-local-and-ci-verification)
retains all three comparisons and checks all official report files against
Draft 2020-12. `scripts/check-report-schemas.py` requires a complete unblocked
summary and the exact expected response file set, so missing reports cannot
silently reduce the schema-check sample. It also checks reports from a completed
comparison with semantic differences; the comparator separately keeps those
differences fatal to the full check.
