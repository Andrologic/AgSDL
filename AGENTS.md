# AgSDL agent instructions

AgSDL is a pre-draft specification. Preserve the distinction between established
decisions, proposals, examples, and open questions.

## Read before changing the project

- Read `docs/scope.md` before proposing repository contents or behavior. It is
  the source of truth for the repository boundary.
- Read `CONTRIBUTING.md` before changing normative behavior or terminology.
- Read the relevant file in `docs/decisions/` before revisiting a recorded
  decision.

## Repository boundary

- Keep changes within the repository boundary defined in `docs/scope.md`.
  Preserve the recorded status of decisions, proposals, and normative text.
- Describe external systems only as needed for AgSDL mappings and conformance,
  using published interfaces and documented behavior.
- Ask the maintainer before starting work that crosses the repository boundary.

## Sources of truth

- Normative semantics belong in `spec/`.
- Schemas enforce the normative text but do not create semantics on their own.
- Examples illustrate the specification but do not override it.
- Record a material semantic change in `proposals/` before merging it into the
  normative specification.

## Working rules

- Write normative specification text in English.
- Define a term once and reuse that exact term.
- Label unresolved design questions explicitly. Do not turn assumptions into
  requirements.
- Treat MCP and A2A services, target framework systems, and runtime
  implementations as external systems. A documented binding does not prove
  implementation support.
- Keep the local checkout on `develop`. Do feature work on `feature/*` branches
  in separate worktrees.
- Keep commits limited to one reviewed step.

## Completion criterion

Run `./scripts/check.sh` after changing documentation, configuration, schemas,
examples, or code. A step is complete only when the command succeeds and the
diff contains no unrelated changes.
