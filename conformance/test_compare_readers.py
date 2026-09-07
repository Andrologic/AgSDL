#!/usr/bin/env python3
"""Focused tests for the official report comparator."""

import base64
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("official_compare", HERE / "compare-readers.py")
compare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare)


def completed(rule):
    return {"rule": rule, "state": "completed", "locations": []}


def excluded(rule, pointer):
    return {"rule": rule, "state": "excluded", "locations": [{"pointer": pointer}]}


def exchange_fixture():
    raw = b'{"contract":"agsdl-0.1.0","annotations":{"value":1}}'
    output = base64.b64encode(raw).decode()
    parsed = compare.neutral.JsonSource(raw)
    start, end = parsed.spans["/annotations"]
    report = {
        "contract": compare.CONTRACT,
        "processor": {"identity": "example/reader", "version": "1"},
        "operation": "exchange",
        "inputs": [{"id": "primary", "sha256": hashlib.sha256(raw).hexdigest()}],
        "results": [{"input": "primary", "unit": "exchange", "phase": None, "verdict": "pass", "findings": [], "checks": [completed("E-PRESERVE")]}],
        "inventory": {"tree": json.loads(raw), "states": [], "opaque": [{"input": "primary", "pointer": "/annotations", "start": start, "end": end}]},
        "losses": [],
        "outputs": [{"id": "primary", "sha256": hashlib.sha256(raw).hexdigest()}],
    }
    case = {
        "operation": "exchange",
        "expected": {
            "results": [{"input": "primary", "unit": "exchange", "phase": None, "verdict": "pass"}],
            "findings": {"mode": "exact", "items": []},
            "checks": [{"input": "primary", "unit": "exchange", "rule": "E-PRESERVE", "state": "completed", "locations": []}],
            "states": [], "absentStates": [], "opaque": [{"input": "primary", "pointer": "/annotations"}], "absentOpaque": [],
            "preservation": "exact-input-boundary",
        },
    }
    return case, {"report": report, "artifacts": {"primary": output}}, {"primary": raw}


def validation_fixture():
    raw = b'{"runtime":{"configurations":[]}}'
    d_rules = [completed(rule) for rule in compare.D_RULES]
    d_rules.extend(excluded(rule, pointer) for rule, pointer in compare.BOUNDARY.items())
    r_rules = [completed(rule) for rule in compare.R_RULES if rule != "R-COMPATIBILITY"]
    r_rules.append(excluded("R-COMPATIBILITY", "/runtime"))
    r_rules.extend(excluded(rule, pointer) for rule, pointer in {**compare.BOUNDARY, **compare.R_BOUNDARY}.items())
    results = [
        {"input": "primary", "unit": "D", "phase": "unresolved-document", "verdict": "pass", "findings": [], "checks": sorted(d_rules, key=lambda item: (item["rule"], item["state"]))},
        {"input": "primary", "unit": "R", "phase": "unresolved-document", "verdict": "pass", "findings": [], "checks": sorted(r_rules, key=lambda item: (item["rule"], item["state"]))},
    ]
    report = {
        "contract": compare.CONTRACT,
        "processor": {"identity": "example/reader", "version": "1"},
        "operation": "validateR",
        "inputs": [{"id": "primary", "sha256": hashlib.sha256(raw).hexdigest()}],
        "results": results,
        "inventory": {"tree": json.loads(raw), "states": [{"input": "primary", "pointer": "/runtime/selected", "state": "absent", "detail": "absent"}], "opaque": []},
        "losses": [], "outputs": [],
    }
    case = {
        "operation": "validateR",
        "expected": {
            "results": [{"input": "primary", "unit": "R", "phase": "unresolved-document", "verdict": "pass"}],
            "findings": {"mode": "exact", "items": []},
            "checks": [{"input": "primary", "unit": "R", "rule": "R-COMPATIBILITY", "state": "excluded", "locations": [{"pointer": "/runtime"}]}],
            "states": [{"input": "primary", "pointer": "/runtime/selected", "state": "absent"}],
            "absentStates": [], "opaque": [], "absentOpaque": [], "preservation": "no-output",
        },
    }
    return case, {"report": report, "artifacts": {}}, {"primary": raw}


