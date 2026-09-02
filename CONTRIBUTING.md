# Contributing to AgSDL

AgSDL is still defining its problem and vocabulary. Early contributions should
reduce ambiguity rather than add syntax quickly.

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
