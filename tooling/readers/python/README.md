# Official AgSDL 0.1.0 Python reader

This directory implements the seven static operations defined by the adopted
[AgSDL 0.1.0 specification](../../../spec/README.md). It emits reports with
`contract:"agsdl-0.1.0"` and processor Edition
`agsdl-reference/python-reader` version `0.1.0`.

The implemented feature Editions are:

| Feature identity | Version | Operation |
| --- | --- | --- |
| `agsdl/inspect` | `0.1.0` | `inspect` |
| `agsdl/validateD` | `0.1.0` | `validateD` |
| `agsdl/validateG` | `0.1.0` | `validateG` |
| `agsdl/resolveG` | `0.1.0` | `resolveG` |
| `agsdl/validateR` | `0.1.0` | `validateR` |
| `agsdl/exchange` | `0.1.0` | `exchange` |
| `agsdl/lossyExchange` | `0.1.0` | `lossyExchange` |

The `agsdl_reader` package contains the official grammar, lossless JSON parser
and rule engine. These started as local copies of the modular candidate engine
and are maintained for the current contract only. Runtime imports and reads do
not depend on `experimental/`. No JavaScript reader is loaded or consulted.

For Python callers, add `tooling/readers/python` to the module search path,
then use the qualified package API:

```python
from agsdl_reader import read

response = read("validateD", primary_bytes, annexes={})
```

Distribute `agsdl_reader/` and `cli.py` together to use the reader outside this
repository. No installation or third-party package is needed. Historical
readers retain their own imports and contract markers; importing this package
before or after either historical reader does not configure their modules.
The former unqualified `from reader import read` is replaced by the package API.

Run the standard-library CLI from the repository root without installation:

```sh
python3 tooling/readers/python/cli.py < request.json
```

The request is one JSON object with `operation`, base64 `primary`, and an
`annexes` object mapping direct dependency ids to base64 bytes. An optional
`losses` array is accepted only for `lossyExchange`. The response contains
`report` and `artifacts`. Host, request and resource errors use stderr and exit
status 2. Document findings are returned in the official report with exit
status 0.

Run the focused suite with:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover \
  -s tooling/readers/python -v
```

All input bytes come from the caller. The reader performs no fetching, engine or
adapter execution, approval intake, authentication, evidence retrieval, state
migration or fallback selection. Its results cover only the requested operation
and phase. The final local comparison with the JavaScript reader covers all 137
official cases without a blocked case, failure or mismatch; this is bounded
static evidence, not exhaustive correctness.
