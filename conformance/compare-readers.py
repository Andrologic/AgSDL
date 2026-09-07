#!/usr/bin/env python3
"""Compare official 0.1.0 reports with normative corpus oracles."""

import argparse
import base64
import importlib.util
import json
import math
from pathlib import Path
import re
import sys


ROOT = Path(__file__).resolve().parent
SUPPORT_PATH = ROOT / "report_support.py"
sys.dont_write_bytecode = True
SPEC = importlib.util.spec_from_file_location("agsdl_json_report_neutral", SUPPORT_PATH)
neutral = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(neutral)

CONTRACT = "agsdl-0.1.0"
FORMAT = "agsdl-conformance-corpus-1"
SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
OPERATIONS = neutral.OPERATIONS
D_RULES = neutral.D_RULES
G_RULES = neutral.G_RULES
R_RULES = {"P-SHAPE", "X-MODE", "R-SELECTION", "R-BINDING", "R-TOOL", "R-CONTENT", "R-COMPATIBILITY"}
BOUNDARY = neutral.BOUNDARY
R_BOUNDARY = neutral.R_BOUNDARY
RANK = neutral.RANK
ASSESSMENTS = {"not-provided", "incompatible", "unknown", "declared-supported", "blocked"}
ASSESSMENT_STATES = {
    "not-provided": "absent",
    "incompatible": "declared",
    "unknown": "unknown",
    "declared-supported": "unchecked",
    "blocked": "unchecked",
}


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def record(value, fields):
    demand(isinstance(value, dict) and set(value) == set(fields.split()), "closed record fields: " + fields)


def text(value, empty=False):
    neutral.text(value, empty=empty)


def load(value):
    return neutral.load(value)


def canonical(value):
    return neutral.canonical(value)


def contains(items, wanted):
    return neutral.contains(items, wanted)


def rules_for(result, operation):
    if result["unit"] == "D":
        return D_RULES
    if result["unit"] == "G":
        if result["input"] != "primary":
            return {"P-SHAPE", "G-TARGET"}
        return G_RULES | ({"G-RESOLVE"} if operation == "resolveG" else set())
    if result["unit"] == "R":
        return R_RULES
    if result["unit"] == "inspect":
        return {"P-SYNTAX"}
    return {"E-LOSS"} if operation == "lossyExchange" else {"E-PRESERVE"}


def at_pointer(tree, path):
    value = tree
    for token in path.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def missing_child(path, parsed):
    if parsed is None or not path or path in parsed.spans:
        return False
    parent, _, token = path.rpartition("/")
    if parent not in parsed.spans:
        return False
    value = at_pointer(parsed.tree, parent)
    return isinstance(value, dict) or (isinstance(value, list) and re.fullmatch(r"0|[1-9][0-9]*", token) is not None)


def validate_location(location, input_id, source, parsed, allow_missing=False, allow_unobservable=False):
    demand(isinstance(location, dict) and len(location) == 1, "closed Location")
    if "pointer" in location:
        neutral.pointer(location["pointer"])
        observed = parsed[input_id] is not None and location["pointer"] in parsed[input_id].spans
        missing = allow_missing and parsed[input_id] is not None and missing_child(location["pointer"], parsed[input_id])
        demand(observed or missing or allow_unobservable, "location is not an observable source record")
    else:
        record(location, "byte")
        demand(neutral.uint(location["byte"]) <= len(source[input_id]), "byte location outside input")


