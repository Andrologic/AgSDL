# Human and software participation examples

[Proposal 0018](../../../proposals/0018-human-and-software-agents.md) defines the
accepted design direction. These complete examples test whether its two scenarios
fit the existing [0017 grammar](../../../proposals/0017-agent-only-kiss-0.2.md).
They are a separate feasibility exercise, not additions to the frozen 42-case
corpus or evidence of human execution support. All provider names are fictional.

## One reviewer, two configurations

[review.json](review.json) declares one reviewer receiving and returning text.
The same Agent and graph have two configurations:

| Configuration | Intended external realization |
| --- | --- |
| automated | A software agent engine receives the prompt and text. |
| human-assisted | A software task broker displays the instructions and text to a person and collects the result. |

`selected` is initially automated. Choosing human-assisted changes only that
selection, not the Agent or graph declarations. Parameters do not invent accounts,
queues or provider APIs. Claims are empty, so both configurations are deliberately
compatibility-inconclusive. Engine names alone confer no human participation,
authentication, support or permission guarantee.

## Review, then authorization to publish

[publication.json](publication.json) declares this path:

```text
review → approve → publish → done
           denied → denied
review / approve / publish failure → failed
```

The reviewer uses the intended human-task broker; the publisher uses the software
engine. The approval gate controls the exact publication call and can present
its reviewed text and scope context before admission. Reviewing successfully
does not approve publication. The application chooses and authenticates the
person receiving the approval request. The format links the gate to the call,
not to an Agent or account. Whether reviewer and approver are the same person
is outside this declaration.

The declarations preserve denial, failure, validity and data-availability rules.
The static check does not enforce them at runtime or implement a human service.
Publication instructions are explanatory; the explicit gate supplies the control.

## Reproduce the static checks

From the repository root, with Python 3 and Node.js available:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s experimental/kiss-0.2/human-participation -v
```

The check runs both existing CLIs on each of six scenarios, validates their report
grammar through the existing comparator and compares every semantic observation
to a hand-authored expectation. It checks no network or external service. The
Python-only repository command does not run this Node.js-dependent check.

| Scenario | Exact observations beyond ordinary unit presence |
| --- | --- |
| Review, selected automated | Compatibility ENGINE inconclusive at `/configurations/automated/agents/0`. |
| Review, selected human-assisted | Compatibility ENGINE inconclusive at `/configurations/human-assisted/agents/0`. |
| Publication | Compatibility ENGINE inconclusive at `/configurations/human-review/agents/0` and `/configurations/human-review/agents/1`. |
| Publication gate failure goes to publish | Same compatibility observations plus flow APPROVAL fail at `/graphs/publication/steps/1`. PATH remains valid; no gap is expected. |
| Publication review output type becomes boolean | Same compatibility observations plus flow APPROVAL-DATA fail at `/graphs/publication/steps/1` and DATA fail at `/graphs/publication/steps/2`. No gap is expected. |
| Review human-assisted Engine gets an unfamiliar name | Same observations as the human-assisted selection; names have no special trust. |

In every case syntax, core, flow, configuration and compatibility are present;
external is absent. All unlisted diagnostics and gaps are absent. Successful
cases have structural passes and inconclusive compatibility. Failed cases retain
the listed flow failures. Report input hashes identify each exact input separately;
changing selected or provider names changes that hash.

Expectations follow 0017 sections 3–7, especially APPROVAL chain, DATA type and
ENGINE support rules. They are not inferred from a reader's output. A passing
check supports only this finite static exercise; human execution and approval
enforcement remain untested.
