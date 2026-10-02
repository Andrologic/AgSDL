# Proposal 0022: concrete flow notation for the 0.2 walkthroughs

Status: **proposed notation, not an adopted grammar, candidate edition or
implementation.** This proposal translates the [worked scenarios](../docs/0.2/worked-scenarios.md)
into JSON sketches. It exercises [0019](0019-agent-prompt-and-resources.md),
[0020](0020-blueprint-flow-0.2.md) and [0021](0021-logic-block-contract-0.2.md).
It does not change the normative specification or the frozen 0017 candidate.

## Problem and scope

The semantic walkthroughs need concrete names and connections before a schema
can be useful. The notation should keep a conversation small, make ordinary
flow readable and allow explicit preparation where data needs reshaping.

The proposed split is an `agents` map and an optional `flow`. An Agent entry
describes one persistent participant's initialization. A flow step refers to it;
revisiting that step sends more work to the same instance. Step names and Agent
names occupy separate maps. No context-reset or hot-reconfiguration syntax is
introduced.

These are complete sketches of each example's Agent/flow portion, not complete
deployable system documents. They deliberately omit an edition marker and the
configuration catalog. Configuration, Call and decision bindings named below
are external requirements of the sketches, not magically available defaults.
Their declarations, validation and capability checks still need a candidate
contract. Missing bindings prevent an execution-support claim.

## Small notation shared by the examples

| Field or form | Proposed meaning |
| --- | --- |
| Agent `configuration` | Explicit reference to a reusable configuration selected before initialization. It supplies Engine, applicable Model, Tools and access. This sketch shows one fixed selection, not configuration alternatives. |
| Agent `prompt` | Optional ordered instruction sources. Omission supplies no initial task. |
| Message `prompt` and `resources` | Ordered instruction sources and supporting information sources. They reuse the same source shape. Resource order does not imply execution order. |
| Source `value` or `uri` | Exactly one inline JSON value or resource URI. An optional `mediaType` describes the representation. Strings in `value` are literal. |
| `flow.entry` | Step receiving an input supplied by the consumer. This proposal supplies no new event transport or autonomous trigger. |
| Step `type` | `agent`, `call`, `condition`, `prepare` or `join`. These are the proposed families from 0021. |
| Step `next` | Destination step names for ordinary completion, or a map from a declared choice to destination lists. All destinations in a selected list activate. |
| Omitted `next` | The current path ends after completion. It does not destroy any Agent or terminate unrelated work. |
| Binding `from` and `path` | Select a value from the associated completed step result. `path` is an array of exact object keys or array indices, not executable code or interpolation. |
| `input` in a binding | The current step input. Other names refer to flow steps; `input` is therefore reserved as a step name in this proposed notation. |

Bindings appear only in fields that explicitly accept a binding, such as a
Condition operand or a Prepare resource selection. A `from` key inside literal
resource data is not evaluated. A missing selected value is an error, with no
fallback to an earlier result. The candidate must define reference scope and
diagnostics before these sketches can become validated artifacts.

For these sketches, an Agent result has `text`, the visible text for the current
completed work, and, when requested, `choice`, its identified final decision.
`text` includes visible progress and final replies in response order, excluding
reasoning and raw Tool exchanges. Its exact assembly remains unresolved.
A Call has the result declared by its contract, such as `exitCode` and `report`.
A Join result retains named members and their complete results.

**Proposed default delivery:** a direct Agent-to-Agent connection supplies the
source's current visible text as information in a Message. The destination's
initial instructions still apply. Prepare adds an authored instruction when
needed. This role assignment is a recommendation for the new grammar, not an
already accepted serialization rule. A consumer cannot silently promote the
source's reply into higher-authority instructions.

Call inputs remain contract-specific. A connection can activate a Call whose
arguments come from its explicit configuration; it need not consume an Agent's
prose. Condition selects a continuation rather than implicitly transforming
the underlying data. Prepare binds the original result when it needs that data.

## 1. A conversation without a graph

```json
{
  "agents": {
    "helper": {"configuration": "project-reader"}
  }
}
```

The required `project-reader` configuration supplies an explicit Engine and
read-only project access through its Tools. It is not a built-in configuration.
The consumer initializes `helper` without an initial prompt, then addresses it
with this Message. Message addressing is outside this content object.

```json
{
  "prompt": [{"value": "Explain why parseDate fails on empty input. Read the supplied source."}],
  "resources": [
    {"uri": "file:///workspace/project/src/parse-date.js", "mediaType": "text/javascript"},
    {"value": "parseDate('') throws an unexpected parser error.", "mediaType": "text/plain"}
  ]
}
```

