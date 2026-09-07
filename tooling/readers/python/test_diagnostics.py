"""Field prerequisites from spec/reports.md and spec/runtime.md.

The 0009 ledger supplies mutation pointers, never expected reports. Assertions
cover determined obligations only; open aggregate and discriminant choices are
intentionally not exact report oracles.
"""
import json
import unittest

from agsdl_reader import read
from test_reader import REPOSITORY, checks, encode, findings

C = '/runtime/configurations/0'
B = C + '/agents/0'
SIBLING = C + '/agents/1'
INSTRUCTIONS = '/definitions/11/payload'
SKILL = '/definitions/12/payload'
TOOL = '/definitions/9/payload'
STEP = '/graphs/0/steps/0'


def document():
    return json.loads((REPOSITORY / 'examples/0.1.0/general-purpose-system.json').read_bytes())


def delete(value, pointer):
    parts = pointer.strip('/').split('/')
    for part in parts[:-1]:
        value = value[int(part)] if isinstance(value, list) else value[part]
    del value[parts[-1]]


def blocked(report, rule):
    return {location['pointer'] for check in checks(report, rule, 'blocked')
            for location in check['locations']}


def finding_locations(report, rule, outcome='fail'):
    return {item['location']['pointer'] for item in findings(report, rule, outcome)}


