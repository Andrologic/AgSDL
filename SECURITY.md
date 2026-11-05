# Security

AgSDL makes promises about safety: a validator that accepts a document says
that every `deny` and `ask` in it is enforced by the agent's harness. A wrong
answer there gives an agent more rights than its document shows.

## What to report privately

- The reference validator accepts a document whose permissions the harness
  cannot enforce, or one that the specification makes invalid.
- A harness module declares an enforcement, such as `sandbox` or `harness`,
  that the harness does not provide, or that can be bypassed.
- The specification or the schema lets a message, a prompt or a result widen
  an agent's permissions.

Report these through GitHub's
[private vulnerability reporting](https://github.com/Andrologic/AgSDL/security/advisories/new).
Do not open a public issue. Give the document, the harness and its version,
and what the agent could do.

Other defects, such as a wrong diagnostic message or a broken example, are
ordinary issues.

## Supported versions

Only the current edition, in the default branch, receives fixes. Earlier
editions stay available from their tags, unchanged.
