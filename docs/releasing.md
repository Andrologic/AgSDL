# Releasing an edition

Maintainers release editions from `main` once the edition's open review is
done. Replace `X.Y.Z` below with the edition.

1. Create a branch from the latest `main`.
2. Mark the edition as published:
   - the status table in `README.md` and the status line of `spec/README.md`;
   - the status paragraph of `AGENTS.md`;
   - the heading of the edition in `CHANGELOG.md`, with the release date;
   - the heading of each module version in `harnesses/*/CHANGELOG.md` that
     ships for the first time.
3. Check that the `$id` of every file in `schema/`, and the `$schema` URI in
   `spec/document.md` and `docs/quickstart.md`, name the tag `vX.Y.Z`.
4. Run `./scripts/check.sh`, then open a pull request to `main`. Merge it
   after review and passing checks.
5. Tag the resulting commit on `main` as `vX.Y.Z`, push the tag, and publish
   a GitHub release whose notes are the edition's section of `CHANGELOG.md`.
6. Open each schema URI and check that it resolves.

Earlier editions are never changed after their tag. A fix to a released
edition is a new edition.
