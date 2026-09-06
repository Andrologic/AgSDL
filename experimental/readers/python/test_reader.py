"""Independent candidate-text witnesses; no shared-reader or engine dependency."""
import base64
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from grammar import CONTRACT
from lossless import Parser, Number, SyntaxFailure, dumps, integer
from reader import read, digest


def k(name, scope='test'):
    return {'scope': scope, 'id': name, 'version': '1'}


def doc():
    return {'contract': CONTRACT, 'root': {'key': k('system'), 'kind': 'System'},
            'definitions': [], 'relations': [], 'exports': [], 'dependencies': [], 'unresolved': [], 'extensions': []}


def definition(d, name, kind, payload=None):
    item = {'key': k(name), 'kind': kind, 'owner': d['root']['key'], 'payload': {} if payload is None else payload}
    d['definitions'].append(item)
    return item


def relation(d, source, rel, target, kind):
    d['relations'].append({'source': k(source), 'relation': rel, 'target': target, 'expectedKind': kind})


def graph_doc():
    d = doc()
    definition(d, 'agent', 'Agent')
    definition(d, 'principal', 'Principal')
    definition(d, 'instructions', 'Instructions')
    definition(d, 'action', 'Action')
    definition(d, 'resource', 'Resource')
    definition(d, 'interface', 'Interface', {'inputs': {'x': 'json'}, 'outputs': {'answer': 'json'}, 'action': k('action')})
    definition(d, 'flow', 'ControlFlow')
    relation(d, 'agent', 'actsAs', k('principal'), 'Principal')
    relation(d, 'agent', 'directedBy', k('instructions'), 'Instructions')
    relation(d, 'agent', 'exposes', k('interface'), 'Interface')
    invoke = {'id': 'call', 'kind': 'invoke', 'agent': k('agent'), 'interface': k('interface'), 'action': k('action'),
              'resources': [k('resource')], 'principal': k('principal'), 'context': {'input': 'x'},
              'inputs': {'x': 'json'}, 'outputs': {'answer': 'json'}, 'bindings': {'x': {'input': 'x'}}, 'success': 'done', 'failure': 'failed'}
    d['graphs'] = [{'definition': k('flow'), 'entry': 'call', 'inputs': {'x': 'json'}, 'outputs': {'answer': 'json'},
                    'steps': [invoke, {'id': 'done', 'kind': 'end', 'outcome': 'success', 'bindings': {'answer': {'step': 'call', 'port': 'answer'}}},
                              {'id': 'failed', 'kind': 'end', 'outcome': 'failure', 'reason': 'call failed'}]}]
    return d


def approval_doc():
    d = graph_doc()
    definition(d, 'approval', 'ApprovalRequirement', {'approvers': [k('principal')], 'validForMs': 1000})
    g = d['graphs'][0]
    g['entry'] = 'gate'
    g['steps'] += [{'id': 'gate', 'kind': 'approval', 'requirement': k('approval'), 'timeoutMs': 500, 'approved': 'call', 'denied': 'refused', 'failure': 'failed'},
                   {'id': 'refused', 'kind': 'end', 'outcome': 'denied', 'reason': 'human refused'}]
    return d


def raw(d):
    return json.dumps(d, ensure_ascii=False).encode()


def run(d, op='validateD', annexes=None):
    return read(op, raw(d), annexes)['report']


def findings(report, rule=None):
    return [f for r in report['results'] for f in r['findings'] if rule is None or f['rule'] == rule]