def assessment_location(state, tree):
    if state["input"] != "primary" or not isinstance(tree, dict):
        return False
    match = re.fullmatch(
        r"/runtime/configurations/(0|[1-9][0-9]*)/agents/(0|[1-9][0-9]*)(?:/tools/(0|[1-9][0-9]*))?",
        state["pointer"],
    )
    runtime = tree.get("runtime")
    if match is None or not isinstance(runtime, dict) or not isinstance(runtime.get("selected"), str):
        return False
    configurations = runtime.get("configurations")
    if not isinstance(configurations, list):
        return False
    index = int(match.group(1))
    selected = [position for position, item in enumerate(configurations)
                if isinstance(item, dict) and item.get("id") == runtime["selected"]]
    if selected != [index]:
        return False
    configuration = configurations[index]
    agents = configuration.get("agents")
    agent_index = int(match.group(2))
    if not isinstance(agents, list) or agent_index >= len(agents) or not isinstance(agents[agent_index], dict):
        return False
    if match.group(3) is None:
        return True
    tools = agents[agent_index].get("tools")
    tool_index = int(match.group(3))
    return isinstance(tools, list) and tool_index < len(tools) and isinstance(tools[tool_index], dict)


def assessment_state(state, tree):
    return state["detail"] in ASSESSMENTS and assessment_location(state, tree)


def state_key(state, tree):
    value = {key: state[key] for key in ("input", "pointer", "state")}
    if assessment_state(state, tree):
        value["detail"] = state["detail"]
    return value


def result_rows(report):
    return [{key: result[key] for key in ("input", "unit", "phase", "verdict")} for result in report["results"]]


def finding_rows(report):
    return [dict(input=result["input"], unit=result["unit"], phase=result["phase"], rule=finding["rule"], location=finding["location"], outcome=finding["outcome"])
            for result in report["results"] for finding in result["findings"]]


def check_rows(report):
    return [dict(input=result["input"], unit=result["unit"], phase=result["phase"], **check)
            for result in report["results"] for check in result["checks"]]


