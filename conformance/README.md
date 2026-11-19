# Conformance

Cases are documents with the diagnostics a validator must report. Run
scenarios are scripted runs with what a host must do. They let another
implementation check that it reads and runs AgSDL 0.3.0 as the specification
says.

## Cases

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

## Run scenarios

Cases check what a validator reports. Run scenarios check what a host does:
each one scripts a run of a valid document and states what the specification
requires of the host in it. This repository runs no flow. Its tests check that
each scenario is well formed, that its document is valid, and that every step
it names exists. A host checks itself by replaying the scenarios.

| Path | Content |
| --- | --- |
| `runs/*.json` | One scenario per file, following the [scenario schema](../schema/run-scenario.schema.json). |

A scenario has a `document`, a path relative to this directory or the
document itself, an optional `entry` message, a `timeline` and an `expect`.

### Replaying the timeline

For replay, configure the host to use each fan-out's declared
`concurrency` without lowering it. When the document omits `concurrency`,
the replay has no fan-out limit. For example, `fanout-keep.json` checks
that both items are running and then ends item 1 first. This setup is
specific to replay. In ordinary runs, the
[fan-out rules](../spec/flow.md#fan-out) allow the host to lower the limit.
If a host cannot use the replay setup, report the affected scenario as
not run.

The host starts the run with the `entry` message, then takes the events in
order. Before each event, and after the last one, it does everything it can
without a further event: it routes outputs, starts and cancels works, decides
joins and answers expired requests. Then:

| Event | Meaning |
| --- | --- |
| `{ "work": "fix", "returns": {...} }` | The running work of `fix` ends with this output, an agent's or an approval's. |
| `{ "work": "tests", "command": { "exitCode": 1, "stdout": "...", "stderr": "..." } }` | The command of the call ended so. The host derives the call's output. |
| `{ "work": "open-issue", "tool": { "content": {...}, "isError": false } }` | The MCP tool of the call returned this result. |
| `{ "work": "fix", "fails": "AGENT_FAILED" }` | The work fails with this code. |
| `{ "work": "release", "request": "ask" }` | The work opens a request that the host puts to a person: an `ask`, a `plan` or a `question`. |
| `{ "work": "release", "answer": "yes" }` | A person answers the work's oldest open request. |
| `{ "steer": { "to": "signal", "nth": 1, "outcome": "received" } }` | Resolve the indicated steer attempt. See below. |
| `{ "elapse": 60000 }` | That many milliseconds pass, for every work running or waiting for a person. Each time limit counts them as the specification says: `timeoutMs` not while a person is asked, `answerTimeoutMs` and an approval's `timeoutMs` only then. |
| `{ "running": [{ "step": "fix", "item": 0 }] }` | A check: exactly these works are running, or waiting for a person, now. |

`work` names a step, or a composition body step by the names leading to it,
joined with `/`, such as `"review/vote"`. `item` is the index of the element
whose path runs the work, in a fan-out. An event names exactly one running
work; a host for which it names none, or several, fails the scenario.

A `steer` event names an attempt by destination step address and `nth`. Count
attempts to inject into current work across all paths to that step, in attempt
order, from 1. Messages that go straight to new work or wait in the queue
without an injection attempt do not count. This is a different count from
`expect.messages[].nth`.

Before replay, the test harness reads the timeline to find the attempts it
must leave pending. It acknowledges each listed attempt when the host sends
it and supplies evidence only at its matching event. An unlisted attempt
confirms receipt immediately, including in timelines with no `steer` event.
Each event must resolve an existing pending attempt exactly once. An extra
injection for the same message fails the scenario. The event outcomes are:

- `received` confirms receipt while the targeted work still counted, even
  if the event comes after the work's completion.
- `not-received` confirms the targeted work became unavailable before
  receipt and the attempt can no longer deliver.
- `uncertain` ends the wait for evidence without establishing receipt or
  non-receipt.

A pending steer is absent from `running`. In a message expectation, a
confirmed steer counts as a delivery when the host receives confirmation,
even if a later attempt was confirmed first, and fallback counts when the queued
message starts its own work. An uncertain attempt provides no confirmed
delivery to check.

The timeline treats stopping a work and confirming that it stopped as one
operation. Hosts can test the wait for a physical stop confirmation with
their own executor tests.

### Expectations

| Field | What the host must have done |
| --- | --- |
| `run` | Ended the run as `"succeeded"` or `"failed"`. |
| `starts` | Started exactly this many works per step. Each compose entry counts once at the compose step's address. Each body work counts at its own address, such as `review/check`. An omitted step has zero starts. A message that joins a current work with `steer` starts none. |
| `messages` | Delivered these messages. `nth` selects a message delivered to the step named by `to`, counting from 1 in delivery order across all paths to that step. This includes `steer` messages that join a current work. `item` selects a fan-out path. `prompt`, `resources`, `element`, the message's `item`, and `comments` are what the message holds. |
| `joins` | Made exactly these join decisions, in timeline order. `nth` selects a decision at the step named by `join`, counting from 1 in that order. |
| `failures` | Reported exactly these failures, in any order. |
| `cancelled` | Cancelled exactly these works for a group that decided, closed or failed, in any order. A work that runs out of its `timeoutMs` is a failure, not listed here. |
| `answers` | Answered these requests itself, after `answerTimeoutMs`. |

Fields that are absent are not checked. In `messages`, only the fields given
are compared, and in `resources` and join `branches`, only the names given.
Those values are patterns: an object matches when each key it gives matches,
so `{ "error": { "code": "TIMEOUT" } }` matches whatever the error's message;
a list matches a list of the same length whose elements match in order; any
other value matches only itself. Parallel works may start in any order, so
no scenario checks one.
