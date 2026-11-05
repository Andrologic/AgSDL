# AgSDL agent instructions

AgSDL 0.3.0 is the current edition, published from tag `v0.3.0`, with
contract marker `agsdl-0.3.0`. Earlier editions remain in their tags.
Do not describe AgSDL as stable.

## Read before changing the project

- `docs/scope.md`: what belongs in this repository.
- `spec/README.md` and the chapter you touch. The specification is the source
  of truth; the schema, validator, examples and modules follow it.
- `docs/decisions/` before revisiting a recorded decision.
- `spec/open-questions.md` before proposing anything listed there.
- `CONTRIBUTING.md` for the kinds of change and the writing rules.

## Rules

- Keep the specification, `schema/agsdl.schema.json`, `tooling/agsdl/`,
  `conformance/` and `examples/` consistent in the same change.
- Harness modules describe what a harness does today, with sources. Never
  invent a harness feature, and never mark support native without evidence.
- The flow links missions; planning, executing and checking a mission happen
  inside one agent. Do not model phases of one mission as steps.
- Write repository documentation in English. Do not commit plans, logs or
  session notes.
- Keep the local checkout on `develop`; work on `feature/*` branches in
  separate worktrees. Keep each commit to one reviewed step.

## Completion criterion

Run `./scripts/check.sh` after any change. A step is complete only when it
passes and the diff contains no unrelated changes.
