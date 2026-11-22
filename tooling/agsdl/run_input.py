"""Isolated run input and operand resolution for hosts."""

from copy import deepcopy
from decimal import Decimal

from . import valueschema
from .schemacheck import pointer


MISSING = object()


class InputError(Exception):
    """A run input or operand cannot be accepted or read."""

    def __init__(self, code, path, message):
        super().__init__(message)
        self.code = code
        self.path = path


def _json(value, path):
    """Reject non-JSON Python values, including non-finite numbers."""
    if value is None or isinstance(value, (bool, int)):
        return
    if isinstance(value, Decimal) and value.is_finite():
        return
    if isinstance(value, str) and not any(0xD800 <= ord(c) <= 0xDFFF for c in value):
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _json(item, path + [index])
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str) or any(0xD800 <= ord(c) <= 0xDFFF for c in key):
                raise InputError("INPUT_INVALID", pointer(path), "invalid object key")
            _json(item, path + [key])
        return
    raise InputError("INPUT_INVALID", pointer(path), "expected a JSON value")


def _select(value, path):
    for index, part in enumerate(path):
        if isinstance(value, dict) and isinstance(part, str) and part in value:
            value = value[part]
        elif (isinstance(value, list) and (not isinstance(part, Decimal) or part.is_finite())
              and valueschema.is_index(part)
              and 0 <= part < len(value)):
            value = value[int(part)]
        else:
            raise InputError("OPERAND", pointer(path[:index + 1]), "cannot read selection")
    if value is MISSING:
        raise InputError("OPERAND", pointer(path), "value is missing")
    return deepcopy(value)


class RunInput:
    """An isolated snapshot of the optional typed input for one run."""

    def __init__(self, value):
        self._value = deepcopy(value) if value is not MISSING else MISSING

    @classmethod
    def accept(cls, flow, value=MISSING):
        """Validate a launch value using an already checked flow declaration.

        JSON numbers use the same int and Decimal representation as jsoninput.
        """
        schema = flow.get("input", MISSING)
        if schema is MISSING:
            if value is not MISSING:
                raise InputError("INPUT_INVALID", "", "flow declares no input")
            return cls(MISSING)
        if value is MISSING:
            raise InputError("INPUT_INVALID", "", "flow input is required")
        try:
            _json(value, [])
            problems = valueschema.validate(value, schema, [])
            if problems:
                path, message = problems[0]
                raise InputError("INPUT_INVALID", path, message)
            return cls(value)
        except RecursionError:
            raise InputError("INPUT_INVALID", "", "input is cyclic or nested too deeply") from None

    @property
    def value(self):
        """Return a copy, or MISSING when the flow has no typed input."""
        return deepcopy(self._value) if self._value is not MISSING else MISSING

    def select(self, path):
        """Read a path from the snapshot."""
        return _select(self._value, path)

    def resolve_arguments(self, arguments, previous=MISSING):
        """Resolve literal, run-input and previous-step operands."""
        resolved = {}
        for name, operand in arguments.items():
            if "input" in operand:
                resolved[name] = self.select(operand["input"])
            elif "path" in operand:
                resolved[name] = _select(previous, operand["path"])
            else:
                resolved[name] = deepcopy(operand["value"])
        return resolved

    def bind_resources(self, resources):
        """Inline input resources while leaving other sources to the host."""
        bound = {}
        for name, resource in resources.items():
            if "input" in resource:
                bound[name] = {"value": self.select(resource["input"]),
                               "mediaType": resource.get("mediaType", "application/json")}
            else:
                bound[name] = deepcopy(resource)
        return bound