class ParserTests(unittest.TestCase):
    def test_lossless_numbers_unicode_positions(self):
        data = '{"é": [1e999999999999999999999, -0.00, 9007199254740993]}'.encode()
        p = Parser(data)
        value = p.parse()
        self.assertEqual(dumps(value).encode(), b'{"\\u00e9":[1e999999999999999999999,-0.00,9007199254740993]}')
        for i, lexeme in enumerate((b'1e999999999999999999999', b'-0.00', b'9007199254740993')):
            start, end = p.spans['/é/' + str(i)]
            self.assertEqual(data[start:end], lexeme)

    def test_duplicates_after_decoding(self):
        for data in (b'{"x":1,"\\u0078":2}', b'{"\\ud83d\\ude00":1,"\xf0\x9f\x98\x80":2}'):
            with self.assertRaises(SyntaxFailure) as caught:
                Parser(data).parse()
            self.assertEqual(caught.exception.offset, data.index(b',') + 1)

    def test_first_error_and_utf8(self):
        cases = [(b'[1,? ,"\xff"]', 3), (b'"\xff"', 1), (b'"\\ud800"', 1), (b'"\\udc00"', 1),
                 (b'01', 1), (b'1.', 2), (b'{"x":', 5), (b'\xef\xbb\xbf{}', 0)]
        for data, expected in cases:
            with self.subTest(data=data), self.assertRaises(SyntaxFailure) as caught:
                Parser(data).parse()
            self.assertEqual(caught.exception.offset, expected)

    def test_utf8_continuation_and_eof_offsets(self):
        for hex_bytes, offset in [('22e25822', 2), ('22e282', 3), ('22e0808022', 2),
                                  ('22eda08022', 2), ('22f490808022', 2), ('22f0908022', 4)]:
            with self.subTest(hex_bytes=hex_bytes), self.assertRaises(SyntaxFailure) as caught:
                Parser(bytes.fromhex(hex_bytes)).parse()
            self.assertEqual(caught.exception.offset, offset)

    def test_safe_uint_without_rounding(self):
        for value, expected in [('1.0e0', 1), ('100e-2', 1), ('1.01', None), ('-0', 0), ('9007199254740991', 9007199254740991),
                                ('9007199254740992', None), ('1e999999999999999', None), ('1e-99999999999', None)]:
            self.assertEqual(integer(Number(value)), expected)
        self.assertIsNone(integer(True))
        self.assertEqual(integer(Number('1' + '0' * 100000 + 'e-100000')), 1)
        self.assertEqual(integer(Number('0.' + '0' * 99999 + '1e100000')), 1)


class DocumentaryTests(unittest.TestCase):
    def test_empty_system_bounded_pass(self):
        report = run(doc())
        self.assertEqual(report['results'][0]['verdict'], 'pass')
        self.assertIn('X-FULL-MODEL', [c['rule'] for c in report['results'][0]['checks']])

    def test_owner_identity_reference_cycle_minima(self):
        cases = []
        d = graph_doc(); d['definitions'][0]['owner'] = k('elsewhere'); cases.append((d, 'D-OWNER'))
        d = graph_doc(); d['definitions'].append(copy.deepcopy(d['definitions'][0])); cases.append((d, 'D-IDENTITY'))
        d = graph_doc(); d['relations'][0]['target'] = k('missing'); cases.append((d, 'D-REFERENCE'))
        d = graph_doc(); relation(d, 'agent', 'contains', k('agent'), 'Agent'); cases.append((d, 'D-CYCLE'))
        d = graph_doc(); d['relations'] = []; cases.append((d, 'D-AGENT'))
        for d, rule in cases:
            with self.subTest(rule=rule):
                report = run(d)
                self.assertEqual(report['results'][0]['verdict'], 'fail')
                self.assertTrue(findings(report, rule))

    def test_fragment_deferral(self):
        d = graph_doc(); d.pop('graphs'); d['root']['kind'] = 'Fragment'; d['exports'] = [k('agent')]
        d['relations'] = [r for r in d['relations'] if r['relation'] != 'exposes']
        d['unresolved'] = [{'subject': k('agent'), 'obligation': 'agent-interface-minimum', 'rule': 'fragment-interface-deferral',
                            'relation': 'exposes', 'expectedKind': 'Interface', 'missingMinimum': 1, 'target': None,
                            'satisfyBy': 'typed-exposes-relation', 'expiresBefore': 'resolved-graph'}]
        report = run(d)
        self.assertEqual(report['results'][0]['verdict'], 'pass')
        self.assertEqual(findings(report, 'D-DEFERRAL')[0]['outcome'], 'deferred')
        d['root']['kind'] = 'System'; d['exports'] = []
        self.assertEqual(run(d)['results'][0]['verdict'], 'fail')

    def test_extensions_unknown_and_custom(self):
        d = doc()
        ext = {'identity': 'example/kind', 'version': '1', 'operations': {'validateD': 'required'}, 'payload': {'x': 1}}
        d['extensions'] = [ext]
        definition(d, 'custom', {'extension': {'identity': 'example/kind', 'version': '1'}, 'name': 'Odd'})
        self.assertEqual(run(d)['results'][0]['verdict'], 'unsupported')
        ext['operations']['validateD'] = {'ignoreRule': 'annotation-only'}
        self.assertEqual(run(d)['results'][0]['verdict'], 'fail')
        d['definitions'] = []; ext['operations'] = {}
        self.assertEqual(run(d)['results'][0]['verdict'], 'inconclusive')

    def test_known_violation_precedes_unsupported(self):
        d = doc(); definition(d, 'a', 'Agent')
        d['extensions'] = [{'identity': 'example/e', 'version': '1', 'operations': {'validateD': 'required'}, 'payload': {}}]
        report = run(d)
        self.assertEqual(report['results'][0]['verdict'], 'fail')
        self.assertEqual({f['outcome'] for f in findings(report)}, {'fail', 'unsupported'})

    def test_shape_partial_checks(self):
        d = doc(); d['definitions'] = [17]
        definition(d, 'a', 'Tool')['owner'] = k('wrong')
        report = run(d)
        self.assertTrue(findings(report, 'P-SHAPE'))
        self.assertTrue(findings(report, 'D-OWNER'))

    def test_invalid_root_kind_blocks_export_form(self):
        d = doc(); d['root']['kind'] = 17
        report = run(d)
        self.assertTrue(any(c['rule'] == 'D-EXPORT' and c['state'] == 'blocked' and {'pointer': '/exports'} in c['locations'] for c in report['results'][0]['checks']))

    def test_unknown_catalog_entry_does_not_prove_target_absent(self):
        d = doc(); d['definitions'] = [17]
        relation(d, 'system', 'uses', k('unknown'), 'Tool')
        report = run(d)
        self.assertFalse(findings(report, 'D-REFERENCE'))
        self.assertTrue(any(c['rule'] == 'D-REFERENCE' and c['state'] == 'blocked' for c in report['results'][0]['checks']))

    def test_dependency_hash_and_delivery(self):
        d = doc(); d['dependencies'] = [{'id': 'a', 'rootKey': k('package'), 'status': 'external', 'requiredFor': ['validateD'], 'sha256': None}]
        self.assertEqual(run(d)['results'][0]['verdict'], 'inconclusive')
        d['dependencies'][0].update(status='included', sha256='0' * 64)
        self.assertTrue(findings(run(d, annexes={'a': b'{}'}), 'D-INTEGRITY'))


