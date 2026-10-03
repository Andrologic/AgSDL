"""Check claimed delivery/configuration records; never deliver or initialize an Agent."""
import json
import sys
from pathlib import Path

from reader import MARKER, SCHEMA, dumps, equal, loads, shape, validate
from sources import normalize_message, normalize_completion


def operand_value(operand, value):
    if 'value' in operand:
        return operand['value']
    for part in operand['path']:
        if isinstance(part, str) and isinstance(value, dict):
            value = value[part]
        elif not isinstance(part, (str, bool)) and isinstance(value, list):
            value = value[int(part)]
        else:
            raise ValueError('Operand container does not match the path.')
    return value


def select_configuration(document, agent_name, current, retained=None):
    config = document['agents'][agent_name]['configuration']
    alternatives = [config] if isinstance(config, str) else list(config['cases'].values())
    if retained is not None:
        if retained not in alternatives:
            raise ValueError('Invalid retained configuration.')
        return retained
    if isinstance(config, str):
        return config
    choice = operand_value(config['select'], current)
    if not isinstance(choice, str):
        raise ValueError('Configuration choice must be a string.')
    return config['cases'][choice]


def validate_origin_record(document, origin, value):
    """Check only the explicitly named origin, preserving nested data boundaries."""
    schema = {'entry': 'Message', 'prepare': 'Message', 'agent': 'Completion',
              'call': 'CallResult', 'join': 'JoinResult', 'error': 'ErrorInput'}.get(origin)
    if schema is None or not shape(value, SCHEMA['$defs'][schema]):
        raise ValueError('Input does not match its claimed origin.')
    if origin in ('entry', 'prepare'):
        # Catalog refs are authored Message content, not arbitrary inline values.
        return normalize_message(value, document)[1]
    if origin == 'agent':
        observations = normalize_completion(value)[1]
        if 'responseMessages' in value:
            assembled = '\n'.join(part for msg in value['responseMessages'] if (part := ''.join(msg)) != '')
            if 'text' in value and value['text'] != assembled:
                raise ValueError('Inconsistent recorded response text.')
        return observations
    # Call data and error details stay literal. Join members have shapes but no
    # independently supplied producing origins; do not infer nested provenance.
    return []


def delivered_message(document, origin, value):
    """Declared adaptation only. Call validate_origin_record before adapting supplied records."""
    if origin in ('entry', 'prepare'):
        return normalize_message(value, document)[0]
    if origin == 'agent':
        text = value.get('text', '')
        if 'responseMessages' in value:
            text = '\n'.join(part for msg in value['responseMessages'] if (part := ''.join(msg)) != '')
        return {'resources': {'result': {'value': text, 'mediaType': 'text/plain'}}}
    key = {'call': 'data', 'join': 'members', 'error': 'error'}[origin]
    return {'resources': {'error' if origin == 'error' else 'result': {
        'value': value if origin == 'join' else value[key], 'mediaType': 'application/json'}}}


def check_delivery(document, agent_name, record):
    report = {'contract': MARKER, 'valid': False,
              'scope': 'recorded-delivery-and-configuration', 'executionSupport': 'not-assessed'}

    def failure(code, message):
        return {**report, 'error': {'code': code, 'message': message, 'details': []}}

    if (not isinstance(agent_name, str) or not validate(document)['valid'] or
            agent_name not in document['agents']):
        return failure('INVALID_REQUEST', 'Select an Agent in a valid document.')
    if not shape(record, SCHEMA['$defs']['DeliveryRecord']):
        return failure('INVALID_RECORD', 'Invalid delivery record shape.')
    try:
        observations = validate_origin_record(document, record['origin'], record['input'])
    except (KeyError, ValueError) as error:
        return failure('INVALID_RECORD', str(error))
    config = document['agents'][agent_name]['configuration']
    allowed = [config] if isinstance(config, str) else list(config['cases'].values())
    if 'retainedConfiguration' in record:
        selected = record['retainedConfiguration']
        if selected not in allowed:
            return failure('INVALID_RECORD', 'Retained configuration is not a declared alternative.')
    elif isinstance(config, str):
        selected = config
    else:
        try:
            choice = operand_value(config['select'], record['input'])
            if not isinstance(choice, str):
                raise ValueError('Configuration case must be a string.')
            selected = config['cases'][choice]
        except (KeyError, IndexError, ValueError):
            return failure('CONFIGURATION', 'Recorded input cannot select a configuration.')
    if record['configuration'] != selected:
        return failure('INVALID_RECORD', 'Claimed configuration differs from the selected or retained one.')

    value, origin = record['input'], record['origin']
    expected = delivered_message(document, origin, value)
    try:
        claimed, claimed_sources = normalize_message(record['message'], document)
    except (KeyError, ValueError):
        return failure('INVALID_RECORD', 'Invalid delivered URI, base or reference.')
    if not equal(claimed, expected):
        return failure('INVALID_RECORD', 'Claimed Message does not preserve the declared origin delivery.')
    return {**report, 'valid': True, 'sources': observations,
            'unassessed': [x['path'] for x in observations + claimed_sources if x['status'] == 'unresolved']}


def main():
    if len(sys.argv) != 4:
        print('Usage: python3 check_delivery.py DOCUMENT.json AGENT RECORD.json', file=sys.stderr)
        return 2
    try:
        report = check_delivery(loads(Path(sys.argv[1]).read_bytes()), sys.argv[2],
                                loads(Path(sys.argv[3]).read_bytes()))
    except (ValueError, UnicodeError, RecursionError, ArithmeticError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(dumps(report))
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
