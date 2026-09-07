"""Closed AgSDL 0.1.0 shapes backed by the pinned Python grammar engine."""
from _reuse import load


CONTRACT = "agsdl-0.1.0"
_legacy = load("_agsdl_010_grammar", "grammar.py")

# Proposal 0013 and AgSDL 0.1.0 have the same shapes. Configure the sole
# edition-sensitive field before any Document validation occurs.
_legacy.CONTRACT = CONTRACT
_document_fields = dict(_legacy.SCHEMAS["Document"][1])
_document_fields["contract"] = _legacy.enum(CONTRACT)
_legacy.SCHEMAS["Document"] = ("record", _document_fields)

KINDS = _legacy.KINDS
SCHEMAS = _legacy.SCHEMAS
array = _legacy.array
enum = _legacy.enum
errors = _legacy.errors
good = _legacy.good
record = _legacy.record
union = _legacy.union

__all__ = [
    "CONTRACT",
    "KINDS",
    "SCHEMAS",
    "array",
    "enum",
    "errors",
    "good",
    "record",
    "union",
]