The file URI is an illustrative configured location, not a repository file or
a portable default path. It requires access on the consuming system. A later
Message, `{"prompt":[{"value":"Suggest a minimal fix without editing files."}]}`,
addresses the same Agent. Nothing here creates a new instance per Message.
Using an absolute URI avoids deciding relative-resource resolution in this step.

## 2. A deterministic test loop

```json
{
  "agents": {
    "developer": {
      "configuration": "project-editor",
      "prompt": [{"value": "Make minimal code changes and explain them. Use test reports as evidence."}]
    }
  },
  "flow": {
    "entry": "develop",
    "steps": {
      "develop": {
        "type": "agent", "agent": "developer",
        "next": ["tests"]
      },
      "tests": {
        "type": "call", "binding": "project-tests",
        "next": ["passed"]
      },
      "passed": {
        "type": "condition",
        "test": {"equals": [{"from": "tests", "path": ["exitCode"]}, {"value": 0}]},
        "next": {"true": [], "false": ["correction"]}
      },
      "correction": {
        "type": "prepare",
        "message": {
          "prompt": [{"value": "Fix the reported failures and explain your changes."}],
          "resources": [{"select": {"from": "tests", "path": ["report"]}, "mediaType": "text/plain"}]
        },
        "next": ["develop"]
      }
    }
  }
}
```

The consumer starts `develop` with a Message asking to fix empty input. The
required `project-editor` configuration grants the intended editing access.
The required `project-tests` binding selects a Call contract, implementation,
workspace and suite. Its normal result is an integer `exitCode` and text `report`.
Under this example's contract, zero passes and nonzero requires correction;
failure to start the process is a technical error rather than a normal result.

The Condition compares values of the required types, without coercing a string
such as `"0"` into an integer. Missing or wrongly typed input is an error rather
than the `false` branch. `true` and `false` are proposed Condition routing names,
not Agent verdict names. An empty destination list ends this path.

Prepare's `select` retrieves the current report as a source's inline value; it
does not fetch or summarize it. The selected value must satisfy the declared
representation. Prepare produces the Message shown and sends it to developer.
These examples omit recovery; a technical error stops the affected path with a
diagnostic. They introduce no automatic retry, rollback or implicit loop limit.

### Which test result does the reference mean?

`from: tests` means the completed test Call that led to this visit to
`correction`. It never means the latest global result of a step named `tests`.
The second visit to `correction` selects the second causally associated report.
If no unique associated result exists, resolution fails instead of guessing.

This is the proposed reference rule to review before implementation. Its
benefit is that authors need no runtime identifiers in the blueprint. Consumers
still need work association internally. The full rules for nested loops,
overlapping graph invocations and parallel reconvergence remain to be specified;
these sketches neither prove them solved nor impose a distributed transport.

## 3. Parallel reviews with one grouped result

```json
{
  "agents": {
    "developer": {
      "configuration": "project-editor",
      "prompt": [{"value": "Implement the requested change. Address review feedback and explain corrections."}]
    },
    "code-reviewer": {
      "configuration": "project-reviewer",
      "prompt": [{"value": "Review the current code. Explain findings and choose accepted or changes_needed only when finished."}]
    },
    "test-reviewer": {
      "configuration": "project-reviewer",
      "prompt": [{"value": "Review current test coverage. Explain findings and choose accepted or changes_needed only when finished."}]
    }
  },
  "flow": {
    "entry": "develop",
    "steps": {
      "develop": {"type": "agent", "agent": "developer", "next": ["code", "coverage"]},
      "code": {
        "type": "agent", "agent": "code-reviewer",
        "decision": {"binding": "review-choice", "choices": ["accepted", "changes_needed"]},
        "next": {"accepted": ["reviews"], "changes_needed": ["reviews"]}
      },
      "coverage": {
        "type": "agent", "agent": "test-reviewer",
        "decision": {"binding": "review-choice", "choices": ["accepted", "changes_needed"]},
        "next": {"accepted": ["reviews"], "changes_needed": ["reviews"]}
      },
      "reviews": {
        "type": "join",
        "group": {"after": "develop", "members": ["code", "coverage"]},
        "next": ["accepted"]
      },
      "accepted": {
        "type": "condition",
        "test": {"all": [
          {"equals": [{"from": "input", "path": ["code", "choice"]}, {"value": "accepted"}]},
          {"equals": [{"from": "input", "path": ["coverage", "choice"]}, {"value": "accepted"}]}
        ]},
        "next": {"true": [], "false": ["correction"]}
      },
      "correction": {
        "type": "prepare",
        "message": {
          "prompt": [{"value": "Address the requested changes in both reviews and explain your corrections."}],
          "resources": [
            {"name": "code-review", "select": {"from": "reviews", "path": ["code", "text"]}},
            {"name": "test-review", "select": {"from": "reviews", "path": ["coverage", "text"]}}
          ]
        },
        "next": ["develop"]
      }
    }
  }
}
```

