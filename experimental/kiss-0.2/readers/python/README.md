# Experimental Python reader

This standard-library-only reader implements the static `validate` operation
of [candidate 0016](../../../../proposals/0016-kiss-experiment-0.2.md), marker
`agsdl-exp-0016-c1`. It reports the six candidate units independently. It does
not execute graphs, discover services, or verify capability evidence.

From the repository root:

```sh
python3 experimental/kiss-0.2/readers/python/cli.py experimental/kiss-0.2/examples/agent-embedded.json
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s experimental/kiss-0.2/readers/python -v
```

The CLI accepts exactly one artifact path. It writes one JSON report to stdout
and exits 0 whenever reporting completes, including negative findings. Usage,
input I/O and resource failures exit 2 without a report.

For the Python API, put this directory on the module search path and import
`validate` from `reader`. `validate(primary_bytes)` accepts bytes and returns a
report dictionary. Host misuse raises `TypeError`; exhausted memory or recursion
raises a resource error. The report hashes the original bytes, not reserialized
JSON. Diagnostics and gaps are separate; their array order is not meaningful.

The reader imports only the existing lossless lexical parser from
`tooling/readers/python/agsdl_reader/lossless.py`. Keep the repository layout
when running it. Candidate semantics are implemented locally, independently of
other readers. Tests record contract expectations for all 14 examples and
adversarial inputs. This experimental implementation does not change the
published AgSDL 0.1 contract or establish runtime support.
