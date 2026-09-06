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


class AuditRegressionTests(unittest.TestCase):
    def test_missing_engine_returns_a_blocked_report(self):
        value = fixture()
        value['runtime']['configurations'][0]['agents'][0].pop('engine')
        actual = report(value)
        pointer = '/runtime/configurations/0/agents/0'
        self.assertTrue(any(item['location']['pointer'] == pointer
                            for item in findings(actual, 'P-SHAPE', 'fail')))
        self.assertTrue(any(check['rule'] == 'R-BINDING' and check['state'] == 'blocked'
                            and {'pointer': pointer} in check['locations']
                            for check in actual['results'][-1]['checks']))

    def test_content_requirement_duplicates_are_rejected(self):
        value = fixture()
        value['definitions'][11]['payload']['requires'] = [
            {'identity': 'example/text', 'version': '1'},
            {'identity': 'example/text', 'version': '1'},
        ]
        requirement = value['definitions'][12]['payload']['requires'][0]
        value['definitions'][12]['payload']['requires'].append(copy.deepcopy(requirement))
        actual = report(value)
        locations = {item['location']['pointer']
                     for item in findings(actual, 'R-CONTENT', 'fail')}
        self.assertIn('/definitions/11/payload', locations)
        self.assertIn('/definitions/12/payload', locations)

    def test_partial_catalogs_keep_independent_findings(self):
        value = fixture()
        binding = value['runtime']['configurations'][0]['agents'][0]
        binding['claims'][0]['status'] = 'unsupported'
        binding['claims'].append(None)
        binding['tools'].append(None)
        binding['tools'][0]['selected'] = 'missing'
        actual = report(value)
        self.assertTrue(findings(actual, 'R-COMPATIBILITY', 'fail'))
        self.assertTrue(any(item['location']['pointer'].endswith('/tools/0')
                            for item in findings(actual, 'R-TOOL', 'fail')))

    def test_missing_choice_catalog_returns_a_blocked_report(self):
        value = fixture()
        value['runtime']['configurations'][0]['agents'][0]['tools'][0].pop('choices')
        actual = report(value)
        pointer = '/runtime/configurations/0/agents/0/tools/0'
        self.assertTrue(any(check['rule'] == 'R-TOOL' and check['state'] == 'blocked'
                            and {'pointer': pointer} in check['locations']
                            for check in actual['results'][-1]['checks']))

    def test_unreadable_skill_closure_does_not_invent_unreachable_applications(self):
        value = fixture()
        value['definitions'][12]['payload']['dependencies'] = None
        actual = report(value)
        self.assertFalse(any('Application content is not reachable' in item['details']
                             for item in findings(actual, 'R-CONTENT', 'fail')))
        self.assertTrue(any(check['rule'] == 'R-CONTENT' and check['state'] == 'blocked'
                            for check in actual['results'][-1]['checks']))

    def test_skill_tools_are_typed_and_external_refs_are_visible(self):
        value = fixture()
        value['definitions'][12]['payload']['tools'].append(
            copy.deepcopy(value['definitions'][11]['key']))
        actual = report(value)
        self.assertTrue(any(item['location']['pointer'] == '/definitions/12/payload'
                            for item in findings(actual, 'R-CONTENT', 'fail')))

        value = fixture()
        value['dependencies'].append({
            'id': 'external-tools',
            'rootKey': {'scope': 'external', 'id': 'package', 'version': '1'},
            'status': 'external', 'requiredFor': [], 'sha256': None,
        })
        value['definitions'][12]['payload']['tools'].append({
            'dependency': 'external-tools',
            'key': {'scope': 'external', 'id': 'tool', 'version': '1'},
        })
        actual = report(value)
        pointer = '/definitions/12/payload/tools/1'
        self.assertIn('external target excluded',
                      {item['detail'] for item in states(actual, pointer)})

    def test_required_tool_payload_is_observed_without_a_binding(self):
        value = fixture()
        for configuration in value['runtime']['configurations']:
            for binding in configuration['agents']:
                binding['tools'] = []
        value['definitions'][9]['payload']['effects'] = 'invalid'
        actual = report(value)
        pointer = '/definitions/9/payload/effects'
        self.assertTrue(any(item['location']['pointer'] == pointer
                            for item in findings(actual, 'P-SHAPE', 'fail')))
        self.assertNotIn('/definitions/9/payload',
                         {item['pointer'] for item in actual['inventory']['opaque']})

    def test_ambiguous_agent_and_unreadable_graph_block_aggregates(self):
        value = fixture()
        value['definitions'].append(copy.deepcopy(value['definitions'][0]))
        actual = report(value)
        agent = '/runtime/configurations/0/agents/0'
        tool = agent + '/tools/0'
        self.assertIn('blocked', {item['detail'] for item in states(actual, agent)})
        self.assertIn('blocked', {item['detail'] for item in states(actual, tool)})

        value = fixture()
        value.pop('graphs')
        actual = report(value)
        self.assertIn('blocked', {item['detail'] for item in states(actual, agent)})
        self.assertIn('blocked', {item['detail'] for item in states(actual, tool)})

    def test_present_null_selection_blocks_compatibility(self):
        value = fixture()
        value['runtime']['selected'] = None
        actual = report(value)
        checks = actual['results'][-1]['checks']
        self.assertTrue(any(check['rule'] == 'R-COMPATIBILITY'
                            and check['state'] == 'blocked' for check in checks))
        self.assertFalse(any(check['rule'] == 'R-COMPATIBILITY'
                             and check['state'] == 'excluded' for check in checks))

    def test_unreadable_tool_identity_blocks_coverage(self):
        value = fixture()
        binding = value['runtime']['configurations'][0]['agents'][0]
        binding['tools'][0]['tool'] = None
        actual = report(value)
        pointer = '/runtime/configurations/0/agents/0'
        self.assertFalse(any(item['location']['pointer'] == pointer
                             and 'missing or duplicate required ToolBinding' in item['details']
                             for item in findings(actual, 'R-TOOL', 'fail')))
        self.assertTrue(any(check['rule'] == 'R-TOOL' and check['state'] == 'blocked'
                            and {'pointer': pointer} in check['locations']
                            for check in actual['results'][-1]['checks']))

    def test_extra_application_field_keeps_order_and_parameter_slices(self):
        value = fixture()
        value['runtime']['configurations'][0]['agents'][0]['applications'][0]['extra'] = True
        actual = report(value)
        self.assertFalse(any('Skill dependency Application must be earlier' in item['details']
                             for item in findings(actual, 'R-CONTENT', 'fail')))
        opaque = {item['pointer'] for item in actual['inventory']['opaque']}
        prefix = '/runtime/configurations/0/agents/0'
        self.assertTrue({prefix + '/parameters',
                         prefix + '/tools/0/choices/0/parameters',
                         prefix + '/applications/0/parameters',
                         prefix + '/applications/1/parameters'} <= opaque)

    def test_custom_kind_at_typed_tool_returns_a_cli_report(self):
        value = fixture()
        value['definitions'][9]['kind'] = {
            'extension': {'identity': 'example/custom', 'version': '1'},
            'name': 'CustomTool',
        }
        value['extensions'].append({
            'identity': 'example/custom', 'version': '1',
            'operations': {'validateD': 'required', 'validateR': 'required'},
            'payload': {},
        })
        request = {'operation': 'validateR', 'primary': base64.b64encode(raw(value)).decode(),
                   'annexes': {}}
        process = subprocess.run([sys.executable, str(Path(__file__).with_name('cli.py'))],
                                 input=json.dumps(request).encode(), capture_output=True,
                                 check=False)
        self.assertEqual(process.returncode, 0, process.stderr)
        actual = json.loads(process.stdout)['report']
        self.assertTrue(findings(actual, 'R-TOOL', 'fail'))

    def test_duplicate_agent_bindings_block_only_affected_aggregates(self):
        value = fixture()
        bindings = value['runtime']['configurations'][0]['agents']
        bindings.append(copy.deepcopy(bindings[0]))
        actual = report(value)
        prefix = '/runtime/configurations/0/agents/'
        for suffix in ('0', '0/tools/0', '2', '2/tools/0'):
            self.assertIn('blocked',
                          {item['detail'] for item in states(actual, prefix + suffix)})
        self.assertIn('declared-supported',
                      {item['detail'] for item in states(actual, prefix + '1')})

    def test_unreadable_earlier_application_blocks_order_conclusion(self):
        value = fixture()
        binding = value['runtime']['configurations'][0]['agents'][0]
        binding['applications'][0]['content'] = None
        actual = report(value)
        pointer = '/runtime/configurations/0/agents/0/applications/1'
        self.assertFalse(any(item['location']['pointer'] == pointer
                             and 'Skill dependency Application must be earlier'
                             in item['details']
                             for item in findings(actual, 'R-CONTENT', 'fail')))
        self.assertTrue(any(check['rule'] == 'R-CONTENT' and check['state'] == 'blocked'
                            and {'pointer': pointer} in check['locations']
                            for check in actual['results'][-1]['checks']))

    def test_duplicate_tool_bindings_block_only_their_aggregates(self):
        value = fixture()
        tools = value['runtime']['configurations'][0]['agents'][0]['tools']
        tools.append(copy.deepcopy(tools[0]))
        actual = report(value)
        prefix = '/runtime/configurations/0/agents/0/tools/'
        for index in ('0', '1'):
            self.assertIn('blocked',
                          {item['detail'] for item in states(actual, prefix + index)})
        self.assertTrue(any('missing or duplicate required ToolBinding' in item['details']
                            for item in findings(actual, 'R-TOOL', 'fail')))

    def test_extra_claim_field_keeps_known_incompatibility(self):
        value = fixture()
        claim = value['runtime']['configurations'][0]['agents'][0]['claims'][0]
        claim['status'] = 'unsupported'
        claim['extra'] = True
        actual = report(value)
        pointer = '/runtime/configurations/0/agents/0'
        self.assertTrue(any(item['location']['pointer'] == pointer
                            for item in findings(actual, 'R-COMPATIBILITY', 'fail')))

    def test_extra_implementation_claim_field_keeps_known_incompatibility(self):
        value = fixture()
        claim = (value['runtime']['configurations'][0]['agents'][0]
                 ['tools'][0]['choices'][0]['claims'][0])
        claim['status'] = 'unsupported'
        claim['extra'] = True
        actual = report(value)
        pointer = '/runtime/configurations/0/agents/0/tools/0'
        self.assertTrue(any(item['location']['pointer'] == pointer
                            for item in findings(actual, 'R-COMPATIBILITY', 'fail')))


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

    def test_operation_fields_remain_independently_checkable(self):
        value = fixture()
        operation = value['definitions'][4]['payload']['operations'][0]
        operation['extra'] = True
        operation['action']['id'] = 'missing'
        actual = report(value, 'validateG')
        self.assertTrue(any(item['location']['pointer'] ==
                            '/definitions/4/payload/operations/0'
                            for item in findings(actual, 'G-TARGET', 'fail')))

    def test_unreadable_invoke_operation_blocks_lookup(self):
        for replacement in ('missing', 'null'):
            with self.subTest(replacement=replacement):
                value = fixture()
                if replacement == 'missing':
                    value['graphs'][0]['steps'][0].pop('operation')
                else:
                    value['graphs'][0]['steps'][0]['operation'] = None
                actual = report(value, 'validateG')
                pointer = '/graphs/0/steps/0'
                self.assertFalse(any(item['location']['pointer'] == pointer
                                     and 'selected Interface operation does not exist'
                                     in item['details']
                                     for item in findings(actual, 'G-TARGET', 'fail')))
                self.assertTrue(any(check['rule'] == 'G-TARGET'
                                    and check['state'] == 'blocked'
                                    and {'pointer': pointer} in check['locations']
                                    for check in actual['results'][-1]['checks']))

    def test_approved_successor_kind_is_checked_when_paths_fail(self):
        value = fixture('approval-two-gates.json')
        value['graphs'][0]['steps'][0]['approved'] = 'ok'
        value['graphs'][0]['steps'][2]['success'] = 'call'
        actual = report(value, 'validateG')
        self.assertTrue(findings(actual, 'G-PATH', 'fail'))
        self.assertTrue(any(item['location']['pointer'] == '/graphs/0/steps/0'
                            for item in findings(actual, 'G-APPROVAL', 'fail')))

    def test_unreadable_approval_fields_do_not_invent_chain_failures(self):
        mutations = (
            lambda graph: graph['steps'][0].update(call=None),
            lambda graph: graph['steps'][1].update(call=None),
            lambda graph: graph['steps'][1].update(kind='invalid'),
        )
        invented = ('approval chain changes call', 'approved chain does not reach call',
                    'call must have one final approved gate',
                    'approved invoke differs from call',
                    'approved successor is not a gate or call')
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                value = fixture('approval-two-gates.json')
                mutate(value['graphs'][0])
                actual = report(value, 'validateG')
                details = ' '.join(item['details']
                                   for item in findings(actual, 'G-APPROVAL', 'fail'))
                self.assertFalse(any(detail in details for detail in invented))
                self.assertTrue(any(check['rule'] == 'G-APPROVAL'
                                    and check['state'] == 'blocked'
                                    for check in actual['results'][-1]['checks']))

    def test_known_bad_successor_kind_survives_unreadable_call(self):
        value = fixture('approval-two-gates.json')
        gate = value['graphs'][0]['steps'][0]
        gate['call'] = None
        gate['approved'] = 'ok'
        actual = report(value, 'validateG')
        self.assertTrue(any(item['location']['pointer'] == '/graphs/0/steps/0'
                            and 'approved successor is not a gate or call'
                            in item['details']
                            for item in findings(actual, 'G-APPROVAL', 'fail')))


if __name__ == '__main__':
    unittest.main()
