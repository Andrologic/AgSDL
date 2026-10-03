# Persistent-Agent flow candidate tools and examples

Status: **bounded experimental candidate `agsdl-exp-flow-0.2-c1`, pending
maintainer adoption and unreleased.** The canonical candidate requirements are
in [spec/0.2/](../../spec/0.2/README.md). This directory supplies derived shapes,
examples and non-normative static tooling. The [remaining release scope](../../spec/0.2/README.md#remaining-release-scope)
separates candidate requirements from review, adoption and implementation evidence.

## Contract and check references

- [Content and configuration](../../spec/0.2/content.md), including Interfaces,
  URI origins and exact support declarations.
- [Flow and lifecycle](../../spec/0.2/flow.md), including graphless delivery,
  composition and protected admission.
- [Static validation and supplied-record checks](../../spec/0.2/validation.md).
- [Derived schema](schema.json). Its shapes enforce the candidate contract;
  they do not establish execution support.

## Read or check an example

| Example | What it exercises |
| --- | --- |
| [Reusable checker](examples/reusable-checker.json) | One local review/check composition, reused with the same Agent and a different Agent. |
| [Protected publication](examples/protected-publication.json) | A scoped Call behind two ordered approvals, with a fresh-attempt denial loop. |
| [Structured report](examples/structured-report.json) | Structured results, catalog URI origins and exact support claims. |
| [Conversation](examples/conversation.json) | One Agent, a reusable configuration and an explicit Engine binding; no initial prompt or graph. |
| [Test loop](examples/test-loop.json) | A persistent developer, custom test Call, deterministic Condition and prepared correction Message. |
| [Parallel reviews](examples/parallel-reviews.json) | Two final decisions grouped for the same developer completion, followed by one correction Message. |
| [Output correction](examples/output-correction.json) | A missing required report produces a diagnostic and a correction Message for the same Agent. |
| [First satisfactory review](examples/first-review.json) | Explicit acceptance rule, with stop-and-wait as the default for remaining work. |
| [Steering](examples/steering.json) | Explicit owner, consumed steering occurrence and a separate error path. Parallel launch does not guarantee the owner is still active; a late delivery is an expected possible failure. |
| [Selected media](examples/selected-media.json) | Preserve a named image Source through Prepare and an identity Condition. |
| [Multimedia and reuse](examples/multimedia-and-reuse.json) | Reusable skill instructions, two Engine choices, multiple media and required versus optional outputs. |

All Engine, Tool, implementation and contract identities are fictional. Their
settings describe example requirements, not installed software or granted
permissions. The fictional Engine contract interprets `workspace` and `access`
in configuration settings; they are not universal Engine-setting names. The examples do not run tests, read resources or start Agents.

From the repository root, using Python 3 and its standard library:

```sh
python3 experimental/agent-flow-0.2/reader.py experimental/agent-flow-0.2/examples/test-loop.json
python3 experimental/agent-flow-0.2/test_reader.py -v
```

Exit codes are 0 for a valid checked document, 1 for an invalid document or
unsupported parse input, and 2 for command usage or file-access failure.
Reports identify their scope and always say `executionSupport: not-assessed`.
With `jsonschema` installed, check the schema and compare shape validation
against a separate implementation:

```sh
python3 experimental/agent-flow-0.2/test_reader.py --schema
```

That optional schema-library comparison covers shapes only. For independent
declaration semantics, run:

```sh
node experimental/agent-flow-0.2/javascript/reader.mjs experimental/agent-flow-0.2/examples/test-loop.json
./scripts/check-readers.sh --compare flow
```

The [corpus guide](conformance/README.md) specifies the oracles, report conventions,
retained evidence and limits. Neither comparison validates runtime behavior.

## Supplied-record commands

The [completion check contract](../../spec/0.2/validation.md#checking-recorded-outputs)
defines the accepted completion record and report scope:

```sh
python3 experimental/agent-flow-0.2/check_completion.py DOCUMENT.json STEP RESULT.json
```

The [delivery check contract](../../spec/0.2/validation.md#checking-recorded-delivery)
defines the claimed input, origin, Message and configuration record:

```sh
python3 experimental/agent-flow-0.2/check_delivery.py DOCUMENT.json AGENT RECORD.json
```

The [admission check contract](../../spec/0.2/validation.md#checking-recorded-admission)
defines the supplied approval consistency record:

```sh
python3 experimental/agent-flow-0.2/check_admission.py DOCUMENT STEP RECORD
```

The [preparation helpers](../../spec/0.2/validation.md#checking-prepared-content)
check supplied content data. These tools do not execute a graph, deliver Messages
or authorize actions.

## Evidence limits

The named cases in [test_reader.py](test_reader.py) exercise the stated static
and record checks. The independent Python/JavaScript [declaration comparison](conformance/README.md)
covers 107 contract-authored cases, with retained complete reports. Supplied-record
checks remain separately scoped Python tooling. The optional
schema-library comparison covers shapes only. Consult the
[validation chapter](../../spec/0.2/validation.md) for each check's limits; no
check establishes Agent continuity, actual delivery, effects or enforcement.
