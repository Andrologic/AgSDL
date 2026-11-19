# 0019. Receipt of a steer message

## Observation

[Issue 8](https://github.com/Andrologic/AgSDL/issues/8) reports observations
from Macro with Codex 0.167.0. The app-server accepted a `turn/steer` request
before emitting the `userMessage` with the client's identifier. It refused a
request sent after `turn/completed`. When the connection dropped before the
matching message event, Macro could not establish receipt. These observations
describe that version and integration.

## Decision

[Delivery](../../spec/flow.md#confirming-a-steer) makes receipt by a specific
work the condition for absorption. An accepted request can outlive that
work. Proof can arrive late and still establish earlier receipt. A work
ending without proof can leave a message pending, so an all join can finish
collecting the other branches while it waits for the sender's outcome.

Fallback to the queue requires proof that the attempt did not deliver and
can no longer do so. Replaying on the basis of completion alone could apply
the same instruction twice. Assuming absorption from the same event could
discard the instruction and let a join continue. A bounded wait and an
explicit `STEER_UNCERTAIN` failure give the sender's path a defined outcome
when evidence is lost.

## Edition

Recommend 0.4.0. The document shape and the immediate-receipt timelines
carry across, but hosts must account for pending branches and handle a new
runtime failure. 0.3.1 would fit an editorial clarification without new
observable outcomes. The edition marker and publication are handled when
the next edition is prepared.
