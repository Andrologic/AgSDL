# 0015. The repository keeps only the current edition

Status: accepted.

## Context

Until 0.2.0, the repository kept every edition side by side: the 0.1
specification at the root of `spec/`, the 0.2 specification under `spec/0.2/`,
three frozen prototypes under `experimental/`, four reader corpora, release
reviews, delivery plans and protocol research. A newcomer could not tell what
was current.

## Decision

- The tree holds only the current edition: one specification, one schema, one
  validator, one set of examples and conformance cases.
- Earlier editions stay available, unchanged, from their Git tags.
- Harness modules are maintained in this repository, under `harnesses/`, so
  that supported harness versions and module updates follow the specification.
- Process records of a given piece of work (plans, review logs, session notes)
  are not committed. Decisions that explain the design are.

## Consequences

`docs/scope.md` was rewritten for this layout. Links to earlier material point
to tags. The changelog summarizes each edition.
