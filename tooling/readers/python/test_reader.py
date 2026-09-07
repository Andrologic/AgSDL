"""Focused tests for the official AgSDL 0.1.0 Python reader."""
import base64
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

from reader import PROCESSOR, read


REPOSITORY = Path(__file__).resolve().parents[3]
HISTORICAL_FIXTURES = (
    REPOSITORY / "experimental" / "modular-candidate-1" / "fixtures"
)
OPERATIONS = (
    "inspect",
    "validateD",
    "validateG",
    "resolveG",
    "validateR",
    "exchange",
    "lossyExchange",
)


def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()


def minimal_document(contract="agsdl-0.1.0"):
    return {
        "contract": contract,
        "root": {
            "key": {"scope": "official", "id": "system", "version": "1"},
            "kind": "System",
        },
        "definitions": [],
        "relations": [],
        "exports": [],
        "dependencies": [],
        "unresolved": [],
        "extensions": [],
    }


def official_fixture(name):
    value = json.loads((HISTORICAL_FIXTURES / name).read_bytes())
    value["contract"] = "agsdl-0.1.0"
    return value


def findings(report, rule, outcome=None):
    selected = [
        item
        for result in report["results"]
        for item in result["findings"]
        if item["rule"] == rule
    ]
    if outcome is None:
        return selected
    return [item for item in selected if item["outcome"] == outcome]


def checks(report, rule, state=None):
    selected = [
        item
        for result in report["results"]
        for item in result["checks"]
        if item["rule"] == rule
    ]
    if state is None:
        return selected
    return [item for item in selected if item["state"] == state]


