# Decisions

Each record states a design decision, its reasons and the alternatives
rejected. The specification states the rules; these records explain them.

| Record | Decision |
| --- | --- |
| [0014](0014-agsdl-0.3-model.md) | The AgSDL 0.3 model: missions and agents, harness modules, permissions, instances, delivery, joins, compositions. |
| [0015](0015-current-edition-repository.md) | The repository keeps only the current edition, and maintains harness modules. |
| [0016](0016-json-documents.md) | Documents are strict JSON, not YAML or JSON5. |
| [0017](0017-licensing-and-contributions.md) | The repository is under Apache 2.0, the AgSDL name is reserved to its editions, and contributions are signed off. |
| [0018](0018-shared-path-cancellation.md) | Stop cancels shared work once and ends its path without a result in the other open groups. |
| [0019](0019-steer-receipt.md) | A steer is absorbed on confirmed receipt. Definite non-receipt permits fallback, and uncertain receipt fails the step. |
| [0020](0020-run-cancellation-and-recovery.md) | A whole-run stop requires confirmed termination, and an abandoned run after host interruption has its own outcome. |

Records 0001 to 0013 concern editions 0.0.1 to 0.2.0. They are available from
the [`v0.2.0`](https://github.com/Andrologic/AgSDL/tree/v0.2.0/docs/decisions) tag.
