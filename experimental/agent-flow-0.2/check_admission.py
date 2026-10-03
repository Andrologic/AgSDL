"""Check a supplied approval record. This is never an authorization service."""
import sys
from pathlib import Path

from reader import MARKER, SCHEMA, dumps, equal, loads, shape, validate
from modular import expand_document, selected_step
from check_delivery import check_delivery, delivered_message, operand_value, select_configuration


def capture(document, address, occurrence, origin, current, retained=None):
    """Reconstruct prospective values from a record; no live state or effects."""
    step, key = selected_step(document, address)
    if step is None or step['type'] not in ('agent', 'call') or 'scope' not in step:
        raise ValueError('Select a scoped Agent or Call.')
    scope = step['scope']
    invocation = {'declaration': document, 'target': list(key), 'occurrence': occurrence,
                  'origin': origin, 'input': current,
                  'scope': {'action': scope['action'], 'resources': scope['resources'],
                            'context': operand_value(scope['context'], current)}}
    if step['type'] == 'call':
        invocation.update(binding=document['bindings'][step['binding']],
                          arguments={k: operand_value(v, current) for k, v in step.get('arguments', {}).items()})
    else:
        selected = select_configuration(document, step['agent'], current, retained)
        message = delivered_message(document, origin, current)
        record = {'origin': origin, 'input': current, 'message': message, 'configuration': selected}
        if retained is not None:
            record['retainedConfiguration'] = retained
        delivery = check_delivery(document, step['agent'], record)
        if not delivery['valid'] or delivery.get('unassessed'):
            raise ValueError('Cannot capture unresolved or inconsistent Message delivery.')
        invocation.update(agent=step['agent'], configuration=selected, message=message)
    return invocation


def approval_chain(flow, target):
    gates = {key: step for key, step in flow['steps'].items()
             if step['type'] == 'approval' and step['call'] == target}
    ordered = []
    current = target
    while gates:
        previous = next((key for key, step in gates.items() if step['next']['approved'] == [current]), None)
        if previous is None:
            raise ValueError('Invalid approval chain.')
        ordered.insert(0, previous)
        current = previous
        del gates[previous]
    return ordered


def check_admission(document, address, record):
    report = {'contract': MARKER, 'valid': False, 'scope': 'recorded-approval-consistency',
              'executionSupport': 'not-assessed', 'authority': 'unassessed'}

    def failure(code, message):
        return {**report, 'error': {'code': code, 'message': message, 'details': []}}

    if not validate(document)['valid']:
        return failure('INVALID_REQUEST', 'Select a valid document.')
    step, key = selected_step(document, address)
    flow, _, _ = expand_document(document, lambda *args: None)
    if step is None or step['type'] not in ('agent', 'call'):
        return failure('INVALID_REQUEST', 'Select an action-bearing step.')
    chain = approval_chain(flow, key)
    if not chain:
        return failure('INVALID_REQUEST', 'Selected action has no declared approval chain.')
    if not shape(record, SCHEMA['$defs']['AdmissionRecord']):
        return failure('INVALID_RECORD', 'Malformed admission record.')
    if step['type'] == 'call' and 'retainedConfiguration' in record:
        return failure('INVALID_RECORD', 'A Call has no Agent configuration retention.')
    # Even Call input has a producing origin; validate its envelope independently.
    origin_schema = {'entry': 'Message', 'prepare': 'Message', 'agent': 'Completion',
                     'call': 'CallResult', 'join': 'JoinResult', 'error': 'ErrorInput'}[record['origin']]
    if not shape(record['input'], SCHEMA['$defs'][origin_schema]):
        return failure('INVALID_RECORD', 'Input does not match its claimed origin.')
    try:
        expected = capture(document, address, record['occurrence'], record['origin'],
                           record['input'], record.get('retainedConfiguration'))
    except (KeyError, IndexError, ValueError):
        return failure('APPROVAL', 'Cannot capture the prospective invocation from the recorded input.')
    if not equal(expected, record['invocation']):
        return failure('APPROVAL', 'Captured invocation differs from actual admission.')
    if len(record['decisions']) != len(chain):
        return failure('APPROVAL', 'Every gate needs one matching approval.')
    previous_decision = None
    for gate, decision in zip(chain, record['decisions']):
        declaration = flow['steps'][gate]
        entered, decided = int(decision['enteredAt']), int(decision['decidedAt'])
        admitted = int(record['admittedAt'])
        timeout, validity = int(declaration['timeoutMs']), int(declaration['validForMs'])
        if (decision['gate'] != list(gate) or decision['occurrence'] != record['occurrence'] or
            not equal(decision['invocation'], expected) or
            not equal(decision['binding'], document['bindings'][declaration['binding']]) or
            decision['decision'] != 'approved' or not decision['authorityConfirmed'] or
            entered > decided or decided >= entered + min(timeout, validity) or
            decided > admitted or admitted >= entered + validity or
            previous_decision is not None and entered < previous_decision):
            return failure('APPROVAL', 'Approval is mismatched, unauthorized by the record, out of order or expired.')
        previous_decision = decided
    return {**report, 'valid': True}


def main():
    if len(sys.argv) != 4:
        print('Usage: python3 check_admission.py DOCUMENT.json STEP RECORD.json', file=sys.stderr)
        return 2
    try:
        address = loads(sys.argv[2].encode()) if sys.argv[2].startswith('[') else sys.argv[2]
        report = check_admission(loads(Path(sys.argv[1]).read_bytes()), address,
                                 loads(Path(sys.argv[3]).read_bytes()))
    except (ValueError, UnicodeError, RecursionError, ArithmeticError, OSError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(dumps(report))
    return 0 if report['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