class IdentityAndHostTests(unittest.TestCase):
    def test_all_seven_operations_emit_official_reports(self):
        source = encode(minimal_document())
        for operation in OPERATIONS:
            with self.subTest(operation=operation):
                response = read(operation, source)
                report = response["report"]
                self.assertEqual(report["contract"], "agsdl-0.1.0")
                self.assertEqual(report["processor"], PROCESSOR)
                self.assertEqual(report["operation"], operation)

    def test_foreign_edition_fails_validation_without_relabelling_input(self):
        foreign = minimal_document("proposal-0013-candidate-1")
        source = encode(foreign)
        report = read("validateD", source)["report"]
        self.assertEqual(report["contract"], "agsdl-0.1.0")
        self.assertEqual(report["inventory"]["tree"]["contract"], foreign["contract"])
        self.assertEqual(report["results"][0]["verdict"], "fail")
        self.assertTrue(findings(report, "P-SHAPE", "fail"))

    def test_exchange_preserves_foreign_bytes_exactly(self):
        source = b' {"contract":"another-edition","opaque":1e999999} \n'
        response = read("exchange", source)
        self.assertEqual(response["report"]["results"][0]["verdict"], "pass")
        self.assertEqual(response["artifacts"], {"primary": source})
        self.assertEqual(
            response["report"]["outputs"][0]["sha256"],
            hashlib.sha256(source).hexdigest(),
        )

    def test_cli_separates_host_errors_from_document_failures(self):
        cli = Path(__file__).with_name("cli.py")
        bad_request = {"operation": "validateD", "primary": "%%%", "annexes": {}}
        process = subprocess.run(
            [sys.executable, str(cli)],
            input=encode(bad_request),
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 2)
        self.assertEqual(process.stdout, b"")
        self.assertIn(b"Error", process.stderr)

        foreign = encode(minimal_document("foreign-1"))
        request = {
            "operation": "validateD",
            "primary": base64.b64encode(foreign).decode(),
            "annexes": {},
        }
        process = subprocess.run(
            [sys.executable, str(cli)],
            input=encode(request),
            capture_output=True,
            check=False,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        response = json.loads(process.stdout)
        self.assertEqual(response["report"]["results"][0]["verdict"], "fail")
        self.assertEqual(response["report"]["contract"], "agsdl-0.1.0")


class ByteAndAnnexTests(unittest.TestCase):
    def test_normative_syntax_offsets_are_byte_offsets(self):
        cases = ((b'"\\ud800"', 1), (b'"\xe2X"', 2), (b'"\xe2\x82', 3))
        for source, expected in cases:
            with self.subTest(source=source):
                report = read("inspect", source)["report"]
                finding = findings(report, "P-SYNTAX", "fail")[0]
                self.assertEqual(finding["location"], {"byte": expected})

    def test_opaque_slice_uses_original_utf8_bytes(self):
        document = minimal_document()
        document["runtime"] = {"note": "é"}
        source = encode(document)
        report = read("validateD", source)["report"]
        runtime_slice = next(
            item
            for item in report["inventory"]["opaque"]
            if item["pointer"] == "/runtime"
        )
        self.assertEqual(
            source[runtime_slice["start"] : runtime_slice["end"]],
            b'{"note":"\xc3\xa9"}',
        )

    def test_resolve_graph_uses_the_supplied_annex_map(self):
        annex = official_fixture("annex-interface-operation--dep.json")
        annex_source = encode(annex)
        primary = official_fixture("annex-interface-operation.json")
        dependency = next(
            item for item in primary["dependencies"] if item["id"] == "dep"
        )
        dependency["sha256"] = hashlib.sha256(annex_source).hexdigest()
        primary_source = encode(primary)

        response = read("resolveG", primary_source, {"dep": annex_source})
        report = response["report"]
        self.assertEqual(report["results"][-1]["verdict"], "pass")
        self.assertEqual(
            [item["id"] for item in report["inputs"]],
            ["primary", "annex/dep"],
        )
        self.assertTrue(
            any(result["input"] == "annex/dep" for result in report["results"])
        )

    def test_failed_annex_d_blocks_the_primary_g_prerequisite(self):
        annex = json.loads(
            (HISTORICAL_FIXTURES / "annex-interface-operation--dep.json").read_bytes()
        )
        annex_source = encode(annex)
        primary = official_fixture("annex-interface-operation.json")
        dependency = next(
            item for item in primary["dependencies"] if item["id"] == "dep"
        )
        dependency["sha256"] = hashlib.sha256(annex_source).hexdigest()
        report = read("resolveG", encode(primary), {"dep": annex_source})["report"]
        primary_g = report["results"][-1]
        self.assertEqual(primary_g["verdict"], "fail")
        self.assertTrue(
            any(
                item["rule"] == "P-PREREQUISITE" and item["state"] == "blocked"
                for item in primary_g["checks"]
            )
        )

    def test_exchange_preserves_primary_and_annex_bytes(self):
        annex = b"arbitrary annex bytes\x00\xff"
        primary = minimal_document()
        primary["dependencies"].append(
            {
                "id": "raw",
                "rootKey": {"scope": "raw", "id": "package", "version": "1"},
                "status": "included",
                "requiredFor": ["exchange"],
                "sha256": hashlib.sha256(annex).hexdigest(),
            }
        )
        source = encode(primary)
        response = read("exchange", source, {"raw": annex})
        self.assertEqual(
            response["artifacts"],
            {"primary": source, "annex/raw": annex},
        )


class GraphAndRuntimeTests(unittest.TestCase):
    def test_readable_agent_failure_survives_an_unreadable_relation(self):
        document = official_fixture("modular-system.json")
        document["relations"].append(copy.deepcopy(document["relations"][0]))
        document["relations"].append({})
        report = read("validateD", encode(document))["report"]
        self.assertTrue(
            any(
                item["location"] == {"pointer": "/definitions/0"}
                for item in findings(report, "D-AGENT", "fail")
            )
        )
        self.assertTrue(checks(report, "D-AGENT", "blocked"))

    def test_duplicate_binding_findings_point_to_the_later_binding(self):
        document = official_fixture("modular-system.json")
        bindings = document["runtime"]["configurations"][0]["agents"]
        bindings.append(copy.deepcopy(bindings[0]))
        report = read("validateR", encode(document))["report"]
        locations = {
            item["location"]["pointer"]
            for item in findings(report, "R-BINDING", "fail")
            if "missing or duplicate AgentBinding" in item["details"]
        }
        self.assertIn("/runtime/configurations/0/agents/2", locations)
        self.assertNotIn("/runtime/configurations/0", locations)

        document = official_fixture("modular-system.json")
        tools = document["runtime"]["configurations"][0]["agents"][0]["tools"]
        tools.append(copy.deepcopy(tools[0]))
        report = read("validateR", encode(document))["report"]
        locations = {
            item["location"]["pointer"]
            for item in findings(report, "R-TOOL", "fail")
            if "missing or duplicate required ToolBinding" in item["details"]
        }
        self.assertIn("/runtime/configurations/0/agents/0/tools/1", locations)
        self.assertNotIn("/runtime/configurations/0/agents/0", locations)

    def test_missing_and_duplicate_agent_locations_are_both_retained(self):
        document = official_fixture("modular-system.json")
        bindings = document["runtime"]["configurations"][0]["agents"]
        bindings.pop(1)
        bindings.append(copy.deepcopy(bindings[0]))
        report = read("validateR", encode(document))["report"]
        locations = {
            item["location"]["pointer"]
            for item in findings(report, "R-BINDING", "fail")
            if "missing or duplicate AgentBinding" in item["details"]
        }
        self.assertIn("/runtime/configurations/0", locations)
        self.assertIn("/runtime/configurations/0/agents/1", locations)

    def test_unreadable_binding_does_not_invent_a_missing_agent(self):
        document = official_fixture("modular-system.json")
        bindings = document["runtime"]["configurations"][0]["agents"]
        bindings[1] = {}
        bindings.append(copy.deepcopy(bindings[0]))
        report = read("validateR", encode(document))["report"]
        locations = {
            item["location"]["pointer"]
            for item in findings(report, "R-BINDING", "fail")
            if "missing or duplicate AgentBinding" in item["details"]
        }
        self.assertNotIn("/runtime/configurations/0", locations)
        self.assertIn("/runtime/configurations/0/agents/2", locations)
        self.assertTrue(checks(report, "R-BINDING", "blocked"))

    def test_external_tool_states_stay_on_ref_fields(self):
        document = official_fixture("modular-system.json")
        tool_ref = {
            "dependency": "external-tools",
            "key": {"scope": "external", "id": "tool", "version": "1"},
        }
        document["dependencies"].append(
            {
                "id": "external-tools",
                "rootKey": {"scope": "external", "id": "package", "version": "1"},
                "status": "external",
                "requiredFor": [],
                "sha256": None,
            }
        )
        document["relations"].append(
            {
                "source": copy.deepcopy(document["definitions"][0]["key"]),
                "relation": "uses",
                "target": copy.deepcopy(tool_ref),
                "expectedKind": "Tool",
            }
        )
        expected_ref_paths = set()
        for configuration_index, configuration in enumerate(
            document["runtime"]["configurations"]
        ):
            for binding_index, binding in enumerate(configuration["agents"]):
                if binding["agent"]["id"] != "agent-a":
                    continue
                tool_index = len(binding["tools"])
                binding["tools"].append(
                    {"tool": copy.deepcopy(tool_ref), "choices": []}
                )
                expected_ref_paths.add(
                    f"/runtime/configurations/{configuration_index}/agents/"
                    f"{binding_index}/tools/{tool_index}/tool"
                )
        report = read("validateR", encode(document))["report"]
        external_states = {
            item["pointer"]
            for item in report["inventory"]["states"]
            if item["detail"] == "external target excluded"
        }
        self.assertTrue(expected_ref_paths <= external_states)
        self.assertFalse(
            any(path.rsplit("/tools/", 1)[0] in external_states for path in expected_ref_paths)
        )

    def test_g_and_r_keep_their_interpretation_boundaries(self):
        graph_document = official_fixture("modular-system.json")
        graph_document["runtime"] = 17
        graph_report = read("validateG", encode(graph_document))["report"]
        self.assertEqual(graph_report["results"][-1]["verdict"], "pass")
        self.assertFalse(
            any(
                item["location"].get("pointer", "").startswith("/runtime")
                for item in findings(graph_report, "P-SHAPE")
            )
        )

        runtime_document = official_fixture("modular-system.json")
        runtime_document["graphs"] = 17
        runtime_report = read("validateR", encode(runtime_document))["report"]
        self.assertFalse(
            any(
                item["location"].get("pointer", "").startswith("/graphs")
                for item in findings(runtime_report, "P-SHAPE")
            )
        )
        self.assertTrue(checks(runtime_report, "R-SELECTION", "blocked"))

    def test_sequential_approval_chain_and_refusal_bypass(self):
        document = official_fixture("approval-two-gates.json")
        report = read("validateG", encode(document))["report"]
        self.assertEqual(report["results"][-1]["verdict"], "pass")

        document = official_fixture("approval-two-gates.json")
        document["graphs"][0]["steps"][0]["denied"] = "call"
        report = read("validateG", encode(document))["report"]
        self.assertTrue(findings(report, "G-APPROVAL", "fail"))

    def test_applications_and_compatibility_remain_independent(self):
        document = official_fixture("modular-system.json")
        report = read("validateR", encode(document))["report"]
        self.assertEqual(report["results"][-1]["verdict"], "pass")
        self.assertIn(
            "declared-supported",
            {item["detail"] for item in report["inventory"]["states"]},
        )

        document = official_fixture("modular-system.json")
        binding = document["runtime"]["configurations"][0]["agents"][0]
        binding["applications"] = binding["applications"][1:]
        binding["claims"][0]["status"] = "unsupported"
        report = read("validateR", encode(document))["report"]
        self.assertTrue(findings(report, "R-CONTENT", "fail"))
        self.assertTrue(findings(report, "R-COMPATIBILITY", "fail"))
        self.assertTrue(findings(report, "R-COMPATIBILITY", "inconclusive"))

    def test_lossy_exchange_always_refuses_output(self):
        source = encode(minimal_document())
        response = read("lossyExchange", source)
        self.assertEqual(response["artifacts"], {})
        self.assertEqual(response["report"]["results"][0]["verdict"], "fail")
        self.assertEqual(response["report"]["losses"][0]["permission"], None)
        self.assertNotIn("candidate", json.dumps(response["report"]))



class PartialDocumentTests(unittest.TestCase):
    def test_relation_semantics_survive_an_extra_member(self):
        value = official_fixture('modular-system.json')
        relation = value['relations'][0]
        relation['target']['id'] = 'missing-principal'
        relation['extra'] = True
        actual = read('validateD', encode(value))['report']
        self.assertIn('/relations/0', {f['location']['pointer']
                      for f in findings(actual, 'D-REFERENCE', 'fail')})

    def test_partial_agent_keeps_an_observable_minimum_failure(self):
        value = official_fixture('modular-system.json')
        value['definitions'][0].pop('payload')
        value['relations'].append(copy.deepcopy(value['relations'][0]))
        actual = read('validateD', encode(value))['report']
        self.assertIn('/definitions/0', {f['location']['pointer']
                      for f in findings(actual, 'D-AGENT', 'fail')})
        self.assertFalse(any({'pointer': '/definitions/0'} in c['locations']
                             for c in checks(actual, 'D-AGENT', 'blocked')))

    def test_reference_uses_readable_key_and_kind_from_partial_definition(self):
        value = official_fixture('modular-system.json')
        value['definitions'][2].pop('payload')
        actual = read('validateD', encode(value))['report']
        self.assertFalse(any({'pointer': '/relations/0'} in c['locations']
                             for c in checks(actual, 'D-REFERENCE', 'blocked')))

    def test_dependency_extra_member_does_not_block_readable_rules(self):
        value = official_fixture('modular-system.json')
        value['dependencies'] = [{
            'id': 'a',
            'rootKey': {'scope': 'dep', 'id': 'root', 'version': '1'},
            'status': 'external',
            'requiredFor': [],
            'sha256': None,
            'extra': True,
        }]
        actual = read('validateD', encode(value))['report']
        for rule in ('D-DEPENDENCY', 'D-INTEGRITY'):
            self.assertTrue(checks(actual, rule, 'completed'))
            self.assertFalse(any({'pointer': '/dependencies/0'} in c['locations']
                                 for c in checks(actual, rule, 'blocked')))

    def test_readable_definition_identity_and_owner(self):
        value = official_fixture('modular-system.json')
        original = value['definitions'][0]
        value['definitions'].append({'key': copy.deepcopy(original['key']),
                                     'owner': dict(value['root']['key'], id='wrong')})
        actual = read('validateD', encode(value))['report']
        path = '/definitions/' + str(len(value['definitions']) - 1)
        for rule in ('D-IDENTITY', 'D-OWNER'):
            self.assertIn(path, {f['location']['pointer'] for f in findings(actual, rule, 'fail')})

    def test_partial_dependency_ids_do_not_invent_undeclared_annexes(self):
        for dependencies, duplicate in (([{'id': 'a'}], False),
                                        ([{'id': 'a'}, {'id': 'a'}], True),
                                        ([{}], False)):
            with self.subTest(dependencies=dependencies):
                value = official_fixture('modular-system.json')
                value['dependencies'] = dependencies
                actual = read('validateD', encode(value), {'a': b'bytes'})['report']
                failures = findings(actual, 'D-DEPENDENCY', 'fail')
                self.assertFalse(any(f['location'] == {'pointer': ''} for f in failures))
                self.assertEqual(any(f['location'] == {'pointer': '/dependencies/1'}
                                     for f in failures), duplicate)

    def test_partial_dependency_keeps_independent_checks(self):
        dep = {'id': 'a', 'rootKey': {'scope': 'dep', 'id': 'root', 'version': '1'},
               'status': 'included', 'requiredFor': ['validateD'], 'sha256': None}
        for field in ('id', 'rootKey', 'requiredFor', 'status', 'sha256'):
            with self.subTest(field=field):
                value = official_fixture('modular-system.json')
                first = copy.deepcopy(dep)
                later = copy.deepcopy(dep)
                later['requiredFor'] = ['validateD', 'validateD', None]
                later['status'] = 'external'
                later.pop(field)
                value['dependencies'] = [first, later]
                actual = read('validateD', encode(value), {'a': b'bytes'})['report']
                self.assertIn('/dependencies/1', {f['location']['pointer']
                              for f in findings(actual, 'D-DEPENDENCY', 'fail')})
                if field not in ('sha256', 'requiredFor'):
                    self.assertIn('/dependencies/1', {f['location']['pointer']
                                  for f in findings(actual, 'D-INTEGRITY', 'inconclusive')})
        value = official_fixture('modular-system.json')
        value['dependencies'] = [dict(dep, sha256='0' * 64)]
        value['dependencies'][0].pop('rootKey')
        actual = read('validateD', encode(value), {'a': b'bytes'})['report']
        self.assertTrue(findings(actual, 'D-INTEGRITY', 'fail'))

    def test_agent_excess_survives_an_unreadable_relation(self):
        value = official_fixture('modular-system.json')
        value['relations'].extend([copy.deepcopy(value['relations'][0]), {}])
        actual = read('validateD', encode(value))['report']
        self.assertIn('/definitions/0', {f['location']['pointer']
                      for f in findings(actual, 'D-AGENT', 'fail')})

if __name__ == '__main__':
    unittest.main()
