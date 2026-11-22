"""Static checks for the experimental declared run input contract."""

import copy

from . import valueschema
from .graph import route_items, step_routes
from .schemacheck import SchemaChecker
from .validator import Checker, DOCUMENT_SCHEMA, Report, load_modules, validate_document

PROTOTYPE_CONTRACT = "agsdl-prototype-run-input"


def _prototype_schema():
    root = copy.deepcopy(DOCUMENT_SCHEMA.root)
    root["properties"]["contract"]["const"] = PROTOTYPE_CONTRACT
    root["properties"]["flow"]["properties"]["input"] = {"$ref": "#/$defs/valueSchema"}
    selection = {"type": "object", "required": ["input"], "additionalProperties": False,
                 "properties": {"input": {"$ref": "#/$defs/path"}}}
    root["$defs"]["operand"]["oneOf"].append(selection)
    resource = copy.deepcopy(selection)
    resource["properties"]["mediaType"] = {"$ref": "#/$defs/mediaType"}
    root["$defs"]["message"]["properties"]["resources"]["additionalProperties"]["oneOf"].append(resource)
    return SchemaChecker(root)


PROTOTYPE_SCHEMA = _prototype_schema()


class PrototypeReport(Report):
    def as_json(self):
        result = super().as_json()
        result["contract"] = PROTOTYPE_CONTRACT
        return result


def _input_reads(document, report):
    flow = document.get("flow", {})
    schema = flow.get("input")
    if schema is not None:
        for where, message in valueschema.consistency(schema, ["flow", "input"]):
            report.error("SCHEMA", where, message)

    def check(path, where, in_composition):
        if in_composition:
            report.error("MESSAGE_PATH", where, "run input cannot be read inside a composition")
        elif schema is None:
            report.error("MESSAGE_PATH", where, "flow has no declared input")
        else:
            _, reason = valueschema.descend(schema, path)
            if reason:
                report.error("MESSAGE_PATH", where, reason)

    def routes(route, where, in_composition):
        for _, _, message, at, _ in route_items(route, where):
            if message:
                for name, resource in message.get("resources", {}).items():
                    if "input" in resource:
                        check(resource["input"], at + ["message", "resources", name, "input"], in_composition)

    scopes = [(flow, ["flow"], False)] if flow else []
    scopes += [(body, ["compositions", name], True)
               for name, body in document.get("compositions", {}).items()]
    for scope, where, in_composition in scopes:
        for name, step in scope["steps"].items():
            at = where + ["steps", name]
            for arg, operand in step.get("arguments", {}).items():
                if "input" in operand:
                    check(operand["input"], at + ["arguments", arg, "input"], in_composition)
            for _, _, route, route_at in step_routes(step, at):
                routes(route, route_at, in_composition)
        if not in_composition and "onError" in scope:
            routes(scope["onError"], where + ["onError"], False)

    # Resolve the first work through compositions, even if a later loop has
    # an incoming edge to that same call. The initial activation has no output.
    if schema is not None:
        scope, where, seen = flow, ["flow"], set()
        while scope.get("entry") in scope.get("steps", {}):
            name = scope["entry"]
            step = scope["steps"][name]
            at = where + ["steps", name]
            if step["type"] == "call":
                for arg, operand in step.get("arguments", {}).items():
                    if "path" in operand:
                        report.error("MESSAGE_PATH", at + ["arguments", arg, "path"],
                                     "the first activation has no previous output")
            if step["type"] != "compose" or step["composition"] in seen:
                break
            name = step["composition"]
            seen.add(name)
            scope = document.get("compositions", {}).get(name, {})
            where = ["compositions", name]


def validate_prototype(document, modules=None):
    """Validate the opt-in prototype, or use the ordinary validator unchanged."""
    if not isinstance(document, dict) or document.get("contract") != PROTOTYPE_CONTRACT:
        return validate_document(document, modules)
    report = PrototypeReport()
    modules = load_modules() if modules is None else modules
    problems = PROTOTYPE_SCHEMA.check(document)
    if problems:
        for where, message in problems:
            report.error("SHAPE", where, message)
        return report
    _input_reads(document, report)
    Checker(document, modules, report).run()
    return report
