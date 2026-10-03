"""Check claimed delivery/configuration records; never deliver or initialize an Agent."""
import json
import sys
from pathlib import Path

from reader import MARKER, SCHEMA, equal, loads, shape, validate


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


def check_delivery(document, agent_name, record):
    report = {'contract': MARKER, 'valid': False,
              'scope': 'recorded-delivery-and-configuration', 'executionSupport': 'not-assessed'}

    def failure(code, message):
        return {**report, 'error': {'code': code, 'message': message, 'details': []}}

    if not validate(document)['valid'] or agent_name not in document['agents']:
        return failure('INVALID_REQUEST', 'Select an Agent in a valid document.')
    if not shape(record, SCHEMA['$defs']['DeliveryRecord']):
        return failure('INVALID_RECORD', 'Invalid delivery record shape.')
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
    if origin in ('entry', 'prepare'):
        if not shape(value, SCHEMA['$defs']['Message']):
            return failure('INVALID_RECORD', 'Message origin requires a Message value.')
        expected = value
    elif origin == 'agent':
        if not shape(value, SCHEMA['$defs']['Completion']):
            return failure('INVALID_RECORD', 'Agent origin requires a completion shape.')
        text = value.get('text', '')
        if 'responseMessages' in value:
            assembled = '\n'.join(part for msg in value['responseMessages'] if (part := ''.join(msg)) != '')
            if 'text' in value and text != assembled:
                return failure('INVALID_RECORD', 'Inconsistent recorded response text.')
            text = assembled
        expected = {'resources': {'result': {'value': text, 'mediaType': 'text/plain'}}}
    else:
        key = {'call': 'data', 'join': 'members', 'error': 'error'}[origin]
        if not isinstance(value, dict) or set(value) != {key}:
            return failure('INVALID_RECORD', 'Origin requires its declared result envelope.')
        if origin == 'error' and not shape(value['error'], SCHEMA['$defs']['Error']):
            return failure('INVALID_RECORD', 'Unknown or malformed terminal failure input.')
        if origin == 'join' and not isinstance(value['members'], dict):
            return failure('INVALID_RECORD', 'Join members must be a map.')
        expected = {'resources': {'error' if origin == 'error' else 'result': {
            'value': value if origin == 'join' else value[key], 'mediaType': 'application/json'}}}
    if not equal(record['message'], expected):
        return failure('INVALID_RECORD', 'Claimed Message does not preserve the declared origin delivery.')
    return {**report, 'valid': True}


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
    print(json.dumps(report, ensure_ascii=True, sort_keys=True))
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
