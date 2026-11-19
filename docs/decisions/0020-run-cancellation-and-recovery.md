# 0020. Whole-run cancellation and recovery

[Issue 9](https://github.com/Andrologic/AgSDL/issues/9) describes two
events outside the graph. A person can ask the host to stop a run. The host
can also shut down or lose the state it needs to continue.

A person's stop ends the whole run as `cancelled` once the host confirms
termination. Pending work and requests are withdrawn and the graph stops
routing as soon as the host commits to the stop. Reusing `failed` would
make a deliberate stop indistinguishable from an unhandled step failure.
Running a failure handler could start more work after the person asked the
host to stop. An executor can acknowledge cancellation before its
background activity ends, so the host waits for confirmation.

Hosts can resume after interruption when they can restore execution with
the same guarantees and reconcile any work in flight. An abandoned run
has outcome `interrupted`, which can carry uncertainty about surviving
activity. Treating a recovered session identifier as sufficient could
duplicate an external action or resume an agent without the permissions or
result checks it had before. A recorded stop survives a restart so recovery
can finish cancellation.

This is a host contract. [The flow specification](../../spec/flow.md#stopping-and-recovering-a-run)
defines the rules. The scenario format adds events and outcomes, and the
document format needs no new fields or harness capability claims.

Target 0.4.0. Existing documents and scenarios retain their shapes and
ordinary execution. Hosts and scenario consumers that assume two terminal
outcomes need to handle two new ones. A 0.3.1 patch would suit a clarification
that preserves the runtime contract. This change adds observable states
and obligations for hosts.
