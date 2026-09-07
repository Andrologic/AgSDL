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

The reader reuses the repository's pinned modular candidate Python rule engine.
The official grammar adapter sets the `agsdl-0.1.0` Document marker before
parsing or validation. The official `read` function invokes the D, G and R rule
operations directly and constructs a new official report. It never invokes the
experimental `read` entry point and never relabels an experimental report or
input. The historical source and corpus stay unchanged. No JavaScript reader is
loaded or consulted.

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
and phase. Full official corpus comparison is a separate integration step.
