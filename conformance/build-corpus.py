#!/usr/bin/env python3
"""Build the official 0.1.0 corpus without invoking a reader.

The historical manifests supply reviewed fixture mutations and expected report
tuples. This builder admits only candidate-2 operations whose rules survive in
0.1.0, converts the selected G records explicitly, and admits every modular
case. It then replaces all oracle citations with normative specification
sections. The historical bytes remain untouched.
"""

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parent
FIXTURES = ROOT / "fixtures"
OFFICIAL = "agsdl-0.1.0"
FORMAT = "agsdl-conformance-corpus-1"
BASE = "c273395b06dc51fdc130c6f9bb2d5d04cc6c8eef"
ALLOWED_CANDIDATE_OPERATIONS = {
    "inspect", "validateD", "validateG", "resolveG", "exchange", "lossyExchange"
}
NORMATIVE_BY_RULE = {
    "P-SYNTAX": ("spec/serialization.md", "JSON lexical grammar"),
    "P-SHAPE": ("spec/serialization.md", "Notation and shared JSON rules"),
    "D-IDENTITY": ("spec/document.md", "D: document declarations"),
    "D-OWNER": ("spec/document.md", "D: document declarations"),
    "D-REFERENCE": ("spec/document.md", "D: document declarations"),
    "D-RELATION": ("spec/document.md", "D: document declarations"),
    "D-CYCLE": ("spec/document.md", "D: document declarations"),
    "D-EXPORT": ("spec/document.md", "D: document declarations"),
    "D-AGENT": ("spec/document.md", "D: document declarations"),
    "D-DEFERRAL": ("spec/document.md", "D: document declarations"),
    "D-DEPENDENCY": ("spec/document.md", "Dependencies, unknowns and extension handling"),
    "D-INTEGRITY": ("spec/document.md", "Dependencies, unknowns and extension handling"),
    "X-MODE": ("spec/document.md", "Dependencies, unknowns and extension handling"),
    "G-TARGET": ("spec/graph.md", "Targets, data and paths"),
    "G-PATH": ("spec/graph.md", "Targets, data and paths"),
    "G-DATA": ("spec/graph.md", "Targets, data and paths"),
    "G-APPROVAL": ("spec/graph.md", "Sequential approvals for one call"),
    "G-RESOLVE": ("spec/document.md", "Dependencies, unknowns and extension handling"),
    "R-SELECTION": ("spec/runtime.md", "Configuration selection and assignments"),
    "R-BINDING": ("spec/runtime.md", "Configuration selection and assignments"),
    "R-TOOL": ("spec/runtime.md", "Configuration selection and assignments"),
    "R-CONTENT": ("spec/runtime.md", "Content composition, application and prerequisites"),
    "R-COMPATIBILITY": ("spec/runtime.md", "Declared compatibility, not readiness"),
    "E-PRESERVE": ("spec/reports.md", "Rule execution and exact exclusion records"),
    "E-LOSS": ("spec/reports.md", "Rule execution and exact exclusion records"),
    "P-PREREQUISITE": ("spec/reports.md", "Rule execution and exact exclusion records"),
    "X-EXECUTION": ("spec/reports.md", "Rule execution and exact exclusion records"),
    "X-FULL-MODEL": ("spec/reports.md", "Rule execution and exact exclusion records"),
    "X-READINESS": ("spec/reports.md", "Rule execution and exact exclusion records"),
    "X-EVIDENCE-ASSESSMENT": ("spec/reports.md", "Rule execution and exact exclusion records"),
}

NEUTRAL_PATH = REPOSITORY / "experimental/candidate-2/compare-readers.py"
sys.dont_write_bytecode = True
NEUTRAL_SPEC = importlib.util.spec_from_file_location("agsdl_corpus_json", NEUTRAL_PATH)
neutral = importlib.util.module_from_spec(NEUTRAL_SPEC)
NEUTRAL_SPEC.loader.exec_module(neutral)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text())


def json_string(value):
    return json.dumps(value, ensure_ascii=False).encode()


def coverage_entries(case):
    entries = case.get("coverage", [])
    if entries and isinstance(entries[0], dict):
        return [f"{entry['rule']}:{entry['variant']}" for entry in entries]
    return list(entries)


