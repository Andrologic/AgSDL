# Bounded KISS 0.2 experiment

Status: **experimental candidate, not normative, not adopted, not published**.
The marker is `agsdl-exp-0016-c2`, not a delivered AgSDL version. The only rule
source is [proposal 0016](../../proposals/0016-kiss-experiment-0.2.md), under the
[prototype mandate](../../docs/decisions/0008-0.2-experiment-directions.md).
[Python](readers/python/README.md) and [JavaScript](readers/javascript/README.md)
readers implement static validation. The [comparison corpus](corpus/README.md)
and [KISS assessment](ASSESSMENT.md) record the bounded c2 evidence.
No runtime or normative conformance implementation is supplied here.
The current published contract remains `agsdl-0.1.0` in release 0.1.1.

## Changes from c1

Candidate c2 clarifies that ASSIGN projects step kinds and invoke Agent refs
without depending on step ids. It also makes explicit that a complete empty
requirement set with a supplied readable choice needs no claim lookup; malformed
claims remain configuration defects. Incomplete requirements, coverage and
effects retain their independent checks. These clarifications change the marker
after the c1 reader baseline was frozen. Both readers now target c2, with
[separate c2 comparison evidence](ASSESSMENT.md). Historical c1 evidence does
not establish c2 agreement.

## Exact example inputs

All files below are complete JSON artifacts, not overlays. They contain fictional
engine/adapter/capability names. Repeated `1` evidence hashes are illustrative
assertion identifiers, not verified evidence. The observations below are reading
guidance derived from 0016, not a second oracle or implementation proof. Units
not present are not-applicable as specified there; syntax passes for every file.

| Input | Intended candidate observation |
| --- | --- |
| [agent-embedded](examples/agent-embedded.json) | Descriptive Agent, no Principal, graph or engine. Core passes; optional units absent. |
| [agent-named](examples/agent-named.json) | Same content and operation as embedded form, with named Definitions. Core passes. Different bytes and Definition identities, not an identity-preserving rewrite. |
| [two-agent-sequence](examples/two-agent-sequence.json) | Two calls, typed success data and explicit failure path. Core/flow pass; no configuration selected. |
| [two-configurations](examples/two-configurations.json) | Same Agent/graph declarations as sequence, two explicit engine assignments and complete content Applications. All present units pass on declarations only. |
| [tool-incompatible](examples/tool-incompatible.json) | Structure remains valid. Selected writer Tool contributes compatibility TOOL fail at `/configurations/primary/agents/0/tools/0`. No fallback or Tool deletion. |
| [governed-call](examples/governed-call.json) | Explicit actor, action/resource/context scope, two ordered human gates and configuration pin. All present units pass statically; no authority, timing or execution proof. |
| [governed-missing-actor](examples/governed-missing-actor.json) | Principal removal produces flow ACTOR fail at `/graphs/release/steps/2`, even though a descriptive Agent may omit it. |
| [required-extension](examples/required-extension.json) | External REQUIRED unsupported plus a gap with cause unsupported at `/extensions/0`; core still passes within its scope. |
| [missing-reference](examples/missing-reference.json) | Core REF fail at `/agents/writer/instructions/0/content`. No fallback content. |
| [ambiguous-reference](examples/ambiguous-reference.json) | Core ID fails at both `/instructions/draft` and `/principals/draft`; REF gap at the consuming slot, no first/last winner. |
| [conflicting-bindings](examples/conflicting-bindings.json) | Configuration ASSIGN fails at `/configurations/primary`; duplicate writer bindings cannot receive complete dependent content/Tool/compatibility checks. The independent reviewer remains checkable. |
| [independent-errors](examples/independent-errors.json) | Missing instruction reference and invalid operation mode both fail in core; required external interpretation remains separately unsupported. One error does not conceal another. |
| [application-order-conflict](examples/application-order-conflict.json) | Reversing two Agent instruction slots in Applications gives CONTENT fail and ENGINE reference gap at `/configurations/ordered/agents/0`. The declared behavior cannot be reordered by engine selection. |
| [unknown-support](examples/unknown-support.json) | Empty writer claims produce compatibility ENGINE inconclusive at `/configurations/primary/agents/0`; structure still passes. Missing evidence is not a structural violation. |
| [duplicate-step-assign](examples/duplicate-step-assign.json) | Exactly D(flow,STEP-ID,/graphs/g/steps,fail) and G(flow,PATH,/graphs/g,{shape}). Configuration passes with no ASSIGN gap; all other diagnostic/gap arrays are empty. Syntax/core pass; compatibility/external are absent/not-applicable. |

The duplicate-step witness has two failure terminals named `e`, no invoke and
an empty configuration AgentBinding array. Its invalid graph does not obscure
the known empty assignment set. Proposal 0016 includes the complete witness.

For the empty-requirement witness, start from `tool-incompatible`, set
`tools.lookup.requires` to `[]` and the selected writer ToolBinding's `claims`
to `[{}]`. The exact observations are
D(configuration,SHAPE,/configurations/primary/agents/0/tools/0/claims/0,fail) and
G(configuration,UNIQUE,/configurations/primary/agents/0/tools/0/claims,{shape}).
All other diagnostic/gap arrays are empty; compatibility passes. This case
does not stand for incomplete requirements or suppress coverage/effects checks.

Applications preserve the Agent's declared slot order and select stable slot ids,
such as `task`, whether the slot's
value is named or embedded. Invoke always selects `rewrite` in that Agent's
explicit Interface choice. The configuration examples copy complete settings
values to both engines; they do not imply inheritance or native-option translation.
Engine configuration edits preserve Agent declaration content, but change exact
artifact identity, as does formatting. No embedded hash creates a circular pin.

## Cost and coverage comparison

| Comparison | Saving | Cost or reduced coverage |
| --- | --- | --- |
| 0014 named Agent → embedded Agent | No standalone Instructions/Interface ids or reference records for single-use values; no Definition versions or module version list. | Two choice branches need identical payload checks. Reused content still benefits from named records. Embedded values have addresses, not Definition identities. |
| 0.1.0 single Agent | No mandatory Principal placeholder, repeated owners or scoped Key triples. | A non-governed description may leave actor undeclared; that is less information. Instructions and an operation remain explicit. |
| 0.1.0 two-Agent sequence | No repeated invoke ports/Principal or placeholder Action/Resource/context for pure text operations. | One Interface per Agent, no conditions/imports/Skills. Governed calls need actor and Scope again. Literal action/resource descriptions do not preserve every old Definition identity. |
| 0014 configuration sketches | No extra shared binding/settings catalogs or version solver. | Complete settings may repeat. Applications and per-Agent bindings remain mandatory; this experiment does not claim fewer declarations for every engine switch. |
| 0.1.0 reports and 0015 direction | No inventory, byte slices, full success trace or exchange output from validation. | No round-trip proof, no complete 0015 implementation claim. Exact candidate rule subjects/dependencies must be implemented and compared. |

These are obligation and coverage comparisons, not line-count claims. The old
examples and 0014/0015 are unchanged. The examples intentionally include failures
and unknowns; being readable JSON is not a positive validation result.

## Comparison evidence

The [dedicated comparison command](corpus/README.md) checks 38 exact inputs
against hand-authored expectations and both independent c2 readers. It retains
raw reports and source metadata outside the checkout. The [assessment](ASSESSMENT.md)
separates observed agreement, declaration measurements and recommendations.
No reader output supplies the oracle. Candidate changes still need review and a
new marker once a reader baseline is frozen. Runtime and engine support remain
outside this evidence.