def selected_binding_fixture():
    case, response, _ = validation_fixture()
    tree = {"runtime": {"configurations": [{"id": "chosen", "agents": [{}]}], "selected": "chosen"}}
    raw = json.dumps(tree, separators=(",", ":")).encode()
    response["report"]["inputs"] = [{"id": "primary", "sha256": hashlib.sha256(raw).hexdigest()}]
    response["report"]["inventory"]["tree"] = tree
    response["report"]["inventory"]["states"] = [{
        "input": "primary",
        "pointer": "/runtime/configurations/0/agents/0",
        "state": "unknown",
        "detail": "unknown",
    }]
    case["expected"]["states"] = []
    return case, response, {"primary": raw}


def resolve_fixture():
    primary = b'{"graphs":[]}'
    annex = b'{"contract":"agsdl-0.1.0"}'
    source = {"primary": primary, "annex/a": annex}
    d_checks = sorted(
        [completed(rule) for rule in compare.D_RULES]
        + [excluded(rule, pointer) for rule, pointer in compare.BOUNDARY.items()],
        key=lambda item: (item["rule"], item["state"]),
    )
    annex_d = {
        "input": "annex/a", "unit": "D", "phase": "unresolved-document", "verdict": "fail",
        "findings": [{"rule": "P-SHAPE", "location": {"pointer": ""}, "outcome": "fail", "details": "missing Document fields"}],
        "checks": deepcopy(d_checks),
    }
    annex_g_checks = sorted(
        [completed("P-SHAPE"), completed("G-TARGET")]
        + [excluded(rule, pointer) for rule, pointer in compare.BOUNDARY.items()],
        key=lambda item: (item["rule"], item["state"]),
    )
    primary_g_checks = sorted(
        [completed(rule) for rule in compare.G_RULES | {"G-RESOLVE"}]
        + [{"rule": "P-PREREQUISITE", "state": "blocked", "locations": [{"pointer": ""}]}]
        + [excluded(rule, pointer) for rule, pointer in compare.BOUNDARY.items()],
        key=lambda item: (item["rule"], item["state"]),
    )
    results = [
        {"input": "primary", "unit": "D", "phase": "unresolved-document", "verdict": "pass", "findings": [], "checks": d_checks},
        annex_d,
        {"input": "annex/a", "unit": "G", "phase": "resolved-graph", "verdict": "fail", "findings": [], "checks": annex_g_checks},
        {"input": "primary", "unit": "G", "phase": "resolved-graph", "verdict": "fail", "findings": [], "checks": primary_g_checks},
    ]
    response = {"report": {
        "contract": compare.CONTRACT,
        "processor": {"identity": "example/reader", "version": "1"},
        "operation": "resolveG",
        "inputs": [{"id": name, "sha256": hashlib.sha256(source[name]).hexdigest()} for name in ("primary", "annex/a")],
        "results": results,
        "inventory": {"tree": json.loads(primary), "states": [], "opaque": []},
        "losses": [], "outputs": [],
    }, "artifacts": {}}
    case = {"operation": "resolveG", "expected": {
        "results": [{"input": "primary", "unit": "G", "phase": "resolved-graph", "verdict": "fail"}],
        "findings": {"mode": "contains", "items": []}, "checks": [], "states": [],
        "absentStates": [], "opaque": [], "absentOpaque": [], "preservation": "no-output",
    }}
    return case, response, source


def syntax_failure_fixture():
    raw = b"{"
    source = {"primary": raw}
    d_checks = [completed("P-SYNTAX")]
    d_checks.extend({"rule": rule, "state": "blocked", "locations": [{"pointer": ""}]} for rule in compare.D_RULES - {"P-SYNTAX"})
    d_checks.extend(excluded(rule, pointer) for rule, pointer in compare.BOUNDARY.items())
    r_checks = [{"rule": rule, "state": "blocked", "locations": [{"pointer": ""}]} for rule in compare.R_RULES]
    r_checks.extend(excluded(rule, pointer) for rule, pointer in {**compare.BOUNDARY, **compare.R_BOUNDARY}.items())
    r_checks.append({"rule": "P-PREREQUISITE", "state": "blocked", "locations": [{"pointer": ""}]})
    results = [
        {
            "input": "primary", "unit": "D", "phase": "unresolved-document", "verdict": "fail",
            "findings": [{"rule": "P-SYNTAX", "location": {"byte": 1}, "outcome": "fail", "details": "unexpected EOF"}],
            "checks": sorted(d_checks, key=lambda item: (item["rule"], item["state"])),
        },
        {
            "input": "primary", "unit": "R", "phase": "unresolved-document", "verdict": "fail",
            "findings": [], "checks": sorted(r_checks, key=lambda item: (item["rule"], item["state"])),
        },
    ]
    response = {"report": {
        "contract": compare.CONTRACT,
        "processor": {"identity": "example/reader", "version": "1"},
        "operation": "validateR",
        "inputs": [{"id": "primary", "sha256": hashlib.sha256(raw).hexdigest()}],
        "results": results,
        "inventory": {"tree": None, "states": [], "opaque": []},
        "losses": [], "outputs": [],
    }, "artifacts": {}}
    case = {"operation": "validateR", "expected": {
        "results": [{"input": "primary", "unit": "R", "phase": "unresolved-document", "verdict": "fail"}],
        "findings": {"mode": "contains", "items": []}, "checks": [], "states": [],
        "absentStates": [], "opaque": [], "absentOpaque": [], "preservation": "no-output",
    }}
    return case, response, source


