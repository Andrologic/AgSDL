# Conformance cases

Documents with the diagnostics a validator must report. They let another
implementation check that it reads AgSDL 0.3.0 as the specification says.

| Path | Content |
| --- | --- |
| `cases/*.json` | One document per case. Some are deliberately not valid JSON. |
| `expected.json` | For each case: a description, and the sorted, distinct error and warning codes. |
| `modules/` | Two fictional harness modules, `example` and `limited`, used by the cases. |

A case passes when a validator, using the modules in `modules/` only, reports
exactly the expected set of error codes and the expected set of warning
codes. A document is valid when it has no error. Paths and messages are not
compared: implementations may word and locate diagnostics differently.

The reference validator runs every case in its tests:

```sh
cd ../tooling
python3 -m unittest discover -s tests
```

To see one case's diagnostics:

```sh
python3 -m agsdl --modules ../conformance/modules ../conformance/cases/join-open-fork.json
```

When you add a case, give it a name that says what it tests, add its
expectation, and keep it as small as the rule allows.
