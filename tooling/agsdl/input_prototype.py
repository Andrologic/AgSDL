"""Inspect declared run inputs and preview MCP arguments without starting a run."""

import argparse
from decimal import Decimal
import json
import sys

from . import jsoninput
from .input_schema import validate_prototype
from .run_input import InputError, MISSING, RunInput
from .validator import MODULES_DIR, ModuleError, load_modules


def json_text(value):
    """Render parsed JSON without rounding Decimal values through a float."""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return "{" + ", ".join(json.dumps(k) + ": " + json_text(v) for k, v in value.items()) + "}"
    if isinstance(value, list):
        return "[" + ", ".join(json_text(item) for item in value) + "]"
    return json.dumps(value)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--modules", default=MODULES_DIR, help="directory of harness modules")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check", help="validate the authored document")
    check.add_argument("document")
    preview = commands.add_parser("preview", help="check a launch value and optionally resolve a call")
    preview.add_argument("document")
    preview.add_argument("--input", metavar="JSON", help="the JSON value supplied at launch")
    preview.add_argument("--call", metavar="STEP", help="top-level MCP call to preview")
    preview.add_argument("--previous", metavar="JSON", help="sample output of the preceding step")
    args = parser.parse_args(argv)
    if args.command == "preview" and args.previous is not None and args.call is None:
        parser.error("--previous requires --call")

    try:
        document = jsoninput.load(args.document)
        report = validate_prototype(document, load_modules(args.modules))
        if args.command == "check" or not report.valid:
            print(json.dumps(report.as_json(), indent=2))
            return 0 if report.valid else 1
        flow = document.get("flow")
        if flow is None:
            parser.error("preview requires a document with a flow")
        supplied = MISSING if args.input is None else jsoninput.parse_bytes(args.input.encode())
        run_input = RunInput.accept(flow, supplied)
        result = {"launch": "accepted"}
        if args.call is not None:
            step = flow["steps"].get(args.call)
            if not step or step["type"] != "call" or "mcp" not in step:
                parser.error("--call must name a top-level MCP call")
            previous = MISSING if args.previous is None else jsoninput.parse_bytes(args.previous.encode())
            result["arguments"] = run_input.resolve_arguments(step.get("arguments", {}), previous)
        print(json_text(result))
        return 0
    except InputError as error:
        result = {"code": error.code, "path": error.path, "message": str(error)}
        if error.code == "INPUT_INVALID":
            result["launch"] = "rejected"
        print(json.dumps(result))
        return 1
    except (OSError, ModuleError, jsoninput.InputError, ValueError) as error:
        print(f"agsdl.input_prototype: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
