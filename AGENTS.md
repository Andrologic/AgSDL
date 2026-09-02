# AgSDL agent instructions

AgSDL is a pre-draft specification. Preserve the distinction between established
decisions, proposals, examples, and open questions.

## Read before changing the project

- Read `docs/scope.md` for the current boundary of the specification.
- Read `CONTRIBUTING.md` before changing normative behavior or terminology.
- Read the relevant file in `docs/decisions/` before revisiting a recorded
  decision.

## Sources of truth

- Normative semantics belong in `spec/`.
- Schemas enforce the normative text but do not create semantics on their own.
- Examples illustrate the specification but do not override it.
- Record a material semantic change in `proposals/` before merging it into the
  normative specification.

## Working rules

- Write normative specification text in English.
- Preserve accents in any French prose.
- Define a term once and reuse that exact term.
- Label unresolved design questions explicitly. Do not turn assumptions into
  requirements.
- Treat MCP, A2A, framework adapters, and runtimes as external systems until an
  integration is implemented and tested.
- Keep the local checkout on `develop`. Do feature work on `feature/*` branches
  in separate worktrees.
- Keep commits limited to one reviewed step.

## Completion criterion

Run `./scripts/check.sh` after changing documentation, configuration, schemas,
examples, or code. A step is complete only when the command succeeds and the
diff contains no unrelated changes.
