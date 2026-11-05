# Contributing to AgSDL

Thank you for helping. AgSDL is a young, unstable language: changes to its
meaning are welcome, but they must stay consistent across the specification,
the schema, the validator and the tests.

## Before you start

- Read the [scope](docs/scope.md). It says what belongs in this repository.
- Read the relevant chapter of the [specification](spec/README.md) and, when
  you revisit a past choice, the [decision](docs/decisions/README.md) behind
  it.
- For anything beyond a fix, open an issue first to discuss the problem.

## Kinds of change

| Change | What to do |
| --- | --- |
| Typo, wording, broken link | Open a pull request. |
| Validator bug | Add a conformance case or a test that fails, then fix it. |
| Harness module update | Change `harnesses/<name>/module.json`, cite your sources in `sources`, bump the module version and update its changelog. |
| New harness module | Add `harnesses/<name>/` with `module.json` and `CHANGELOG.md`, and list it in [harnesses/README.md](harnesses/README.md). |
| Change of meaning | Discuss it in an issue, then update together the specification, the schema, the validator, the conformance cases and the examples. Record the reasons in a new decision when the change is significant. |

A harness module describes what the harness does today, as documented or
visible in its code. It never describes plans, and never invents features.

## Writing rules

- Write in English, in short sentences.
- Define a term once, then use exactly that term.
- Keep requirements in `spec/`. Examples and decisions illustrate and explain;
  they do not add rules.
- Label unsettled design questions in [open questions](spec/open-questions.md).
- Do not commit plans, logs or notes about one piece of work.

## Checks

Run, from the repository root:

```sh
./scripts/check.sh
```

It needs Python 3.9 or newer and nothing else. It checks whitespace and local
Markdown links, runs the validator tests and conformance cases, checks the run
scenarios, and validates the examples. A change is complete when it passes and
the diff contains nothing unrelated.

## Git workflow

Stable history lives on `main`; integration happens on `develop`. Work on a
`feature/*` branch and open a pull request to `develop`.
