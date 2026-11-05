# Releasing an edition

An edition is released by a maintainer, from `develop`, once its open review
is done. Replace `X.Y.Z` below with the edition.

1. Run `./scripts/check.sh`. It must pass.
2. Mark the edition as published:
   - the status table in `README.md` and the status line of `spec/README.md`;
   - the status paragraph of `AGENTS.md`;
   - the heading of the edition in `CHANGELOG.md`, with the release date;
   - the heading of each module version in `harnesses/*/CHANGELOG.md` that
     ships for the first time.
3. Check that the `$id` of every file in `schema/`, and the `$schema` URI in
   `spec/document.md` and `docs/quickstart.md`, name the tag `vX.Y.Z`.
4. Merge `develop` into `main`.
5. Tag `main` as `vX.Y.Z`, push the tag, and publish a GitHub release whose
   notes are the edition's section of `CHANGELOG.md`.
6. Open each schema URI and check that it resolves.

Earlier editions are never changed after their tag. A fix to a released
edition is a new edition.
