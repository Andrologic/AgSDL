# Independent modular JavaScript reader

This experimental reader implements `proposal-0013-candidate-1` from
[proposal 0013](../../../../proposals/0013-modular-mvp-contract.md), integrated
at contract revision `280347eec4e2e051d296f9271bfccc86c98d4d40`. The proposal
file SHA-256 pinned by the corpus is
`7c9e2aa8e5c6d7c8c0b419aaf3afb666f9ad3510057c98dc7f0f3ac3e904773b`.
The inherited proposal 0012 source is revision
`009a51eb301688f06d29bb7e2f1784e3c4a4cc98`, SHA-256
`9f0ead2cbe9a5e158e3017f1ba692cbd3cba69e9240048130dc49c19c1222e07`.
Neither proposal is normative or adopted.

The implementation reuses the historical JavaScript reader's lossless JSON
scanner and inherited D implementation. A contract parameter keeps D source
validation exact for each edition. G and R have separate modular shapes and
validation paths. The reader never changes input bytes or relabels a
candidate-2 report as candidate-1.

## Run

Node.js and its standard library are sufficient.

```sh
node experimental/modular-candidate-1/readers/javascript/cli.mjs < request.json
node --test experimental/modular-candidate-1/readers/javascript/reader.test.mjs
```

The CLI accepts exactly one JSON request on stdin. `primary` and each `annexes`
value are canonical base64 bytes. `operation` is one of `inspect`, `validateD`,
`validateG`, `resolveG`, `validateR`, `exchange` or `lossyExchange`. Optional
`losses` is accepted only for `lossyExchange`. Output is `{report,artifacts}`;
host-request errors use stderr and exit status 2.

The reader is offline and direct-annex only. It executes no described Agent,
engine, adapter, approval or parameters. Compatibility findings retain declared
claims and evidence identities; they do not establish support, readiness,
permission or evidence authenticity. Missing selections and choices never
trigger fallback. Exact exchange copies supplied bytes or refuses output.

## Verify

```sh
node --test experimental/readers/javascript/reader.test.mjs
node --test experimental/modular-candidate-1/readers/javascript/reader.test.mjs
python3 experimental/modular-candidate-1/compare-readers.py \
  --reader '["javascript-a","node","experimental/modular-candidate-1/readers/javascript/cli.mjs"]' \
  --reader '["javascript-b","node","experimental/modular-candidate-1/readers/javascript/cli.mjs"]' \
  --reports /tmp/agsdl-modular-javascript
./scripts/check.sh
git diff --check
```

Using two labels for one command validates this reader twice against every
targeted corpus assertion. It does not establish independence or agreement
between languages. The 26-case corpus is a bounded witness set, so the local
tests also cover marker separation, partial prerequisites, duplicate operation
selection, outbound operations, additional content, multi-node Skill cycles and
host-request errors.