def infer_report_coverage(case):
    """Add only variants demonstrated by the case's written report oracle."""
    entries = set(case["coverage"])
    # G never executes D-DEFERRAL. The historical label described a scope limit,
    # while the official oracle records a deferred D finding and a failing
    # G-TARGET. Keeping it as a Check variant would overstate the report.
    entries.discard("D-DEFERRAL:excluded")
    expected = case["expected"]
    findings = expected["findings"]["items"]
    findings_by_rule = {}
    for finding in findings:
        findings_by_rule.setdefault(finding["rule"], set()).add(finding["outcome"])
        variant = {
            "fail": "negative",
            "unsupported": "unsupported",
            "inconclusive": "inconclusive",
            "deferred": "deferred",
        }[finding["outcome"]]
        entries.add(f"{finding['rule']}:{variant}")
    for check in expected["checks"]:
        rule = check["rule"]
        if check["state"] in {"blocked", "excluded"}:
            entries.add(f"{rule}:{check['state']}")
        elif rule not in findings_by_rule:
            entries.add(f"{rule}:positive")
    case["coverage"] = sorted(entries)


def convert_graph_records(document):
    """Apply the explicit 0012 G to 0.1.0 record conversion."""
    definitions = document.get("definitions")
    if isinstance(definitions, list):
        for definition in definitions:
            if not isinstance(definition, dict) or definition.get("kind") != "Interface":
                continue
            payload = definition.get("payload")
            if not isinstance(payload, dict) or "operations" in payload:
                continue
            if not {"inputs", "outputs", "action"} <= set(payload):
                continue
            operation = {
                "id": "default",
                "direction": "inbound",
                "mode": "request-response",
                "action": payload["action"],
                "inputs": payload["inputs"],
                "outputs": payload["outputs"],
            }
            extra = {key: value for key, value in payload.items()
                     if key not in {"inputs", "outputs", "action"}}
            definition["payload"] = {"operations": [operation], **extra}
    graphs = document.get("graphs")
    if isinstance(graphs, list):
        for graph in graphs:
            if not isinstance(graph, dict) or not isinstance(graph.get("steps"), list):
                continue
            for step in graph["steps"]:
                if not isinstance(step, dict):
                    continue
                if step.get("kind") == "invoke" and "operation" not in step:
                    step["operation"] = "default"
                elif (step.get("kind") == "approval" and "call" not in step and
                      isinstance(step.get("approved"), str)):
                    step["call"] = step["approved"]


def apply_edits(data, edits):
    for start, end, replacement in sorted(edits, reverse=True):
        data = data[:start] + replacement + data[end:]
    return data


def convert_document(data, operation, preserve_syntax_error=False):
    if preserve_syntax_error:
        return data
    try:
        document = json.loads(data)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return data
    if not isinstance(document, dict):
        return data
    try:
        source = neutral.JsonSource(data)
    except (ValueError, UnicodeError, RecursionError):
        return data
    edits = []
    if document.get("contract") in {
        "proposal-0012-candidate-2", "proposal-0013-candidate-1"
    }:
        start, end = source.spans["/contract"]
        edits.append((start, end, json_string(OFFICIAL)))
    if operation in {"validateG", "resolveG"}:
        original = deepcopy(document)
        convert_graph_records(document)
        definitions = original.get("definitions")
        converted = document.get("definitions")
        if isinstance(definitions, list) and isinstance(converted, list):
            for index, (before, after) in enumerate(zip(definitions, converted)):
                if (isinstance(before, dict) and isinstance(after, dict) and
                        before.get("payload") != after.get("payload")):
                    pointer = f"/definitions/{index}/payload"
                    start, end = source.spans[pointer]
                    edits.append((start, end, json_string(after["payload"])))
        graphs = original.get("graphs")
        converted_graphs = document.get("graphs")
        if isinstance(graphs, list) and isinstance(converted_graphs, list):
            for graph_index, (before_graph, after_graph) in enumerate(zip(graphs, converted_graphs)):
                before_steps = before_graph.get("steps") if isinstance(before_graph, dict) else None
                after_steps = after_graph.get("steps") if isinstance(after_graph, dict) else None
                if not isinstance(before_steps, list) or not isinstance(after_steps, list):
                    continue
                for step_index, (before, after) in enumerate(zip(before_steps, after_steps)):
                    added = set(after) - set(before) if isinstance(before, dict) and isinstance(after, dict) else set()
                    if added not in (set(), {"operation"}, {"call"}):
                        raise RuntimeError("unexpected graph conversion")
                    if added:
                        name = next(iter(added))
                        pointer = f"/graphs/{graph_index}/steps/{step_index}"
                        _, end = source.spans[pointer]
                        insertion = b", " + json_string(name) + b": " + json_string(after[name])
                        edits.append((end - 1, end - 1, insertion))
    return apply_edits(data, edits)