class ComparatorTests(unittest.TestCase):
    def test_reuses_candidate_two_neutral_parser(self):
        self.assertEqual(
            compare.neutral.__file__,
            str(HERE.parent / "experimental" / "candidate-2" / "compare-readers.py"),
        )
        left = compare.load(b'{"n":9007199254740991,"b":true}')
        right = compare.load(b'{"n":9007199254740991.0,"b":true}')
        self.assertEqual(compare.canonical(left), compare.canonical(right))
        self.assertNotEqual(compare.canonical(left["n"]), compare.canonical(left["b"]))

    def test_exact_exchange_bytes_and_hashes(self):
        case, response, source = exchange_fixture()
        self.assertEqual(compare.observe(case, response, source), [])
        response["artifacts"]["primary"] = base64.b64encode(b"changed").decode()
        self.assertTrue(compare.observe(case, response, source))

    def test_rejects_wrong_edition_and_missing_rule(self):
        case, response, source = validation_fixture()
        self.assertEqual(compare.observe(case, response, source), [])
        wrong = deepcopy(response)
        wrong["report"]["contract"] = "proposal-0012-candidate-2"
        self.assertTrue(compare.observe(case, wrong, source))
        missing = deepcopy(response)
        missing["report"]["results"][1]["checks"] = [item for item in missing["report"]["results"][1]["checks"] if item["rule"] != "R-TOOL"]
        self.assertTrue(compare.observe(case, missing, source))

    def test_absent_child_state_and_oracle_are_checked(self):
        case, response, source = validation_fixture()
        self.assertEqual(compare.observe(case, response, source), [])
        response["report"]["inventory"]["states"] = []
        self.assertTrue(compare.observe(case, response, source))

    def test_slice_must_select_exact_source_value(self):
        case, response, source = exchange_fixture()
        self.assertEqual(compare.observe(case, response, source), [])
        response["report"]["inventory"]["opaque"][0]["end"] += 1
        self.assertTrue(compare.observe(case, response, source))

    def test_exchange_slice_boundaries_are_exhaustive(self):
        case, response, source = exchange_fixture()
        response["report"]["inventory"]["opaque"] = []
        self.assertTrue(compare.observe(case, response, source))

    def test_assessment_detail_is_a_comparison_key(self):
        case, response, source = selected_binding_fixture()
        first = deepcopy(response)
        second = deepcopy(response)
        first["report"]["inventory"]["states"][0].update(state="unchecked", detail="blocked")
        second["report"]["inventory"]["states"][0].update(state="unchecked", detail="declared-supported")
        self.assertEqual(compare.observe(case, first, source), [])
        self.assertEqual(compare.observe(case, second, source), [])
        self.assertNotEqual(compare.comparison(first)["states"], compare.comparison(second)["states"])

    def test_ordinary_state_prose_is_set_normalized(self):
        case, response, source = validation_fixture()
        baseline = deepcopy(response)
        response["report"]["inventory"]["states"].append({
            "input": "primary", "pointer": "/runtime/selected", "state": "absent",
            "detail": "Selection not supplied",
        })
        self.assertEqual(compare.observe(case, response, source), [])
        self.assertEqual(compare.comparison(baseline)["states"], compare.comparison(response)["states"])

        response["report"]["inventory"]["states"][-1]["detail"] = "unknown"
        self.assertEqual(compare.observe(case, response, source), [])
        self.assertEqual(compare.comparison(baseline)["states"], compare.comparison(response)["states"])

    def test_compatibility_keeps_fail_and_inconclusive_at_one_binding(self):
        case, response, source = validation_fixture()
        result = response["report"]["results"][1]
        result["checks"] = [item for item in result["checks"] if item["rule"] != "R-COMPATIBILITY"]
        result["checks"].append(completed("R-COMPATIBILITY"))
        result["checks"].sort(key=lambda item: (item["rule"], item["state"]))
        result["findings"] = [
            {"rule": "R-COMPATIBILITY", "location": {"pointer": "/runtime"}, "outcome": "fail", "details": "known incompatible requirement"},
            {"rule": "R-COMPATIBILITY", "location": {"pointer": "/runtime"}, "outcome": "inconclusive", "details": "application not provided"},
        ]
        result["verdict"] = "fail"
        case["expected"]["results"][-1]["verdict"] = "fail"
        case["expected"]["findings"] = {"mode": "contains", "items": []}
        case["expected"]["checks"] = []
        self.assertEqual(compare.observe(case, response, source), [])

    def test_resolve_aggregates_annex_prerequisites(self):
        case, response, source = resolve_fixture()
        self.assertEqual(compare.observe(case, response, source), [])
        invalid_annex = deepcopy(response)
        invalid_annex["report"]["results"][2]["checks"].append(
            {"rule": "P-PREREQUISITE", "state": "blocked", "locations": [{"pointer": ""}]}
        )
        invalid_annex["report"]["results"][2]["checks"].sort(key=lambda item: (item["rule"], item["state"]))
        self.assertTrue(compare.observe(case, invalid_annex, source))
        response["report"]["results"][-1]["checks"] = [
            item for item in response["report"]["results"][-1]["checks"]
            if item["rule"] != "P-PREREQUISITE"
        ]
        self.assertTrue(compare.observe(case, response, source))

    def test_assessment_state_mapping_is_enforced(self):
        case, response, source = selected_binding_fixture()
        response["report"]["inventory"]["states"][0].update(
            state="declared", detail="declared-supported"
        )
        self.assertTrue(compare.observe(case, response, source))

    def test_conflicting_assessments_at_one_binding_are_rejected(self):
        case, response, source = selected_binding_fixture()
        response["report"]["inventory"]["states"].append({
            "input": "primary",
            "pointer": "/runtime/configurations/0/agents/0",
            "state": "declared",
            "detail": "incompatible",
        })
        self.assertTrue(compare.observe(case, response, source))

    def test_missing_binding_indices_are_not_assessment_locations(self):
        case, response, _ = selected_binding_fixture()
        tree = {"runtime": {"configurations": [{"id": "chosen", "agents": []}], "selected": "chosen"}}
        raw = json.dumps(tree, separators=(",", ":")).encode()
        response["report"]["inputs"] = [{"id": "primary", "sha256": hashlib.sha256(raw).hexdigest()}]
        response["report"]["inventory"]["tree"] = tree
        state = response["report"]["inventory"]["states"][0]
        state["pointer"] = "/runtime/configurations/0/agents/99"
        source = {"primary": raw}
        self.assertFalse(compare.assessment_state(state, tree))
        self.assertEqual(compare.observe(case, response, source), [])
        prose = deepcopy(response)
        prose["report"]["inventory"]["states"][0]["detail"] = "ordinary prose"
        self.assertEqual(compare.comparison(response)["states"], compare.comparison(prose)["states"])

        tree = {"runtime": {"configurations": [{"id": "chosen", "agents": [{"tools": []}]}], "selected": "chosen"}}
        raw = json.dumps(tree, separators=(",", ":")).encode()
        response["report"]["inputs"] = [{"id": "primary", "sha256": hashlib.sha256(raw).hexdigest()}]
        response["report"]["inventory"]["tree"] = tree
        state["pointer"] = "/runtime/configurations/0/agents/0/tools/99"
        source = {"primary": raw}
        self.assertFalse(compare.assessment_state(state, tree))
        self.assertEqual(compare.observe(case, response, source), [])

    def test_existing_tool_binding_is_an_assessment_location(self):
        tree = {"runtime": {"configurations": [{"id": "chosen", "agents": [{"tools": [{}]}]}], "selected": "chosen"}}
        state = {
            "input": "primary", "pointer": "/runtime/configurations/0/agents/0/tools/0",
            "state": "unknown", "detail": "unknown",
        }
        self.assertTrue(compare.assessment_state(state, tree))

    def test_unparseable_input_accepts_only_fixed_check_locations(self):
        case, response, source = syntax_failure_fixture()
        self.assertEqual(compare.observe(case, response, source), [])
        target = next(
            item for item in response["report"]["results"][1]["checks"]
            if item["rule"] == "R-CONTENT"
        )
        target["locations"] = [{"pointer": "/runtime"}]
        self.assertTrue(compare.observe(case, response, source))


if __name__ == "__main__":
    unittest.main()
