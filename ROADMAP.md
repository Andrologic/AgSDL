# Roadmap

## Host implementations

- Track coverage of the new run scenarios in Macro and its Argentic runtime.
  Add a Macro harness module once a release supports the edition and its
  capabilities can be documented.

## Toward 1.0

- A second, independent validator that agrees with the reference validator on
  every conformance case.
- At least two hosts running the same documents across several harnesses.
- Exporters and adapters for the main harnesses, in hosts and other projects
  that need them.
- More agent properties where harnesses share a meaning: limits, compaction,
  tool allow-lists.
- A governance model for a stable release: maintainers, decision rules and
  versioning authority.