def validate_report(response, case, source):
    record(response, "report artifacts")
    report = response["report"]
    operation = case["operation"]
    unit, phase = OPERATIONS[operation]
    record(report, "contract processor operation inputs results inventory losses outputs")
    demand(report["contract"] == CONTRACT and report["operation"] == operation, "report edition/operation mismatch")
    neutral.edition(report["processor"])
    for field in ("inputs", "results", "losses", "outputs"):
        demand(isinstance(report[field], list), field + " must be an array")
    input_order = ["primary"] + sorted(name for name in source if name != "primary")
    expected_inputs = [{"id": name, "sha256": neutral.digest(source[name])} for name in input_order]
    demand(report["inputs"] == expected_inputs, "input order/hash/boundary mismatch")
    for item in report["outputs"]:
        record(item, "id sha256")
        text(item["id"])
        demand(isinstance(item["sha256"], str) and neutral.HASH.fullmatch(item["sha256"]), "invalid output hash")

    parsed = {}
    for name, data in source.items():
        try:
            parsed[name] = neutral.JsonSource(data)
        except (ValueError, UnicodeError, RecursionError):
            parsed[name] = None

    identities = []
    for result in report["results"]:
        record(result, "input unit phase verdict findings checks")
        demand(result["input"] in source and result["verdict"] in RANK, "Result input or verdict")
        demand(isinstance(result["findings"], list) and isinstance(result["checks"], list), "Result arrays")
        identities.append((result["input"], result["unit"], result["phase"]))
    demand(len(identities) == len(set(identities)), "duplicate Result")
    demand(identities and identities[-1] == ("primary", unit, phase), "requested Result missing or not last")
    if unit not in {"G", "R"}:
        demand(identities == [("primary", unit, phase)], "unrequested Result")
    else:
        demand(identities[0] == ("primary", "D", "unresolved-document"), "missing primary D prerequisite")
        if unit == "R" or operation != "resolveG":
            demand(len(identities) == 2, "unexpected prerequisite Result")
        else:
            middle = identities[1:-1]
            annex_d = [name for name, item_unit, item_phase in middle if item_unit == "D" and item_phase == "unresolved-document"]
            annex_g = [name for name, item_unit, item_phase in middle if item_unit == "G" and item_phase == "resolved-graph"]
            demand(middle == [(name, "D", "unresolved-document") for name in sorted(annex_d)] + [(name, "G", "resolved-graph") for name in annex_g], "annex Result ordering")
            demand(set(annex_g) <= set(annex_d), "annex G missing D prerequisite")

    for result in report["results"]:
        input_id = result["input"]
        executed = rules_for(result, operation)
        boundaries = dict(BOUNDARY) if result["unit"] in {"D", "G", "R"} else {}
        if result["unit"] == "R":
            boundaries.update(R_BOUNDARY)
        prerequisites = []
        if result["unit"] in {"G", "R"}:
            if input_id == "primary":
                prerequisites = [item for item in report["results"][:report["results"].index(result)] if item["unit"] in {"D", "G"}]
            else:
                prerequisites = [item for item in report["results"] if item["unit"] == "D" and item["input"] == input_id]
        d_failed = input_id == "primary" and result["unit"] in {"G", "R"} and any(
            item["unit"] == "D" and item["verdict"] != "pass" for item in prerequisites
        )
        allowed = executed | set(boundaries) | ({"P-PREREQUISITE"} if d_failed else set())
        seen = []
        for check in result["checks"]:
            record(check, "rule state locations")
            demand(check["rule"] in allowed and check["state"] in {"completed", "blocked", "excluded"}, "Check rule/state outside scope")
            demand(isinstance(check["locations"], list), "Check locations")
            seen.append((check["rule"], check["state"]))
            for location in check["locations"]:
                explicit_missing = check["state"] == "excluded" and input_id == "primary" and (
                    result["unit"] == "G" and location == {"pointer": "/graphs"}
                    or result["unit"] == "R" and location == {"pointer": "/runtime"}
                )
                fixed_boundary = check["rule"] in boundaries and location == {"pointer": boundaries[check["rule"]]}
                unparsed_root_block = parsed[input_id] is None and check["state"] == "blocked" and location == {"pointer": ""}
                validate_location(
                    location, input_id, source, parsed,
                    allow_missing=explicit_missing,
                    allow_unobservable=fixed_boundary or unparsed_root_block,
                )
            neutral.unique(check["locations"], "Check location")
            demand(check["locations"] == sorted(check["locations"], key=neutral.loc_key), "Check locations not sorted")
            demand(check["locations"] == [] if check["state"] == "completed" else bool(check["locations"]), "Check locations/state mismatch")
            if check["rule"] in boundaries:
                demand(check == {"rule": check["rule"], "state": "excluded", "locations": [{"pointer": boundaries[check["rule"]]}]}, "documentary exclusion mismatch")
            if check["rule"] == "P-PREREQUISITE":
                demand(check == {"rule": "P-PREREQUISITE", "state": "blocked", "locations": [{"pointer": ""}]}, "prerequisite Check mismatch")
        demand(len(seen) == len(set(seen)) and seen == sorted(seen), "duplicate or unsorted Checks")
        demand({rule for rule, _ in seen} == allowed, "missing rule coverage in Result")

        finding_keys = []
        for finding in result["findings"]:
            record(finding, "rule location outcome details")
            text(finding["details"])
            demand(finding["rule"] in executed, "Finding rule outside scope")
            demand(finding["outcome"] in {"fail", "unsupported", "inconclusive", "deferred"}, "Finding outcome")
            validate_location(
                finding["location"], input_id, source, parsed,
                allow_unobservable=(
                    finding["rule"] == "E-LOSS"
                    and finding["location"] == {"pointer": ""}
                ),
            )
            demand((finding["rule"], "completed") in seen, "Finding has no completed Check")
            demand(("byte" in finding["location"]) == (finding["rule"] == "P-SYNTAX"), "Finding location kind")
            finding_keys.append((finding["rule"], canonical(finding["location"]), finding["outcome"]))
        demand(len(finding_keys) == len(set(finding_keys)), "duplicate Finding tuple")
        syntax_failure = any(
            item["input"] == input_id and item["unit"] in {"D", "inspect"}
            and any(finding["rule"] == "P-SYNTAX" and finding["outcome"] == "fail" for finding in item["findings"])
            for item in report["results"]
        )
        if syntax_failure:
            for rule in executed - {"P-SYNTAX"}:
                demand([state for candidate, state in seen if candidate == rule] == ["blocked"], "downstream Check not blocked after syntax failure")
        prior_rank = [RANK[item["verdict"]] for item in prerequisites]
        rank = max([0, *prior_rank, *[RANK[item["outcome"]] for item in result["findings"] if item["outcome"] != "deferred"], *[1 for _, state in seen if state == "blocked"]])
        demand(RANK[result["verdict"]] == rank, "Result verdict disagrees with evidence")

    inventory = report["inventory"]
    record(inventory, "tree states opaque")
    demand(isinstance(inventory["states"], list) and isinstance(inventory["opaque"], list), "inventory arrays")
    primary_tree = parsed["primary"].tree if parsed["primary"] else None
    demand(canonical(inventory["tree"]) == canonical(primary_tree), "inventory tree differs from source")
    observed_inputs = {"primary"} | {
        result["input"] for result in report["results"]
        if operation == "resolveG" and result["unit"] == "D"
    }
    assessment_keys = {}
    for state in inventory["states"]:
        record(state, "input pointer state detail")
        demand(state["input"] in observed_inputs and state["state"] in {"absent", "unknown", "declared", "unchecked"}, "State scope/domain")
        neutral.pointer(state["pointer"])
        text(state["detail"])
        dependency_probe = (
            operation in {"inspect", "exchange", "lossyExchange"}
            and state["input"] == "primary"
            and state["pointer"] == "/dependencies"
            and state["state"] == "unchecked"
            and (parsed["primary"] is None or not isinstance(primary_tree, dict))
        )
        virtual_missing = (
            state["state"] == "absent"
            and parsed[state["input"]] is not None
            and missing_child(state["pointer"], parsed[state["input"]])
            and (
                (state["input"] in observed_inputs
                    and state["pointer"] in {"/graphs", "/runtime"})
                or (state["input"] == "primary"
                    and operation in {"inspect", "exchange", "lossyExchange"}
                    and state["pointer"] == "/dependencies")
                or (state["input"] == "primary" and operation == "validateR"
                    and state["pointer"] == "/runtime/selected")
                or (state["input"] == "primary" and operation == "validateR" and re.fullmatch(
                    r"/runtime/configurations/(0|[1-9][0-9]*)/agents/(0|[1-9][0-9]*)/tools/(0|[1-9][0-9]*)/selected",
                    state["pointer"],
                ) is not None)
            )
        )
        demand(
            dependency_probe or virtual_missing
            or (parsed[state["input"]] is not None and (
                state["pointer"] in parsed[state["input"]].spans
            )),
            "State pointer is not observable",
        )
        key = canonical(state_key(state, primary_tree))
        if assessment_state(state, primary_tree):
            demand(state["state"] == ASSESSMENT_STATES[state["detail"]], "assessment detail/state mismatch")
            assessment_key = (state["input"], state["pointer"])
            demand(assessment_key not in assessment_keys or assessment_keys[assessment_key] == key,
                   "conflicting aggregate assessment States")
            assessment_keys[assessment_key] = key
    for input_id in observed_inputs:
        tree = parsed[input_id].tree if parsed[input_id] else None
        if isinstance(tree, dict):
            for field in ("graphs", "runtime"):
                selected = input_id == "primary" and (
                    (field == "graphs" and unit == "G")
                    or (field == "runtime" and unit == "R")
                )
                expected_state = "absent" if field not in tree else "declared" if selected else "unchecked"
                entries = [
                    state for state in inventory["states"]
                    if state["input"] == input_id and state["pointer"] == "/" + field
                ]
                demand(
                    len(entries) == 1 and entries[0]["state"] == expected_state,
                    "container State missing or inconsistent",
                )
    if operation in {"inspect", "exchange", "lossyExchange"}:
        dependencies = [
            state for state in inventory["states"]
            if state["input"] == "primary" and state["pointer"] == "/dependencies"
        ]
        demand(len(dependencies) == 1, "dependency inventory State missing")
        if parsed["primary"] is None or not isinstance(primary_tree, dict):
            demand(dependencies[0]["state"] == "unchecked", "unreadable dependency inventory mismatch")
        elif "dependencies" not in primary_tree:
            demand(dependencies[0]["state"] == "absent", "absent dependency inventory mismatch")
        elif not isinstance(primary_tree["dependencies"], list):
            demand(dependencies[0]["state"] == "unchecked", "malformed dependency inventory mismatch")
    slices_by_input = {name: [] for name in source}
    slice_keys = set()
    for item in inventory["opaque"]:
        record(item, "input pointer start end")
        demand(item["input"] in observed_inputs and parsed[item["input"]] is not None, "Slice input")
        neutral.pointer(item["pointer"])
        start, end = neutral.uint(item["start"]), neutral.uint(item["end"])
        demand(parsed[item["input"]].spans.get(item["pointer"]) == (start, end), "Slice is not exact source span")
        key = (item["input"], item["pointer"])
        demand(key not in slice_keys, "duplicate Slice")
        slice_keys.add(key)
        slices_by_input[item["input"]].append((start, end))
    for spans in slices_by_input.values():
        ordered = sorted(spans)
        demand(all(left[1] <= right[0] for left, right in zip(ordered, ordered[1:])), "overlapping Slices")
    for state in inventory["states"]:
        for item in inventory["opaque"]:
            if item["pointer"] and state["input"] == item["input"]:
                demand(
                    not state["pointer"].startswith(item["pointer"] + "/"),
                    "State discovered inside opaque Slice",
                )
        for parent in inventory["states"]:
            if (parent["input"] == state["input"] and parent["state"] == "absent"
                    and not assessment_state(parent, primary_tree)):
                demand(
                    not state["pointer"].startswith(parent["pointer"] + "/"),
                    "State below absent parent",
                )
    if operation in {"inspect", "exchange", "lossyExchange"}:
        neutral.validate_slices(inventory["opaque"], source, parsed, operation, {"primary"})

    for loss in report["losses"]:
        record(loss, "input location information reason permission")
        demand(operation == "lossyExchange" and loss["input"] in source and loss["permission"] is None, "Loss outside operation/boundary")
        text(loss["information"])
        text(loss["reason"])
        validate_location(
            loss["location"], loss["input"], source, parsed,
            allow_unobservable=loss["location"] == {"pointer": ""},
        )
    neutral.unique(report["losses"], "Loss")
    demand(bool(report["losses"]) == (operation == "lossyExchange"), "missing or unexpected Loss records")

    artifacts = response["artifacts"]
    demand(isinstance(artifacts, dict), "artifacts map")
    decoded = {}
    for name, encoded in artifacts.items():
        text(name)
        demand(isinstance(encoded, str), "artifact base64")
        decoded[name] = base64.b64decode(encoded, validate=True)
    demand(len(report["outputs"]) == len(decoded), "output/artifact boundary mismatch")
    demand(set(decoded) <= set(source), "output artifact outside input boundary")
    expected_outputs = [
        {"id": name, "sha256": neutral.digest(decoded[name])}
        for name in input_order if name in decoded
    ]
    demand(report["outputs"] == expected_outputs, "output hashes or order")
    return decoded


