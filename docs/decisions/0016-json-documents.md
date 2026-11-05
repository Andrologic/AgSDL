# 0016. Documents are strict JSON

Status: accepted.

## Context

A document describes agents, permissions and flows that people review for
safety. Authors of long flows ask for comments and lighter syntax, as YAML or
JSON5 give.

## Decision

A document is UTF-8 JSON, read strictly: no byte order mark, no duplicate
keys, exact numbers ([Document](../../spec/document.md#json-input)). Text for
people goes in `title` and `description`, which every document, agent, step
and composition accepts.

## Reasons

- One document has one reading. Common YAML readers turn `no` or `off` into
  `false` and `1.10` into the number `1.1`, and anchors and merge keys let one
  value hide another: a reviewer could approve a permission that reads
  differently to the host.
- Duplicate keys are refused, because readers disagree on which one wins.
- Every language and every editor reads JSON, and JSON Schema checks it while
  people type.
- `description` fields carry the explanations that comments would, and they
  reach tools and agents too, where comments would be dropped.

## Consequences

Authors who prefer another syntax can write it and convert it to JSON before
validating: the JSON is the document. Rejected: YAML, for the reasons above,
and JSON5 or JSON with comments, which most JSON readers refuse and which
would make strict reading depend on the parser.
