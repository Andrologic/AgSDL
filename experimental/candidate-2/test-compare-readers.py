#!/usr/bin/env python3
"""Tests of comparison machinery using synthetic reports, never reader evidence."""
import base64
import copy
from decimal import Decimal
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("compare_readers", HERE / "compare-readers.py")
harness = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = harness
SPEC.loader.exec_module(harness)


def fixture(operation="inspect", raw=b"{}"):
    digest = hashlib.sha256(raw).hexdigest()
    result = {"input": "primary", "unit": operation, "phase": None,
              "verdict": "pass", "findings": [],
              "checks": [{"rule": "P-SYNTAX" if operation == "inspect" else "E-PRESERVE",
                          "state": "completed", "locations": []}]}
    states = [{"input": "primary", "pointer": "/" + field,
               "state": "absent", "detail": "Field is absent"}
              for field in ("graphs", "runtime", "dependencies")]
    response = {"report": {"contract": "proposal-0012-candidate-2",
        "processor": {"identity": "test/synthetic", "version": "1"},
        "operation": operation, "inputs": [{"id": "primary", "sha256": digest}],
        "results": [result], "inventory": {"tree": harness.load(raw.decode()),
        "states": states, "opaque": []}, "losses": [], "outputs": []}, "artifacts": {}}
    expected = {"results": [{key: result[key] for key in ("input", "unit", "phase", "verdict")}],
                "findings": {"mode": "exact", "items": []}, "checks": [],
                "states": [{key: value for key, value in state.items() if key != "detail"}
                           for state in states], "absentStates": [], "opaque": [],
                "absentOpaque": [], "preservation": "no-output"}
    if operation == "exchange":
        response["artifacts"] = {"primary": base64.b64encode(raw).decode()}
        response["report"]["outputs"] = [{"id": "primary", "sha256": digest}]
        expected["preservation"] = "exact-input-boundary"
    return {"name": "synthetic", "operation": operation, "expected": expected}, response, {"primary": raw}


