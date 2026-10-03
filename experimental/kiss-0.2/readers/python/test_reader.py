"""Expectations transcribed from proposal 0017, not another reader's output."""
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from reader import validate, lexical, EDITION

HERE = Path(__file__).resolve().parent
EXAMPLES = HERE.parents[1] / 'examples'


def document(name):
    return json.loads((EXAMPLES / (name + '.json')).read_text())


def read(value):
    return validate(json.dumps(value).encode())


def unit(report, name):
    return next(r for r in report['results'] if r['unit'] == name)


def observations(report):
    ds, gs = set(), set()
    for r in report['results']:
        ds.update((r['unit'], x['code'], x['location'], x['outcome']) for x in r['diagnostics'])
        gs.update((r['unit'], x['code'], x['location'], tuple(sorted(x['causes']))) for x in r['incomplete'])
    return ds, gs


def D(u, c, p, o='fail'):
    return u, c, p, o


def G(u, c, p, *causes):
    return u, c, p, tuple(sorted(causes or ('shape',)))


class ReaderTests(unittest.TestCase):
    def test_duplicate_and_unreadable_slot_ids_union_causes(self):
        for malformed in (None, {}, [], 17):
            d = document('two-configurations')
            slots = d['agents']['writer']['instructions']
            slots.extend([copy.deepcopy(slots[0]), copy.deepcopy(slots[0])])
            slots[2]['id'] = malformed
            ds = [D('core', 'SHAPE', '/agents/writer/instructions/2/id'),
                  D('core', 'SLOT-ID', '/agents/writer/instructions')]
            gs = [G('core', 'SLOT-ID', '/agents/writer/instructions')]
            gs += [G('configuration', 'CONTENT', '/configurations/' + c + '/agents/0', 'reference', 'shape')
                   for c in ('primary', 'alternate')]
            gs += [G('compatibility', 'ENGINE', '/configurations/primary/agents/0', 'reference', 'shape')]
            self.assert_observations(d, ds, gs)
            d['configurations']['primary']['agents'][0]['claims'][0]['status'] = 'unsupported'
            self.assert_observations(d, ds + [D('compatibility', 'ENGINE', '/configurations/primary/agents/0')], gs)

    def test_c2_assignment_without_step_id_lookup(self):
        d = document('duplicate-step-assign')
        self.assert_observations(d, [D('flow', 'STEP-ID', '/graphs/g/steps')], [G('flow', 'PATH', '/graphs/g')])
        self.assertEqual(unit(read(d), 'configuration')['outcome'], 'pass')
        del d['graphs']['g']['steps'][1]['id']
        self.assert_observations(d, [D('flow', 'SHAPE', '/graphs/g/steps/1')],
                                 [G('flow', 'STEP-ID', '/graphs/g/steps'), G('flow', 'PATH', '/graphs/g')])
        del d['graphs']['g']['steps'][1]['kind']
        self.assertIn(G('configuration', 'ASSIGN', '/configurations/c'), observations(read(d))[1])

    def test_scope_resources_container_and_elements(self):
        p = '/graphs/release/steps/2'
        for resources in (None, {}, 'x', [], [None]):
            d = document('governed-call')
            d['graphs']['release']['steps'][2]['scope']['resources'] = resources
            location = p + '/scope/resources'
            shape = location + '/0' if resources == [None] else location
            gap = location if isinstance(resources, list) else p + '/scope'
            self.assert_observations(d, [D('flow', 'SHAPE', shape)], [G('flow', 'SCOPE', p), G('flow', 'UNIQUE', gap)])
        d['graphs']['release']['steps'][2]['scope']['resources'] = ['x', 'x']
        self.assert_observations(d, [D('flow', 'UNIQUE', location)])

    def test_terminal_approval_target_failure(self):
        p = '/graphs/release/steps/'
        for call in ('missing', 'end'):
            d = document('governed-call')
            # Select an existing end for the wrong-kind branch.
            if call != 'missing':
                call = next(s['id'] for s in d['graphs']['release']['steps'] if s['kind'] == 'end')
            d['graphs']['release']['steps'][0].update(call=call, timeoutMs=None)
            self.assert_observations(d,
                [D('flow', 'SHAPE', p + '0/timeoutMs'), D('flow', 'APPROVAL', p + '0'), D('flow', 'APPROVAL', p + '1')],
                [G('flow', 'APPROVAL-DATA', p + '0', 'reference')])

    def test_graph_input_binding_has_no_producer_availability_clause(self):
        d = document('duplicate-step-assign')
        g = d['graphs']['g']
        g['inputs'] = g['outputs'] = {'x': 'string'}
        g['steps'][0].update(outcome='success', bindings={'x': {'input': 'x'}})
        del g['steps'][0]['reason']
        self.assert_observations(d, [D('flow', 'STEP-ID', '/graphs/g/steps')], [G('flow', 'PATH', '/graphs/g')])

    def test_extra_edition_key_preserves_observable_requirement(self):
        d = document('tool-incompatible')
        binding = d['configurations']['primary']['agents'][0]['tools'][0]
        binding['claims'][0]['capability']['extra'] = True
        report = read(d)
        ds, gs = observations(report)
        self.assertIn(D('compatibility', 'TOOL', '/configurations/primary/agents/0/tools/0'), ds)
        self.assertNotIn(G('compatibility', 'TOOL', '/configurations/primary/agents/0/tools/0'), gs)

    def assert_observations(self, doc, ds=(), gs=()):
        self.assertEqual(observations(read(doc)), (set(ds), set(gs)))

    def test_example_observations(self):
        for name in ('agent-embedded', 'agent-named', 'two-agent-sequence', 'two-configurations', 'governed-call'):
            with self.subTest(name=name):
                self.assert_observations(document(name))
        self.assert_observations(document('tool-incompatible'), [D('compatibility', 'TOOL', '/configurations/primary/agents/0/tools/0')])
        self.assert_observations(document('governed-missing-scope'), [D('flow', 'SCOPE', '/graphs/release/steps/2')], [G('flow', 'APPROVAL-DATA', '/graphs/release/steps/' + str(i)) for i in (0, 1)])
        self.assert_observations(document('required-extension'), [D('external', 'REQUIRED', '/extensions/0', 'unsupported')], [G('external', 'REQUIRED', '/extensions/0', 'unsupported')])
        self.assert_observations(document('missing-reference'), [D('core', 'REF', '/agents/writer/instructions/0/content')])
        self.assert_observations(document('ambiguous-reference'), [D('core', 'ID', '/instructions/draft'), D('core', 'ID', '/interfaces/draft')], [G('core', 'REF', '/agents/writer/instructions/0/content', 'reference')])
        self.assert_observations(document('independent-errors'), [D('core', 'REF', '/agents/writer/instructions/0/content'), D('core', 'SHAPE', '/interfaces/text/operations/rewrite/mode'), D('external', 'REQUIRED', '/extensions/0', 'unsupported')], [G('external', 'REQUIRED', '/extensions/0', 'unsupported')])
        self.assert_observations(document('unknown-support'), [D('compatibility', 'ENGINE', '/configurations/primary/agents/0', 'inconclusive')])
        self.assert_observations(document('application-order-conflict'), [D('configuration', 'CONTENT', '/configurations/ordered/agents/0')], [G('compatibility', 'ENGINE', '/configurations/ordered/agents/0', 'reference')])
        p = '/configurations/primary/agents/'
        self.assert_observations(document('conflicting-bindings'), [D('configuration', 'ASSIGN', '/configurations/primary')], [G(u, c, p + str(i), 'reference') for i in (0, 2) for u, c in (('configuration', 'CONTENT'), ('configuration', 'TOOLS'), ('compatibility', 'ENGINE'), ('compatibility', 'TOOL'))])

    def test_removed_actor_fields_are_rejected_without_lookup(self):
        d = document('agent-embedded')
        d['principals'] = {}
        self.assert_observations(d, [D('core', 'SHAPE', '/principals')])
        del d['principals']
        d['agents']['writer']['principal'] = {'ref': 'missing'}
        self.assert_observations(d, [D('core', 'SHAPE', '/agents/writer/principal')])
        d = document('governed-call')
        d['graphs']['release']['steps'][0]['approvers'] = [{'ref': 'missing'}]
        self.assert_observations(d, [D('flow', 'SHAPE', '/graphs/release/steps/0/approvers')],
                                 [G('flow', 'APPROVAL', '/graphs/release/steps/' + str(i)) for i in (0, 1)])

    def test_explicit_scope_does_not_require_actor_or_readable_other_trigger(self):
        d = document('governed-call')
        d['agents']['writer']['tools'] = [{'ref': 'missing'}]
        ds, gs = observations(read(d))
        self.assertIn(D('core', 'REF', '/agents/writer/tools/0'), ds)
        self.assertFalse(any(x[1] == 'SCOPE' for x in ds | gs))

    def test_report_and_absence(self):
        raw = b'{"edition":"agsdl-exp-0017-c1","agents":{}}\n'
        result = validate(raw)
        self.assertEqual(result['input']['sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(set(result), {'edition', 'processor', 'operation', 'input', 'results'})
        self.assertEqual(result['edition'], 'agsdl-exp-0017-c1')
        self.assertEqual(result['processor'], {'identity': 'agsdl-experimental/python-kiss', 'version': '3'})
        old = json.loads(raw)
        old['edition'] = 'agsdl-exp-0016-c2'
        self.assert_observations(old, [D('core', 'SHAPE', '/edition')],
                                 [G(u, 'CHECKS', '') for u in ('flow', 'configuration', 'compatibility', 'external')])
        self.assertEqual(len(result['results']), 6)
        self.assertEqual([x['outcome'] for x in result['results']], ['pass', 'pass'] + ['not-applicable'] * 4)
        self.assertNotEqual(result['input']['sha256'], validate(raw.rstrip())['input']['sha256'])
        d = json.loads(raw)
        d.update(graphs={}, configurations={}, extensions=[])
        self.assertEqual([x['outcome'] for x in read(d)['results']], ['pass'] * 4 + ['not-applicable', 'pass'])

    def test_nonobject_roots(self):
        for raw in (b'null', b'[]', b'"x"', b'3', b'true'):
            with self.subTest(raw=raw):
                r = validate(raw)
                self.assertEqual(observations(r), ({D('core', 'SHAPE', '')}, {G(u, 'CHECKS', '') for u in ('core', 'flow', 'configuration', 'compatibility', 'external')}))
                self.assertEqual([x['outcome'] for x in r['results']], ['pass', 'fail'] + ['inconclusive'] * 4)
                self.assertEqual([x['presence'] for x in r['results']], ['present'] + ['undetermined'] * 5)

    def test_strict_json_and_opaque_numbers(self):
        for raw in (b'\xef\xbb\xbf{}', b'{"x":1,"x":2}', b'{"x":1,"\\u0078":2}', b'"\\ud800"', b'"\xed\xa0\x80"', b'NaN', b'{}{}', b'{"x":01}', b'[1,]', b'"\xe2X"'):
            with self.subTest(raw=raw):
                self.assertEqual(observations(validate(raw)), ({D('syntax', 'SYNTAX', '')}, {G(u, 'CHECKS', '') for u in ('core', 'flow', 'configuration', 'compatibility', 'external')}))
        raw = b'{"edition":"agsdl-exp-0017-c1","agents":{},"annotations":1e999999999999999999999999}'
        self.assertEqual(unit(validate(raw), 'core')['outcome'], 'pass')
        value = lexical.Parser(b'9007199254740993').parse()
        self.assertIsNone(lexical.integer(value))
        self.assertEqual(lexical.integer(lexical.Parser(b'1e2').parse()), 100)
        self.assertIsNone(lexical.integer(lexical.Parser(b'1.1').parse()))
        with self.assertRaises(TypeError):
            validate('{}')

    def test_binding_choice_witness(self):
        d = document('two-agent-sequence')
        p = '/graphs/pipeline/steps/1'
        for value in ({'input': 'text', 'step': 'draft-call', 'port': 'text'}, {}, {'port': 'text'}):
            d['graphs']['pipeline']['steps'][1]['bindings']['text'] = value
            self.assert_observations(d, [D('flow', 'SHAPE', p + '/bindings/text')], [G('flow', 'DATA', p)])
        d['graphs']['pipeline']['steps'][1]['bindings']['text'] = {'input': 17}
        self.assert_observations(d, [D('flow', 'SHAPE', p + '/bindings/text/input')], [G('flow', 'DATA', p)])

    def test_unknown_kind_witness(self):
        d = document('two-agent-sequence')
        del d['graphs']['pipeline']['steps'][0]['kind']
        p = '/graphs/pipeline/steps/'
        gaps = [G('flow', c, p + '0') for c in ('REF', 'OPERATION', 'DATA', 'SCOPE', 'APPROVAL', 'APPROVAL-DATA', 'UNIQUE')]
        gaps += [G('flow', 'PATH', '/graphs/pipeline'), G('flow', 'DATA', p + '1', 'reference', 'path'), G('flow', 'DATA', p + '2', 'path'), G('flow', 'SCOPE', p + '1')]
        self.assert_observations(d, [D('flow', 'SHAPE', p + '0')], gaps)

    def test_missing_required_agent_catalog_blocks_lookups(self):
        d = document('two-agent-sequence')
        del d['agents']
        p = '/graphs/pipeline/steps/'
        gs = [G('core', code, '') for code in ('ID', 'REF', 'SLOT-ID', 'UNIQUE')]
        for i in (0, 1):
            gs.append(G('flow', 'REF', p + str(i) + '/agent', 'reference'))
            gs.extend(G('flow', code, p + str(i), 'reference') for code in ('OPERATION', 'DATA', 'SCOPE'))
        gs.append(G('flow', 'DATA', p + '2', 'reference'))
        self.assert_observations(d, [D('core', 'SHAPE', '')], gs)

    def test_missing_gate_target_witness(self):
        d = document('governed-call')
        d['graphs']['release']['steps'][0]['call'] = 'missing'
        p = '/graphs/release/steps/'
        self.assert_observations(d, [D('flow', 'APPROVAL', p + '0'), D('flow', 'APPROVAL', p + '1')], [G('flow', 'APPROVAL-DATA', p + '0', 'reference')])

    def test_unreadable_incoming_approval_call(self):
        p = '/graphs/release/steps/'
        for absent in (True, False):
            with self.subTest(absent=absent):
                d = document('governed-call')
                if absent:
                    del d['graphs']['release']['steps'][0]['call']
                else:
                    d['graphs']['release']['steps'][0]['call'] = None
                ds = [D('flow', 'SHAPE', p + ('0' if absent else '0/call'))]
                gs = [G('flow', 'APPROVAL', p + '0'), G('flow', 'APPROVAL-DATA', p + '0'), G('flow', 'APPROVAL', p + '1')]
                self.assert_observations(d, ds, gs)
                with tempfile.NamedTemporaryFile(suffix='.json') as artifact:
                    artifact.write(json.dumps(d).encode())
                    artifact.flush()
                    result = subprocess.run([sys.executable, str(HERE / 'cli.py'), artifact.name], capture_output=True)
                self.assertEqual(result.returncode, 0)
                self.assertEqual(result.stderr, b'')
                self.assertEqual(observations(json.loads(result.stdout)), (set(ds), set(gs)))

        # An independent known violation survives the blocked incoming link.
        d['graphs']['release']['steps'][2]['scope']['resources'] *= 2
        ds.append(D('flow', 'UNIQUE', p + '2/scope/resources'))
        self.assert_observations(d, ds, gs)

    def test_independent_binding_identity_witness(self):
        d = document('two-configurations')
        del d['configurations']['primary']['agents'][0]['agent']
        d['configurations']['primary']['agents'][1]['claims'][0]['status'] = 'unsupported'
        p = '/configurations/primary/agents/'
        gaps = [G('configuration', c, p + '0') for c in ('REF', 'CONTENT', 'TOOLS')]
        gaps += [G('configuration', 'ASSIGN', '/configurations/primary'), G('compatibility', 'ENGINE', p + '0'), G('compatibility', 'TOOL', p + '0')]
        self.assert_observations(d, [D('configuration', 'SHAPE', p + '0'), D('compatibility', 'ENGINE', p + '1')], gaps)

    def test_independent_claim_status_witness(self):
        d = document('two-configurations')
        claims = d['configurations']['primary']['agents'][0]['claims']
        claims[0]['status'] = 'unsupported'
        claims[1]['status'] = 17
        p = '/configurations/primary/agents/0'
        self.assert_observations(d, [D('configuration', 'SHAPE', p + '/claims/1/status'), D('compatibility', 'ENGINE', p)], [G('configuration', 'UNIQUE', p + '/claims'), G('compatibility', 'ENGINE', p)])

    def test_empty_requirements_need_no_claim_lookup(self):
        d = document('tool-incompatible')
        d['tools']['lookup']['requires'] = []
        d['configurations']['primary']['agents'][0]['tools'][0]['claims'] = [{}]
        p = '/configurations/primary/agents/0/tools/0'
        ds = [D('configuration', 'SHAPE', p + '/claims/0')]
        gs = [G('configuration', 'UNIQUE', p + '/claims')]
        self.assert_observations(d, ds, gs)
        self.assertEqual(unit(read(d), 'compatibility')['outcome'], 'pass')
        d['tools']['lookup']['requires'] = [{}]
        self.assert_observations(d, ds + [D('core', 'SHAPE', '/tools/lookup/requires/0')],
                                 gs + [G('core', 'UNIQUE', '/tools/lookup/requires'), G('compatibility', 'TOOL', p)])

    def test_omission_witnesses_and_null_choices(self):
        d = document('two-configurations')
        p = '/configurations/primary/agents/0'
        d['configurations']['primary']['agents'][0]['applications'] = []
        self.assert_observations(d, [D('configuration', 'CONTENT', p)], [G('compatibility', 'ENGINE', p, 'reference')])
        d = document('tool-incompatible')
        d['configurations']['primary']['agents'][0]['tools'] = []
        self.assert_observations(d, [D('configuration', 'TOOLS', p)], [G('compatibility', 'TOOL', p, 'reference')])
        d = document('tool-incompatible')
        d['configurations']['primary']['agents'][0]['tools'][0]['implementation'] = None
        self.assert_observations(d, [D('compatibility', 'TOOL', p + '/tools/0', 'inconclusive')])
        d = document('two-configurations')
        d['configurations']['primary']['agents'][0]['engine'] = None
        self.assert_observations(d, [D('compatibility', 'ENGINE', p, 'inconclusive')])

    def test_governance_guardrails(self):
        d = document('governed-call')
        g = d['graphs']['release']
        g['entry'] = 'send'
        r = read(d)
        self.assertIn(D('flow', 'PATH', '/graphs/release'), observations(r)[0])
        self.assertIn(G('flow', 'APPROVAL', '/graphs/release/steps/0', 'path'), observations(r)[1])
        d = document('two-agent-sequence')
        d['interfaces']['text']['operations']['rewrite']['effects'] = 'unknown'
        self.assert_observations(d, [D('flow', 'SCOPE', '/graphs/pipeline/steps/' + str(i)) for i in (0, 1)])
        d = document('governed-call')
        d['graphs']['release']['steps'][0]['timeoutMs'] = True
        self.assertIn(D('flow', 'SHAPE', '/graphs/release/steps/0/timeoutMs'), observations(read(d))[0])

    def test_data_failure_path_and_missing_operation(self):
        d = document('two-agent-sequence')
        d['graphs']['pipeline']['steps'][0]['failure'] = 'review-call'
        self.assert_observations(d, [D('flow', 'DATA', '/graphs/pipeline/steps/1')])
        d = document('two-agent-sequence')
        d['graphs']['pipeline']['steps'][1]['operation'] = 'absent'
        ds, gs = observations(read(d))
        self.assertIn(D('flow', 'OPERATION', '/graphs/pipeline/steps/1'), ds)
        self.assertIn(G('flow', 'DATA', '/graphs/pipeline/steps/2', 'reference'), gs)

    def test_null_target_port_types_block_only_type_comparison(self):
        d = document('two-agent-sequence')
        d['interfaces']['text']['operations']['rewrite']['inputs']['text'] = None
        ds = [D('core', 'SHAPE', '/interfaces/text/operations/rewrite/inputs/text')]
        gs = [G('flow', 'DATA', '/graphs/pipeline/steps/' + str(i)) for i in (0, 1)]
        self.assert_observations(d, ds, gs)
        d['graphs']['pipeline']['steps'][0]['bindings']['text'] = {'input': 'missing'}
        self.assert_observations(d, ds + [D('flow', 'DATA', '/graphs/pipeline/steps/0')], gs)

        # The null target does not hide an independent known type mismatch.
        d['graphs']['pipeline']['steps'][0]['bindings']['text'] = {'input': 'text'}
        d['interfaces']['text']['operations']['rewrite']['inputs']['flag'] = 'boolean'
        for step in d['graphs']['pipeline']['steps'][:2]:
            step['bindings']['flag'] = {'input': 'text'}
        self.assert_observations(d, ds + [D('flow', 'DATA', '/graphs/pipeline/steps/' + str(i)) for i in (0, 1)], gs)

        d = document('two-agent-sequence')
        d['graphs']['pipeline']['outputs']['text'] = None
        self.assert_observations(d, [D('flow', 'SHAPE', '/graphs/pipeline/outputs/text')],
                                 [G('flow', 'DATA', '/graphs/pipeline/steps/2')])

        d = document('governed-call')
        d['agents']['writer']['interface']['value']['operations']['rewrite']['inputs']['text'] = None
        self.assert_observations(d, [D('core', 'SHAPE', '/agents/writer/interface/value/operations/rewrite/inputs/text')],
                                 [G('flow', 'APPROVAL-DATA', '/graphs/release/steps/' + str(i)) for i in (0, 1)]
                                 + [G('flow', 'DATA', '/graphs/release/steps/2')])

    def test_cli_exit_codes(self):
        cmd = [sys.executable, str(HERE / 'cli.py')]
        for args in ([], ['missing-file-that-does-not-exist'], ['a', 'b']):
            p = subprocess.run(cmd + args, capture_output=True)
            self.assertEqual(p.returncode, 2)
            self.assertEqual(p.stdout, b'')
            self.assertTrue(p.stderr)
        p = subprocess.run(cmd + [str(EXAMPLES / 'tool-incompatible.json')], capture_output=True)
        self.assertEqual(p.returncode, 0)
        self.assertEqual(unit(json.loads(p.stdout), 'compatibility')['outcome'], 'fail')
        self.assertEqual(p.stderr, b'')


if __name__ == '__main__':
    unittest.main()
