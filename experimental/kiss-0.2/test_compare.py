import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import compare


class ComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest, _ = compare.load_cases()
        cls.cases = {c['name']: c for c in cls.manifest['cases']}

    def report(self, name='duplicate-and-unreadable-slots'):
        case = self.cases[name]
        return case, compare.expected_report(case)

    def test_report_rejects_malformed_records_and_collections(self):
        case, baseline = self.report()
        def change(path, value):
            result = copy.deepcopy(baseline)
            owner = result
            for key in path[:-1]:
                owner = owner[key]
            owner[path[-1]] = value
            return result
        variants = [
            (['edition'], 'agsdl-exp-0016-c2'), (['operation'], 'inspect'),
            (['processor'], {'identity': '', 'version': 'v'}),
            (['processor'], {'identity': 'p', 'version': 'v', 'extra': 0}),
            (['processor', 'version'], 1), (['input', 'id'], 'other'),
            (['input', 'sha256'], 'a' * 64), (['input', 'sha256'], 'A' * 64),
            (['results'], baseline['results'][:5]),
            (['results'], baseline['results'][:5] + [baseline['results'][0]]),
            (['results', 0, 'unit'], 'inventory'), (['results', 0, 'phase'], 'remote'),
            (['results', 0, 'subject'], '/other'), (['results', 0, 'presence'], 'unknown'),
            (['results', 0, 'presence'], 'undetermined'),
            (['results', 0, 'outcome'], 'fail'), (['results', 0, 'diagnostics'], {}),
            (['results', 1, 'diagnostics', 0, 'code'], 'ENGINE'),
            (['results', 1, 'diagnostics', 0, 'location'], '/bad~2'),
            (['results', 1, 'diagnostics', 0, 'outcome'], 'pass'),
            (['results', 1, 'diagnostics', 0, 'message'], ''),
            (['results', 1, 'diagnostics', 0, 'message'], 4),
            (['results', 1, 'diagnostics', 0, 'message'], '\ud800'),
            (['results', 1, 'diagnostics'], baseline['results'][1]['diagnostics'] * 2),
            (['results', 1, 'incomplete'], baseline['results'][1]['incomplete'] * 2),
            (['results', 1, 'incomplete', 0, 'causes'], []),
            (['results', 1, 'incomplete', 0, 'causes'], ['shape', 'shape']),
            (['results', 1, 'incomplete', 0, 'causes'], ['unknown']),
            (['results', 1, 'incomplete', 0, 'code'], 'ENGINE'),
        ]
        for path, value in variants:
            with self.subTest(path=path, value=value):
                # ASCII encoding deliberately retains a lone surrogate for the decoder test.
                raw = json.dumps(change(path, value)).encode()
                with self.assertRaises(ValueError):
                    compare.normalize(raw, case['sha256'])
        for path in ([], ['input'], ['results', 0], ['results', 1, 'diagnostics', 0],
                     ['results', 1, 'incomplete', 0]):
            bad = copy.deepcopy(baseline)
            owner = bad
            for key in path:
                owner = owner[key]
            owner['extra'] = None
            with self.subTest(extra=path), self.assertRaises(ValueError):
                compare.normalize(compare.encoded(bad), case['sha256'])

    def test_json_decoder_rejects_parasites_and_duplicate_members(self):
        case, report = self.report()
        raw = compare.encoded(report)
        for bad in (b'log\n' + raw, raw + b'{}', b'\xef\xbb\xbf' + raw,
                    raw.replace(b'"operation": "validate"', b'"operation":"validate","operation":"validate"'),
                    raw.replace(b'"version": "agsdl-exp-0017-c1"', b'"version":NaN'),
                    raw.replace(b'"version": "agsdl-exp-0017-c1"', b'"version":"\xff"')):
            with self.subTest(raw=bad[:30]), self.assertRaises(ValueError):
                compare.normalize(bad, case['sha256'])

    def run_reports(self, case, first, second, returncode=0, timeout=False):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary) / 'case'
            responses = [subprocess.CompletedProcess(['mock'], returncode, compare.encoded(r), b'')
                         for r in (first, second)]
            effect = subprocess.TimeoutExpired(['mock'], 0.01, b'partial', b'error') if timeout else responses
            with patch('compare.subprocess.run', side_effect=effect) as runner:
                result = compare.run_case(case, directory, {'python': ['mock'], 'javascript': ['mock']})
            self.assertEqual(runner.call_count, 2)
            self.assertEqual(runner.call_args_list[0].args[0][-1], runner.call_args_list[1].args[0][-1])
            self.assertEqual((directory / 'primary.input').read_bytes(), (compare.HERE / case['input']).read_bytes())
            self.assertTrue((directory / 'python.stdout').exists())
            self.assertTrue((directory / 'javascript.stderr').exists())
            return result

    def test_shared_wrong_agreement_fails_oracle(self):
        case, report = self.report('missing-reference')
        report['results'][1].update(diagnostics=[], outcome='pass')
        result = self.run_reports(case, report, report)
        self.assertTrue(result['agreement'])
        self.assertFalse(result['passed'])
        self.assertTrue(all(r['validReport'] and not r['oracleMatch'] for r in result['readers'].values()))

    def test_reader_disagreement_fails(self):
        case, good = self.report('missing-reference')
        bad = copy.deepcopy(good)
        bad['results'][1]['diagnostics'][0]['location'] = '/wrong'
        result = self.run_reports(case, good, bad)
        self.assertFalse(result['agreement'])
        self.assertFalse(result['passed'])
        self.assertTrue(result['readers']['python']['oracleMatch'])

    def test_malformed_and_failed_and_incomplete_processes_fail(self):
        case, good = self.report()
        bad = copy.deepcopy(good)
        bad['extra'] = True
        for first, code, timeout in ((bad, 0, False), (good, 2, False), (good, 0, True)):
            with self.subTest(code=code, timeout=timeout):
                result = self.run_reports(case, first, good, returncode=code, timeout=timeout)
                self.assertFalse(result['passed'])
                self.assertFalse(result['readers']['python']['validReport'])

    def test_allowed_reordering_processor_and_messages_pass(self):
        case, first = self.report()
        second = copy.deepcopy(first)
        second['processor'] = {'identity': 'different', 'version': 'different'}
        second['results'].reverse()
        for result in second['results']:
            result['diagnostics'].reverse()
            result['incomplete'].reverse()
            for diagnostic in result['diagnostics']:
                diagnostic['message'] = 'Different wording'
            for gap in result['incomplete']:
                gap['causes'].reverse()
        self.assertTrue(self.run_reports(case, first, second)['passed'])

    def test_cli_refuses_existing_evidence_and_checkout(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            keep = directory / 'keep'
            keep.write_text('unchanged')
            for output in (directory, compare.HERE / 'must-not-create'):
                run = subprocess.run([sys.executable, str(compare.HERE / 'compare.py'), str(output)],
                                     capture_output=True)
                self.assertEqual(run.returncode, 2)
            self.assertEqual(keep.read_text(), 'unchanged')
            self.assertFalse((compare.HERE / 'must-not-create').exists())

    def test_command_exit_tracks_oracle_grammar_and_agreement(self):
        case, good = self.report('missing-reference')
        wrong = copy.deepcopy(good)
        wrong['results'][1].update(diagnostics=[], outcome='pass')
        malformed = copy.deepcopy(good)
        malformed['extra'] = True
        for first, second, expected_exit in ((good, good, 0), (wrong, wrong, 1),
                                              (good, wrong, 1), (malformed, good, 1)):
            with tempfile.TemporaryDirectory() as temporary:
                output = Path(temporary) / 'new'
                manifest = dict(self.manifest, cases=[case])
                responses = [subprocess.CompletedProcess(['mock'], 0, compare.encoded(r), b'')
                             for r in (first, second)]
                with patch('compare.load_cases', return_value=(manifest, compare.encoded(manifest))), \
                     patch('compare.git', return_value='test'), \
                     patch('compare.subprocess.check_output', return_value='test-runtime'), \
                     patch('compare.subprocess.run', side_effect=responses), \
                     patch('sys.argv', ['compare.py', str(output)]), \
                     patch('builtins.print'):
                    self.assertEqual(compare.main(), expected_exit)
                summary = json.loads((output / 'summary.json').read_bytes())
                self.assertEqual(summary['passed'], int(expected_exit == 0))

    def test_materialized_provenance_matches_exact_bytes(self):
        for case in self.manifest['cases']:
            provenance = case['provenance']
            actual = (compare.HERE / case['input']).read_bytes()
            with self.subTest(case=case['name']):
                if provenance['kind'] == 'exact bytes':
                    self.assertEqual(actual, bytes.fromhex(provenance['hex']))
                elif provenance['kind'] == 'materialized mutation':
                    base = (compare.HERE / provenance['baseInput']).read_bytes()
                    self.assertEqual(compare.digest(base), provenance['baseSha256'])
                    value = json.loads(base)
                    for mutation in provenance['mutations']:
                        parts = [p.replace('~1', '/').replace('~0', '~')
                                 for p in mutation['path'].split('/')[1:]]
                        owner = value
                        for part in parts[:-1]:
                            owner = owner[int(part)] if isinstance(owner, list) else owner[part]
                        key = int(parts[-1]) if isinstance(owner, list) else parts[-1]
                        if mutation['op'] == 'remove':
                            del owner[key]
                        else:
                            self.assertEqual(mutation['op'], 'replace')
                            owner[key] = mutation['value']
                    self.assertEqual(actual, compare.encoded(value))


if __name__ == '__main__':
    unittest.main()
