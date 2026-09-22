# Proposal 0015: lightweight validation reports for 0.2

Status: **PROPOSED**, not adopted and not implemented. This proposal covers
planning points 4 and 11 only. The published release is 0.1.1; its contract
remains `agsdl-0.1.0`, as recorded in the
[release status](../README.md#release-status-and-history).

## Problem and scope

A third-party program needs to know what was checked, what failed, and where.
Today, implementing a validation feature also requires a source inventory,
opaque byte slices, detailed rule execution records, and exact report
conventions. This makes a small validator carry preservation and inspection
machinery even when it never writes a document.

Recommend a small validation report with explicit coverage and diagnostics,
separate from optional inspection and byte-preserving exchange. Keep independent
checks after a local error. Compare semantic observations rather than report
presentation order. No implementation's existing output determines these rules.

This is a report proposal, not a replacement agent model. Here a **unit** means
a named, versioned set of static checks; a **subject** is the input location to
which a check applies. These terms do not choose the final object names or
module layout being designed in proposal 0014. Example unit names, codes and
JSON field names below are candidate notation, not reserved 0.2 identities.
No reader, schema, corpus, oracle, runtime or product integration is introduced.

## Current obligations and proposed separation

[The specification index](../spec/README.md#edition-and-feature-identities)
makes each operation's full input, inventory, output, diagnostic, prerequisite
and exclusion rules part of its feature. A selectable subset cannot claim that
feature. [Reports](../spec/reports.md) defines the closed report grammar and
exact rule/state/location records. This proposal changes none of those rules.

| Current 0.1.0 obligation | PROPOSED 0.2 treatment | Consequence |
| --- | --- | --- |
| Contract, processor Edition, operation, input ids and SHA-256 | Retain report edition, processor identity/version, operation, input ids and hashes. | Results remain tied to exact supplied bytes; identity is not authenticity. |
| Unit, phase and prerequisite results | Retain an exact versioned scope, phase, presence and explicit incomplete coverage. | A local check cannot masquerade as resolution or whole-document validation. |
| Findings with rule, outcome and location | Retain stable codes and locations; prose is optional. | Software can act without parsing messages. |
| Completed/excluded/blocked Check arrays for every rule | Make full successful execution traces optional; retain all applicable checks not performed and their causes. | Small successful reports; callers still see gaps. Full traces remain useful for debugging. |
| Inventory.tree, exhaustive states and maximal opaque slices | Optional inspection output, outside validation success. | A validator need not return a second document or byte offsets for every opaque value. A compact report alone cannot reconstruct unknown data. |
| Input/output byte accounting and exact preservation | Separate exchange capability, never required of a read-only validator. | Validation does not prove round-trip preservation. A writer must state its own preservation contract. |
| Losses and outputs arrays even for validation | Omit when there is no transformation. | No empty transformation machinery in the ordinary validation report. |
| Sorted Inputs, some Results and Checks | Compare collections by keys; presentation order is informative. | Unicode collation no longer affects report equivalence. Source arrays still retain semantic order and pointers. |
| Mandatory refusal feature lossyExchange | Do not include a refusal-only operation in the new core. | A rejected transformation needs no separate conformance feature. No lossy output is thereby permitted. |

### Unknown data, bytes and validity are separate

PROPOSED: a reader may accept a permitted opaque value without understanding
it. This says nothing about its domain validity. An unknown required semantic
module prevents a complete validation result; it is never silently ignored.
An optional annotation can remain uninterpreted only when the adopted unit
explicitly permits that treatment. Arbitrary unknown members of a closed record
still fail shape; unknown data is not a general escape from validation.

Conserving unknown data means keeping its information, including nested unknown
members, exact strings and numeric values. It is stronger than silently dropping
fields but weaker than preserving source bytes. For example, reformatting
`{"x":1e0}` as `{"x":1}` can conserve the numeric value but changes bytes and
hashes. Rounding an opaque `9007199254740993` to `9007199254740992` loses data.
A host JSON parse/serialize cycle is therefore not sufficient evidence of
unknown-data conservation. Strict JSON validity is a third, separate property;
copying malformed bytes exactly can preserve them without validating them.

A read-only validation report makes no conservation promise. A tool offering
exact exchange must retain the original supplied bytes and boundary under that
separately specified capability. A future rewriting operation would need an
explicit unknown-data and loss policy before adoption; this proposal supplies
none. Removing lossyExchange from a future core does not authorize omission,
conversion or rewriting. The current operation still unconditionally refuses,
returns E-LOSS and no output, including when callers assert permission. Its
current contract and historical evidence remain unchanged.

## PROPOSED compact report rules

The following is a candidate contract for arbitration, not normative 0.2 text.

A report identifies its edition, processor, operation and every supplied input
by id and SHA-256. Each result identifies one input, requested unit/version,
phase and subject pointer. Required prerequisite scopes appear as separate
results, referenced by the dependent result. Their observations are not copied.
The scope definition fixes the full check set, mandatory prerequisites,
applicability conditions and external lookup boundary. Implementations cannot
select a convenient subset and still report a unit pass.

Every result carries:

- `presence`: `present`, `absent` or `undetermined`, for the selected subject.
  Absence requires a readable parent and an observed missing optional member.
  An unreadable parent cannot establish absence. An empty present array is
  present, not absent. A missing required member is a shape failure.
- `outcome`: `pass`, `fail`, `unsupported`, `inconclusive` or `not-applicable`.
  `pass` requires all applicable checks and prerequisites to succeed within the
  declared scope. `fail` requires an observed violation. `unsupported` means
  required interpretation is unavailable to the processor. `inconclusive`
  means other necessary facts or checks are unavailable. `not-applicable` is
  reserved for an observed absent optional subject after prerequisites pass
  and any scope-wide obligations complete successfully.
- `diagnostics`: observations with stable `code`, `outcome` and `location`.
  An optional `message` explains the issue. The result supplies the input id.
- `incomplete`: all applicable checks not performed, each with `code`,
  affected `location` and `reason`: `blocked`, `unsupported` or `unavailable`.
  These are coverage facts, not new document violations. The code identifies
  the affected check. A prerequisite reference or source location may explain
  the cause. Omit successful check traces, not gaps.

The versioned scope also explicitly lists excluded work, such as execution,
readiness and external resolution in a local-only unit. Fixed exclusions need
not repeat in every report. Input-dependent exclusions must be explicit in
`incomplete` as unavailable, or in a separately named, narrower scope fixed by
the contract. A reader cannot invent such a narrower scope at run time.
No result certifies full-model validity, execution or engine availability.
In particular, absent execution evidence is outside this static report's
claim; a supplied hash of a declaration does not turn it into execution proof.

For each result, aggregate observed failures and prerequisites first, then
unsupported interpretation, then incomplete work or explicit unknown facts:
`fail` precedes `unsupported`, which precedes `inconclusive`. Preserve all
independent diagnostics and gaps even when a higher-precedence outcome wins.
Only then choose `not-applicable` for observed optional absence, or `pass`.
A present subject with a known empty check domain can pass. An absent subject
cannot pass existence or cause a failed prerequisite to disappear.
Cancellation or a resource limit adds an explicit gap at the affected subject
and makes the result at least inconclusive. An already observed fail or
unsupported outcome retains its higher precedence; all observed diagnostics
remain. An interruption can never produce a complete pass. A transport failure that
prevents producing a report is an API failure, not a validation result.

Locations use an input-relative JSON Pointer for parsed values, with `~0` and
`~1` escaping. Missing mandatory fields point to their existing parent;
wrong-type and extra-field failures point to that field. Syntax failures use
a zero-based UTF-8 byte offset; retain the existing strict parsing and first
error convention in [Reports](../spec/reports.md), including its surrogate
witnesses, rather than define another parser policy here. No parsed child
locations are fabricated after parse failure.

One diagnostic is emitted per code/location/outcome. Several explanations of
that tuple belong in optional prose; duplicate tuples are disallowed. An
aggregate rule such as cycle detection reports once at its declared collection
subject, not once per traversal path. Different failure and unknown outcomes
at the same subject remain distinct. The future adopted unit must assign each
check its exact subject and data prerequisites; generic dependency prose alone
is insufficient to implement a complete rule inventory.

### Candidate reports

These short fragments show `results` only. Each complete report also carries
its edition, processor, operation and input ids/hashes as specified above.
They are illustrative reports, not 0.1.0 schema instances or 0.2 test oracles.
The example unit `local@candidate` assumes shape and local reference checks;
`module@candidate` checks a required module; `optional@candidate` checks an
optional subject. Their final names and inventories remain unassigned.

A required module is well-declared but unknown to this reader. This is support
insufficiency, not proof that the document violates that module:

```json
{"results":[{"input":"primary","unit":"module@candidate","phase":"local","subject":"/modules/0","presence":"present","outcome":"unsupported","diagnostics":[{"code":"REQUIRED-MODULE","outcome":"unsupported","location":{"pointer":"/modules/0"}}],"incomplete":[{"code":"MODULE-CONTENT","location":{"pointer":"/modules/0"},"reason":"unsupported"}]}]}
```

A local required identity is missing. Its dependent lookup cannot run, but a
separate readable record still contains a reference to a demonstrably absent
local target. Both the shape violation and independent reference failure survive:

```json
{"results":[{"input":"primary","unit":"local@candidate","phase":"local","subject":"","presence":"present","outcome":"fail","diagnostics":[{"code":"SHAPE","outcome":"fail","location":{"pointer":"/items/0"}},{"code":"REFERENCE","outcome":"fail","location":{"pointer":"/items/1/target"}}],"incomplete":[{"code":"LOOKUP","location":{"pointer":"/items/0"},"reason":"blocked"}]}]}
```

Here the independent target uses a separate, fully readable catalog. If it
used the incomplete identity catalog containing `/items/0`, missing-target
absence could not be proved and its lookup would also be blocked.

A readable document omits an optional subject, and its prerequisites passed:

```json
{"results":[{"input":"primary","unit":"optional@candidate","phase":"local","subject":"/optional","presence":"absent","outcome":"not-applicable","diagnostics":[],"incomplete":[]}]}
```

This records observed absence; it validates neither an existing optional unit
nor its existence. A UI should say "optional subject absent", not "unit valid".

A present subject has no violation in the readable data, but a necessary fact
is explicitly unknown. This is neither invalidity nor unsupported interpretation:

```json
{"results":[{"input":"primary","unit":"local@candidate","phase":"local","subject":"","presence":"present","outcome":"inconclusive","diagnostics":[{"code":"UNKNOWN-FACT","outcome":"inconclusive","location":{"pointer":"/requiredFact"}}],"incomplete":[{"code":"FACT-CHECK","location":{"pointer":"/requiredFact"},"reason":"unavailable"}]}]}
```

## PROPOSED resolution of the open diagnostic questions

The witnesses below refer to the existing
[diagnostic dossier](../docs/reviews/0009-0.1.1-diagnostic-expectations.md).
They explain future behavior using existing paths, without requiring those
objects or rules to survive the 0.2 model. The same principle applies to any
future equivalent check. The determinate 0.1.1 corrections are not reopened.

### Unicode order

Treat input/result/diagnostic/gap collections as unordered keyed collections.
Input ids are unique; result keys are input/unit/phase/subject. Diagnostics and
gaps use their respective tuples above. Duplicate keys or tuples invalidate a
report; comparison must reject duplicates before constructing sets or maps.
No report textual sort is a conformance condition. Optional inventories and
traces likewise have no portable ordering requirement under this proposal.

Witness: annex ids U+E000 and U+10000 containing the same `{}` bytes, following
primary `{}`. Either report order is equivalent. Both distinct ids must
be present, each with the exact hash of its supplied bytes; the hashes in this
witness are identical. Unicode normalization, ASCII restrictions, locale
collation and UTF-16 order are unnecessary. Pointer strings compare exactly as
decoded scalar sequences, with no normalization. Source array ordering and
array-index pointers remain significant; this is not permission to sort input.

Python may use its native scalar order and JavaScript its native UTF-16 order
for display. A future comparator compares keyed content without requiring
one producer's sort. It must also ignore order in prerequisite-reference lists
and reject duplicate references. Thus the dossier's Unicode ambiguity becomes
irrelevant to the compact report. If canonical serialized reports later become
necessary for signing, specify a separate canonical encoding then.

### Aggregates and dependent checks: groups E and I

Use field-level data dependencies, not a whole-record-validity flag. A local
assessment depends on its own readable identity, requirements and claims and
on the completeness of its own required closure. It does not depend on global
coverage of sibling bindings. A collection-wide coverage check does depend on
a complete identity catalog. Positive local assessment never validates the
surrounding configuration or the assessed record's entire shape.

Group E witness: delete `/runtime/configurations/0/agents/0/agent`. Shape fails
at that binding. Its identity lookup, required content/tool enumeration and
aggregate assessment are blocked. Exact configuration coverage is blocked at
`/runtime/configurations/0`. The readable second binding's local capability
assessment remains checkable if its own inputs and closure are complete;
keep its observable capability findings. Do not infer a missing binding from
an incomplete catalog. If both records instead contain the same readable
identity, that concrete ambiguity blocks identity-dependent assessments for
that identity; there is no first or last winner.

Group I witness: delete `/definitions/12/payload/tools`. Shape fails there;
required Tool enumeration and Tool-coverage assessment for consuming bindings
are blocked. Their engine capability assessment is still independently
checkable because, under the current example's requirement definition,
Skill.tools contributes no engine requirement. Known Tool requirements and
individual Tool assessments remain observable. A combined "all configuration
requirements satisfied" claim would need complete Tool coverage and is blocked.
Prefer omitting that redundant combined aggregate from the lightweight report.

Python and JavaScript would both separate local capability inputs from global
binding/tool coverage. For E this rejects JavaScript's sibling aggregate blocks;
for Skill.tools it rejects a blanket Agent capability block. This selection
follows the stated data dependency, not either reader's general algorithm.
The comparator would compare the required gaps and local outcomes, not the
current runtime inventory State or completed/blocked trace layout. It would
still reject an omitted gap, suppressed independent diagnostic or false pass.

### Content recognition dependencies: group I target/at

Witnesses: delete `/definitions/11/payload/target` or
`/definitions/11/payload/at` independently. Report shape failure. A check of
application-point agreement needs the missing field and is blocked at its
consuming Application. Recognizing referenced content for requirement
collection depends on its readable kind and reference, not those fields.
Its readable format/requires still contribute requirements; dependency and
ordering checks run if their own inputs are readable. Content recognition
alone does not certify valid or applicable instructions.

Python would remove whole-payload R-CONTENT and binding capability blocks caused
solely by target/at absence. JavaScript would retain its independently readable
checks. Both must block any actual application-point comparison they expose;
the current R unit does not separately define that comparison, so no new 0.1.0
rule is implied. A future comparator uses the adopted unit's explicit dependency
map, not either existing full report. If 0.2 has no application-point check,
that particular gap is inapplicable; shape and readable requirements still
follow the rules above.

### Missing discriminants: group G

Witness: delete `/graphs/0/steps/0/kind` from an otherwise valid invoke.
Report one shape diagnostic at `/graphs/0/steps/0`. Validate only common fields
whose constraints are stated independently of the variant, such as a common
id if the future grammar defines it there. Do not infer invoke from its other
members; do not classify variant-specific members as fallback extra fields.
Block checks that need a selected variant. Continue independent sibling checks.
The same rule applies to malformed or unknown discriminants in a closed union;
unknown discriminants in an expressly extensible union instead follow its
required-module support rules. Missing mandatory discriminants always fail.

JavaScript would stop emitting the twelve fallback extra-field diagnostics in
the dossier; Python's parent-only shape result matches this witness but is not
the rule's source. Both must preserve any independently defined common-field
failure and dependent gaps. A future comparator requires that diagnostic set
and rejects inferred variants. A known variant still receives its complete
closed-record extra-field checks.

## Cross-reader agreement boundary

For identical input bytes, request, scope edition and declared interpretation
support, readers must agree on input identities/hashes, result keys, observed
presence, prerequisite references, outcomes, diagnostic code/location/outcome
tuples and incomplete check/location/reason tuples. Those fields are portable.
Support differences can legitimately produce unsupported versus a completed
assessment, but must be explicit; compare common supported scopes separately.
A comparator cannot turn one processor's missing support into document invalidity.

Messages, processor names/versions, display order, source excerpts and optional
successful traces are informative. Optional inspection output needs its own
capability contract before exact inventory comparisons are claimed. Timing,
resource-limit circumstances and actual execution evidence are not portable
static verdicts. A resource-limited result must retain its incompleteness;
a comparator reports such evidence as incomplete rather than accepting it as
an equivalent complete pass. No text-message matching is needed.

## Alternatives and compatibility

Keeping the entire 0.1.0 report minimizes migration work, but retains the
inventory and trace implementation burden. Making every diagnostic informative
would be smaller, but prevents dependable third-party automation and hides
reader disagreement. Choosing scalar order for every report would resolve the
Unicode witness, but adds an encoding convention where keyed equality suffices.
Blanket blocking after any malformed record is simpler internally, but suppresses
independent evidence and can hide a known incompatibility.

Recommend the compact report and dependency rules above as one coherent future
contract. This is a breaking report change, requiring a separately adopted
report edition and feature identities. It cannot be emitted with the current
`agsdl-0.1.0` marker. Existing readers, schemas, seven operations, snapshots and
comparison commands keep their contracts unchanged. An adapter may display a
0.1.0 report compactly as a non-normative view, but cannot claim a 0.2 result:
current reports do not settle the open diagnostic questions or define 0.2 scope.
A compact report also cannot recreate omitted inventory or full traces.

After arbitration, adoption would require explicit unit inventories, dependency
and location rules, normative edits, and separate implementation/conformance
work. Those later steps must validate the new agreement boundary with both
readers. This proposal provides candidate witnesses, not executable proof.

## Security and operational limits

Reports can contain attacker-controlled ids, pointers and optional messages.
Consumers escape them for display and logs, treat map keys as ordinary data,
and do not interpret them as file paths, URLs or instructions. Source excerpts
and inventories can leak secrets; omit them by default. Hashes bind observed
bytes but do not authenticate a source or establish the truth of claims.
Resource limits must report incomplete work rather than truncate into success.

No report grants permission to execute, fetch dependencies, load module code,
select an engine or transform unknown content. Required-module support is a
statement of interpretation coverage, not automatic installation. Capability
declarations remain separate from runtime evidence. The stop/edit/restart
boundary remains: an edited configuration changes the prospective execution's
pin, and static validation provides no hot-reload or migration permission.

## Indispensable maintainer decision

Approve or reject the proposed separation and portable agreement boundary as
a direction for a later 0.2 contract, including the absence outcome and the
field-level dependency rules. For example, should a third-party validator be
allowed to return a scoped pass with no inventory or successful traces, while
still returning a gap for every applicable check it could not perform?
Recommendation: yes. Retain the current contract until a separate adoption.

Final unit/module names and concrete rule inventories must be settled with the
model proposal before normative drafting. That is a dependency, not permission
to choose agent semantics here. Canonical report signing, lossy transformation
policy and richer inspection profiles are unnecessary to this first decision.