def observe(case, response, source):
    try:
        artifacts = validate_report(response, case, source)
        report = response["report"]
        expected = case["expected"]
        errors = []
        actual_results = result_rows(report)
        if any(not contains(actual_results, item) for item in expected["results"]):
            errors.append("required Result differs from oracle")
        findings = finding_rows(report)
        wanted = expected["findings"]["items"]
        if expected["findings"]["mode"] == "exact":
            keys = ("input", "unit", "rule", "location", "outcome")
            if {canonical({key: item[key] for key in keys}) for item in findings} != {canonical(item) for item in wanted}:
                errors.append("findings differ from exact oracle")
        elif any(not contains(findings, item) for item in wanted):
            errors.append("required Finding missing")
        checks = check_rows(report)
        for target in expected["checks"]:
            metadata = {key: value for key, value in target.items() if key != "locations"}
            matches = [item for item in checks if contains([item], metadata)]
            wanted_locations = {canonical(item) for item in target["locations"]}
            if not any(wanted_locations <= {canonical(item) for item in match["locations"]} for match in matches):
                errors.append("required Check or location missing: " + target["rule"])
        states = report["inventory"]["states"]
        for target in expected["states"]:
            if not contains(states, target):
                errors.append("required State missing: " + target["pointer"])
        for target in expected["absentStates"]:
            if any(item["input"] == target["input"] and item["pointer"].startswith(target["pointerPrefix"]) for item in states):
                errors.append("forbidden State: " + target["pointerPrefix"])
        for target in expected["opaque"]:
            if not contains(report["inventory"]["opaque"], target):
                errors.append("required opaque Slice missing: " + target["pointer"])
        for target in expected["absentOpaque"]:
            if contains(report["inventory"]["opaque"], target):
                errors.append("forbidden opaque Slice: " + target["pointer"])
        if expected["preservation"] == "exact-input-boundary":
            if artifacts != source:
                errors.append("output bytes or boundary changed")
        elif artifacts or report["outputs"]:
            errors.append("unexpected output")
        if "losses" in expected:
            wanted_losses = expected["losses"]
            if (len(report["losses"]) != len(wanted_losses)
                    or any(not contains(report["losses"], item) for item in wanted_losses)):
                errors.append("prospective losses differ from oracle")
        return errors
    except (ValueError, TypeError, KeyError, IndexError, OverflowError, RecursionError) as exc:
        return ["invalid response: " + str(exc)]


