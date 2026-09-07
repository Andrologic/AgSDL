"""Official, offline AgSDL 0.1.0 Python reader. No described system runs."""
from .grammar import CONTRACT, array, good
from .lossless import integer
from . import core as _core


PROCESSOR = {"identity": "agsdl-reference/python-reader", "version": "0.1.0"}

def _validate_losses(losses):
    if losses is None:
        return
    if not isinstance(losses, list):
        raise ValueError("losses must be an array")
    for loss in losses:
        if (
            not isinstance(loss, dict)
            or set(loss) != {"input", "location", "information", "reason", "permission"}
            or loss["permission"] is not None
            or any(not good("text", loss[name]) for name in ("input", "information", "reason"))
        ):
            raise ValueError("invalid loss record")
        location = loss["location"]
        valid_pointer = (
            isinstance(location, dict)
            and set(location) == {"pointer"}
            and isinstance(location["pointer"], str)
        )
        valid_byte = (
            isinstance(location, dict)
            and set(location) == {"byte"}
            and (
                (
                    type(location["byte"]) is int
                    and 0 <= location["byte"] <= 9007199254740991
                )
                or integer(location["byte"]) is not None
            )
        )
        if not (valid_pointer or valid_byte):
            raise ValueError("invalid loss location")


def read(operation, primary, annexes=None, losses=None):
    """Return an official report and byte artifacts from caller-supplied bytes."""
    annexes = {} if annexes is None else annexes
    if (
        operation not in _core.OPERATIONS
        or not isinstance(primary, bytes)
        or not isinstance(annexes, dict)
        or any(
            not isinstance(name, str) or not name or not isinstance(raw, bytes)
            for name, raw in annexes.items()
        )
    ):
        raise ValueError("invalid AgSDL 0.1.0 request")
    if losses is not None and operation != "lossyExchange":
        raise ValueError("losses only permitted for lossyExchange")
    _validate_losses(losses)

    document = _core.Document(primary)
    input_bytes = {
        "primary": primary,
        **{"annex/" + name: raw for name, raw in sorted(annexes.items())},
    }
    results = []
    artifacts = {}
    loss_records = []
    annex_documents = []
    extra_states = []

    if operation == "inspect":
        result = _core.Result("primary", "inspect", None, ["P-SYNTAX"])
        result.complete("P-SYNTAX")
        if document.syntax:
            result.find(
                "P-SYNTAX",
                detail=str(document.syntax),
                byte=document.syntax.offset,
            )
        results.append(result)
    elif operation in ("exchange", "lossyExchange"):
        rule = "E-PRESERVE" if operation == "exchange" else "E-LOSS"
        result = _core.Result("primary", "exchange", None, [rule])
        if operation == "lossyExchange":
            result.find("E-LOSS", "", "AgSDL 0.1.0 permits no lossy exchange")
            loss_records = losses or [
                {
                    "input": "primary",
                    "location": {"pointer": ""},
                    "information": "unspecified requested loss",
                    "reason": "no omission permission in AgSDL 0.1.0",
                    "permission": None,
                }
            ]
        else:
            result.complete("E-PRESERVE")
            if good(array("Dependency"), document.obj.get("dependencies")):
                _core.dependency_checks(document, annexes, result, exchange=True)
            if result.verdict() == "pass":
                artifacts = dict(input_bytes)
        results.append(result)
    else:
        prerequisite = _core.validate_d(document, annexes)
        results.append(prerequisite)
        if operation == "validateR":
            result = _core.validate_r(document)
            result.parents.append(prerequisite)
            if prerequisite.verdict() != "pass":
                result.block("P-PREREQUISITE", whole=True)
            results.append(result)
            extra_states = document.r_states
        elif operation in ("validateG", "resolveG"):
            graph = _core.GraphValidation(document, annexes, operation == "resolveG")
            graph.check()
            graph.finish()
            result = graph.result
            result.parents.append(prerequisite)
            if prerequisite.verdict() != "pass":
                result.block("P-PREREQUISITE", whole=True)
            annex_documents = [
                value
                for _, value in sorted(graph.loaded.items())
                if value is not None
            ]
            if any(value.d.verdict() != "pass" for value in annex_documents):
                result.block("P-PREREQUISITE", whole=True)
            results += [value.d for value in annex_documents]
            results += [value for _, value in sorted(graph.annex_results.items())]
            results.append(result)
            extra_states = graph.extra_states

    states, slices = _core.inventory(document, operation, extra_states)
    for annex_document in annex_documents:
        annex_states, annex_slices = _core.inventory(
            annex_document,
            "resolveG",
            extra_states,
            primary=False,
        )
        states.extend(annex_states)
        slices.extend(annex_slices)

    report = {
        "contract": CONTRACT,
        "processor": dict(PROCESSOR),
        "operation": operation,
        "inputs": [
            {"id": name, "sha256": _core.digest(raw)}
            for name, raw in input_bytes.items()
        ],
        "results": [result.export() for result in results],
        "inventory": {"tree": document.tree, "states": states, "opaque": slices},
        "losses": loss_records,
        "outputs": [
            {"id": name, "sha256": _core.digest(raw)}
            for name, raw in artifacts.items()
        ],
    }
    return {"report": report, "artifacts": artifacts}


__all__ = ["CONTRACT", "PROCESSOR", "read"]