class OperationTests(unittest.TestCase):
    def test_inspect_exchange_invalid_bytes(self):
        data = b'{ bad \xff'
        inspected = read('inspect', data)
        self.assertEqual(inspected['report']['results'][0]['verdict'], 'fail')
        copied = read('exchange', data)
        self.assertEqual(copied['artifacts'], {'primary': data})
        self.assertEqual(copied['report']['results'][0]['verdict'], 'pass')
        self.assertEqual(copied['report']['inventory']['opaque'], [])

    def test_opaque_runtime_and_graph_scope(self):
        d = doc(); d['graphs'] = 17; d['runtime'] = {}
        dr = run(d); gr = run(d, 'validateG'); rr = run(d, 'validateR')
        self.assertEqual(dr['results'][-1]['verdict'], 'pass')
        self.assertEqual(gr['results'][-1]['verdict'], 'fail')
        self.assertEqual(rr['results'][-1]['verdict'], 'fail')
        self.assertNotIn('/runtime/selection', [s['pointer'] for s in dr['inventory']['states']])

    def test_malformed_dependency_inventory_priority(self):
        dep = {'id': 'd', 'rootKey': k('p'), 'status': 'external', 'requiredFor': [], 'sha256': None}
        d = {'dependencies': [dep, 17]}
        for op in ('inspect', 'exchange', 'lossyExchange'):
            report = run(d, op)
            self.assertFalse(any(s['pointer'].startswith('/dependencies/') for s in report['inventory']['states']))
            self.assertIn('/dependencies', [s['pointer'] for s in report['inventory']['opaque']])
        d = doc(); d['dependencies'] = [dep, 17]
        self.assertIn('/dependencies/0/sha256', [s['pointer'] for s in run(d)['inventory']['states']])

    def test_loss_refusal_and_unit(self):
        result = read('lossyExchange', b'{}')
        r = result['report']['results'][0]
        self.assertEqual((r['unit'], r['phase'], r['verdict']), ('exchange', None, 'fail'))
        self.assertEqual(result['artifacts'], {})
        self.assertEqual(len(result['report']['losses']), 1)

    def test_exchange_accounting_refusal(self):
        d = doc(); d['dependencies'] = [{'id': 'd', 'rootKey': k('p'), 'status': 'external', 'requiredFor': ['exchange'], 'sha256': None}]
        result = read('exchange', raw(d))
        self.assertEqual(result['artifacts'], {})
        self.assertEqual(result['report']['results'][0]['verdict'], 'fail')

    def test_runtime_assertions_never_ready(self):
        d = doc(); definition(d, 'agent', 'Tool')
        d['runtime'] = {'requirements': [{'id': 'r', 'capability': {'identity': 'custom/cap', 'version': 'x'}, 'subject': k('agent')}],
                        'selection': {'engine': {'identity': 'custom/engine', 'version': 'x'}, 'interface': {'identity': 'custom/api', 'version': 'x'},
                                      'evidence': [{'requirement': 'r', 'claim': 'satisfied', 'artifact': None}]}}
        report = run(d, 'validateR')
        self.assertEqual(report['results'][-1]['verdict'], 'pass')
        self.assertEqual({c['rule'] for c in report['results'][-1]['checks'] if c['state'] == 'excluded'},
                         {'X-READINESS', 'X-EVIDENCE-ASSESSMENT', 'X-EXECUTION', 'X-FULL-MODEL'})
        self.assertTrue(any(s['state'] == 'unknown' for s in report['inventory']['states']))
        d['runtime']['requirements'].append(copy.deepcopy(d['runtime']['requirements'][0]))
        self.assertTrue(findings(run(d, 'validateR'), 'R-REQUIREMENT'))

    def test_inventory_state_details_are_nonempty_and_keep_subjects(self):
        d = graph_doc()
        d['dependencies'] = [{'id': 'external', 'rootKey': k('other'), 'status': 'external',
                              'requiredFor': [], 'sha256': None}]
        d['graphs'][0]['steps'][0]['resources'] = [{'dependency': 'external', 'key': k('resource')}]
        requirement = {'id': 'missing-claim', 'capability': {'identity': 'owner/c', 'version': '1'},
                       'subject': k('agent')}
        claimed = dict(requirement, id='claimed')
        d['runtime'] = {'requirements': [requirement, claimed],
                        'selection': {'engine': {'identity': 'owner/e', 'version': '1'},
                                      'interface': {'identity': 'owner/i', 'version': '1'},
                                      'evidence': [{'requirement': 'claimed', 'claim': 'satisfied', 'artifact': None}]}}
        collected = []
        for value in (doc(), d):
            for operation in ('inspect', 'validateD', 'validateG', 'resolveG', 'validateR', 'exchange', 'lossyExchange'):
                with self.subTest(operation=operation, runtime='runtime' in value):
                    states = run(value, operation)['inventory']['states']
                    for state in states:
                        self.assertIsInstance(state['detail'], str)
                        self.assertTrue(state['detail'])
                    collected.extend(states)
        self.assertTrue(any(s['state'] == 'unknown' for s in collected))
        self.assertTrue(any(s['detail'] == 'external target excluded' for s in collected))
        self.assertTrue(any(s['detail'] == 'evidence assessment excluded' for s in collected))
        missing = [s for s in collected if s['pointer'] == '/runtime/selection/evidence' and s['state'] == 'absent']
        self.assertEqual([s['detail'] for s in missing], ['missing-claim'])

    def test_runtime_hosting_and_claim_duplicates(self):
        d = doc(); definition(d, 'subject', 'Tool')
        d['runtime'] = {'requirements': [{'id': 'r', 'capability': {'identity': 'owner/c', 'version': '1'}, 'subject': k('subject')}],
                        'selection': {'engine': {'identity': 'owner/e', 'version': '1'}, 'interface': {'identity': 'owner/i', 'version': '1'},
                                      'hosting': k('subject'), 'evidence': []}}
        self.assertTrue(findings(run(d, 'validateR'), 'R-SELECTION'))
        d['runtime']['selection'].pop('hosting')
        claim = {'requirement': 'r', 'claim': 'indeterminate', 'artifact': None}
        d['runtime']['selection']['evidence'] = [claim, copy.deepcopy(claim)]
        self.assertTrue(findings(run(d, 'validateR'), 'R-SELECTION'))

    def test_no_semantic_shape_for_inspection_or_copy(self):
        for value in ({'dependencies': 17}, [], None):
            for op in ('inspect', 'exchange'):
                report = run(value, op)
                self.assertEqual(report['results'][0]['verdict'], 'pass')
                self.assertFalse(findings(report, 'P-SHAPE'))
                self.assertIsNone(report['results'][0]['phase'])

    def test_malformed_runtime_collections_block_semantic_checks(self):
        d = doc(); d['runtime'] = {'requirements': 17}
        r = run(d, 'validateR')['results'][-1]
        self.assertTrue(any(c['rule'] == 'R-REQUIREMENT' and c['state'] == 'blocked' for c in r['checks']))
        d['runtime'] = {'requirements': [], 'selection': {'engine': {'identity': 'a/b', 'version': '1'},
                         'interface': {'identity': 'a/c', 'version': '1'}, 'evidence': 17}}
        r = run(d, 'validateR')['results'][-1]
        self.assertTrue(any(c['rule'] == 'R-SELECTION' and c['state'] == 'blocked' for c in r['checks']))

    def test_unreadable_requirement_catalog_blocks_claim_lookup(self):
        d = doc(); d['runtime'] = {'requirements': 17, 'selection': {
            'engine': {'identity': 'audit/e', 'version': '1'}, 'interface': {'identity': 'audit/i', 'version': '1'},
            'evidence': [{'requirement': 'r', 'claim': 'satisfied', 'artifact': None}]}}
        report = run(d, 'validateR')
        self.assertFalse(findings(report, 'R-SELECTION'))
        self.assertTrue(any(c['rule'] == 'R-SELECTION' and c['state'] == 'blocked' for c in report['results'][-1]['checks']))
        d['runtime']['selection']['evidence'] *= 2
        self.assertTrue(findings(run(d, 'validateR'), 'R-SELECTION'))

    def test_cli_lossless_tree_and_artifacts(self):
        primary = b'{"annotations":1e999999999999999999}'
        request = {'operation': 'exchange', 'primary': base64.b64encode(primary).decode(), 'annexes': {}}
        proc = subprocess.run([sys.executable, str(Path(__file__).with_name('cli.py'))], input=raw(request), capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        parsed = Parser(proc.stdout).parse()
        self.assertEqual(parsed['report']['inventory']['tree']['annotations'].lexeme, '1e999999999999999999')
        self.assertEqual(base64.b64decode(parsed['artifacts']['primary']), primary)


class GraphTests(unittest.TestCase):
    def test_local_graph_both_phases(self):
        for op in ('validateG', 'resolveG'):
            report = run(graph_doc(), op)
            self.assertEqual(report['results'][-1]['verdict'], 'pass', findings(report))

    def test_bad_success_path_and_cycle(self):
        d = graph_doc(); d['graphs'][0]['steps'][0]['failure'] = 'done'; d['graphs'][0]['steps'].pop()
        report = run(d, 'validateG')
        self.assertTrue(findings(report, 'G-DATA'))
        d = graph_doc(); d['graphs'][0]['steps'][0]['failure'] = 'call'
        self.assertTrue(findings(run(d, 'validateG'), 'G-PATH'))

    def test_approval_guard_and_time_shape(self):
        d = approval_doc()
        self.assertEqual(run(d, 'resolveG')['results'][-1]['verdict'], 'pass')
        d['graphs'][0]['steps'][3]['denied'] = 'call'; d['graphs'][0]['steps'].pop()
        self.assertTrue(findings(run(d, 'resolveG'), 'G-APPROVAL'))
        d = approval_doc(); d['graphs'][0]['steps'][3]['timeoutMs'] = True
        self.assertTrue(findings(run(d, 'validateG'), 'P-SHAPE'))

    def test_equivalent_long_integer_timeout_is_valid(self):
        original = raw(approval_doc())
        replacement = b'"timeoutMs": ' + b'1' + b'0' * 100000 + b'e-100000'
        changed = original.replace(b'"timeoutMs": 500', replacement)
        self.assertNotEqual(original, changed)
        self.assertEqual(read('validateG', changed)['report']['results'][-1]['verdict'], 'pass')

    def test_interface_type_and_action(self):
        d = graph_doc(); d['definitions'][5]['payload']['outputs']['answer'] = 'string'
        self.assertTrue(findings(run(d, 'validateG'), 'G-DATA'))
        d = graph_doc(); d['definitions'][5]['payload']['action'] = k('resource')
        self.assertTrue(findings(run(d, 'validateG'), 'G-TARGET'))

    def test_external_graph_resolution(self):
        annex = graph_doc(); annex.pop('graphs'); annex['root']['kind'] = 'Fragment'
        annex['definitions'] = [v for v in annex['definitions'] if v['kind'] != 'ControlFlow']
        annex['exports'] = [v['key'] for v in annex['definitions']]
        data = raw(annex)
        d = graph_doc()
        # Retain the graph and its local ControlFlow, import every invocation target.
        d['definitions'] = [v for v in d['definitions'] if v['kind'] == 'ControlFlow']
        d['relations'] = []
        call = d['graphs'][0]['steps'][0]
        for field in ('agent', 'interface', 'action', 'principal'):
            call[field] = {'dependency': 'a', 'key': call[field]}
        call['resources'] = [{'dependency': 'a', 'key': k('resource')}]
        d['dependencies'] = [{'id': 'a', 'rootKey': annex['root']['key'], 'status': 'included', 'requiredFor': [], 'sha256': digest(data)}]
        report = run(d, 'resolveG', {'a': data})
        self.assertEqual(report['results'][-1]['verdict'], 'pass', findings(report))
        d['dependencies'][0]['status'] = 'external'
        self.assertEqual(run(d, 'validateG')['results'][-1]['verdict'], 'pass')
        self.assertEqual(run(d, 'resolveG')['results'][-1]['verdict'], 'fail')

    def test_condition_boolean_and_no_implicit_coercion(self):
        d = graph_doc(); g = d['graphs'][0]
        g['inputs']['go'] = 'boolean'
        g['entry'] = 'branch'
        g['steps'].append({'id': 'branch', 'kind': 'condition', 'test': {'input': 'go'},
                           'true': 'call', 'false': 'failed', 'failure': 'failed'})
        self.assertEqual(run(d, 'validateG')['results'][-1]['verdict'], 'pass')
        g['inputs']['go'] = 'string'
        self.assertTrue(findings(run(d, 'validateG'), 'G-DATA'))

    def test_approval_cannot_present_future_invocation_output(self):
        d = approval_doc()
        d['graphs'][0]['steps'][0]['context'] = {'step': 'call', 'port': 'answer'}
        report = run(d, 'validateG')
        self.assertIn('/graphs/0/steps/3', [f['location']['pointer'] for f in findings(report, 'G-DATA')])

    def test_required_annex_without_graph_and_unknown_hash(self):
        annex = doc(); data = raw(annex)
        d = doc(); d['dependencies'] = [{'id': 'a', 'rootKey': annex['root']['key'], 'status': 'included',
                                        'requiredFor': ['resolveG'], 'sha256': None}]
        report = run(d, 'resolveG', {'a': data})
        self.assertEqual(report['results'][-1]['verdict'], 'inconclusive')
        self.assertTrue(findings(report, 'G-RESOLVE'))
        d['dependencies'][0]['rootKey'] = k('wrong')
        self.assertEqual(run(d, 'resolveG', {'a': data})['results'][-1]['verdict'], 'fail')

    def test_transitive_reference_is_unsupported_not_fetched(self):
        annex = doc(); annex['root']['kind'] = 'Fragment'
        definition(annex, 'iface', 'Interface', {'inputs': {'x': 'json'}, 'outputs': {'answer': 'json'},
                                               'action': {'dependency': 'nested', 'key': k('action', 'elsewhere')}})
        annex['exports'] = [k('iface')]
        annex['dependencies'] = [{'id': 'nested', 'rootKey': k('p', 'elsewhere'), 'status': 'external', 'requiredFor': [], 'sha256': None}]
        data = raw(annex); d = graph_doc()
        ref = {'dependency': 'a', 'key': k('iface')}
        d['graphs'][0]['steps'][0]['interface'] = ref
        d['relations'][2]['target'] = ref
        d['dependencies'] = [{'id': 'a', 'rootKey': annex['root']['key'], 'status': 'included', 'requiredFor': [], 'sha256': digest(data)}]
        report = run(d, 'resolveG', {'a': data})
        self.assertEqual(report['results'][-1]['verdict'], 'unsupported', findings(report))
        self.assertEqual(len(report['inputs']), 2)
        self.assertTrue(any(f['outcome'] == 'unsupported' for f in findings(report, 'G-RESOLVE')))
        annex_g = next(r for r in report['results'] if r['unit'] == 'G' and r['input'] != 'primary')
        self.assertEqual(annex_g['verdict'], 'pass')
        self.assertTrue(any(c['rule'] == 'G-TARGET' and c['state'] == 'excluded' for c in annex_g['checks']))
        self.assertFalse(any(c['state'] == 'blocked' for c in annex_g['checks']))

    def test_selected_key_collision_with_unconsumed_local_definition(self):
        d = graph_doc(); annex = doc(); annex['root']['kind'] = 'Fragment'; annex['root']['key'] = k('fragment')
        definition(annex, 'resource', 'Resource'); annex['exports'] = [k('resource')]
        data = raw(annex)
        d['dependencies'] = [{'id': 'a', 'rootKey': annex['root']['key'], 'status': 'included', 'requiredFor': [], 'sha256': digest(data)}]
        d['graphs'][0]['steps'][0]['resources'] = [{'dependency': 'a', 'key': k('resource')}]
        report = run(d, 'resolveG', {'a': data})
        self.assertEqual(report['results'][-1]['verdict'], 'fail')
        self.assertTrue(findings(report, 'G-RESOLVE'))

    def test_malformed_approval_and_condition_fields_keep_report(self):
        d = approval_doc()
        d['graphs'][0]['inputs']['flag'] = 'boolean'
        d['graphs'][0]['entry'] = 'condition'
        d['graphs'][0]['steps'].append({'id': 'condition', 'kind': 'condition', 'test': {'input': 'flag'},
                                       'true': 'gate', 'false': 'failed', 'failure': 'failed'})
        for index in (3, 5):
            for field in d['graphs'][0]['steps'][index]:
                for bad in (None, {}, [], True, -1):
                    changed = copy.deepcopy(d)
                    changed['graphs'][0]['steps'][index][field] = bad
                    report = run(changed, 'validateG')
                    self.assertEqual(report['results'][-1]['verdict'], 'fail')
                    self.assertTrue(findings(report, 'P-SHAPE'))

    def test_duplicate_steps_preserve_independent_targets(self):
        d = graph_doc()
        duplicate = copy.deepcopy(d['graphs'][0]['steps'][0])
        d['graphs'][0]['steps'][0]['agent'] = k('missing')
        d['graphs'][0]['steps'].append(duplicate)
        report = run(d, 'validateG')
        self.assertTrue(findings(report, 'G-PATH'))
        self.assertTrue(findings(report, 'G-TARGET'))
        self.assertFalse(findings(report, 'G-DATA'))
        self.assertTrue(any(c['rule'] == 'G-DATA' and c['state'] == 'blocked'
                            for c in report['results'][-1]['checks']))

    def test_unreadable_producer_ports_block_consumer(self):
        d = graph_doc(); d['graphs'][0]['steps'][0]['outputs'] = 17
        report = run(d, 'validateG')
        self.assertTrue(findings(report, 'P-SHAPE'))
        self.assertFalse(findings(report, 'G-DATA'))
        self.assertTrue(any(c['rule'] == 'G-DATA' and c['state'] == 'blocked'
                            for c in report['results'][-1]['checks']))

    def test_malformed_step_shapes_do_not_crash(self):
        for field in graph_doc()['graphs'][0]['steps'][0]:
            for bad in (None, [], {}, True, 17):
                d = graph_doc(); d['graphs'][0]['steps'][0][field] = bad
                report = run(d, 'validateG')
                self.assertNotEqual(report['results'][-1]['verdict'], 'pass', (field, bad))


class ComparisonRegressionTests(unittest.TestCase):
    def states(self, report, unit, rule):
        result = next(r for r in report['results'] if r['input'] == 'primary' and r['unit'] == unit)
        return {c['state'] for c in result['checks'] if c['rule'] == rule}

    def test_unreadable_relations_do_not_prove_agent_minima_missing(self):
        d = graph_doc(); del d['relations']
        report = run(d)
        self.assertFalse(findings(report, 'D-AGENT'))
        for rule in ('D-AGENT', 'D-RELATION', 'D-CYCLE'):
            self.assertEqual(self.states(report, 'D', rule), {'blocked'})

    def test_absent_collection_blocks_existing_affected_records(self):
        for absent in (True, False):
            d = graph_doc()
            if absent:
                del d['relations']
            else:
                d['relations'] = 17
            report = run(d)
            checks = report['results'][0]['checks']
            locations = next(c['locations'] for c in checks if c['rule'] == 'D-RELATION' and c['state'] == 'blocked')
            self.assertEqual(locations, [{'pointer': '' if absent else '/relations'}])
            agent_locations = next(c['locations'] for c in checks if c['rule'] == 'D-AGENT' and c['state'] == 'blocked')
            self.assertEqual(agent_locations, [{'pointer': '/definitions/0'}])

    def test_ambiguous_source_blocks_kind_check_but_checks_duplicate_tuples(self):
        d = graph_doc(); d['definitions'].append(copy.deepcopy(d['definitions'][0]))
        d['relations'].append(copy.deepcopy(d['relations'][0]))
        report = run(d)
        self.assertTrue(findings(report, 'D-RELATION'))
        self.assertEqual(self.states(report, 'D', 'D-RELATION'), {'completed', 'blocked'})
        self.assertEqual(self.states(report, 'D', 'D-AGENT'), {'blocked'})

    def test_unreadable_definitions_do_not_prove_missing_reference(self):
        d = graph_doc(); d['definitions'] = None
        report = run(d)
        self.assertFalse(findings(report, 'D-REFERENCE'))
        self.assertIn('blocked', self.states(report, 'D', 'D-RELATION'))
        self.assertEqual(self.states(report, 'D', 'D-OWNER'), {'blocked'})

    def test_malformed_and_empty_domains_have_distinct_coverage(self):
        for field, operation, unit, rules in (
                ('graphs', 'validateG', 'G', ('G-TARGET', 'G-PATH', 'G-DATA', 'G-APPROVAL')),
                ('runtime', 'validateR', 'R', ('R-REQUIREMENT', 'R-SELECTION'))):
            d = doc(); d[field] = 17
            report = run(d, operation)
            for rule in rules:
                self.assertEqual(self.states(report, unit, rule), {'blocked'})
        d = doc(); d['graphs'] = []
        report = run(d, 'validateG')
        for rule in ('G-TARGET', 'G-PATH', 'G-DATA', 'G-APPROVAL'):
            self.assertEqual(self.states(report, 'G', rule), {'completed'})
        d['runtime'] = {'requirements': [], 'selection': {'engine': {'identity': 'a/b', 'version': '1'},
                                                       'interface': {'identity': 'a/c', 'version': '1'}, 'evidence': []}}
        report = run(d, 'validateR')
        for rule in ('R-REQUIREMENT', 'R-SELECTION'):
            self.assertEqual(self.states(report, 'R', rule), {'completed'})

    def test_payload_extra_field_does_not_hide_typed_checks(self):
        d = graph_doc()
        payload = next(v['payload'] for v in d['definitions'] if v['kind'] == 'Interface')
        payload['extra'] = True
        report = run(d, 'validateG')
        self.assertTrue(findings(report, 'P-SHAPE'))
        self.assertEqual(self.states(report, 'G', 'G-TARGET'), {'completed'})
        self.assertEqual(self.states(report, 'G', 'G-DATA'), {'completed'})
        payload['inputs'] = None
        payload['outputs'] = {'answer': 'boolean'}
        payload['action'] = k('missing')
        report = run(d, 'validateG')
        self.assertTrue(findings(report, 'G-TARGET'))
        self.assertTrue(findings(report, 'G-DATA'))
        self.assertEqual(self.states(report, 'G', 'G-DATA'), {'completed', 'blocked'})

    def test_missing_annex_blocks_consuming_checks(self):
        d = graph_doc()
        d['dependencies'] = [{'id': 'a', 'rootKey': k('annex'), 'status': 'external', 'requiredFor': [], 'sha256': None}]
        d['graphs'][0]['steps'][0]['resources'] = [{'dependency': 'a', 'key': k('resource')}]
        report = run(d, 'resolveG')
        self.assertTrue(findings(report, 'G-RESOLVE'))
        for rule in ('G-TARGET', 'G-RESOLVE'):
            self.assertEqual(self.states(report, 'G', rule), {'completed', 'blocked'})

    def test_absent_graph_still_checks_dependency_portion(self):
        d = doc()
        self.assertEqual(self.states(run(d, 'resolveG'), 'G', 'G-RESOLVE'), {'completed', 'excluded'})
        d['dependencies'] = [{'id': 'a', 'rootKey': k('annex'), 'status': 'external', 'requiredFor': ['resolveG'], 'sha256': None}]
        self.assertTrue(findings(run(d, 'resolveG'), 'G-RESOLVE'))

    def test_malformed_runtime_parent_has_no_selection_inventory(self):
        d = doc(); d['runtime'] = {'requirements': [], 'selection': {'engine': {'identity': 'a/b', 'version': '1'},
                                  'interface': {'identity': 'a/c', 'version': '1'}, 'provider': {'identity': 'bad', 'version': '1'}, 'evidence': []}}
        report = run(d, 'validateR')
        self.assertFalse(any(s['pointer'].startswith('/runtime/selection') for s in report['inventory']['states']))


if __name__ == '__main__':
    unittest.main()