`project-reviewer` is one reusable configuration used to initialize two distinct
Agents. Sharing it does not merge their contexts. The required `review-choice`
binding identifies the final decision for the current completed work and
requires a visible review report. It maps to the declared choices without
guessing from arbitrary prose. Its actual mechanism can differ by integration;
the string in the sketch is not an implementation or evidence of support.

Join defaults to all-required. `group.after` associates each group with the
developer completion that started these reviews. `members` names the two
expected steps, independently of their mutually exclusive choices. This form
is proposed for the illustrated fork-and-join pattern; a general membership
grammar is still open. A required member that fails cannot be silently dropped.

The Join supplies `code` and `coverage` results to Condition. Prepare explicitly
selects their texts as separate named information sources. A decision written
in visible text stays there; a Tool-only decision is not injected into it.
The same Agents participate in later rounds. Old or duplicate results cannot
fill a new group or reopen a completed one.

As in the walkthrough, no other writer changes the reviewed workspace while
reviews run. That is an example assumption, not a lock supplied by `group.after`.
Stopping a failed path does not prove an active sibling has stopped.

## Custom behavior and reuse

The `project-tests` binding can select a custom implementation of the fictional
`example/test-suite` version `1` contract from the walkthrough. Call's graph
shape remains unchanged. The binding must expose contract identity and version,
arguments, implementation selection, effects and support requirements. It cannot
hide an alternative scheduling rule or bypass a required approval.

The Call and Condition can later be wrapped in the proposed local composition
from 0021. This proposal keeps them expanded to inspect data references first.
Composition declarations and parameter binding are not specified here. There
is no arbitrary plugin code, package download or interpreter in these sketches.

## Alternatives and consequences

One generic object for every concept would make a simple Agent declare unused
flow machinery. Inline Agent configurations on every step would obscure which
visits share an instance. Maps plus references keep those concerns separate.

Embedding expressions in strings would require another parser and escaping
rules. Structured operands make data references distinct from literal content.
Only equality and Boolean conjunction are exercised here; a general expression
language is not needed to describe these examples.

Explicit Prepare steps add visible nodes only when content changes. The simple
handoff uses default delivery. A future editor may collapse a local composition,
but the language does not prescribe a graphical editor contract.

## Security and compatibility

Resource content retains its information role even when it contains instructions.
URI references and configuration declarations grant no access. Call effects and
protected-action admission still require enforcement by the consuming software.
A favorable review is not an approval. No binding executes during static reading.

These sketches are documentation only. They are not valid inputs for existing
AgSDL readers and allocate no version marker. Passing repository checks or
parsing their JSON does not establish semantic conformance or runtime support.
No automatic migration from 0.1 or the frozen experiment is implied.

## Review gates before a candidate

| Proposed choice | Review needed |
| --- | --- |
| Direct response text delivered as information | Confirm the default role; keep an explicit Prepare for authored follow-up instructions. |
| References resolve through the current causal work | Specify static reference scope and ambiguous/missing-result diagnostics, including loops and overlapping invocations. |
| Join groups anchored to a source completion | Check more complex graphs before generalizing this fork-and-join notation. |
| Separate configuration and integration bindings | Define a concrete reusable catalog with visible contracts, parameters, capabilities and compatibility rules. Names alone are insufficient. |

The remaining candidate work also includes closed object shapes, identifier
rules, text assembly and no-visible-text results, required output constraints,
configuration alternatives, relative resource resolution, recovery syntax,
iteration limits, composition bindings and scoped approvals. Queue/steering
overlap and first-satisfactory Join ties and pending stops remain open under
0020/0021. Their absence from these examples does not remove accepted directions
from 0.2 or declare them supported.

After review, select an explicit candidate scope and marker, then derive schema,
serialized fixtures and independent-reader checks from its written semantics.
Do not use schema defaults to decide the open questions in this proposal.
