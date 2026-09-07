#!/usr/bin/env python3
"""Check the four documented examples through the existing reader CLIs."""
import argparse
import base64
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / 'examples' / '0.1.0'
OPERATIONS = {
    'inspect': [('inspect', None, 'pass')],
    'validateD': [('D', 'unresolved-document', 'pass')],
    'validateG': [('D', 'unresolved-document', 'pass'), ('G', 'unresolved-document', 'pass')],
    'resolveG': [('D', 'unresolved-document', 'pass'), ('G', 'resolved-graph', 'pass')],
    'validateR': [('D', 'unresolved-document', 'pass'), ('R', 'unresolved-document', 'pass')],
    'exchange': [('exchange', None, 'pass')],
    'lossyExchange': [('exchange', None, 'fail')],
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jsonschema', action='store_true', help='also check derived shapes')
    args = parser.parse_args()
    validators = {}
    if args.jsonschema:
        from jsonschema import Draft202012Validator
        schema = json.loads((ROOT / 'schemas/agsdl.schema.json').read_text())
        for name in ['Document', 'InterfacePayload', 'ToolPayload', 'InstructionsPayload', 'SkillPayload']:
            validators[name] = Draft202012Validator(dict(schema, **{'$ref': '#/$defs/' + name}))
        from referencing import Registry, Resource
        registry = Registry().with_resource('agsdl.schema.json', Resource.from_contents(schema))
        for name, filename in [('G', 'G'), ('R', 'R'), ('Report', 'report')]:
            validators[name] = Draft202012Validator(
                json.loads((ROOT / ('schemas/' + filename + '.schema.json')).read_text()), registry=registry)

    count = 0
    for filename in ['minimal-document.json', 'single-agent.json', 'two-agent-sequence.json', 'general-purpose-system.json']:
        raw = (EXAMPLES / filename).read_bytes()
        document = json.loads(raw)
        if validators:
            validators['Document'].validate(document)
            for field, name in [('graphs', 'G'), ('runtime', 'R')]:
                if field in document:
                    validators[name].validate(document[field])
            # These examples select their Interface in G and reach every
            # Tool/Instructions/Skill in R. Other payloads remain opaque.
            for definition in document['definitions']:
                kind = definition['kind']
                if ((kind == 'Interface' and 'graphs' in document) or
                    (kind in ['Tool', 'Instructions', 'Skill'] and 'runtime' in document)):
                    validators[kind + 'Payload'].validate(definition['payload'])
        for operation, expected in OPERATIONS.items():
            request = json.dumps({'operation': operation, 'primary': base64.b64encode(raw).decode(), 'annexes': {}})
            for label, command in [('python', [sys.executable, 'tooling/readers/python/cli.py']),
                                   ('javascript', ['node', 'tooling/readers/javascript/cli.mjs'])]:
                result = subprocess.run(command, input=request, text=True, capture_output=True,
                                        cwd=ROOT, timeout=30, check=True,
                                        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
                response = json.loads(result.stdout)
                report = response['report']
                actual = [(r['unit'], r['phase'], r['verdict']) for r in report['results']]
                if actual != expected or any(r['input'] != 'primary' for r in report['results']):
                    raise ValueError(f'{filename} {label} {operation}: {actual}, expected {expected}')
                expected_artifacts = {'primary': base64.b64encode(raw).decode()} if operation == 'exchange' else {}
                if response['artifacts'] != expected_artifacts:
                    raise ValueError(f'{filename} {label} {operation}: unexpected artifacts')
                if validators:
                    validators['Report'].validate(report)
                count += 1
        print(f'{filename}: both readers, seven operations passed')
    print(f'{count} responses checked; schemas {"checked" if validators else "not requested"}')


if __name__ == '__main__':
    main()
