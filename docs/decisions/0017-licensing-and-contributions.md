# 0017. Licensing, the AgSDL name and contributions

Status: accepted.

## Context

The repository had a `LICENSE` file with the Apache License 2.0 and no other
statement: no copyright holder, no rule on the AgSDL name, no terms for
contributions. AgSDL is a specification meant to be implemented by harnesses,
hosts and tools that other people build.

## Decision

- The whole repository stays under the Apache License 2.0: specification,
  schemas, tooling, harness modules, examples and conformance cases.
- A `NOTICE` file states the copyright: Andrologic SAS and the AgSDL
  contributors.
- Only this repository defines AgSDL editions. A modified specification uses
  another name. A tool or harness may say that it implements an edition.
- Contributions are accepted under the Apache License 2.0. Each commit from a
  contributor carries a `Signed-off-by` line under the Developer Certificate
  of Origin.

## Reasons

- Apache 2.0 grants a patent license from each contributor, and ends it for
  whoever sues over a patent. An implementer needs that grant. MIT has none.
- CC BY 4.0 for the specification was rejected. It excludes patent rights,
  and Creative Commons does not recommend it for code. The specification, the
  schemas and the tooling change in the same commit, so one license avoids a
  split inside one change. Apache 2.0 already requires redistributors to keep
  notices and mark changes.
- The license grants no right to the name (section 6). Without a rule, a
  modified specification could call itself "AgSDL 0.3", and the contract
  marker would lose its meaning. The conformance cases and run scenarios let
  an implementation check its claim.
- The Developer Certificate of Origin records that each contributor may submit
  the change. A contributor license agreement was rejected: it needs a legal
  document and a signing tool, and Apache 2.0 already covers patents and
  commercial use. Only an agreement would allow a later change of license;
  that freedom is not needed for an open specification.

## Consequences

`NOTICE` is added at the root. The README states the license and the rule on
the name. `CONTRIBUTING.md` asks for `git commit -s`. Commits made before this
record carry no sign-off; they are covered by the transfer of the author's
rights to Andrologic SAS. Registering AgSDL as a trademark is a separate
decision for Andrologic SAS.
