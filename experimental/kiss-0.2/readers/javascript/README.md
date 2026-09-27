# Experimental JavaScript KISS reader

This independent reader implements the six static units of
[proposal 0016](../../../../proposals/0016-kiss-experiment-0.2.md), marker
`agsdl-exp-0016-c2`, frozen at base
`2d79f4d6a7999feb41742705e0abc78377dbe337`. It is experimental, not a normative
0.2 implementation or execution engine. Its processor identity is
`agsdl-experimental/javascript-kiss-reader`, version `0016-c2`.

From the repository root, with Node.js supporting `node --test`:

```sh
node experimental/kiss-0.2/readers/javascript/cli.mjs experimental/kiss-0.2/examples/agent-embedded.json
node --test experimental/kiss-0.2/readers/javascript/reader.test.mjs
```

The CLI accepts exactly one artifact path, reads its original bytes and writes
one candidate Report JSON to stdout. Exit 0 means a complete report was produced,
including negative or unsupported results. Exit 2 reports usage, I/O or resource
failure on stderr with no partial report. No dependencies are installed, and no
network, engine, adapter or external evidence is accessed.

The API is synchronous:

```js
import { readFileSync } from 'node:fs';
import { validate } from './experimental/kiss-0.2/readers/javascript/reader.mjs';
const report = validate(readFileSync('artifact.json'));
```

`validate` accepts Buffer or Uint8Array, returns the Report and throws on host
misuse or a resource failure preventing completion. Syntax failures produce
reports, not API errors. The hash identifies the exact input bytes. The existing
[strict lexical parser](../../../../tooling/readers/javascript/json.mjs) retains
opaque numeric lexemes without floating-point conversion; its numeric wrappers
are never treated as ordinary record objects. No official semantic rules or
Python implementation are imported. The validator returns no rewritten artifact
and makes no round-trip preservation claim.

Shape checks, graph checks and configuration checks live in small separate
modules. Readable projections are separate from complete shape validity so that
independent diagnostics survive malformed siblings. Reports have no aggregate
whole-document verdict. A declared compatibility failure does not imply a
structural failure; a pass proves neither execution readiness nor authenticated
support. Diagnostic arrays and gap causes are unordered collections.

Tests derive their expectations from the candidate, including its exact section
5 witnesses, malformed discriminants, optional absence, strict JSON, governance,
claim independence, configuration coverage and CLI errors. They do not replace
a shared cross-reader corpus or establish Python/JavaScript agreement. The
repository's `check.sh` does not run this new suite; run both commands explicitly
when changing this reader. Resource exhaustion may throw before a report is
available; there is no partial-success or interruption result in this edition.

Candidate c2 explicitly keeps ASSIGN independent of step-id lookup and skips
claim lookup for a completely known empty requirement set. Exact tests cover
both witnesses. DATA projects port names and individual types separately, so
a malformed sibling port does not hide a readable type or binding-name error.
