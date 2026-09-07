#!/usr/bin/env python3
"""Check the official corpus without invoking an AgSDL reader."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parent
REPOSITORY = ROOT.parent
FIXTURES = ROOT / "fixtures"
MANIFEST = FIXTURES / "manifest.json"
CONTRACT = "agsdl-0.1.0"
FORMAT = "agsdl-conformance-corpus-1"
OPERATIONS = {
    "inspect": ("inspect", None),
    "validateD": ("D", "unresolved-document"),
    "validateG": ("G", "unresolved-document"),
    "resolveG": ("G", "resolved-graph"),
    "validateR": ("R", "unresolved-document"),
    "exchange": ("exchange", None),
    "lossyExchange": ("exchange", None),
}
UNIT_RULES = {
    "D": {"P-SYNTAX", "P-SHAPE", "D-IDENTITY", "D-OWNER", "D-REFERENCE",
          "D-RELATION", "D-CYCLE", "D-EXPORT", "D-AGENT", "D-DEFERRAL",
          "D-DEPENDENCY", "D-INTEGRITY", "X-MODE"},
    "G": {"P-SHAPE", "X-MODE", "G-TARGET", "G-PATH", "G-DATA",
          "G-APPROVAL", "G-RESOLVE", "P-PREREQUISITE"},
    "R": {"P-SHAPE", "X-MODE", "R-SELECTION", "R-BINDING", "R-TOOL",
          "R-CONTENT", "R-COMPATIBILITY", "P-PREREQUISITE"},
    "inspect": {"P-SYNTAX"},
    "exchange": {"E-PRESERVE", "E-LOSS"},
}
BOUNDARY_RULES = {"X-EXECUTION", "X-FULL-MODEL", "X-READINESS",
                  "X-EVIDENCE-ASSESSMENT"}
RULES = set().union(*UNIT_RULES.values(), BOUNDARY_RULES)
VERDICTS = {"pass", "fail", "unsupported", "inconclusive"}
CHECK_STATES = {"completed", "blocked", "excluded"}
FINDING_VARIANTS = {
    "fail": "negative", "unsupported": "unsupported",
    "inconclusive": "inconclusive", "deferred": "deferred",
}
POINTER = re.compile(r"(?:/(?:[^~/]|~[01])*)*\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
SAFE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def exact(value, required, optional=()):
    require(isinstance(value, dict), "expected object")
    keys = set(value)
    require(set(required) <= keys <= set(required) | set(optional),
            f"closed fields differ: {sorted(keys)}")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pointer_value(value, pointer):
    if pointer == "":
        return True, value
    current = value
    for token in pointer.split("/")[1:]:
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and re.fullmatch(r"0|[1-9][0-9]*", token):
            index = int(token)
            if index >= len(current):
                return False, None
            current = current[index]
        else:
            return False, None
    return True, current


def check_location(location):
    require(isinstance(location, dict) and len(location) == 1, "closed Location")
    if "pointer" in location:
        require(isinstance(location["pointer"], str) and
                POINTER.fullmatch(location["pointer"]), "invalid pointer")
    else:
        require(set(location) == {"byte"} and type(location["byte"]) is int and
                0 <= location["byte"] <= 9007199254740991, "invalid byte location")


def heading_exists(path, heading):
    return any(line in {"# " + heading, "## " + heading, "### " + heading}
               for line in path.read_text().splitlines())


def coverage_has_oracle(case, rule, variant):
    expected = case["expected"]
    findings = expected["findings"]["items"]
    checks = expected["checks"]
    if variant in FINDING_VARIANTS.values():
        return any(item["rule"] == rule and
                   FINDING_VARIANTS[item["outcome"]] == variant
                   for item in findings)
    if variant in {"blocked", "excluded"}:
        explicit = any(item["rule"] == rule and item["state"] == variant
                       for item in checks)
        if rule == "D-REFERENCE" and variant == "excluded":
            explicit = explicit or any(
                item["state"] == "unchecked" and item["pointer"].startswith("/relations/")
                for item in expected["states"]
            )
        return explicit
    if variant == "positive":
        explicit = (any(item["rule"] == rule and item["state"] == "completed"
                        for item in checks) and
                    not any(item["rule"] == rule for item in findings))
        unit = next((name for name, rules in UNIT_RULES.items() if rule in rules), None)
        implicit = any(item["unit"] == unit and item["verdict"] == "pass"
                       for item in expected["results"])
        if rule == "G-RESOLVE":
            implicit = implicit and case["operation"] == "resolveG"
        if rule == "E-LOSS":
            implicit = False
        return explicit or implicit
    if variant == "unknown":
        return any(item["state"] == "unknown" or item.get("detail") == "unknown"
                   for item in expected["states"])
    return False


def check_expected(case, inputs):
    expected = case["expected"]
    exact(expected, {"results", "findings", "checks", "states", "absentStates",
                     "opaque", "absentOpaque", "preservation"}, {"losses"})
    for field in ("results", "checks", "states", "absentStates", "opaque",
                  "absentOpaque"):
        require(isinstance(expected[field], list), f"{field} must be a list")
    requested = OPERATIONS[case["operation"]]
    identities = []
    for result in expected["results"]:
        exact(result, {"input", "unit", "phase", "verdict"})
        require(result["input"] in inputs and result["verdict"] in VERDICTS,
                "invalid Result oracle")
        identities.append((result["input"], result["unit"], result["phase"]))
    require(identities and identities[-1] == ("primary", *requested),
            "requested Result must be last")
    require(len(identities) == len(set(identities)), "duplicate Result oracle")
    if requested[0] in {"G", "R"}:
        require(identities[0] == ("primary", "D", "unresolved-document"),
                "missing primary D prerequisite")
    exact(expected["findings"], {"mode", "items"})
    require(expected["findings"]["mode"] in {"contains", "exact"},
            "finding comparison mode")
    for finding in expected["findings"]["items"]:
        exact(finding, {"input", "unit", "rule", "location", "outcome"})
        require(finding["input"] in inputs and
                finding["rule"] in UNIT_RULES[finding["unit"]] and
                finding["outcome"] in FINDING_VARIANTS,
                "invalid Finding oracle")
        check_location(finding["location"])
    for check in expected["checks"]:
        exact(check, {"input", "unit", "rule", "state", "locations"})
        require(check["input"] in inputs and check["state"] in CHECK_STATES and
                check["rule"] in UNIT_RULES[check["unit"]] | BOUNDARY_RULES,
                "invalid Check oracle")
        require(isinstance(check["locations"], list), "Check locations")
        require((check["state"] == "completed") == (check["locations"] == []),
                "completed/location invariant")
        for location in check["locations"]:
            check_location(location)
    for state in expected["states"]:
        exact(state, {"input", "pointer", "state"}, {"detail", "detailRequirement"})
        require(state["input"] in inputs and POINTER.fullmatch(state["pointer"]) and
                state["state"] in {"absent", "unknown", "declared", "unchecked"},
                "invalid State oracle")
    for item in expected["absentStates"]:
        exact(item, {"input", "pointerPrefix"})
        require(item["input"] in inputs and POINTER.fullmatch(item["pointerPrefix"]),
                "invalid absent State oracle")
    for field in ("opaque", "absentOpaque"):
        for item in expected[field]:
            exact(item, {"input", "pointer"})
            require(item["input"] in inputs and POINTER.fullmatch(item["pointer"]),
                    "invalid Slice oracle")
    require(expected["preservation"] in {"no-output", "exact-input-boundary"},
            "invalid preservation oracle")
    if case["operation"] == "lossyExchange":
        require(isinstance(expected.get("losses"), list) and expected["losses"],
                "lossyExchange requires prospective losses")


def check_manifest(manifest):
    exact(manifest, {"format", "contract", "normativeBase", "normativeSources",
                     "schemas", "historicalDerivation", "coverage", "cases"})
    require(manifest["format"] == FORMAT and manifest["contract"] == CONTRACT,
            "manifest identity")
    require(subprocess.check_output(["git", "rev-parse", manifest["normativeBase"]],
                                    text=True).strip() == manifest["normativeBase"],
            "normative base does not resolve exactly")
    for name, expected in manifest["normativeSources"].items():
        path = (REPOSITORY / name).resolve()
        require(path.is_relative_to(REPOSITORY / "spec") and
                HASH.fullmatch(expected) and digest(path) == expected,
                f"normative source changed: {name}")
        source = subprocess.check_output(
            ["git", "show", manifest["normativeBase"] + ":" + name]
        )
        require(hashlib.sha256(source).hexdigest() == expected,
                f"normative base mismatch: {name}")
    for name, expected in manifest["schemas"].items():
        path = (REPOSITORY / name).resolve()
        require(path.is_relative_to(REPOSITORY / "schemas") and
                HASH.fullmatch(expected) and digest(path) == expected,
                f"schema changed: {name}")
    derivation = manifest["historicalDerivation"]
    exact(derivation, {"candidate2Cases", "modularCases",
                       "excludedCandidate2Operations", "reason"})
    require(derivation["excludedCandidate2Operations"] == ["validateR"],
            "historical R exclusion")
    require(set(manifest["coverage"]) == RULES, "official rule matrix differs")
    cases = manifest["cases"]
    require(isinstance(cases, list) and cases, "cases")
    names = [case.get("name") for case in cases]
    require(len(names) == len(set(names)) and all(SAFE.fullmatch(name) for name in names),
            "unsafe or duplicate case name")
    require({case["operation"] for case in cases} == set(OPERATIONS),
            "all seven operations require cases")
    require(sum(name.startswith("candidate2-") for name in names) ==
            derivation["candidate2Cases"], "candidate-2 count")
    require(sum(name.startswith("modular-") for name in names) ==
            derivation["modularCases"], "modular count")
    by_name = {case["name"]: case for case in cases}
    for case in cases:
        exact(case, {"name", "status", "primary", "annexes", "operation", "source",
                     "coverage", "scenarios", "schemaAssertions", "expected",
                     "derivation"}, {"losses"})
        require(case["status"] == "ready" and case["operation"] in OPERATIONS,
                "case status/operation")
        exact(case["derivation"], {"family", "historicalCase", "method"})
        require(case["derivation"]["family"] in {"candidate2", "modular"},
                "derivation family")
        require(isinstance(case["source"], list) and case["source"],
                "normative sources")
        for source in case["source"]:
            exact(source, {"document", "section"})
            path = (FIXTURES / source["document"]).resolve()
            require(path.is_relative_to(REPOSITORY / "spec") and
                    heading_exists(path, source["section"]),
                    "oracle source must be a normative section")
        artifacts = {"primary": case["primary"], **{"annex/" + name: metadata
                     for name, metadata in case["annexes"].items()}}
        values = {}
        for input_id, metadata in artifacts.items():
            exact(metadata, {"path", "sha256"})
            path = (FIXTURES / metadata["path"]).resolve()
            require(path.is_relative_to(FIXTURES) and path.is_file() and
                    HASH.fullmatch(metadata["sha256"]) and
                    digest(path) == metadata["sha256"], "fixture hash/path")
            try:
                values[input_id] = json.loads(path.read_text())
            except (json.JSONDecodeError, UnicodeDecodeError):
                values[input_id] = None
        if isinstance(values["primary"], dict):
            require(values["primary"].get("contract") not in {
                "proposal-0012-candidate-2", "proposal-0013-candidate-1"
            }, "historical marker leaked into official input")
        require(isinstance(case["coverage"], list), "case coverage")
        check_expected(case, artifacts)
        for association in case["coverage"]:
            require(re.fullmatch(
                r"[A-Z-]+:(?:positive|negative|unknown|inconclusive|unsupported|deferred|blocked|excluded)",
                association) is not None, "coverage association")
            rule, variant = association.split(":", 1)
            require(rule in RULES and case["name"] in
                    manifest["coverage"][rule].get(variant, []),
                    "reverse coverage association")
            require(coverage_has_oracle(case, rule, variant),
                    f"coverage lacks oracle evidence: {association} in {case['name']}")
        require(isinstance(case["schemaAssertions"], list), "schema assertions")
        for assertion in case["schemaAssertions"]:
            exact(assertion, {"entry", "input", "pointer", "valid"})
            require(assertion["input"] in values and
                    isinstance(assertion["valid"], bool) and
                    POINTER.fullmatch(assertion["pointer"]), "schema assertion")
            require(pointer_value(values[assertion["input"]], assertion["pointer"])[0],
                    "schema assertion pointer")
    for rule, variants in manifest["coverage"].items():
        require(isinstance(variants, dict) and variants, "coverage variants")
        for variant, listed in variants.items():
            require(isinstance(listed, list) and listed and len(listed) == len(set(listed)),
                    "coverage case list")
            for name in listed:
                require(name in by_name and f"{rule}:{variant}" in by_name[name]["coverage"],
                        "forward coverage association")


def validate_shapes(manifest):
    try:
        from jsonschema import Draft202012Validator
    except ImportError as exc:
        raise ValueError("--jsonschema requires an installed jsonschema package") from exc
    for path in sorted((REPOSITORY / "schemas").glob("*.json")):
        Draft202012Validator.check_schema(json.loads(path.read_text()))
    schema = json.loads((REPOSITORY / "schemas/agsdl.schema.json").read_text())
    for case in manifest["cases"]:
        values = {"primary": None}
        for input_id, metadata in {
            "primary": case["primary"],
            **{"annex/" + name: item for name, item in case["annexes"].items()},
        }.items():
            try:
                values[input_id] = json.loads((FIXTURES / metadata["path"]).read_text())
            except (json.JSONDecodeError, UnicodeDecodeError):
                values[input_id] = None
        for assertion in case["schemaAssertions"]:
            _, value = pointer_value(values[assertion["input"]], assertion["pointer"])
            scoped = {"$schema": schema["$schema"],
                      "$ref": f"#/$defs/{assertion['entry']}",
                      "$defs": schema["$defs"]}
            valid = not any(Draft202012Validator(scoped).iter_errors(value))
            require(valid == assertion["valid"],
                    f"schema assertion differs: {case['name']} {assertion['entry']}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonschema", action="store_true",
                        help="validate recorded shapes with installed Draft 2020-12 support")
    args = parser.parse_args(argv)
    try:
        manifest = json.loads(MANIFEST.read_text())
        check_manifest(manifest)
        if args.jsonschema:
            validate_shapes(manifest)
    except (ValueError, KeyError, TypeError, OSError, subprocess.CalledProcessError,
            json.JSONDecodeError) as exc:
        print(f"official corpus check failed: {exc}", file=sys.stderr)
        return 1
    suffix = " and Draft 2020-12 assertions" if args.jsonschema else ""
    print(f"{len(manifest['cases'])} official cases checked{suffix}.")
    print("No reader, runtime or described Agent was executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
