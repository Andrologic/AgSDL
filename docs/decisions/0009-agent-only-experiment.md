# Decision 0009: remove Principal from the 0.2 experiment

- Status: accepted experiment change; no normative adoption or publication.
- Date: 2026-09-28.
- Starting revision: `f2a20f28f8d03baa1f7cb1bb4f477ea4dd3706b0`.

The maintainer rejected the separate Principal concept for the intended Agent
system description and authorized its removal from the experimental candidate.
This supersedes direction 4 of [Decision 0008](0008-0.2-experiment-directions.md)
for the new experiment only. It does not amend the published 0.1.0 contract.

[Proposal 0017](../../proposals/0017-agent-only-kiss-0.2.md) defines
`agsdl-exp-0017-c1`: remove the Principal catalog, Agent principal references and
approval recipient lists. Users, accounts, authentication, permissions and the
selection of human decision-makers belong to the consuming application. People
are not reclassified as Agents. No substitute actor field is introduced.

Approval steps, call links, scope, effects, ordered chains, data availability,
deadlines and refusal paths retain their existing meaning. A static report
still proves no authentication, authorization, timing enforcement or execution.
Engine, Agent and Configuration remain distinct. No other simplification is
authorized by this decision; further candidates are for maintainer review.

Proposal 0016 and Decision 0008 remain historical sources. The c2 reader,
example and corpus snapshot is retained in Git at the starting revision above;
its evidence cannot be relabelled as the new candidate. No automatic or lossless
migration is promised. Existing actor/recipient information needs an explicit
handling decision outside the new format before moving an artifact to it.

Implement the revised examples, both static readers and an independently
specified comparison corpus before claiming new-edition agreement. Keep raw
reports and work planning outside the checkout. Normative adoption, deployment
and publication remain separate decisions.