class JsonTests(unittest.TestCase):
    def test_rejects_ambiguous_or_non_json_responses(self):
        for text in ('{"x":1,"x":2}', '{"a":{"x":1,"x":2}}', 'NaN',
                     'Infinity', '-Infinity', '"\\ud800"', '{"\\udfff":0}', '{} {}'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                harness.load(text)

    def test_numbers_remain_exact_and_distinct_from_booleans(self):
        values = harness.load('[true,1,1.0,9007199254740993,9007199254740992,1e400,1e-400]')
        self.assertNotEqual(harness.canonical(values[0]), harness.canonical(values[1]))
        self.assertEqual(harness.canonical(values[1]), harness.canonical(values[2]))
        self.assertNotEqual(harness.canonical(values[3]), harness.canonical(values[4]))
        self.assertEqual(values[3], Decimal('9007199254740993'))
        self.assertEqual(values[5], Decimal('1e400'))
        self.assertEqual(values[6], Decimal('1e-400'))
        huge = harness.load('[1e999999999999999999999999999999999999,10e999999999999999999999999999999999998,0e999999999999999999999999999999999999]')
        self.assertEqual(harness.canonical(huge[0]), harness.canonical(huge[1]))
        self.assertEqual(harness.canonical(huge[2]), harness.canonical(0))


class ObservationTests(unittest.TestCase):
    def test_complete_synthetic_inspect_and_exchange(self):
        for operation in ('inspect', 'exchange'):
            with self.subTest(operation=operation):
                case, response, source = fixture(operation)
                self.assertEqual(harness.observe(case, response, source), [])

    def test_closed_shape_and_truncation(self):
        case, response, source = fixture()
        malformed = [None, [], {}, {"report": {}}, {"report": None, "artifacts": {}}]
        for field in response['report']:
            changed = copy.deepcopy(response)
            del changed['report'][field]
            malformed.append(changed)
        changed = copy.deepcopy(response)
        changed['report']['unexpected'] = 1
        malformed.append(changed)
        for item in malformed:
            with self.subTest(response=item):
                self.assertTrue(harness.observe(case, item, source))

    def test_rejects_duplicate_records(self):
        case, response, source = fixture()
        for path in [('inputs',), ('results',)]:
            changed = copy.deepcopy(response)
            target = changed['report']
            for key in path:
                target = target[key]
            target.append(copy.deepcopy(target[0]))
            with self.subTest(path=path):
                self.assertTrue(harness.observe(case, changed, source))
        changed = copy.deepcopy(response)
        changed['report']['results'][0]['checks'] *= 2
        self.assertTrue(harness.observe(case, changed, source))

    def test_missing_result_and_false_pass_are_rejected(self):
        case, response, source = fixture()
        response['report']['results'] = []
        self.assertTrue(harness.observe(case, response, source))
        case, response, source = fixture()
        case['expected']['findings']['mode'] = 'contains'
        response['report']['results'][0]['findings'] = [{
            'rule': 'P-SYNTAX', 'location': {'byte': 0}, 'outcome': 'fail', 'details': 'Synthetic failure'}]
        self.assertTrue(harness.observe(case, response, source))

    def test_input_and_output_hash_and_bytes(self):
        for target in ('inputs', 'outputs'):
            case, response, source = fixture('exchange')
            response['report'][target][0]['sha256'] = '0' * 64
            with self.subTest(target=target):
                self.assertTrue(harness.observe(case, response, source))
        case, response, source = fixture('exchange')
        replacement = b'{ }'
        response['artifacts']['primary'] = base64.b64encode(replacement).decode()
        response['report']['outputs'][0]['sha256'] = hashlib.sha256(replacement).hexdigest()
        self.assertTrue(harness.observe(case, response, source))
        response['artifacts']['primary'] = 'invalid base64!'
        self.assertTrue(harness.observe(case, response, source))

    def test_tree_preserves_boolean_and_large_number(self):
        for raw, replacement in [(b'{"v":true}', 1), (b'{"v":9007199254740993}', 9007199254740992)]:
            case, response, source = fixture(raw=raw)
            response['report']['inventory']['tree']['v'] = replacement
            with self.subTest(raw=raw):
                self.assertTrue(harness.observe(case, response, source))

    def test_opaque_span_selects_exact_value_bytes(self):
        raw = b'{"runtime": {"n":1e400}}'
        case, response, source = fixture(raw=raw)
        response['report']['inventory']['states'][1]['state'] = 'unchecked'
        case['expected']['states'][1]['state'] = 'unchecked'
        span = {'input': 'primary', 'pointer': '/runtime'}
        # Locate the value directly in fixture bytes, preserving its numeric lexeme.
        span['start'] = raw.index(b'{', 1)
        span['end'] = len(raw) - 1
        response['report']['inventory']['opaque'] = [span]
        case['expected']['opaque'] = [{'input': 'primary', 'pointer': '/runtime'}]
        self.assertEqual(harness.observe(case, response, source), [])
        for start, end in [(span['start'] + 1, span['end']), (span['start'], span['end'] + 1), (-1, span['end'])]:
            changed = copy.deepcopy(response)
            changed['report']['inventory']['opaque'][0].update(start=start, end=end)
            with self.subTest(start=start, end=end):
                self.assertTrue(harness.observe(case, changed, source))

    def test_oracle_results_are_a_required_subset(self):
        case, response, source = fixture()
        case['expected']['results'] = []
        self.assertEqual(harness.observe(case, response, source), [])


    def test_check_locations_are_a_required_subset(self):
        raw = (HERE / 'fixtures' / 'empty-system.json').read_bytes()
        case, response, source = fixture(raw=raw)
        case['operation'] = response['report']['operation'] = 'validateD'
        result = response['report']['results'][0]
        result.update(unit='D', phase='unresolved-document')
        rules = ['D-AGENT', 'D-CYCLE', 'D-DEFERRAL', 'D-DEPENDENCY', 'D-EXPORT',
                 'D-IDENTITY', 'D-INTEGRITY', 'D-OWNER', 'D-REFERENCE', 'D-RELATION',
                 'P-SHAPE', 'P-SYNTAX', 'X-MODE']
        result['checks'] = [{'rule': rule, 'state': 'completed', 'locations': []} for rule in rules]
        result['checks'].extend({'rule': rule, 'state': 'excluded', 'locations': [{'pointer': ''}]}
                                for rule in ('X-EXECUTION', 'X-FULL-MODEL'))
        result['checks'].sort(key=lambda item: (item['rule'], item['state']))
        response['report']['inventory']['states'] = response['report']['inventory']['states'][:2]
        case['expected']['results'][0].update(unit='D', phase='unresolved-document')
        case['expected']['states'] = case['expected']['states'][:2]
        case['expected']['checks'] = [{'input': 'primary', 'unit': 'D', 'rule': 'X-EXECUTION',
                                      'state': 'excluded', 'locations': []}]
        self.assertEqual(harness.observe(case, response, source), [])
        case['expected']['checks'][0]['locations'] = [{'pointer': '/missing'}]
        self.assertTrue(harness.observe(case, response, source))

    def test_rejects_nonmaximal_and_hidden_inventory(self):
        raw = b'{"runtime":{"n":1}}'
        case, response, source = fixture(raw=raw)
        for row in (response['report']['inventory']['states'], case['expected']['states']):
            row[1]['state'] = 'unchecked'
        index = harness.JsonSource(raw)
        response['report']['inventory']['opaque'] = [dict(input='primary', pointer='/runtime/n',
            start=index.spans['/runtime/n'][0], end=index.spans['/runtime/n'][1])]
        self.assertTrue(harness.observe(case, response, source))
        response['report']['inventory']['opaque'] = [dict(input='primary', pointer='/runtime',
            start=index.spans['/runtime'][0], end=index.spans['/runtime'][1])]
        self.assertEqual(harness.observe(case, response, source), [])
        response['report']['inventory']['states'].append(dict(input='primary', pointer='/runtime/n', state='declared', detail='Hidden'))
        self.assertTrue(harness.observe(case, response, source))

    def test_loss_oracle_and_free_default_reason(self):
        case, response, source = fixture()
        case['operation'] = response['report']['operation'] = 'lossyExchange'
        result = response['report']['results'][0]
        result.update(unit='exchange', verdict='fail', checks=[dict(rule='E-LOSS', state='completed', locations=[])],
            findings=[dict(rule='E-LOSS', location={'pointer':''}, outcome='fail', details='Refused')])
        case['expected']['results'][0].update(unit='exchange', verdict='fail')
        case['expected']['findings'] = dict(mode='exact', items=[dict(input='primary', unit='exchange', rule='E-LOSS', location={'pointer':''}, outcome='fail')])
        loss = dict(input='primary', location={'pointer':''}, information='unspecified requested loss', permission=None)
        case['expected']['losses'] = [loss]
        response['report']['losses'] = [dict(loss, reason='One wording')]
        self.assertEqual(harness.observe(case, response, source), [])
        other = copy.deepcopy(response)
        other['report']['losses'][0]['reason'] = 'Another wording'
        self.assertEqual(harness.observe(case, other, source), [])
        self.assertEqual(harness.comparison(response), harness.comparison(other))
        other['report']['losses'][0]['information'] = 'different content'
        self.assertTrue(harness.observe(case, other, source))
        case['expected']['losses'][0].update(information='supplied request', reason='preserve my reason')
        response['report']['losses'][0].update(information='supplied request', reason='wrong reason')
        self.assertTrue(harness.observe(case, response, source))

    def test_missing_claim_oracle_checks_requirement_id(self):
        raw = (HERE / 'fixtures/runtime-missing-claim.json').read_bytes()
        case, response, source = fixture(raw=raw)
        case['operation'] = response['report']['operation'] = 'validateR'
        def result(unit, rules, boundaries):
            checks = [dict(rule=r, state='completed', locations=[]) for r in rules]
            checks += [dict(rule=r, state='excluded', locations=[{'pointer':p}]) for r,p in boundaries.items()]
            return dict(input='primary', unit=unit, phase='unresolved-document', verdict='pass', findings=[], checks=sorted(checks,key=lambda c:(c['rule'],c['state'])))
        response['report']['results'] = [result('D', harness.D_RULES, harness.BOUNDARY),
            result('R', harness.R_RULES, dict(harness.BOUNDARY, **harness.R_BOUNDARY))]
        case['expected']['results'] = [{k:r[k] for k in ('input','unit','phase','verdict')} for r in response['report']['results']]
        states = [dict(input='primary',pointer='/graphs',state='absent',detail='Absent'),
            dict(input='primary',pointer='/runtime',state='declared',detail='Declared'),
            dict(input='primary',pointer='/runtime/selection/evidence',state='absent',detail='Missing claim for cap')]
        response['report']['inventory']['states'] = states
        case['expected']['states'] = [dict(input='primary',pointer='/runtime/selection/evidence',state='absent',detailRequirement='cap')]
        index = harness.JsonSource(raw)
        p = '/definitions/0/payload'
        response['report']['inventory']['opaque'] = [dict(input='primary',pointer=p,start=index.spans[p][0],end=index.spans[p][1])]
        self.assertEqual(harness.observe(case,response,source), [])
        case['expected']['states'][0]['detailRequirement'] = 'another'
        self.assertTrue(harness.observe(case,response,source))

    def test_observed_annex_cannot_omit_all_slices(self):
        case, response, source = fixture()
        case['operation'] = response['report']['operation'] = 'resolveG'
        annex = b'{"annotations":{"important":true}}'
        source['annex/a'] = annex
        response['report']['inputs'].append(dict(id='annex/a',sha256=hashlib.sha256(annex).hexdigest()))
        def result(input_id, unit, phase, rules):
            checks=[dict(rule=r,state='completed',locations=[]) for r in rules]
            checks += [dict(rule=r,state='excluded',locations=[{'pointer':p}]) for r,p in harness.BOUNDARY.items()]
            return dict(input=input_id,unit=unit,phase=phase,verdict='pass',findings=[],checks=sorted(checks,key=lambda c:(c['rule'],c['state'])))
        response['report']['results']=[result('primary','D','unresolved-document',harness.D_RULES),
            result('annex/a','D','unresolved-document',harness.D_RULES),
            result('primary','G','resolved-graph',harness.G_RULES|{'G-RESOLVE'})]
        response['report']['inventory']['states']=[dict(input=i,pointer='/'+field,state='absent',detail='Absent') for i in source for field in ('graphs','runtime')]
        case['expected']['results']=[];case['expected']['states']=[]
        # Synthetic reports test transport coherence only, not the D validity of {}.
        self.assertTrue(harness.observe(case,response,source))
        index=harness.JsonSource(annex)
        response['report']['inventory']['opaque']=[dict(input='annex/a',pointer='/annotations',start=index.spans['/annotations'][0],end=index.spans['/annotations'][1])]
        self.assertEqual(harness.observe(case,response,source),[])

    def test_syntax_failure_blocks_downstream_checks(self):
        case,response,source=fixture()
        source['primary']=b'{';response['report']['inputs'][0]['sha256']=hashlib.sha256(b'{').hexdigest()
        case['operation']=response['report']['operation']='validateD'
        result=response['report']['results'][0]
        result.update(unit='D',phase='unresolved-document',verdict='fail',findings=[dict(rule='P-SYNTAX',location={'byte':1},outcome='fail',details='Unexpected EOF')])
        result['checks']=[dict(rule=r,state='completed',locations=[]) for r in harness.D_RULES]
        result['checks'] += [dict(rule=r,state='excluded',locations=[{'pointer':p}]) for r,p in harness.BOUNDARY.items()]
        result['checks'].sort(key=lambda c:(c['rule'],c['state']))
        response['report']['inventory']=dict(tree=None,states=[],opaque=[])
        case['expected']['results']=[];case['expected']['states']=[]
        case['expected']['findings']=dict(mode='contains',items=[])
        self.assertTrue(harness.observe(case,response,source))
        for check in result['checks']:
            if check['rule'] in harness.D_RULES-{'P-SYNTAX'}:
                check.update(state='blocked',locations=[{'pointer':''}])
        result['checks'].sort(key=lambda c:(c['rule'],c['state']))
        self.assertEqual(harness.observe(case,response,source),[])

    def test_state_sets_ignore_repeated_tuples_only(self):
        case,response,source=fixture()
        response['report']['inventory']['states'].append(dict(response['report']['inventory']['states'][0],detail='Another description'))
        self.assertEqual(harness.observe(case,response,source),[])
        clean=copy.deepcopy(response)
        clean['report']['inventory']['states'].pop()
        self.assertEqual(harness.comparison(response),harness.comparison(clean))
        # The state value remains significant even when the pointer is identical.
        response['report']['inventory']['states'][-1]['state']='unchecked'
        self.assertTrue(harness.observe(case,response,source))
        self.assertNotEqual(harness.comparison(response),harness.comparison(clean))

    def test_blocked_pointer_names_affected_record_not_missing_value(self):
        case,response,source=fixture(raw=b'{"record":{},"items":[],"scalar":1}')
        case['operation']=response['report']['operation']='validateD'
        result=response['report']['results'][0]
        result.update(unit='D',phase='unresolved-document',verdict='inconclusive')
        result['checks']=[dict(rule=r,state='completed',locations=[]) for r in harness.D_RULES]
        result['checks'] += [dict(rule=r,state='excluded',locations=[{'pointer':p}]) for r,p in harness.BOUNDARY.items()]
        blocked=dict(rule='D-RELATION',state='blocked',locations=[{'pointer':'/relations'}])
        result['checks'].append(blocked);result['checks'].sort(key=lambda c:(c['rule'],c['state']))
        response['report']['inventory']['states']=response['report']['inventory']['states'][:2]
        case['expected']['results']=[];case['expected']['states']=[]
        for path in ['', '/record', '/items', '/scalar']:
            blocked['locations']=[{'pointer':path}]
            with self.subTest(path=path): self.assertEqual(harness.observe(case,response,source),[])
        for path in ['/relations','/record/missing','/record/~0~1','/items/0','/missing/child','/scalar/child','/items/01','/items/-','/record/~2bad']:
            blocked['locations']=[{'pointer':path}]
            with self.subTest(path=path): self.assertTrue(harness.observe(case,response,source))
        blocked.update(state='excluded',locations=[{'pointer':'/relations'}])
        result['checks'].sort(key=lambda c:(c['rule'],c['state']))
        self.assertTrue(harness.observe(case,response,source))

    def test_findings_still_use_observable_parent_for_missing_field(self):
        case,response,source=fixture()
        # Finding P-SHAPE for a missing member points to its observable parent.
        case['operation']=response['report']['operation']='validateD'
        result=response['report']['results'][0]
        result.update(unit='D',phase='unresolved-document',verdict='fail',findings=[dict(rule='P-SHAPE',location={'pointer':'/relations'},outcome='fail',details='Missing')])
        result['checks']=[dict(rule=r,state='completed',locations=[]) for r in harness.D_RULES]
        result['checks'] += [dict(rule=r,state='excluded',locations=[{'pointer':p}]) for r,p in harness.BOUNDARY.items()]
        result['checks'].sort(key=lambda c:(c['rule'],c['state']))
        response['report']['inventory']['states']=response['report']['inventory']['states'][:2]
        case['expected']['results']=[];case['expected']['states']=[];case['expected']['findings']=dict(mode='contains',items=[])
        self.assertTrue(harness.observe(case,response,source))
        result['findings'][0]['location']={'pointer':''}
        self.assertEqual(harness.observe(case,response,source),[])


class ComparisonTests(unittest.TestCase):
    def test_ignores_processor_prose_and_state_order(self):
        _, response, _ = fixture()
        other = copy.deepcopy(response)
        other['report']['processor'] = {'identity': 'another/synthetic', 'version': '2'}
        other['report']['inventory']['states'].reverse()
        for state in other['report']['inventory']['states']:
            state['detail'] = 'Different wording'
        self.assertEqual(harness.comparison(response), harness.comparison(other))

    def test_compares_full_report_beyond_oracle_subset(self):
        _, response, _ = fixture()
        for field, value in [('state', 'unchecked'), ('pointer', '/another')]:
            other = copy.deepcopy(response)
            other['report']['inventory']['states'][0][field] = value
            with self.subTest(field=field):
                self.assertNotEqual(harness.comparison(response), harness.comparison(other))
        other = copy.deepcopy(response)
        other['report']['results'][0]['checks'][0]['state'] = 'blocked'
        other['report']['results'][0]['checks'][0]['locations'] = [{'pointer': ''}]
        self.assertNotEqual(harness.comparison(response), harness.comparison(other))


    def test_missing_claim_identity_survives_prose_normalization(self):
        _, response, _ = fixture()
        response['report']['inventory']['tree'] = {'runtime': {'requirements': [
            {'id': 'cap'}, {'id': 'other'}]}}
        response['report']['inventory']['states'] = [{
            'input': 'primary', 'pointer': '/runtime/selection/evidence',
            'state': 'absent', 'detail': 'cap'}]
        other = copy.deepcopy(response)
        other['report']['inventory']['states'][0]['detail'] = 'Missing claim for cap'
        self.assertEqual(harness.comparison(response), harness.comparison(other))
        other['report']['inventory']['states'][0]['detail'] = 'Missing claim for other'
        self.assertNotEqual(harness.comparison(response), harness.comparison(other))
        duplicate = copy.deepcopy(response)
        duplicate['report']['inventory']['states'].append(dict(duplicate['report']['inventory']['states'][0], detail='Missing claim for cap'))
        self.assertEqual(harness.comparison(response), harness.comparison(duplicate))
        duplicate['report']['inventory']['states'].append(other['report']['inventory']['states'][0])
        self.assertNotEqual(harness.comparison(response), harness.comparison(duplicate))


class CliTests(unittest.TestCase):
    def invoke(self, first, second, timeout='2'):
        workspace = tempfile.TemporaryDirectory(prefix='agsdl-comparison-test-')
        self.addCleanup(workspace.cleanup)
        directory = Path(workspace.name)
        argv = [sys.executable, '-B', str(HERE / 'compare-readers.py'),
                '--case', 'empty-object-inspect', '--reports', str(directory / 'reports'),
                '--timeout', timeout]
        for label, program in [('first', first), ('second', second)]:
            argv.extend(['--reader', json.dumps([label, sys.executable, '-B', '-c', program])])
        process = subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 timeout=15, text=True)
        return process, directory / 'reports'

    def assert_saved(self, directory):
        self.assertTrue((directory / 'summary.json').is_file())
        for label in ('first', 'second'):
            for stream in ('stdout', 'stderr'):
                self.assertTrue((directory / ('empty-object-inspect.' + label + '.' + stream)).is_file())

    def test_reader_labels_are_safe_and_distinct(self):
        with tempfile.TemporaryDirectory(prefix='agsdl-label-test-') as temp:
            for labels in [('same','same'),('../escape','safe')]:
                argv=[sys.executable,'-B',str(HERE/'compare-readers.py'),'--reports',str(Path(temp)/'reports')]
                for label in labels:
                    argv += ['--reader',json.dumps([label,sys.executable,'-c','raise SystemExit(99)'])]
                proc=subprocess.run(argv,capture_output=True,timeout=5)
                self.assertNotEqual(proc.returncode,0)
                self.assertFalse((Path(temp)/'reports').exists())

    def report_program(self):
        raw = (HERE / 'fixtures' / 'empty-object-inspect.json').read_bytes()
        _, response, _ = fixture(raw=raw)
        # This fixed report exists only to exercise the harness transport.
        return 'import sys; sys.stdin.read(); print(' + repr(json.dumps(response)) + ')'

    def test_preserves_protocol_error_output(self):
        program = 'import sys; sys.stdin.read(); print("not JSON"); print("diagnostic", file=sys.stderr)'
        process, directory = self.invoke(program, program)
        self.assertNotEqual(process.returncode, 0)
        self.assert_saved(directory)
        self.assertEqual((directory / 'empty-object-inspect.first.stdout').read_text(), 'not JSON\n')
        self.assertEqual((directory / 'empty-object-inspect.first.stderr').read_text(), 'diagnostic\n')

    def test_timeout_retains_partial_output(self):
        program = 'import time; print("started", flush=True); time.sleep(5)'
        process, directory = self.invoke(program, program, timeout='0.15')
        self.assertNotEqual(process.returncode, 0)
        self.assert_saved(directory)
        self.assertIn('started', (directory / 'empty-object-inspect.first.stdout').read_text())
        self.assertIn('timeout', (directory / 'summary.json').read_text().lower())

    def test_two_fixed_reports_are_compared(self):
        program = self.report_program()
        process, directory = self.invoke(program, program)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assert_saved(directory)

    def test_significant_report_change_fails(self):
        first = self.report_program()
        second = first.replace('"state": "absent"', '"state": "unchecked"', 1)
        self.assertNotEqual(first, second)
        process, directory = self.invoke(first, second)
        self.assertNotEqual(process.returncode, 0)
        self.assert_saved(directory)


if __name__ == '__main__':
    unittest.main()