def replace_dependency_hash(data, index, new_hash):
    source = neutral.JsonSource(data)
    start, end = source.spans[f"/dependencies/{index}/sha256"]
    return apply_edits(data, [(start, end, json_string(new_hash))])


def source_for(case):
    rules = {entry.split(":", 1)[0] for entry in case["coverage"]}
    operation = case["operation"]
    if not rules:
        if operation in {"validateG", "resolveG", "validateR"}:
            rules.add("P-PREREQUISITE")
        elif operation == "inspect":
            rules.add("P-SYNTAX")
        elif operation == "lossyExchange":
            rules.add("E-LOSS")
        else:
            rules.add("E-PRESERVE")
    sources = sorted({NORMATIVE_BY_RULE[rule] for rule in rules})
    if "P-SYNTAX" in rules:
        sources.append(("spec/reports.md", "Reports and deterministic diagnostics"))
    if "P-SHAPE" in rules:
        if operation in {"validateG", "resolveG"}:
            sources.append(("spec/graph.md", "G: closed simple-graph grammar"))
        elif operation == "validateR":
            sources.append(("spec/runtime.md", "R: configurations and reusable content"))
        else:
            sources.append(("spec/document.md", "D: document declarations"))
    if "G-TARGET" in rules:
        sources.append(("spec/graph.md", "Interface operations"))
    sources = sorted(set(sources))
    return [{"document": "../../" + path, "section": section}
            for path, section in sources]


def assertion_entries(case, documents, inherited=()):
    assertions = []
    if ("P-SYNTAX:negative" in case["coverage"] or
            case["name"].endswith("interpreted-number-exact")):
        return assertions
    primary = documents["primary"]
    try:
        parsed = json.loads(primary)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return []
    operation = case["operation"]
    findings = case["expected"]["findings"]["items"]

    def shape_valid(unit, input_id="primary"):
        return not any(item["input"] == input_id and item["unit"] == unit and
                       item["rule"] == "P-SHAPE" and item["outcome"] == "fail"
                       for item in findings)

    if operation in {"validateD", "validateG", "resolveG", "validateR"}:
        assertions.append({"entry": "Document", "input": "primary", "pointer": "",
                           "valid": shape_valid("D")})
    if isinstance(parsed, dict) and operation in {"validateG", "resolveG"} and "graphs" in parsed:
        graph_invalid = case["name"].endswith(("approval-zero-timeout",
                                               "graphs-scalar-validateG"))
        assertions.append({"entry": "Graphs", "input": "primary", "pointer": "/graphs",
                           "valid": not graph_invalid})
        if case["name"].endswith("selected-payload-closed"):
            interface_index = next(
                index for index, definition in enumerate(parsed.get("definitions", []))
                if isinstance(definition, dict) and definition.get("kind") == "Interface"
            )
            assertions.append({"entry": "InterfacePayload", "input": "primary",
                               "pointer": f"/definitions/{interface_index}/payload",
                               "valid": False})
    if isinstance(parsed, dict) and operation == "validateR" and "runtime" in parsed:
        assertions.append({"entry": "RuntimeDeclaration", "input": "primary",
                           "pointer": "/runtime", "valid": True})
    identities = {(item["entry"], item.get("input", "primary"), item["pointer"])
                  for item in assertions}
    for item in inherited:
        normalized = {"entry": item["entry"], "input": item.get("input", "primary"),
                      "pointer": item["pointer"], "valid": item["valid"]}
        identity = (normalized["entry"], normalized["input"], normalized["pointer"])
        if identity not in identities:
            assertions.append(normalized)
            identities.add(identity)
    return assertions


