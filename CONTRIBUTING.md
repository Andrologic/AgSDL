# Contributing to AgSDL

AgSDL has a published, bounded 0.1.0 first-draft contract and continues to
define the broader problem and vocabulary. Contributions should reduce ambiguity
and preserve the status of normative, proposed, experimental and illustrative
material.

## Repository boundary

Read `docs/scope.md` before proposing a new artifact or tool. Contributions may
address any category included in that boundary, including language artifacts,
repository maintenance material, and reference tooling. Research, proposals,
examples, and normative text keep the status defined by the repository's source
hierarchy. Submitting a contribution does not make its content normative.

Base descriptions of external systems on published interfaces and documented
behavior relevant to an AgSDL mapping or conformance requirement.

## Types of change

Editorial corrections may go directly through a pull request when they do not
alter meaning.

A proposal is required when a change:

- adds, removes, or changes a normative concept;
- changes validation or conformance behavior;
- introduces a serialization rule or extension mechanism;
- changes compatibility, security, or governance policy.

Create proposals under `proposals/` and use the next available four-digit
identifier. A proposal must state its problem, scope, consequences, alternatives,
and unresolved questions.

For immutable proposal snapshots, record adoption in a separate decision and
the [proposal register](proposals/README.md), as established by
[Decision 0007](docs/decisions/0007-adopt-0.1.0-contract.md). Preserve the pinned
proposal bytes and historical status. Apply adopted semantics separately in
`spec/`; an adoption record does not itself publish a release.

Current publication status is maintained in the
[README](README.md#release-status-and-history).

## Git workflow

The stable history lives on `main`. Integration happens on `develop`. Create
work in a separate worktree on a `feature/*` branch, then merge it into `develop`
after review.

## Verification

Run:

```sh
./scripts/check.sh
```

The check must succeed before a change is committed.

The command requires Python 3 and uses no third-party Python packages. Its
Markdown link check verifies that local inline-link and image destinations
exist. It resolves relative paths from the Markdown file, strips query and
fragment suffixes, decodes percent escapes, and skips fenced code blocks,
same-line inline code spans, external URI schemes, site-root paths, and
anchor-only links.

This is a repository check, not a CommonMark parser. It recognizes destinations
on the same line as `](`, including paths enclosed in angle brackets. It does
not check reference-style or HTML links, heading anchors, remote URLs, indented
code blocks, multiline code spans, or destinations with nested parentheses.


### Reader commands

`./scripts/check.sh` runs all three Python reader suites and the corpus checks.
Node.js is not required for that command. From the repository root, run the six
Python and JavaScript reader suites with:

```sh
./scripts/check-readers.sh
```

This separate command requires Python 3 and Node.js with `node --test` support.
It uses their standard libraries and installs no packages. To compare all three
corpora, which additionally requires Python 3.9 or newer, run:

```sh
./scripts/check-readers.sh --compare
```

The comparison mode covers candidate-2, modular candidate-1 and official 0.1.0
in separate temporary report directories. Select one with `--compare
candidate-2`, `--compare modular`, `--compare official` or `--compare 0.1.0`.
The command prints each summary, preserves a nonzero comparator exit and removes
its temporary reports on exit unless `AGSDL_REPORTS_DIR` is set. It does not run the reader test suites. Use the
[experimental guide](experimental/README.md#retain-comparison-reports) or
[official corpus guide](conformance/README.md#reader-comparison) to retain raw
reports.

Run the official focused suites directly with:

```sh
node --test tooling/readers/javascript/reader.test.mjs
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tooling/readers/python -v
```

See the [tooling guide](tooling/README.md) for request preparation and evidence
limits.

### Full local and CI verification

With Python 3.9+, Node.js with `node --test` support and `jsonschema` installed
in the active Python environment, use a new empty directory outside the checkout:

```sh
./scripts/check-full.sh /tmp/agsdl-verification
```

This runs `check.sh`, all six reader suites, all three corpus comparisons,
`conformance/check-corpus.py --jsonschema`, Draft 2020-12 validation of every
produced official report, and `scripts/check-examples.py --jsonschema` for the
56 example responses. Checks run sequentially. Independent checks continue after
failure, and the command exits nonzero if any check fails. Logs, exit statuses,
raw comparator responses, summaries, the tested SHA, dirty status and manifest
SHA-256 remain in that directory. A dirty status means the SHA alone does not
identify the tested content; retain the diff too or rerun on a clean commit.

The GitHub Actions workflow runs this same command with full Git history for
historical provenance, Python 3.12, Node.js 22 and `jsonschema` 4.23.0. Its artifact
upload runs even after a check fails. Running locally does not execute that
workflow remotely or publish a release. `./scripts/check.sh` still requires
only Python and its standard library, with Git provenance checked in checkouts.

To retain just the three comparisons, run:

```sh
AGSDL_REPORTS_DIR=/tmp/agsdl-comparisons ./scripts/check-readers.sh --compare
python3 scripts/check-report-schemas.py /tmp/agsdl-comparisons/official-0.1.0
```

The reports directory must be empty. Without `AGSDL_REPORTS_DIR`, the comparison
command continues to remove its temporary reports on exit.
