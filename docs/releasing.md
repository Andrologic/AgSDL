# Releasing AgSDL

A distribution tag identifies the tools, schemas and specifications shipped
together. The language edition identifies the contract a host executes.
Project and archive formats have their own markers. For example, distribution
`v0.5.0` ships `agsdl-0.4.0`, `agsdl-project-1` and `agsdl-archive-1`.

1. Create a release branch from the latest `main`.
2. Update the distribution and language status in `README.md`,
   `spec/README.md` and `AGENTS.md`. Add a dated section to `CHANGELOG.md`.
   Date the changelog of each harness module that ships a new version.
3. Give new or revised schemas a canonical `$id` at the new tag. Keep the
   published IDs of unchanged schemas. Check that the document schema URI
   in `spec/document.md` and `docs/quickstart.md` matches the language edition.
4. Run `./scripts/check.sh`. For a distribution that ships packaging changes,
   pack and restore the example project both with and without Git history.
   Open a pull request to `main` and merge after review and passing checks.
5. Tag the resulting commit on `main` as `vX.Y.Z`, push the tag and publish
   a GitHub release with the new section of `CHANGELOG.md` as its notes.
6. Verify that each canonical schema URI resolves to the shipped schema and
   that relative schema references resolve from the tag.

Published tags are immutable. Ship corrections in a subsequent release.
