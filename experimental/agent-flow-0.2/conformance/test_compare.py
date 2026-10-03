"""Fault-oriented checks for the neutral comparison, not reader internals."""
from copy import deepcopy
from contextlib import redirect_stdout
import io
from decimal import Decimal
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
from compare import agree, canonical, decode, exact, run, validate
from cases import cases

REPORT = {'contract':'agsdl-exp-flow-0.2-c1', 'valid':True,
          'scope':'document-shape-and-declared-references','executionSupport':'not-assessed',
          'findings':[],'sources':[],'support':[],'coreNeeds':[],'unassessed':[]}
CASE = {'name':'fault','bytes':b'{}','codes':[],'assertions':{},'source':'comparator self-test'}


class ComparatorFaults(unittest.TestCase):
    def test_malformed_report_does_not_abort_remaining_cases(self):
        for broken in [None, [], {}, {'findings': None}, dict(REPORT, findings=[None]),
                       dict(REPORT, sources={}), dict(REPORT, expandedFlow={})]:
            with self.subTest(broken=broken), tempfile.TemporaryDirectory() as tmp:
                replies = iter([broken, REPORT, REPORT, REPORT])
                def response(*args, **kwargs):
                    return subprocess.CompletedProcess(args[0], 0, json.dumps(next(replies)).encode(), b'')
                with patch('compare.cases', return_value=[CASE, dict(CASE, name='after-fault')]), patch('compare.subprocess.run', side_effect=response):
                    with redirect_stdout(io.StringIO()):
                        failed = run(Path(tmp))
                summary = json.loads((Path(tmp)/'summary.json').read_text())
                self.assertTrue(failed)
                self.assertEqual(summary['count'], 2)
                self.assertTrue(summary['cases'][1]['agreement'])

    def paired_fault(self, bad, case=CASE, expected_error=None):
        with tempfile.TemporaryDirectory() as tmp:
            raw = bad if isinstance(bad, bytes) else json.dumps(bad).encode()
            replies = iter([raw, raw, json.dumps(REPORT).encode(), json.dumps(REPORT).encode()])
            def response(*args, **kwargs):
                return subprocess.CompletedProcess(args[0], 0, next(replies), b'')
            with patch('compare.cases', return_value=[case, dict(CASE, name='after-fault')]), patch('compare.subprocess.run', side_effect=response), redirect_stdout(io.StringIO()):
                self.assertTrue(run(Path(tmp)))
            summary = json.loads((Path(tmp)/'summary.json').read_text())
            self.assertEqual(summary['count'], 2)
            self.assertEqual(summary['failures'], 2)
            self.assertTrue(summary['cases'][1]['agreement'])
            self.assertEqual(summary['cases'][1]['readers'], {'python': [], 'javascript': []})
            if expected_error:
                for errors in summary['cases'][0]['readers'].values():
                    self.assertTrue(any(expected_error in e for e in errors), errors)

    def test_unsupported_decimal_exponent_rejects_both_reports_and_continues(self):
        self.paired_fault(b'{"number":1e9999999999999999999999}', expected_error='unsupported report numeric representation')
        with self.assertRaises(ValueError):
            decode('{"number":1e9999999999999999999999}')

    def test_identical_malformed_requirements_are_not_agreement_evidence(self):
        for requirement in [{}, {'contract': {}}, {'contract': {'identity':'x','version':1}},
                            {'contract': {'identity':'x','version':'1'}, 'parameters': []},
                            {'contract': {'identity':'x','version':'1'}, 'extra': True}]:
            with self.subTest(requirement=requirement):
                broken = deepcopy(REPORT)
                broken['support'] = [{'path':'/bindings/e', 'status':'unknown', 'requirements':[
                    {'requirement':requirement, 'status':'unknown'}]}]
                self.paired_fault(broken, expected_error='invalid requirement assessment')

    def test_identical_malformed_expanded_records_are_rejected(self):
        case = next(c for c in cases() if c['name'] == 'composition-origin')
        clean = deepcopy(REPORT)
        clean['expandedFlow'] = {'entry':['use','a'], 'steps':[{
            'address':['use','a'], 'source':'/compositions/part/steps/a', 'invocation':'/flow/steps/use',
            'step':{'type':'agent','agent':'worker','next':[]}}]}
        mutations = [
            lambda r: r['expandedFlow'].update(entry=['bad/name']),
            lambda r: r['expandedFlow']['steps'][0].update(address=['a','b','c']),
            lambda r: r['expandedFlow']['steps'][0].update(source='not a pointer'),
            lambda r: r['expandedFlow']['steps'][0].update(invocation='/bad~2pointer'),
            lambda r: r['expandedFlow']['steps'][0].update(step={}),
            lambda r: r['expandedFlow']['steps'][0].update(step={'type':'unknown'}),
            lambda r: r['expandedFlow']['steps'][0].update(step={'type':'agent'}),
            lambda r: r['expandedFlow']['steps'][0]['step'].update(next=['a']),
            lambda r: r['expandedFlow']['steps'][0]['step'].update(next=[['bad/name']]),
            lambda r: r['expandedFlow']['steps'][0]['step'].update(agent=''),
            lambda r: r['expandedFlow']['steps'][0]['step'].update(maxVisits=True),
            lambda r: r['expandedFlow']['steps'][0]['step'].update(extra=True),
        ]
        for mutation in mutations:
            broken=deepcopy(clean);mutation(broken)
            with self.subTest(broken=broken):
                self.paired_fault(broken, case, 'invalid expanded')
        self.assertEqual(validate(clean, case), [])
        self.paired_fault(REPORT, case, 'expanded flow presence')

    def test_pointers_and_stage_presence_are_structural_boundaries(self):
        for field, value in [('sources', [{'path':'bad','baseUri':None,'uri':'x','resolved':None,'status':'unresolved'}]),
                             ('coreNeeds', [{'path':'/bad~3','need':'x','status':'unassessed'}]),
                             ('unassessed', ['/bad~']),
                             ('findings', [{'code':'REFERENCE','path':'not-pointer'}])]:
            broken=deepcopy(REPORT);broken[field]=value
            with self.subTest(field=field):
                self.paired_fault(broken)
        broken=deepcopy(REPORT)
        broken.update(valid=False, scope='parse', findings=[{'code':'PARSE','path':''}])
        self.paired_fault(broken, dict(CASE,codes=['PARSE']), 'observations after parse or shape failure')
        broken.pop('sources');broken.pop('support');broken.pop('coreNeeds');broken.pop('unassessed')
        self.assertEqual(validate(broken, dict(CASE,codes=['PARSE'])), [])
        broken=deepcopy(REPORT);broken.pop('sources')
        self.paired_fault(broken, expected_error='missing declaration observations')
        broken=deepcopy(REPORT);broken['expandedFlow']={'entry':['a'],'steps':[]}
        self.paired_fault(broken, expected_error='expanded flow presence')

    def test_documented_invalid_projection_placeholders_remain_structurally_valid(self):
        case = next(c for c in cases() if c['name'] == 'composition-parameter')
        broken=deepcopy(REPORT)
        broken.update(valid=False, findings=[{'code':'COMPOSITION','path':'/flow/steps/use'},
            {'code':'REFERENCE','path':'/compositions/part/steps/a/agent','invocation':'/flow/steps/use'}])
        broken['expandedFlow']={'entry':['use','a'],'steps':[{'address':['use','a'],
            'source':'/compositions/part/steps/a','invocation':'/flow/steps/use',
            'step':{'type':'agent','agent':'','next':[]}}]}
        self.assertEqual(validate(broken,case), [])
        from report_shape import expanded_step
        gate = {'type':'approval','call':['use','a'],'binding':'engine','timeoutMs':1,
                'validForMs':1,'next':{'approved':[],'denied':[]}}
        self.assertTrue(expanded_step(gate, invalid_substitution=True))
        self.assertFalse(expanded_step(gate))

    def test_invalid_report_primitives_are_rejected(self):
        for broken in [[], None, {}, dict(REPORT, valid=1), dict(REPORT, findings=[{'code':'X'}]), dict(REPORT, sources={})]:
            self.assertTrue(validate(broken, CASE))
        with self.assertRaises(ValueError):
            decode('{"valid":true,"valid":false}')
        with self.assertRaises(ValueError):
            decode('{"value":NaN}')

    def test_comparison_preserves_numbers_booleans_and_declaration_array_order(self):
        self.assertNotEqual(exact(True), exact(1))
        self.assertEqual(exact(Decimal('1.00')), exact(1))
        self.assertNotEqual(exact(Decimal('9007199254740992.1')), exact(9007199254740992))
        left = deepcopy(REPORT)
        left['support'] = [{'path':'/agents/a','requirements':[{'requirement':{'parameters':{'order':[1,2]}}}]}]
        right = deepcopy(left)
        right['support'][0]['requirements'][0]['requirement']['parameters']['order'].reverse()
        self.assertNotEqual(canonical(left), canonical(right))

    def test_comparison_preserves_all_observation_fields_and_multiplicity(self):
        left = deepcopy(REPORT)
        left['sources'] = [{'path':'/x','baseUri':None,'uri':'x','resolved':None,'status':'unresolved'}]
        left['coreNeeds'] = [{'path':'/a','need':'queued-delivery','status':'unassessed'}]
        left['support'] = [{'path':'/a','status':'unknown','requirements':[]}]
        left['unassessed'] = ['/x']
        left['expandedFlow'] = {'entry':['a'],'steps':[{'address':['a'],'source':'/flow/steps/a','invocation':None,'step':{'type':'prepare','message':{}}}]}
        for field in ['sources','coreNeeds','support','unassessed','expandedFlow']:
            right=deepcopy(left);right.pop(field)
            self.assertNotEqual(canonical(left),canonical(right),field)
        right=deepcopy(left);right['expandedFlow']['steps'][0]['invocation']='/flow/steps/use'
        self.assertNotEqual(canonical(left),canonical(right))
        right=deepcopy(left);right['sources']*=2
        self.assertNotEqual(canonical(left),canonical(right))

    def test_observation_order_and_unicode_object_order_are_nonsemantic(self):
        left=deepcopy(REPORT);left['coreNeeds']=[{'path':'/𐀀','need':'x'},{'path':'/\ue000','need':'y'}]
        right=deepcopy(left);right['coreNeeds'].reverse()
        self.assertEqual(canonical(left),canonical(right))
        self.assertEqual(exact({'𐀀':1,'\ue000':2}),exact({'\ue000':2,'𐀀':1}))

    def test_case_factory_has_no_mutation_leak_and_covers_every_document_rule(self):
        first=cases();second=cases()
        self.assertEqual(first,second)
        self.assertEqual(len({x['name'] for x in first}),len(first))
        self.assertEqual(set(c for x in first for c in x['codes']), {
            'PARSE','SHAPE','REFERENCE','DUPLICATE','RESOURCE_COLLISION','OUTPUT_FORMAT','ROUTES','STEERING',
            'JOIN_POLICY','JOIN_GROUP','UNREACHABLE','COMPOSITION','APPROVAL','SCOPE','VALUE_SCHEMA','URI','SOURCE','CLAIM'})


if __name__ == '__main__':
    unittest.main()
