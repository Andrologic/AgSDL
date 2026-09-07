"""Compatibility facade; prefer the qualified agsdl_reader package API."""
from agsdl_reader import CONTRACT, PROCESSOR, read

__all__ = ['CONTRACT', 'PROCESSOR', 'read']
