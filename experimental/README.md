# Experimental candidates

The adopted 0.2.0 tools are in [tooling/0.2/](../tooling/0.2/README.md). Earlier editions
remain available for reproducing their evidence and tracing the adopted 0.1.0
contract. Each marker has its own meaning and corpus.

| Candidate | Marker | Role and guide |
| --- | --- | --- |
| Agent-only KISS | `agsdl-exp-0017-c1` | [Frozen prototype](kiss-0.2/README.md) with a [42-case assessment](kiss-0.2/ASSESSMENT.md); predates the persistent-Agent model. |
| Modular candidate-1 | `proposal-0013-candidate-1` | [Historical corpus and readers](modular-candidate-1/README.md), 26 cases. Source for part of the adopted 0.1.0 contract. |
| Candidate-2 | `proposal-0012-candidate-2` | [Historical corpus and readers](candidate-2/README.md), 121 cases. Source for inherited 0.1.0 rules. |

The official 0.1 specification lives in [spec/](../spec/README.md); the adopted
0.2.0 specification is in [spec/0.2/](../spec/0.2/README.md). Experimental
agreement does not adopt an edition or establish execution support. See the
[release status](../README.md#release-status-and-history) for published versions.

## Reader checks

Use the [shared commands](../CONTRIBUTING.md#reader-commands) for candidate-2,
modular, official and persistent-Agent flow readers. The frozen KISS candidate
keeps its separate checks documented in its guide above.

## Retain comparison reports

The [full verification procedure](../CONTRIBUTING.md#full-local-and-ci-verification)
retains comparison output and logs. For a single experiment, use its own
[candidate-2](candidate-2/README.md#comparing-reader-commands),
[modular](modular-candidate-1/README.md#compare-the-readers),
[flow declaration](../tooling/0.2/conformance/README.md) or
[KISS](kiss-0.2/corpus/README.md) comparison command with a new evidence directory.
The 0.2.0 edition has independent Python and JavaScript declaration readers.
Its optional schema-library comparison remains a shape check only; declaration
agreement establishes no supplied-record or execution support.
