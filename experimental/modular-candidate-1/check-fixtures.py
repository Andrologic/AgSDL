#!/usr/bin/env python3
"""Check modular corpus provenance, hashes, coverage and oracle structure."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / "fixtures"
MANIFEST = FIXTURES / "manifest.json"
CONTRACT = "proposal-0013-candidate-1"
FORMAT = "agsdl-modular-corpus-1"
OPERATIONS = {
    "validateG": ("G", "unresolved-document"),
    "resolveG": ("G", "resolved-graph"),
    "validateR": ("R", "unresolved-document"),
    "inspect": ("inspect", None),
    "exchange": ("exchange", None),
    "lossyExchange": ("exchange", None),
}
RESULT_PHASES = {
    "D": {"unresolved-document"},
    "G": {"unresolved-document", "resolved-graph"},
    "R": {"unresolved-document"},
    "inspect": {None},
    "exchange": {None},
}
VERDICTS = {"pass", "inconclusive", "unsupported", "fail"}
ASSESSMENT_STATES = {
    "not-provided": "absent",
    "incompatible": "declared",
    "unknown": "unknown",
    "declared-supported": "unchecked",
    "blocked": "unchecked",
}
RULES = {
    "P-SHAPE", "G-TARGET", "G-DATA", "G-APPROVAL",
    "R-SELECTION", "R-BINDING", "R-TOOL", "R-CONTENT",
    "R-COMPATIBILITY", "E-PRESERVE",
}
UNIT_RULES = {
    "D": set(),
    "G": {"P-SHAPE", "G-TARGET", "G-DATA", "G-APPROVAL"},
    "R": {"P-SHAPE", "R-SELECTION", "R-BINDING", "R-TOOL", "R-CONTENT", "R-COMPATIBILITY"},
    "inspect": set(),
    "exchange": {"E-PRESERVE"},
}
UNIT_EXTRA_CHECK_RULES = {
    "D": {"X-EXECUTION", "X-FULL-MODEL"},
    "G": {"X-EXECUTION", "X-FULL-MODEL"},
    "R": {"X-EXECUTION", "X-FULL-MODEL", "X-READINESS", "X-EVIDENCE-ASSESSMENT"},
    "inspect": set(),
    "exchange": set(),
}
REQUIRED_SCENARIOS = {
    "two-configurations", "two-agents-different-engines",
    "selection-absent-no-fallback", "selection-unknown-no-fallback",
    "engine-absent-no-fallback", "tool-choice-absent-no-fallback",
    "declared-incompatible-not-readiness", "declared-unknown-not-readiness",
    "declared-supported", "missing-application-preserves-incompatibility",
    "tool-specific-parameters", "content-reuse-order",
    "content-dependency-order", "content-dependency-cycle",
    "interface-two-operations-selected-individually", "approval-two-gates",
    "approval-success-refusal", "approval-refusal-bypass",
    "approval-call-invalid", "approval-input-unavailable",
    "external-runtime-reference-excluded", "exact-exchange-new-payload-slices",
    "exact-exchange-accounting-refusal",
    "partial-prerequisite-keeps-independent-failure",
}
POINTER = re.compile(r"(?:/(?:[^~/]|~[01])*)*\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact_fields(value, required, optional=()):
    require(isinstance(value, dict), "expected object")
    keys = set(value)
    require(set(required) <= keys <= set(required) | set(optional), f"closed fields differ: {sorted(keys)}")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check_location(location):
    require(isinstance(location, dict) and len(location) == 1, "closed Location")
    if "pointer" in location:
        require(isinstance(location["pointer"], str) and POINTER.fullmatch(location["pointer"]), "invalid pointer")
    else:
        require(set(location) == {"byte"} and type(location["byte"]) is int and location["byte"] >= 0, "invalid byte location")


def pointer_value(value, pointer):
    if pointer == "":
        return True, value
    current = value
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and re.fullmatch(r"0|[1-9][0-9]*", token) and int(token) < len(current):
            current = current[int(token)]
        else:
            return False, None
    return True, current


def pointer_or_missing_child(value, pointer):
    exists, _ = pointer_value(value, pointer)
    if exists or not pointer:
        return exists
    parent, _, token = pointer.rpartition("/")
    parent_exists, container = pointer_value(value, parent)
    return parent_exists and (isinstance(container, dict) or isinstance(container, list) and re.fullmatch(r"0|[1-9][0-9]*", token))


def coverage_evidence(case, rule, variant):
    expected = case["expected"]
    findings = expected["findings"]["items"]
    checks = expected["checks"]
    states = expected["states"]
    if variant == "positive":
        return any(x["rule"] == rule and x["state"] == "completed" for x in checks)
    if variant == "negative":
        return any(x["rule"] == rule and x["outcome"] == "fail" for x in findings)
    if variant == "inconclusive":
        return any(x["rule"] == rule and x["outcome"] == "inconclusive" for x in findings)
    if variant == "unknown":
        return (any(x["rule"] == rule and x["outcome"] == "inconclusive" for x in findings)
                and any(x.get("state") == "unknown" or x.get("detail") == "unknown" for x in states))
    if variant in {"blocked", "excluded"}:
        return any(x["rule"] == rule and x["state"] == variant for x in checks)
    return False


def check_manifest(manifest):
    exact_fields(manifest, {"format", "contract", "contractBase", "contractSha256", "inheritedContract", "schema", "requiredScenarios", "coverage", "cases"})
    require(manifest["format"] == FORMAT and manifest["contract"] == CONTRACT, "manifest edition")
    require(re.fullmatch(r"[0-9a-f]{40}", manifest["contractBase"]), "contract base")
    contract = (FIXTURES / "../../../proposals/0013-modular-mvp-contract.md").resolve()
    require(sha256(contract) == manifest["contractSha256"], "proposal 0013 bytes changed")
    source_contract = subprocess.run(
        ["git", "show", manifest["contractBase"] + ":proposals/0013-modular-mvp-contract.md"],
        check=True, stdout=subprocess.PIPE,
    ).stdout
    require(hashlib.sha256(source_contract).hexdigest() == manifest["contractSha256"], "proposal source revision differs")
    inherited = manifest["inheritedContract"]
    exact_fields(inherited, {"marker", "base", "sha256"})
    require(inherited["marker"] == "proposal-0012-candidate-2", "inherited marker")
    require(re.fullmatch(r"[0-9a-f]{40}", inherited["base"]), "inherited base")
    inherited_bytes = subprocess.run(
        ["git", "show", inherited["base"] + ":proposals/0012-minimal-0.1.0-contract.md"],
        check=True, stdout=subprocess.PIPE,
    ).stdout
    require(hashlib.sha256(inherited_bytes).hexdigest() == inherited["sha256"], "inherited 0012 bytes changed")
    schema = manifest["schema"]
    exact_fields(schema, {"path", "sha256"})
    schema_path = (FIXTURES / schema["path"]).resolve()
    require(schema_path.is_relative_to(ROOT) and sha256(schema_path) == schema["sha256"], "schema hash")
    source_schema = subprocess.run(
        ["git", "show", manifest["contractBase"] + ":experimental/modular-candidate-1/schemas/modular.schema.json"],
        check=True, stdout=subprocess.PIPE,
    ).stdout
    require(hashlib.sha256(source_schema).hexdigest() == schema["sha256"], "schema source revision differs")

    require(set(manifest["coverage"]) == RULES, "modified rule coverage differs")
    cases = manifest["cases"]
    require(isinstance(cases, list) and cases, "cases")
    names = [item.get("name") for item in cases]
    require(all(isinstance(x, str) and x for x in names) and len(names) == len(set(names)), "case names")
    by_name = {item["name"]: item for item in cases}
    scenarios = set()

    for case in cases:
        exact_fields(case, {"name", "status", "primary", "annexes", "operation", "source", "coverage", "scenarios", "schemaAssertions", "expected"}, {"blocker"})
        require(case["status"] in {"ready", "blocked"}, "case status")
        require(case["operation"] in OPERATIONS, "operation")
        require(isinstance(case["schemaAssertions"], list) and case["schemaAssertions"], "schemaAssertions")
        for assertion in case["schemaAssertions"]:
            exact_fields(assertion, {"entry", "pointer", "valid"})
            require(isinstance(assertion["entry"], str) and assertion["entry"], "schema entry")
            require(isinstance(assertion["pointer"], str) and POINTER.fullmatch(assertion["pointer"]), "schema pointer")
            require(isinstance(assertion["valid"], bool), "schema validity")
        require(isinstance(case["annexes"], dict), "annexes")
        source = case["source"]
        exact_fields(source, {"document", "sections"})
        require((FIXTURES / source["document"]).resolve() == contract, "oracle source document")
        text = contract.read_text()
        require(isinstance(source["sections"], list) and source["sections"], "oracle source sections")
        require(all(("## " + heading) in text or ("### " + heading) in text for heading in source["sections"]), "oracle source heading")
        require(isinstance(case["scenarios"], list) and case["scenarios"], "case scenarios")
        scenarios.update(case["scenarios"])
        exact_fields(case["primary"], {"path", "sha256"})
        artifacts = [case["primary"], *case["annexes"].values()]
        for artifact in artifacts:
            exact_fields(artifact, {"path", "sha256"})
            path = (FIXTURES / artifact["path"]).resolve()
            require(path.is_relative_to(FIXTURES) and path.is_file(), "fixture path")
            require(HASH.fullmatch(artifact["sha256"]) and sha256(path) == artifact["sha256"], "fixture hash")
        source_values = {"primary": json.loads((FIXTURES / case["primary"]["path"]).read_text())}
        source_values.update({"annex/" + name: json.loads((FIXTURES / metadata["path"]).read_text()) for name, metadata in case["annexes"].items()})
        if case["status"] == "blocked":
            require(case.get("blocker") and case["expected"] is None, "blocked case oracle")
            continue
        expected = case["expected"]
        exact_fields(expected, {"results", "findings", "checks", "states", "absentStates", "opaque", "absentOpaque", "preservation"})
        for field in ("results", "checks", "states", "absentStates", "opaque", "absentOpaque"):
            require(isinstance(expected[field], list), f"{field} list")
        unit, phase = OPERATIONS[case["operation"]]
        result_identities = []
        for item in expected["results"]:
            exact_fields(item, {"input", "unit", "phase", "verdict"})
            require(item["input"] in source_values, "Result input")
            require(item["unit"] in RESULT_PHASES and item["phase"] in RESULT_PHASES[item["unit"]], "Result unit/phase")
            require(item["verdict"] in VERDICTS, "Result verdict")
            result_identities.append((item["input"], item["unit"], item["phase"]))
        require(len(result_identities) == len(set(result_identities)), "duplicate Result oracle")
        require(result_identities.count(("primary", unit, phase)) == 1, "requested Result oracle")
        exact_fields(expected["findings"], {"mode", "items"})
        require(expected["findings"]["mode"] in {"contains", "exact"}, "finding mode")
        for item in expected["findings"]["items"]:
            exact_fields(item, {"input", "unit", "rule", "location", "outcome"})
            require(item["rule"] in UNIT_RULES.get(item["unit"], set()) and item["outcome"] in {"fail", "unsupported", "inconclusive", "deferred"}, "finding oracle")
            require(item["unit"] in RESULT_PHASES and any(identity[:2] == (item["input"], item["unit"]) for identity in result_identities), "finding Result identity")
            check_location(item["location"])
            require(item["input"] in source_values, "finding input")
            if "pointer" in item["location"]:
                require(pointer_value(source_values[item["input"]], item["location"]["pointer"])[0], "finding pointer is not a source value")
        for item in expected["checks"]:
            exact_fields(item, {"input", "unit", "rule", "state", "locations"})
            require(item["rule"] in UNIT_RULES.get(item["unit"], set()) | UNIT_EXTRA_CHECK_RULES.get(item["unit"], set()), "check rule")
            require(item["state"] in {"completed", "blocked", "excluded"}, "check state")
            require(item["unit"] in RESULT_PHASES and any(identity[:2] == (item["input"], item["unit"]) for identity in result_identities), "check Result identity")
            require(isinstance(item["locations"], list), "check locations")
            for location in item["locations"]:
                check_location(location)
                if "pointer" in location:
                    require(item["input"] in source_values and pointer_value(source_values[item["input"]], location["pointer"])[0], "Check pointer is not a source value")
        for item in expected["states"]:
            exact_fields(item, {"input", "pointer", "state"}, {"detail"})
            require(item["state"] in {"absent", "unknown", "declared", "unchecked"}, "state domain")
            if item.get("detail") in ASSESSMENT_STATES:
                require(item["state"] == ASSESSMENT_STATES[item["detail"]], "assessment detail/state mismatch")
            require(POINTER.fullmatch(item["pointer"]), "state pointer")
            require(item["input"] in source_values and pointer_or_missing_child(source_values[item["input"]], item["pointer"]), "State pointer is not observable")
        for item in expected["absentStates"]:
            exact_fields(item, {"input", "pointerPrefix"})
            require(isinstance(item["pointerPrefix"], str) and POINTER.fullmatch(item["pointerPrefix"]), "absent State pointer prefix")
            require(item["input"] in source_values, "absent State input")
        for field in ("opaque", "absentOpaque"):
            for item in expected[field]:
                exact_fields(item, {"input", "pointer"})
                require(POINTER.fullmatch(item["pointer"]), "opaque pointer")
                require(item["input"] in source_values and pointer_value(source_values[item["input"]], item["pointer"])[0], "opaque pointer is not a source value")
        require(expected["preservation"] in {"no-output", "exact-input-boundary"}, "preservation")
        associations = set(case["coverage"])
        require(all(re.fullmatch(r"[A-Z-]+:(?:positive|negative|unknown|inconclusive|blocked|excluded)", x) for x in associations), "coverage association")
        for association in associations:
            rule, variant = association.split(":")
            require(rule in RULES, "unknown covered rule")
            require(case["name"] in manifest["coverage"][rule].get(variant, []), "reverse coverage index")
            require(coverage_evidence(case, rule, variant), f"coverage lacks oracle evidence: {association} in {case['name']}")

    require(set(manifest["requiredScenarios"]) == scenarios, "requiredScenarios index")
    require(REQUIRED_SCENARIOS <= scenarios, "minimum scenario missing")
    for rule, variants in manifest["coverage"].items():
        require({"positive", "negative"} <= set(variants), f"positive/negative witnesses missing for {rule}")
        for variant, listed in variants.items():
            require(isinstance(listed, list) and listed and len(listed) == len(set(listed)), "coverage list")
            for name in listed:
                require(name in by_name and f"{rule}:{variant}" in by_name[name]["coverage"], "forward coverage index")


def validate_shapes(manifest):
    try:
        from jsonschema import Draft202012Validator
        from referencing import Registry, Resource
    except ImportError as exc:
        raise ValueError("--jsonschema requires an already installed jsonschema package") from exc
    schema_path = (FIXTURES / manifest["schema"]["path"]).resolve()
    schema = json.loads(schema_path.read_text())
    registry = Registry()
    for path in [schema_path, *(ROOT.parent / "candidate-2" / "schemas").glob("*.schema.json")]:
        registry = registry.with_resource(path.resolve().as_uri(), Resource.from_contents(json.loads(path.read_text())))
    for case in manifest["cases"]:
        if case["status"] != "ready":
            continue
        document = json.loads((FIXTURES / case["primary"]["path"]).read_text())
        for assertion in case["schemaAssertions"]:
            instance = document
            for token in assertion["pointer"].split("/")[1:]:
                token = token.replace("~1", "/").replace("~0", "~")
                instance = instance[int(token)] if isinstance(instance, list) else instance[token]
            scoped = {"$schema": schema["$schema"], "$id": schema_path.as_uri(), "$ref": f"#/$defs/{assertion['entry']}", "$defs": schema["$defs"]}
            errors = list(Draft202012Validator(scoped, registry=registry).iter_errors(instance))
            require(bool(errors) != assertion["valid"], f"schema expectation differs for {case['name']} {assertion['entry']} {assertion['pointer']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonschema", action="store_true", help="use an already installed Draft 2020-12 validator")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(MANIFEST.read_text())
        check_manifest(manifest)
        if args.jsonschema:
            validate_shapes(manifest)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        print(f"modular corpus check failed: {exc}", file=sys.stderr)
        return 1
    suffix = " and scoped Draft 2020-12 shapes" if args.jsonschema else ""
    print(f"{len(manifest['cases'])} modular cases: hashes, source editions, scenarios, rule coverage and oracles checked{suffix}.")
    print("No reader, runtime or described agent was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
