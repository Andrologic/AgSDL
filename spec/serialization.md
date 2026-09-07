# Serialization and operations

[Specification index](README.md).

## Notation and shared JSON rules

In the tables, listed fields are required unless followed by `?`. Each record
is closed: no other members are allowed. `T[]` means an array of T, empty unless
a minimum is stated. `Edition[]` has no duplicate Editions, checked by the
owning semantic rule rather than a second P-SHAPE finding. Array order has
meaning only where stated. `map<T>` means an object whose keys are nonempty strings
and values have type T. Map keys such as `__proto__` have ordinary data meaning.
`text` is a nonempty Unicode string; `JSON` is any JSON value, including null.
`uint` is an integer in 0..9007199254740991; `positive` excludes zero. A literal
in quotes is the only permitted string value. Absence is permitted only at `?`;
null is permitted only where explicitly listed or inside JSON. There are no
implicit values, conversions, merge rules or fetching operations.

Parsing accepts one UTF-8 JSON value without BOM, duplicate member names, invalid
Unicode scalar values or trailing non-whitespace content. JSON numbers use the
JSON number grammar; interpreted uint/positive values are checked mathematically
without binary floating-point rounding. Opaque numbers retain their original
lexeme without a magnitude limit. D shape requires the parsed root to be a
Document object; inspect/exchange can inventory or copy other JSON roots.
Object order has no semantic meaning. Arrays
retain order for locations; only steps connected by edges determine scheduling.
Equality of strings compares decoded Unicode scalar sequences exactly, without
case folding, Unicode normalization, URI normalization or version ordering.

| Type | Fields or values |
| --- | --- |
| Key | `scope:text`, `id:text`, `version:text` |
| Edition | `identity:text`, `version:text`; identity matches `[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*` in full |
| Ref | Key, or exactly `dependency:text`, `key:Key` |
| Hash | 64 lowercase hexadecimal characters |
| Kind | One known-kind string below, or exactly `extension:Edition`, `name:text` |
| Ports | map of `"string"`, `"boolean"` or `"json"` |
| Binding | Exactly `input:text`, or exactly `step:text`, `port:text` |

Key equality compares all three fields; a version is an exact opaque identity,
not a range, selector or compatibility promise. Edition equality compares both
fields. A local scope/id pair has one version and record, including the root.
Across supplied documents different versions can coexist. A Ref wrapper always
means external, even when its key shares a local scope. Kind equality compares
the string or all fields of the custom Kind. No custom Kind aliases a core kind.

The closed known-kind list for local definitions is `Agent`, `Principal`,
`Interface`, `Instructions`, `Role`, `Skill`, `ControlFlow`, `Action`, `Resource`,
`ApprovalRequirement`, `Tool`, `Model`, `Environment`, `Runtime`, `Deployment`,
`Policy`, `Memory`, `Knowledge`, `State`, `Topology`, `Protocol`. These names
activate only the checks defined by this edition. Other concepts,
including occurrences, are opaque evidence or declared extensions. Root kinds
are separate. A custom Kind's exact extension Edition must occur once in the
same document's extension array. Generic use/containment can name a custom
Kind; it cannot satisfy a core Agent, Interface or other typed minimum.

## JSON lexical grammar

The following notation uses `*` for zero or more, `?` for optional and `|` for
alternation. Quoted punctuation denotes a literal character. Whitespace `ws` is zero or more of U+0020, U+0009, U+000A or U+000D. The UTF-8 encoding and Unicode
constraints above apply before accepting any value.

```text
artifact = ws value ws
value    = object | array | string | number | "true" | "false" | "null"
object   = "{" ws (member (ws "," ws member)*)? ws "}"
member   = string ws ":" ws value
array    = "[" ws (value (ws "," ws value)*)? ws "]"
number   = "-"? ("0" | nonzero digit*) ("." digit+)? exponent?
exponent = ("e" | "E") ("+" | "-")? digit+
digit    = "0" | nonzero
nonzero  = "1" | "2" | "3" | "4" | "5" | "6" | "7" | "8" | "9"
```

Here `+` means one or more. A string is enclosed in U+0022 quotation marks.
Its content is zero or more unescaped Unicode scalars from U+0020 upward,
excluding U+0022 and U+005C, or escapes. An escape is U+005C followed by one of
`"`, `\`, `/`, `b`, `f`, `n`, `r`, `t`, or `u` and exactly four hexadecimal digits.
Hexadecimal digits are 0-9, a-f and A-F. The short escapes decode to quote,
backslash, slash, backspace, form feed, line feed, carriage return and tab,
respectively. Unicode escapes decode to scalars; high/low surrogate pairs encode
one supplementary scalar and unpaired surrogates fail. Object member names
must be unique after decoding, including escape-equivalent spellings.
There are no comments, trailing commas, NaN, Infinity or leading plus signs.
[Reports](reports.md) defines the first-error byte locations, including the
surrogate lookahead convention. These lexical rules do not round numbers or
normalize decoded strings.

## Operations, phases and supplied inputs

A request is exactly `operation`, `primary` as a byte string, and `annexes` as a
map of byte strings. Operation is one of `inspect`, `validateD`, `validateG`,
`resolveG`, `validateR`, `exchange`, `lossyExchange`. An optional `losses` array
is allowed only with lossyExchange and uses the [Loss record](reports.md). Callers
provide the entire observed input boundary. Byte strings and maps describe the
host API, not a new transport. Annex map keys are exact dependency ids of the
primary document. No other files, URLs, secrets or processes are accessed.

| Operation | Coverage and phase |
| --- | --- |
| inspect | Syntax and D inventory, no semantic validation verdict. Return source tree and opaque slices when parseable; otherwise bytes and syntax finding. |
| validateD | D rules, phase `unresolved-document`. |
| validateG | D prerequisite plus G local rules, phase `unresolved-document`. External G obligations are recorded unchecked, outside this phase's positive scope. |
| resolveG | D prerequisite plus G local rules and direct external G target checks against supplied annexes, phase `resolved-graph`. This is a bounded G graph, not full model resolution. |
| validateR | D prerequisite plus R rules, phase `unresolved-document`; no deployment assessment. |
| exchange | Exact byte preservation and dependency accounting, phase null; independent of semantic validation. |
| lossyExchange | Refuse output, phase null; report all requested losses, or one whole-artifact loss if none supplied. |

The requested Result's unit and phase are fixed, independent of input validity:

| Operation | Result unit | Result phase |
| --- | --- | --- |
| inspect | inspect | null |
| validateD | D | unresolved-document |
| validateG | G | unresolved-document |
| resolveG | G | resolved-graph |
| validateR | R | unresolved-document |
| exchange | exchange | null |
| lossyExchange | exchange | null |

D prerequisite Results always have unit D and phase unresolved-document;
selected-annex G Results have unit G and phase resolved-graph. These assignments
also apply when parsing fails or an operation refuses output.

G/R operations include a separate D result in the report. A failing, unsupported
or inconclusive D result prevents dependent checks from claiming success. It
does not convert unchecked G/R rules into passes. No operation not requested,
apart from this explicit prerequisite, gets a result. G validates all graphs
present, R validates the runtime container present. Absence of either container
is valid and reported `absent`, with its rules not applicable; it grants no
engine selection or graph. No operation executes the described behavior.