class DiagnosticPrerequisiteTests(unittest.TestCase):
    def report(self, pointer, operation='validateR', source=None):
        source = document() if source is None else source
        delete(source, pointer)
        report = read(operation, encode(source))['report']
        parent = pointer.rsplit('/', 1)[0]
        self.assertIn(parent, finding_locations(report, 'P-SHAPE'))
        self.assertEqual(report['results'][-1]['verdict'], 'fail')
        return report

    def completed(self, report, rule):
        self.assertEqual(checks(report, rule, 'completed'),
                         [{'rule': rule, 'state': 'completed', 'locations': []}])

    def test_all_ledger_missing_fields_fail_shape_at_parent(self):
        ledger = json.loads((REPOSITORY / 'docs/reviews/0009-0.1.1-diagnostic-expectations.json').read_bytes())
        for case in ledger['cases']:
            with self.subTest(pointer=case['remove']):
                self.report(case['remove'], case['operation'])

    def test_root_kind_and_empty_export_domain_are_independent_of_key(self):
        report = self.report('/root/key', 'validateD')
        self.completed(report, 'D-EXPORT')
        self.assertNotIn('/exports', blocked(report, 'D-EXPORT'))
        report = self.report('/root/kind', 'validateD')
        self.completed(report, 'D-EXPORT')
        self.assertIn('/exports', blocked(report, 'D-EXPORT'))

    def test_nonempty_export_keeps_unreadable_root_identity_blocked(self):
        source = document()
        source['root']['kind'] = 'PackageVersion'
        source['exports'] = [source['definitions'][0]['key']]
        report = self.report('/root/key', 'validateD', source)
        self.assertIn('/exports/0', blocked(report, 'D-EXPORT'))
        self.completed(report, 'D-EXPORT')

    def test_missing_configuration_enumeration_is_not_empty(self):
        report = self.report('/runtime/configurations')
        for rule in ('R-SELECTION', 'R-BINDING', 'R-TOOL', 'R-CONTENT', 'R-COMPATIBILITY'):
            self.assertIn('/runtime', blocked(report, rule))
            self.assertFalse(checks(report, rule, 'completed'))

    def test_missing_configuration_id_keeps_independent_selection_checks(self):
        report = self.report(C + '/id')
        self.assertTrue({'/runtime', C} <= blocked(report, 'R-SELECTION'))
        self.completed(report, 'R-SELECTION')

    def test_missing_selected_bindings_blocks_assessment(self):
        report = self.report(C + '/agents')
        self.assertIn(C, blocked(report, 'R-COMPATIBILITY'))
        self.assertFalse(checks(report, 'R-COMPATIBILITY', 'completed'))
        self.completed(report, 'R-BINDING')
        self.completed(report, 'R-SELECTION')

    def test_missing_agent_blocks_coverage_and_keeps_sibling_findings(self):
        source = document()
        sibling = source['runtime']['configurations'][0]['agents'][1]
        sibling['claims'][0]['status'] = 'unsupported'
        report = self.report(B + '/agent', source=source)
        self.assertTrue({B, C} <= blocked(report, 'R-BINDING'))
        self.assertTrue({B, B + '/applications/0', B + '/applications/1'} <= blocked(report, 'R-CONTENT'))
        self.assertTrue({B, B + '/tools/0'} <= blocked(report, 'R-TOOL'))
        self.assertTrue({B, B + '/tools/0'} <= blocked(report, 'R-COMPATIBILITY'))
        self.assertIn(SIBLING, finding_locations(report, 'R-COMPATIBILITY'))
        self.completed(report, 'R-BINDING')

    def test_absent_engine_or_claims_is_not_null_or_empty(self):
        for field in ('engine', 'claims'):
            with self.subTest(field=field):
                source = document()
                choice = source['runtime']['configurations'][0]['agents'][0]['tools'][0]['choices'][0]
                choice['claims'][0]['status'] = 'unsupported'
                report = self.report(B + '/' + field, source=source)
                self.assertIn(B, blocked(report, 'R-COMPATIBILITY'))
                self.assertNotIn(B, finding_locations(report, 'R-COMPATIBILITY', 'inconclusive'))
                self.assertIn(B + '/tools/0', finding_locations(report, 'R-COMPATIBILITY'))
                self.assertFalse(any(state['pointer'] == B for state in report['inventory']['states']))

    def test_absent_engine_keeps_independent_missing_application(self):
        source = document()
        source['runtime']['configurations'][0]['agents'][0]['applications'] = []
        report = self.report(B + '/engine', source=source)
        self.assertIn(B, finding_locations(report, 'R-CONTENT'))
        self.assertIn(B, finding_locations(report, 'R-COMPATIBILITY', 'inconclusive'))
        self.assertIn(B, blocked(report, 'R-COMPATIBILITY'))

    def test_missing_invoke_resources_keeps_readable_target_checks(self):
        source = document()
        source['graphs'][0]['steps'][0]['action'] = source['graphs'][0]['steps'][0]['agent']
        report = self.report(STEP + '/resources', 'validateG', source)
        self.assertIn(STEP, blocked(report, 'G-TARGET'))
        self.completed(report, 'G-TARGET')
        self.assertIn(STEP, finding_locations(report, 'G-TARGET'))

    def test_missing_discriminant_blocks_dependent_checks(self):
        report = self.report(STEP + '/kind', 'validateG')
        self.assertIn(STEP, blocked(report, 'G-TARGET'))

    def test_content_nonrequirements_do_not_block_semantics(self):
        for payload, fields in ((INSTRUCTIONS, ('body',)),
                                (SKILL, ('inputs', 'outputs', 'preconditions', 'completion'))):
            for field in fields:
                with self.subTest(field=field):
                    report = self.report(payload + '/' + field)
                    self.assertNotIn(payload, blocked(report, 'R-CONTENT'))
                    self.assertFalse({B, SIBLING} & blocked(report, 'R-COMPATIBILITY'))
                    self.completed(report, 'R-CONTENT')
                    self.completed(report, 'R-COMPATIBILITY')

    def test_missing_format_blocks_assessment_but_keeps_known_capabilities(self):
        source = document()
        for binding in source['runtime']['configurations'][0]['agents']:
            binding['claims'][0]['status'] = 'unsupported'
        report = self.report(INSTRUCTIONS + '/format', source=source)
        self.assertNotIn(INSTRUCTIONS, blocked(report, 'R-CONTENT'))
        self.assertTrue({B, SIBLING} <= blocked(report, 'R-COMPATIBILITY'))
        self.assertTrue({B, SIBLING} <= finding_locations(report, 'R-COMPATIBILITY'))
        self.completed(report, 'R-CONTENT')

    def test_open_content_dependencies_keep_observable_capability_findings(self):
        for pointer in (INSTRUCTIONS + '/target', INSTRUCTIONS + '/at', SKILL + '/tools'):
            with self.subTest(pointer=pointer):
                source = document()
                for binding in source['runtime']['configurations'][0]['agents']:
                    binding['claims'][0]['status'] = 'unsupported'
                report = self.report(pointer, source=source)
                self.assertTrue({B, SIBLING} <= finding_locations(report, 'R-COMPATIBILITY'))
                if pointer == SKILL + '/tools':
                    self.assertIn(SKILL, blocked(report, 'R-CONTENT'))
                # No exact aggregate oracle for target/at or Skill.tools.

    def test_missing_tool_semantic_fields_block_partial_rule(self):
        for field in ('action', 'failures', 'requires'):
            with self.subTest(field=field):
                report = self.report(TOOL + '/' + field)
                self.assertIn(TOOL, blocked(report, 'R-TOOL'))
                self.completed(report, 'R-TOOL')
                self.assertNotIn(TOOL, finding_locations(report, 'R-TOOL'))

    def test_tool_ports_do_not_supply_capability_assessment(self):
        for field in ('inputs', 'outputs'):
            with self.subTest(field=field):
                report = self.report(TOOL + '/' + field)
                self.assertFalse({B + '/tools/0', SIBLING + '/tools/0'} & blocked(report, 'R-COMPATIBILITY'))
                self.completed(report, 'R-TOOL')
                self.completed(report, 'R-COMPATIBILITY')
