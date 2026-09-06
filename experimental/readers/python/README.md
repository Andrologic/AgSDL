# Independent Python candidate reader

Experimental implementation of [proposal 0012, candidate-2](../../../proposals/0012-minimal-0.1.0-contract.md).
This is not an adopted AgSDL implementation or a conformance claim.

Semantic source: repository revision
`b02c7933f33e439bc45c94e01e96dfb7b77c6eb4`, proposal file SHA-256
`872e5fa38f3e52828e64678c8a212ff5591f8bb21d5f34a24a3ebc768cdfce8e`.
The Python implementation and its tests were written from that text without
reading or importing another reader, a shared validator engine or SDK.

## Local CLI

Python 3 with the standard library is sufficient. From the repository root:

```sh
python3 experimental/readers/python/cli.py < request.json > response.json
python3 -m unittest discover -s experimental/readers/python -v
```

The CLI reads exactly one JSON request on stdin. For example, inspecting the
bytes `{}` uses:

```json
{"operation":"inspect","primary":"e30=","annexes":{}}
```

Fields are `operation`, base64 `primary`, and `annexes`, an object mapping
explicit dependency ids to base64 bytes. `losses` is an optional Loss array only
for `lossyExchange`. The response is exactly `report` and `artifacts`; artifact
values are base64 under `primary` or `annex/<dependencyId>`. Inputs and outputs
are entirely supplied by the caller. No path, URL, secret, plugin or engine is
loaded from the described document.

The seven operations are `inspect`, `validateD`, `validateG`, `resolveG`,
`validateR`, `exchange` and `lossyExchange`. Document invalidity is returned in
the report with CLI exit status 0. Invalid request envelopes, invalid base64 or
host resource failures use stderr and exit status 2, without a fabricated
candidate validation result.

## Python API and lossless values

Put this directory on the Python module path, then call:

```python
from reader import read
from lossless import dumps

response = read("inspect", b"{}", {})
report_json = dumps(response["report"])
```

`read(operation, primary_bytes, annex_bytes_by_id, losses=None)` returns a
report plus raw byte artifacts. `inventory.tree` uses `lossless.Number` for JSON
numbers, preserving their original lexeme without a floating-point conversion.
Use `lossless.dumps` when serializing reports; the standard `json.dumps` does
not encode this lossless number type. The CLI already uses the lossless writer.
Opaque slices use zero-based, half-open UTF-8 byte spans into the original
inputs. Exact exchange returns those inputs unchanged, including invalid JSON.

## Covered checks and limits

- D checks closed shapes, scoped identity, owners, relations, local cycles,
  Agent minima and the single Fragment Interface deferral, exports, extension
  modes, declared dependency accounting and supplied hashes.
- G checks all supplied graphs, typed local targets and selected Interface and
  ApprovalRequirement payloads, finite paths, Boolean conditions, port equality,
  success-edge data availability and approval-only access to protected invokes.
  `resolveG` checks supplied direct annexes and their D results, exported targets
  and selected-key collisions. Transitive selected references yield unsupported;
  they are never fetched.
- R checks declarations, subjects, selection fields and evidence-claim links.
  It retains custom engine names and unverified assertions. Its report excludes
  evidence assessment, readiness and execution.
- Inspection, validation and byte preservation have separate rules and verdicts.
  Lossy exchange always refuses output. Semantic extension interpretation is
  unsupported as prescribed by candidate-2; annotation-only modes are bounded
  to the candidate's core permission.

Tests cover positive and negative witnesses, syntax byte locations, decoded
member duplicates, Unicode surrogates, exact safe integers, very large opaque
numbers, partial malformed records, unknown information, phase differences,
CLI preservation and direct versus unavailable/transitive dependencies. Shared
corpus comparison with a second implementation has not been run in this lot.
Passing these tests is implementation evidence for these witnesses only.

The reader performs static checks, not authentication, approval intake,
authorization, engine execution or product integration. Resource exhaustion
can terminate a request; deeply nested JSON is subject to the Python host's
recursion limit and memory availability. Such a host error is not a pass or a
new AgSDL language restriction. No source-network or runtime evidence is claimed.


Pending candidate clarification: unpaired surrogate locations
-----------------------------------------------------------

The JSON byte sequences `"\ud800"` (hex `225c756438303022`) and
`"\ud800\u0041"` (hex `225c75643830305c753030343122`) are rejected with
P-SYNTAX at byte 1, the initial escape. Candidate-2 does not explicitly settle
whether this location should instead identify the byte revealing that a valid
pair cannot follow. For the first witness that would be the closing quote at
byte 7; for the second, the first incompatible low-surrogate hexadecimal digit
at byte 9. Recommendation: specify these witnesses, together with truncation at
EOF, before comparison or adoption. This reader retains its existing escape-start
convention pending that decision; it does not amend the proposal.
