"""Official reader access to the pinned lossless Python JSON implementation."""
from _reuse import load


_legacy = load("_agsdl_010_lossless", "lossless.py")

Parser = _legacy.Parser
SyntaxFailure = _legacy.SyntaxFailure
dumps = _legacy.dumps
integer = _legacy.integer
pointer = _legacy.pointer

__all__ = ["Parser", "SyntaxFailure", "dumps", "integer", "pointer"]
