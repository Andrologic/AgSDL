"""Focused implementation tests for the modular candidate-1 Python reader."""
import base64
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

from reader import read
from lossless import dumps


ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / 'fixtures'
SPEC = importlib.util.spec_from_file_location('modular_compare', ROOT / 'compare-readers.py')
compare = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(compare)


def fixture(name='modular-system.json'):
    return json.loads((FIXTURES / name).read_bytes())


def raw(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()


def report(value, operation='validateR'):
    return read(operation, raw(value))['report']


def findings(value, rule, outcome=None):
    found = [item for result in value['results'] for item in result['findings'] if item['rule'] == rule]
    return [item for item in found if outcome is None or item['outcome'] == outcome]


def states(value, pointer):
    return [item for item in value['inventory']['states'] if item['pointer'] == pointer]


class CorpusTests(unittest.TestCase):
    def test_all_twenty_two_oracles(self):
        manifest = json.loads((FIXTURES / 'manifest.json').read_bytes())
        self.assertEqual(len(manifest['cases']), 22)
        for case in manifest['cases']:
            with self.subTest(case=case['name']):
                primary = (FIXTURES / case['primary']['path']).read_bytes()
                annexes = {name: (FIXTURES / item['path']).read_bytes() for name, item in case['annexes'].items()}
                response = read(case['operation'], primary, annexes)
                wire_response = compare.load(dumps({
                    'report': response['report'],
                    'artifacts': {name: base64.b64encode(data).decode() for name, data in response['artifacts'].items()},
                }).encode())
                source = {'primary': primary, **{'annex/' + name: data for name, data in annexes.items()}}
                self.assertEqual(compare.observe(case, wire_response, source), [])

    def test_seven_operations_keep_modular_marker(self):
        data = (FIXTURES / 'modular-system.json').read_bytes()
        for operation in ('inspect', 'validateD', 'validateG', 'resolveG', 'validateR', 'exchange', 'lossyExchange'):
            with self.subTest(operation=operation):
                response = read(operation, data)
                self.assertEqual(response['report']['contract'], 'proposal-0013-candidate-1')

    def test_cli_preserves_the_modular_envelope(self):
        data = (FIXTURES / 'modular-system.json').read_bytes()
        request = {'operation': 'validateR', 'primary': base64.b64encode(data).decode(), 'annexes': {}}
        process = subprocess.run([sys.executable, str(Path(__file__).with_name('cli.py'))],
                                 input=json.dumps(request).encode(), capture_output=True, check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        response = json.loads(process.stdout)
        self.assertEqual(set(response), {'report', 'artifacts'})
        self.assertEqual(response['report']['contract'], 'proposal-0013-candidate-1')


class StructuralTests(unittest.TestCase):
    def test_unselected_configuration_is_still_checked(self):
        value = fixture()
        choice = value['runtime']['configurations'][1]['agents'][0]['tools'][0]['choices'][0]
        value['runtime']['configurations'][1]['agents'][0]['tools'][0]['choices'].append(copy.deepcopy(choice))
        actual = report(value)
        self.assertTrue(findings(actual, 'R-TOOL', 'fail'))
        self.assertEqual(actual['results'][-1]['verdict'], 'fail')

    def test_malformed_tool_collection_keeps_content_checks(self):
        value = fixture()
        value['runtime']['configurations'][0]['agents'][0]['tools'] = None
        actual = report(value)
        result = actual['results'][-1]
        self.assertTrue(any(check['rule'] == 'R-TOOL' and check['state'] == 'blocked'
                            for check in result['checks']))
        self.assertTrue(any(check['rule'] == 'R-CONTENT' and check['state'] == 'completed'
                            for check in result['checks']))

    def test_unknown_tool_choice_blocks_its_assessment(self):
        value = fixture()
        tool = value['runtime']['configurations'][0]['agents'][0]['tools'][0]
        tool['selected'] = 'missing'
        actual = report(value)
        pointer = '/runtime/configurations/0/agents/0/tools/0'
        self.assertTrue(findings(actual, 'R-TOOL', 'fail'))
        self.assertIn('blocked', {item['detail'] for item in states(actual, pointer)})

    def test_duplicate_engine_claim_blocks_aggregate_but_keeps_known_failure(self):
        value = fixture()
        binding = value['runtime']['configurations'][0]['agents'][0]
        duplicate = copy.deepcopy(binding['claims'][0])
        duplicate['status'] = 'unsupported'
        binding['claims'].append(duplicate)
        binding['claims'][1]['status'] = 'unsupported'
        actual = report(value)
        pointer = '/runtime/configurations/0/agents/0'
        self.assertTrue(findings(actual, 'R-BINDING', 'fail'))
        self.assertTrue(findings(actual, 'R-COMPATIBILITY', 'fail'))
        self.assertIn('blocked', {item['detail'] for item in states(actual, pointer)})

    def test_missing_local_skill_dependency_is_not_provided(self):
        value = fixture()
        value['definitions'][12]['payload']['dependencies'][0]['id'] = 'missing'
        actual = report(value)
        pointer = '/runtime/configurations/0/agents/0'
        self.assertTrue(any(item['location']['pointer'] == '/definitions/12/payload'
                            for item in findings(actual, 'R-CONTENT', 'fail')))
        self.assertTrue(findings(actual, 'R-COMPATIBILITY', 'inconclusive'))
        self.assertIn('not-provided', {item['detail'] for item in states(actual, pointer)})

    def test_unreachable_application_is_rejected(self):
        value = fixture()
        binding = value['runtime']['configurations'][0]['agents'][0]
        extra = copy.deepcopy(binding['applications'][0])
        extra['content']['id'] = 'unrelated'
        value['definitions'].append({
            'key': {'scope': 'mvp', 'id': 'unrelated', 'version': '1'},
            'kind': 'Instructions', 'owner': value['root']['key'],
            'payload': {'target': 'Agent', 'at': 'before-invoke',
                        'format': {'identity': 'example/text', 'version': '1'},
                        'body': 'Unrelated.', 'requires': []},
        })
        binding['applications'].append(extra)
        actual = report(value)
        self.assertTrue(any(item['location']['pointer'].endswith('/applications/2')
                            for item in findings(actual, 'R-CONTENT', 'fail')))


class GraphTests(unittest.TestCase):
    def test_duplicate_selected_operation_blocks_lookup(self):
        value = fixture()
        interface = value['definitions'][4]['payload']['operations']
        interface.append(copy.deepcopy(interface[0]))
        actual = report(value, 'validateG')
        self.assertTrue(findings(actual, 'G-TARGET', 'fail'))
        self.assertTrue(any(check['rule'] == 'G-TARGET' and check['state'] == 'blocked'
                            for check in actual['results'][-1]['checks']))

    def test_unreadable_operation_index_does_not_invent_absence(self):
        value = fixture('operation-not-found.json')
        value['definitions'][4]['payload']['operations'][0]['id'] = None
        actual = report(value, 'validateG')
        step = '/graphs/0/steps/0'
        self.assertFalse(any(item['location']['pointer'] == step
                             for item in findings(actual, 'G-TARGET', 'fail')))
        self.assertTrue(any(check['rule'] == 'G-TARGET' and check['state'] == 'blocked'
                            and {'pointer': step} in check['locations']
                            for check in actual['results'][-1]['checks']))

    def test_outbound_operation_cannot_be_invoked(self):
        value = fixture()
        value['definitions'][4]['payload']['operations'][0]['direction'] = 'outbound'
        actual = report(value, 'validateG')
        self.assertTrue(any(item['location']['pointer'] == '/graphs/0/steps/0'
                            for item in findings(actual, 'G-TARGET', 'fail')))

    def test_parallel_gate_path_is_rejected(self):
        value = fixture('approval-two-gates.json')
        graph = value['graphs'][0]
        graph['inputs']['flag'] = 'boolean'
        graph['entry'] = 'branch'
        graph['steps'].insert(0, {'id': 'branch', 'kind': 'condition', 'test': {'input': 'flag'},
                                  'true': 'legal', 'false': 'finance', 'failure': 'failed'})
        graph['steps'][1]['approved'] = 'call'
        actual = report(value, 'validateG')
        self.assertTrue(findings(actual, 'G-APPROVAL', 'fail'))

    def test_later_gate_rejects_an_ordinary_incoming_edge(self):
        value = fixture('approval-two-gates.json')
        graph = value['graphs'][0]
        graph['inputs']['flag'] = 'boolean'
        graph['entry'] = 'branch'
        graph['steps'].insert(0, {'id': 'branch', 'kind': 'condition', 'test': {'input': 'flag'},
                                  'true': 'legal', 'false': 'finance', 'failure': 'failed'})
        actual = report(value, 'validateG')
        self.assertTrue(any(item['location']['pointer'] == '/graphs/0/steps/2'
                            for item in findings(actual, 'G-APPROVAL', 'fail')))


if __name__ == '__main__':
    unittest.main()