def loss_key(loss):
    if (loss["input"] == "primary" and loss["location"] == {"pointer": ""}
            and loss["information"] == "unspecified requested loss"):
        return {key: value for key, value in loss.items() if key != "reason"}
    return loss


def comparison(response):
    report = response["report"]
    return {
        "contract": report["contract"], "operation": report["operation"],
        "inputs": canonical(report["inputs"]),
        "results": frozenset(canonical(item) for item in result_rows(report)),
        "findings": frozenset(canonical(item) for item in finding_rows(report)),
        "checks": frozenset(canonical(item) for item in check_rows(report)),
        "states": frozenset(canonical(state_key(item, report["inventory"]["tree"])) for item in report["inventory"]["states"]),
        "opaque": frozenset(canonical(item) for item in report["inventory"]["opaque"]),
        "tree": canonical(report["inventory"]["tree"]),
        "losses": frozenset(canonical(loss_key(item)) for item in report["losses"]),
        "outputs": frozenset(canonical(item) for item in report["outputs"]),
        "artifacts": tuple(sorted((name, base64.b64decode(data, validate=True)) for name, data in response["artifacts"].items())),
    }


def request_bytes(case, primary, annexes):
    request = {
        "operation": case["operation"],
        "primary": base64.b64encode(primary).decode(),
        "annexes": {
            name: base64.b64encode(data).decode()
            for name, data in annexes.items()
        },
    }
    if case.get("losses") is not None:
        request["losses"] = case["losses"]
    return json.dumps(
        request, separators=(",", ":"), ensure_ascii=False,
        default=lambda value: neutral.uint(value),
    ).encode("utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path, nargs="?", default=ROOT / "fixtures" / "manifest.json")
    parser.add_argument("--reader", action="append", required=True, help="JSON array [safe label, executable, arguments...]")
    parser.add_argument("--reports", type=Path, required=True)
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--case", action="append", dest="case_names")
    args = parser.parse_args(argv)
    try:
        demand(math.isfinite(args.timeout) and 0 < args.timeout <= 300, "timeout must be in (0,300]")
        readers = []
        for raw in args.reader:
            entry = json.loads(raw)
            demand(isinstance(entry, list) and len(entry) >= 2 and all(isinstance(item, str) and item for item in entry), "reader requires label and argv")
            demand(SAFE.fullmatch(entry[0]), "unsafe reader label")
            readers.append(entry)
        demand(len(readers) >= 2 and len({item[0] for item in readers}) == len(readers), "two readers with unique labels required")
        manifest = load(args.manifest.read_bytes())
        demand(manifest["contract"] == CONTRACT and manifest["format"] == FORMAT, "wrong corpus edition/format")
        names = [case["name"] for case in manifest["cases"]]
        demand(len(names) == len(set(names)) and all(SAFE.fullmatch(name) for name in names), "unsafe or duplicate case name")
        demand(not args.case_names or set(args.case_names) <= set(names), "unknown selected case")
        args.reports.mkdir(parents=True, exist_ok=True)
        demand(not any(args.reports.iterdir()), "reports directory must be empty")
    except (ValueError, TypeError, KeyError, OSError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    failures, blocked = [], []
    completed = 0
    for case in manifest["cases"]:
        if args.case_names and case["name"] not in args.case_names:
            continue
        if case["status"] == "blocked":
            blocked.append({"case": case["name"], "blocker": case["blocker"]})
            continue
        try:
            def artifact(metadata):
                path = (args.manifest.parent / metadata["path"]).resolve()
                demand(path.is_relative_to(args.manifest.parent.resolve()), "artifact escapes manifest directory")
                data = path.read_bytes()
                demand(neutral.digest(data) == metadata["sha256"], "fixture hash mismatch")
                return data
            primary = artifact(case["primary"])
            annexes = {name: artifact(metadata) for name, metadata in case["annexes"].items()}
            source = {"primary": primary, **{"annex/" + name: data for name, data in annexes.items()}}
            wire = request_bytes(case, primary, annexes)
        except (ValueError, TypeError, KeyError, OSError) as exc:
            failures.append({"case": case["name"], "issue": str(exc)})
            continue
        observations = {}
        for label, *command in readers:
            stdout = stderr = b""
            try:
                code, stdout, stderr, error = neutral.run_reader(command, wire, args.timeout)
                demand(error is None, error or "reader error")
                demand(code == 0, "reader exit " + str(code))
                response = load(stdout)
                errors = observe(case, response, source)
                failures.extend({"case": case["name"], "reader": label, "issue": error} for error in errors)
                if not errors:
                    observations[label] = comparison(response)
            except (ValueError, TypeError, KeyError, OSError, RecursionError) as exc:
                failures.append({"case": case["name"], "reader": label, "issue": str(exc)})
            finally:
                (args.reports / f"{case['name']}.{label}.stdout").write_bytes(stdout)
                (args.reports / f"{case['name']}.{label}.stderr").write_bytes(stderr)
        if len(observations) == len(readers):
            first = readers[0][0]
            for label in [item[0] for item in readers[1:]]:
                for field, value in observations[first].items():
                    if observations[label][field] != value:
                        failures.append({"case": case["name"], "reader": label, "issue": "cross-reader mismatch: " + field})
        completed += 1
    summary = {"cases": completed, "readers": [item[0] for item in readers], "blocked": blocked, "failures": failures,
               "scope": "AgSDL 0.1.0 report contract, normative corpus oracles, exact slices and exchange bytes; no oracle derivation or runtime execution"}
    (args.reports / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))
    return int(bool(blocked or failures))


if __name__ == "__main__":
    raise SystemExit(main())
