"""Check recorded Agent outputs without executing an Agent or fetching its files."""
import json
import sys
from pathlib import Path

from reader import MARKER, SCHEMA, loads, pointer, shape, validate


def check_completion(document, step_name, result):
    report = {'contract': MARKER, 'valid': False,
              'scope': 'recorded-output-constraints', 'executionSupport': 'not-assessed'}

    def invalid_request(message):
        return {**report, 'error': {'code': 'INVALID_REQUEST', 'message': message, 'details': []}}

    if not validate(document)['valid']:
        return invalid_request('Validate the document before checking a completion.')
    step = document.get('flow', {}).get('steps', {}).get(step_name)
    if step is None or step['type'] != 'agent':
        return invalid_request('Select a declared Agent step.')
    if not shape(result, SCHEMA['$defs']['Completion']):
        return {**report, 'error': {'code': 'INVALID_RECORD',
                'message': 'The completion record does not match its declared shape.', 'details': []}}

    interface = document['agents'][step['agent']].get('interface', {})
    results = result.get('results', {})
    allowed = interface.get('outputMediaTypes')
    details = []

    def violation(location, rule, expected):
        details.append({'path': pointer(location), 'rule': rule, 'expected': expected})

    if result.get('text', '') and allowed is not None and 'text/plain' not in allowed:
        violation(['text'], 'format', allowed)
    for name, source in results.items():
        if allowed is not None and source.get('mediaType') not in allowed:
            violation(['results', name, 'mediaType'], 'format', allowed)
    for name, constraint in interface.get('results', {}).items():
        if name not in results:
            if constraint.get('required', False):
                violation(['results', name], 'required', constraint['mediaTypes'])
        elif results[name].get('mediaType') not in constraint['mediaTypes']:
            violation(['results', name, 'mediaType'], 'format', constraint['mediaTypes'])

    if 'decision' in step and result.get('choice') not in step['decision']['choices']:
        violation(['choice'], 'choice', step['decision']['choices'])

    if details:
        return {**report, 'error': {'code': 'OUTPUT_CONSTRAINT',
                'message': 'Complete or correct the required outputs for this work.',
                'details': details}}
    return {**report, 'valid': True}


def main():
    if len(sys.argv) != 4:
        print('Usage: python3 check_completion.py DOCUMENT.json STEP RESULT.json', file=sys.stderr)
        return 2
    try:
        report = check_completion(loads(Path(sys.argv[1]).read_bytes()), sys.argv[2],
                                  loads(Path(sys.argv[3]).read_bytes()))
    except (ValueError, UnicodeError, RecursionError, ArithmeticError):
        print('Invalid or unsupported JSON input.', file=sys.stderr)
        return 2
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