def prepare_case(case, family, source_root):
    result = deepcopy(case)
    result["name"] = family + "-" + result["name"]
    result["coverage"] = coverage_entries(result)
    infer_report_coverage(result)
    result["scenarios"] = [family + "-" + scenario for scenario in result.get("scenarios", [case["name"]])]
    result.pop("reviewWitnesses", None)
    result.pop("blocker", None)
    result["status"] = "ready"
    if family == "candidate2" and result["operation"] in {"validateG", "resolveG"}:
        for check in result["expected"]["checks"]:
            if (check["input"].startswith("annex/") and
                    check["rule"] == "G-TARGET" and check["state"] == "excluded"):
                for location in check["locations"]:
                    if location.get("pointer", "").endswith("/payload"):
                        location["pointer"] += "/operations/0"
    artifacts = {"primary": result["primary"], **{"annex/" + name: metadata
                 for name, metadata in result["annexes"].items()}}
    transformed = {}
    old_hashes = {}
    for input_id, metadata in artifacts.items():
        data = (source_root / metadata["path"]).read_bytes()
        old_hashes[input_id] = digest(data)
        transformed[input_id] = convert_document(
            data,
            result["operation"],
            preserve_syntax_error="P-SYNTAX:negative" in result["coverage"],
        )

    try:
        primary = json.loads(transformed["primary"])
    except (json.JSONDecodeError, UnicodeDecodeError):
        primary = None
    if isinstance(primary, dict) and isinstance(primary.get("dependencies"), list):
        for index, dependency in enumerate(primary["dependencies"]):
            if not isinstance(dependency, dict):
                continue
            annex_id = "annex/" + str(dependency.get("id"))
            if annex_id in transformed and dependency.get("sha256") == old_hashes[annex_id]:
                transformed["primary"] = replace_dependency_hash(
                    transformed["primary"], index, digest(transformed[annex_id])
                )

    output_metadata = {}
    for input_id, data in transformed.items():
        source_name = artifacts[input_id]["path"]
        output_name = family + "/" + source_name
        path = FIXTURES / output_name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        output_metadata[input_id] = {"path": output_name, "sha256": digest(data)}
    result["primary"] = output_metadata["primary"]
    result["annexes"] = {name: output_metadata["annex/" + name]
                         for name in case["annexes"]}
    result["source"] = source_for(result)
    result["schemaAssertions"] = assertion_entries(
        result, transformed, case.get("schemaAssertions", ())
    )
    result["derivation"] = {
        "family": family,
        "historicalCase": case["name"],
        "method": "marker-and-hash" if family == "modular" else
                  "explicit-g-record-conversion" if result["operation"] in {"validateG", "resolveG"}
                  else "marker-and-hash",
    }
    return result


def main():
    candidate_root = REPOSITORY / "experimental/candidate-2/fixtures"
    modular_root = REPOSITORY / "experimental/modular-candidate-1/fixtures"
    candidate = load(candidate_root / "manifest.json")
    modular = load(modular_root / "manifest.json")
    cases = [prepare_case(case, "candidate2", candidate_root)
             for case in candidate["cases"]
             if case["status"] == "ready" and case["operation"] in ALLOWED_CANDIDATE_OPERATIONS]
    cases.extend(prepare_case(case, "modular", modular_root)
                 for case in modular["cases"] if case["status"] == "ready")
    names = [case["name"] for case in cases]
    if len(names) != len(set(names)):
        raise RuntimeError("duplicate official case name")
    coverage = {}
    for case in cases:
        for entry in case["coverage"]:
            rule, variant = entry.split(":", 1)
            coverage.setdefault(rule, {}).setdefault(variant, []).append(case["name"])
    spec = {}
    for path in sorted((REPOSITORY / "spec").glob("*.md")):
        spec[str(path.relative_to(REPOSITORY))] = digest(path.read_bytes())
    schemas = {}
    for path in sorted((REPOSITORY / "schemas").glob("*.json")):
        schemas[str(path.relative_to(REPOSITORY))] = digest(path.read_bytes())
    manifest = {
        "format": FORMAT,
        "contract": OFFICIAL,
        "normativeBase": BASE,
        "normativeSources": spec,
        "schemas": schemas,
        "historicalDerivation": {
            "candidate2Cases": sum(case["name"].startswith("candidate2-") for case in cases),
            "modularCases": sum(case["name"].startswith("modular-") for case in cases),
            "excludedCandidate2Operations": ["validateR"],
            "reason": "Candidate-2 R was replaced. Its D, inspect, exchange and lossyExchange records are mechanically reusable. Its G records receive the explicit Operation and call conversion documented by Decision 0007 traceability.",
        },
        "coverage": coverage,
        "cases": cases,
    }
    (FIXTURES / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print(f"wrote {len(cases)} official cases")


if __name__ == "__main__":
    main()
