# Contributing to AgSDL

AgSDL is still defining its problem and vocabulary. Early contributions should
reduce ambiguity rather than add syntax quickly.

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
