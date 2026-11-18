# 0018. Cancellation of a path shared by open joins

A valid graph can put the same path in two join groups. When one group
closes with `remaining: "stop"`, the work on that path can still be needed
by the other group. AgSDL 0.3.0 left that interaction unspecified.
[Issue 4](https://github.com/Andrologic/AgSDL/issues/4) describes the case.

Stop cancels the work once. An open group that also waits for the path
accounts for it as ended without a result after termination is confirmed.
Unstarted fan-out elements are withdrawn. Each affected group can then apply
its normal waiting rules.

Keeping the work alive for another group would weaken the guarantee given by
`stop`. Closing every affected group would discard results from other paths.
Waiting for confirmed termination keeps the next work from racing with work
that is still stopping, including when the affected join uses `finish`.

[Waiting modes](../../spec/flow.md#waiting-modes) defines the rule. The
conformance scenarios cover a pending fan-out, a fan-out with active work,
and all joins that receive one branch without a result. They exercise both
running and queued work.
