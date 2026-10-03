"""Check recorded Agent outputs without executing an Agent or fetching its files."""
import json
import sys
from pathlib import Path

from reader import MARKER, SCHEMA, dumps, loads, pointer, shape, validate
from modular import selected_step
from declarations import constraint_matches
from sources import normalize_completion


def check_completion(document, step_name, result):
    report = {'contract': MARKER, 'valid': False,
              'scope': 'recorded-output-constraints', 'executionSupport': 'not-assessed'}

    def invalid_request(message):
        return {**report, 'error': {'code': 'INVALID_REQUEST', 'message': message, 'details': []}}

    if not validate(document)['valid']:
        return invalid_request('Validate the document before checking a completion.')
    step, _ = selected_step(document, step_name)
    if (step is None or step['type'] != 'agent' or
            step.get('delivery', 'queue') == 'steering'):
        return invalid_request('Select a declared Agent step.')
    if not shape(result, SCHEMA['$defs']['Completion']):
        return {**report, 'error': {'code': 'INVALID_RECORD',
                'message': 'The completion record does not match its declared shape.', 'details': []}}

    if 'choice' in result and 'decision' not in step:
        return {**report, 'error': {'code': 'INVALID_RECORD',
                'message': 'This Agent step declares no decision; omit choice.', 'details': []}}

    text = result.get('text', '')
    if 'responseMessages' in result:
        assembled = '\n'.join(part for message in result['responseMessages']
                              if (part := ''.join(message)) != '')
        if 'text' in result and text != assembled:
            return {**report, 'error': {'code': 'INVALID_RECORD',
                    'message': 'Text differs from the recorded response Message assembly.', 'details': []}}
        text = assembled

    try:
        normalized, sources = normalize_completion(result)
    except ValueError:
        return {**report, 'error': {'code': 'INVALID_RECORD', 'message': 'Invalid URI or base.', 'details': []}}
    unassessed = [x['path'] for x in sources if x['status'] == 'unresolved']

    interface = document['agents'][step['agent']].get('interface', {})
    results = result.get('results', {})
    allowed = interface.get('outputMediaTypes')
    details = []

    def violation(location, rule, expected):
        details.append({'path': pointer(location), 'rule': rule, 'expected': expected})

    if text and allowed is not None and 'text/plain' not in allowed:
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

        if name in results and 'valueSchema' in constraint:
            if 'uri' in results[name]:
                if pointer(['results', name]) not in unassessed:
                    unassessed.append(pointer(['results', name]))
            elif not constraint_matches(results[name]['value'], constraint['valueSchema']):
                violation(['results', name, 'value'], 'structure', constraint['valueSchema'])

    if 'decision' in step and result.get('choice') not in step['decision']['choices']:
        violation(['choice'], 'choice', step['decision']['choices'])

    if details:
        return {**report, 'error': {'code': 'OUTPUT_CONSTRAINT',
                'message': 'Complete or correct the required outputs for this work.',
                'details': details}}
    return {**report, 'valid': True, 'text': text, 'normalizedResults': normalized.get('results', {}),
            'sources': sources, 'unassessed': unassessed,
            'constraintAssessment': 'unassessed' if unassessed else 'checked'}


def main():
    if len(sys.argv) != 4:
        print('Usage: python3 check_completion.py DOCUMENT.json STEP RESULT.json', file=sys.stderr)
        return 2
    try:
        address = loads(sys.argv[2].encode()) if sys.argv[2].startswith('[') else sys.argv[2]
        report = check_completion(loads(Path(sys.argv[1]).read_bytes()), address,
                                  loads(Path(sys.argv[3]).read_bytes()))
    except (ValueError, UnicodeError, RecursionError, ArithmeticError):
        print('Invalid or unsupported JSON input.', file=sys.stderr)
        return 2
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(dumps(report))
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
