"""Package isolation from historical imports and repository-only files."""
import base64
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from test_reader import OPERATIONS, encode, minimal_document

READER = Path(__file__).resolve().parent
REPOSITORY = READER.parents[2]


class IsolationTests(unittest.TestCase):
    def test_both_import_orders_with_each_historical_edition(self):
        for directory, marker in (
            ('experimental/readers/python', 'proposal-0012-candidate-2'),
            ('experimental/modular-candidate-1/readers/python', 'proposal-0013-candidate-1'),
        ):
            for official_first in (True, False):
                with self.subTest(edition=marker, official_first=official_first):
                    # Each historical edition has its own process, as their old
                    # unqualified imports are not a shared public package API.
                    script = '''
import importlib, json, sys
sys.path[:0] = [sys.argv[2], sys.argv[1]]
names = ['agsdl_reader', 'reader'] if sys.argv[3] == 'True' else ['reader', 'agsdl_reader']
modules = {name: importlib.import_module(name) for name in names}
source = json.loads(sys.argv[5])
for name, marker in [('agsdl_reader', 'agsdl-0.1.0'), ('reader', sys.argv[4])]:
    for input_marker in ('agsdl-0.1.0', sys.argv[4]):
        source['contract'] = input_marker
        report = modules[name].read('validateD', json.dumps(source).encode())['report']
        assert report['contract'] == marker, report
        assert report['results'][0]['verdict'] == ('pass' if marker == input_marker else 'fail'), report
import reader
assert reader.Result.find.__defaults__[1] == 'candidate rule violation'
assert 'grammar' in sys.modules and sys.modules['grammar'].CONTRACT == sys.argv[4]
'''
                    process = subprocess.run(
                        [sys.executable, '-B', '-c', script, str(READER),
                         str(REPOSITORY / directory), str(official_first), marker,
                         json.dumps(minimal_document())], capture_output=True,
                    )
                    self.assertEqual(process.returncode, 0, process.stderr.decode())

    def test_compatibility_facade_loaded_after_historical_reader(self):
        for directory, marker in (
            ('experimental/readers/python', 'proposal-0012-candidate-2'),
            ('experimental/modular-candidate-1/readers/python', 'proposal-0013-candidate-1'),
        ):
            with self.subTest(edition=marker):
                script = """
import importlib.util, json, sys
sys.path[:0] = [sys.argv[2], sys.argv[1]]
import reader as historical
spec = importlib.util.spec_from_file_location('official_facade', sys.argv[1] + '/reader.py')
official = importlib.util.module_from_spec(spec)
spec.loader.exec_module(official)
source = json.loads(sys.argv[4])
for module, marker in [(official, 'agsdl-0.1.0'), (historical, sys.argv[3])]:
    source['contract'] = marker
    report = module.read('validateD', json.dumps(source).encode())['report']
    assert report['contract'] == marker
    assert report['results'][0]['verdict'] == 'pass', report
assert historical.Result.find.__defaults__[1] == 'candidate rule violation'
"""
                process = subprocess.run(
                    [sys.executable, '-B', '-c', script, str(READER),
                     str(REPOSITORY / directory), marker, json.dumps(minimal_document())],
                    capture_output=True,
                )
                self.assertEqual(process.returncode, 0, process.stderr.decode())

    def test_distribution_without_experimental(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)
            shutil.copytree(READER / 'agsdl_reader', target / 'agsdl_reader',
                            ignore=shutil.ignore_patterns('__pycache__'))
            shutil.copy2(READER / 'cli.py', target / 'cli.py')
            source = (REPOSITORY / 'examples/0.1.0/general-purpose-system.json').read_bytes()
            for operation in OPERATIONS:
                with self.subTest(operation=operation):
                    request = {'operation': operation,
                               'primary': base64.b64encode(source).decode(),
                               'annexes': {}}
                    process = subprocess.run(
                        [sys.executable, '-B', str(target / 'cli.py')], cwd=target,
                        input=encode(request), capture_output=True,
                    )
                    self.assertEqual(process.returncode, 0, process.stderr.decode())
                    report = json.loads(process.stdout)['report']
                    self.assertEqual(report['contract'], 'agsdl-0.1.0')
                    self.assertEqual(report['results'][-1]['verdict'],
                                     'fail' if operation == 'lossyExchange' else 'pass')
