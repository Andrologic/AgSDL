#!/usr/bin/env python3
"""Read one AgSDL 0.1.0 request from stdin and write one response."""
import base64
import binascii
import sys

from agsdl_reader.lossless import Parser, SyntaxFailure, dumps
from agsdl_reader import read


def main():
    try:
        request = Parser(sys.stdin.buffer.read()).parse()
        allowed = {"operation", "primary", "annexes", "losses"}
        required = {"operation", "primary", "annexes"}
        if not isinstance(request, dict) or not required <= request.keys() or request.keys() - allowed:
            raise ValueError(
                "request fields must be operation, primary, annexes and optional losses"
            )
        if (
            not isinstance(request["primary"], str)
            or not isinstance(request["annexes"], dict)
            or any(not isinstance(value, str) for value in request["annexes"].values())
        ):
            raise ValueError("primary and annexes must contain base64 strings")
        if "losses" in request and not isinstance(request["losses"], list):
            raise ValueError("losses must be an array when supplied")
        response = read(
            request["operation"],
            base64.b64decode(request["primary"], validate=True),
            {
                name: base64.b64decode(value, validate=True)
                for name, value in request["annexes"].items()
            },
            request.get("losses"),
        )
        response["artifacts"] = {
            name: base64.b64encode(raw).decode("ascii")
            for name, raw in response["artifacts"].items()
        }
        sys.stdout.write(dumps(response) + "\n")
        return 0
    except (ValueError, TypeError, binascii.Error, SyntaxFailure, RecursionError) as error:
        sys.stderr.write(type(error).__name__ + ": " + str(error) + "\n")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
