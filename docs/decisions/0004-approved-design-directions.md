# Decision 0004: reconcile the model and prepare a bounded exchange contract

- Status: accepted design directions; detailed proposal changes remain proposed
- Date: 2026-09-05

## Context and maintainer decision

The [implementation-readiness review](../reviews/0003-implementation-readiness.md)
identified five decision gates. The maintainer approved option A for each on
2026-09-05, after reviewing the alternatives and conceptual examples. This
decision records that authorization. It does not adopt a normative language,
serialization, schema, feature identifier, or third-party integration.

## Approved directions

1. **Composition.** A complete System may use exclusively imported Agent
   definitions. Participation in the System must be distinct from lifecycle
   ownership. Imported definitions retain their original lifecycle owner.
2. **Authorization evidence.** One Action occurrence may be directly associated
   with several Authorization decisions. Each decision remains associated with
   its evaluated requirement and the relevant Policy application point. A
   decision for one requirement does not satisfy a different required check.
   This selects direct accounting rather than a new aggregate-decision model;
   it does not implement an authorization engine.
3. **Conformance.** Use implementation features and conformance profiles rather
   than requiring a general conformance-level model. Reconcile requirements and
   traceability accordingly. Feature contracts need defined scope and evidence
   before stable feature identities can be published. This direction amends
   the reference to conformance levels in Decision 0001.
4. **Incomplete fragments.** Permit validation by phase. An incomplete fragment
   may pass unresolved-document validation only when its missing obligations
   are explicitly declared and permitted to be deferred at that phase. A
   required obligation still missing at resolved-graph validation prevents a
   positive verdict for the graph in scope. The permitted deferrals and their
   declaration requirements must be explicit; incompleteness alone is not
   permission to bypass an invariant.
5. **First external contract.** Prepare a bounded contract for reading,
   inspection, structural validation, and exchange. It should distinguish local
   and imported definitions, expose missing and unsupported information, and
   define preservation and loss reporting for the covered information. Submit
   its exact scope and processing rules for maintainer review before normative
   adoption. Execution equivalence is outside this first contract.

## Consequences and limits

Existing proposals may be reconciled with these directions, with corresponding
conceptual examples and traceability. Their status remains proposed. Detailed
alternatives that require a further material choice remain visibly open or
explicitly proposed for review; they must not be presented as accepted here.

The distinction between definition identity and Principal identity remains
established in proposal 0002. The precise meaning of its Agent-to-Identity
relation must be addressed in preparing the first contract, without assuming
that the earlier wording correction settled it.

The earlier readiness review remains a record of its base commit. Its findings
are not silently rewritten to describe later revisions. The local work plan
records which findings have been addressed and which questions remain.

All execution of this work and integration remains local. The maintainer has
authorized worktrees, review, commits, and merges into `develop`. Publication,
deployment, changes in other repositories, and adoption of the precise first
normative contract remain outside this authorization.
