"""Tests for the static, non-normative Mermaid flow view."""
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reader import loads
from render_mermaid import render

ROOT = Path(__file__).parent


def example(name):
    return loads((ROOT / 'examples' / (name + '.json')).read_bytes())


class RenderMermaidTests(unittest.TestCase):
    def test_every_example_renders_each_step_once(self):
        for path in sorted((ROOT / 'examples').glob('*.json')):
            document = loads(path.read_bytes())
            text = render(document)
            self.assertTrue(text.startswith('flowchart TD\n'), path.name)
            nodes = re.findall(r'^  s(\d+)[\[{(]', text, re.MULTILINE)
            steps = len(document.get('flow', {}).get('steps', {}))
            self.assertEqual(sorted(map(int, nodes)), list(range(steps)), path.name)

    def test_routes_errors_and_protection_are_labelled(self):
        text = render(example('protected-publication'))
        self.assertIn('s0 -- "approved" --> s1', text)
        self.assertIn('s0 -. "protects" .-> s2', text)
        self.assertIn('s2 -. "error" .-> s4', text)
        self.assertIn('s0{{"owner-approval<br/>approval: authorization"}}', text)

    def test_graphless_document(self):
        self.assertEqual(render(example('conversation')), 'flowchart TD\n  empty["No flow declared"]\n')

    def test_labels_escape_mermaid_syntax(self):
        document = example('conversation')
        document['flow'] = {'entry': 'a', 'steps': {'a': {'type': 'agent', 'agent': 'helper'}}}
        document['agents']['x"<y>&'] = document['agents'].pop('helper')
        document['flow']['steps']['a']['agent'] = 'x"<y>&'
        self.assertIn('agent: x#quot;#lt;y#gt;#amp;', render(document))

    def test_cli_rejects_invalid_and_unreadable_documents(self):
        script = str(ROOT / 'render_mermaid.py')
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory, 'invalid.json')
            invalid.write_text('{"contract":"agsdl-0.2.0"}')
            broken = Path(directory, 'broken.json')
            broken.write_text('{')
            self.assertEqual(subprocess.run([sys.executable, script, str(invalid)], capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run([sys.executable, script, str(broken)], capture_output=True).returncode, 1)
            self.assertEqual(subprocess.run([sys.executable, script, str(Path(directory, 'absent.json'))], capture_output=True).returncode, 2)
            self.assertEqual(subprocess.run([sys.executable, script], capture_output=True).returncode, 2)
        result = subprocess.run([sys.executable, script, str(ROOT / 'examples' / 'test-loop.json')], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith('flowchart TD\n'))


if __name__ == '__main__':
    unittest.main()
