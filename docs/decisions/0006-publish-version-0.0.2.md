# Decision 0006: publish version 0.0.2 as a conceptual pre-draft

- Status: accepted
- Date: 2026-09-05

## Context

[Decision 0005](0005-version-0.0.2.md) authorized local preparation of a
non-normative conceptual candidate. The preparation and closure are recorded in
the [local work record](../plans/2026-09-05-version-0.0.2.md). The maintainer
subsequently requested publication, integration on `main`, the version tag,
and synchronization of the remote repository before work toward `0.1.0`.

## Decision

Publish the reviewed `0.0.2` scope as a non-normative conceptual pre-draft under
the annotated Git tag `v0.0.2`, attached to the release commit on `main`.
Publish a GitHub prerelease, following the classification used for `0.0.1`.
Push `main`, `develop`, and this tag to the existing AgSDL origin repository.
Keep the main local checkout on `develop`, synchronized with the release.

This authorization supersedes the local-only restriction of the preparation
phase for these publication operations. Earlier records describe the actions
performed in their own phases; they are not statements of current release state.

## Scope and consequences

The [release notes](../releases/0.0.2.md) describe the reviewed cumulative work.
All eleven proposals remain proposed. Publication does not adopt proposal 0011,
any serialization, schema, conformance profile, or external binding. No software
support, execution equivalence, or interoperability claim follows from the tag.

The intended next milestone is an implementable `0.1.0` draft. This decision
does not choose its detailed scope or authorize implementation changes in
Macro, Agent Graph Studio, or other repositories.
