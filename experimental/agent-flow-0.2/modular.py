"""Finite local expansion and approval-chain checks, without scheduling work."""
from copy import deepcopy


def routes(step):
    nxt = step.get('next', [])
    return list(nxt.values()) if isinstance(nxt, dict) else [nxt]


def check_approvals(flow, document, fail):
    steps = flow['steps']
    edges = {name: [] for name in steps}
    for name, step in steps.items():
        nxt = step.get('next', [])
        for label, targets in (nxt.items() if isinstance(nxt, dict) else [('next', nxt)]):
            for target in targets:
                if target in edges:
                    edges[target].append((name, label))
        for target in step.get('onError', []):
            if target in edges:
                edges[target].append((name, 'onError'))
    targets = {}
    for name, step in steps.items():
        loc = ['flow', 'steps', name]
        scope = step.get('scope')
        if scope and len(scope['resources']) != len(set(scope['resources'])):
            fail('DUPLICATE', loc + ['scope', 'resources'])
        if step['type'] == 'call':
            effects = document['bindings'].get(step['binding'], {}).get('effects')
            if effects in ('external', 'unknown') and not scope:
                fail('SCOPE', loc)
        if step['type'] != 'approval':
            continue
        action = steps.get(step['call'])
        if (action is None or action['type'] not in ('agent', 'call') or
                action.get('delivery') == 'steering'):
            fail('APPROVAL', loc)
            continue
        if 'scope' not in action:
            fail('SCOPE', ['flow', 'steps', step['call']])
        targets.setdefault(step['call'], []).append(name)
    for target, gates in targets.items():
        gate_set = set(gates)
        previous = {}
        bad = False
        for gate in gates:
            approved = steps[gate]['next']['approved']
            if len(approved) != 1 or approved[0] not in gate_set | {target}:
                bad = True
                continue
            destination = approved[0]
            if destination in previous:
                bad = True
            previous[destination] = gate
        first = gate_set - previous.keys()
        if len(first) != 1 or target not in previous:
            bad = True
        chain = []
        cursor = next(iter(first), None)
        while cursor in gate_set and cursor not in chain:
            chain.append(cursor)
            approved = steps[cursor]['next']['approved']
            cursor = approved[0] if len(approved) == 1 else None
        if cursor != target or set(chain) != gate_set:
            bad = True
        if not bad:
            for later in chain[1:] + [target]:
                if edges[later] != [(previous[later], 'approved')] or flow['entry'] == later:
                    bad = True
            # Refusal may begin a fresh attempt at the first gate, never bypass it.
            for index, gate in enumerate(chain):
                todo = steps[gate]['next']['denied'] + steps[gate].get('onError', [])
                seen = set()
                while todo:
                    current = todo.pop()
                    if current == chain[0] or current in seen or current not in steps:
                        continue
                    if current in chain[index + 1:] or current == target:
                        bad = True
                    seen.add(current)
                    todo.extend(t for rs in routes(steps[current]) + [steps[current].get('onError', [])] for t in rs)
        if bad:
            for gate in gates:
                fail('APPROVAL', ['flow', 'steps', gate])


def expand_document(document, fail):
    """Use tuple addresses internally; retain authored and invocation locations."""
    compositions = document.get('compositions', {})
    templates = []
    for name, body in compositions.items():
        base = ['compositions', name]
        parameters = body.get('agentParameters', [])
        if len(parameters) != len(set(parameters)) or len(body['outputs']) != len(set(body['outputs'])):
            fail('DUPLICATE', base)
        exported = set()
        synthetic = deepcopy(body['steps'])
        paths = {k: base + ['steps', k] for k in synthetic}
        paths[('entry',)] = base + ['entry']
        sentinels = {}
        for local, step in synthetic.items():
            loc = base + ['steps', local]
            if step['type'] == 'agent' and isinstance(step['agent'], dict):
                param = step['agent']['parameter']
                if param not in parameters:
                    fail('COMPOSITION', loc + ['agent'])
                step['agent'] = ('parameter', param)
            normal = routes(step)
            if any(len(rs) != 1 for rs in normal):
                fail('COMPOSITION', loc + ['next'])
            if len(step.get('onError', [])) > 1:
                fail('COMPOSITION', loc + ['onError'])
            for error, rs in [(False, rs) for rs in normal] + [(True, step.get('onError', []))]:
                for i, target in enumerate(rs):
                    if isinstance(target, dict):
                        output = target.get('output')
                        if output is not None:
                            exported.add(output)
                            if output not in body['outputs']:
                                fail('COMPOSITION', loc + ['next'])
                        sentinel = ('export', output if output is not None else 'error')
                        rs[i] = sentinel
                        sentinels[sentinel] = {'type': 'prepare', 'message': {}}
                        paths[sentinel] = loc
        if exported != set(body['outputs']):
            fail('COMPOSITION', base + ['outputs'])
        synthetic.update(sentinels)
        templates.append(({'entry': body['entry'], 'steps': synthetic}, paths,
                          [('parameter', p) for p in parameters]))

    authored = document.get('flow')
    if not authored:
        return None, {}, templates
    uses = authored['steps']
    entries = {}
    for name, step in uses.items():
        for field, code in (('call', 'APPROVAL'), ('steers', 'STEERING')):
            if field in step and uses.get(step[field], {}).get('type') == 'compose':
                fail(code, ['flow', 'steps', name, field])
        if step['type'] != 'compose':
            entries[name] = (name,)
            continue
        body = compositions.get(step['composition'])
        loc = ['flow', 'steps', name]
        if body is None:
            fail('REFERENCE', loc + ['composition'])
            entries[name] = (name,)
            continue
        entries[name] = (name, body['entry'])
        if set(step['agents']) != set(body.get('agentParameters', [])) or set(step['next']) != set(body['outputs']):
            fail('COMPOSITION', loc)
        for param, agent in step['agents'].items():
            if agent not in document['agents']:
                fail('REFERENCE', loc + ['agents', param])
        if any(other['type'] == 'join' and name in other['members'] for other in uses.values()):
            fail('COMPOSITION', loc)
    expanded, origins = {}, {}

    def outer(target):
        return entries.get(target, (target,))

    for name, step in uses.items():
        body = compositions.get(step.get('composition')) if step['type'] == 'compose' else None
        if step['type'] == 'compose' and body is None:
            continue
        records = body['steps'].items() if body else [(None, step)]
        for local, original in records:
            address = (name, local) if body else (name,)
            item = deepcopy(original)
            source = ['compositions', step['composition'], 'steps', local] if body else ['flow', 'steps', name]
            origins[address] = (source, ['flow', 'steps', name] if body else None)
            if body and item['type'] == 'agent' and isinstance(item['agent'], dict):
                item['agent'] = step['agents'].get(item['agent']['parameter'], '')
            def resolve(target):
                if not body:
                    return [outer(target)]
                if isinstance(target, str):
                    return [(name, target)]
                if 'output' in target:
                    return [outer(t) for t in step['next'].get(target['output'], [])]
                return [outer(t) for t in step.get('onError', [])]
            nxt = item.get('next', [])
            if isinstance(nxt, dict):
                item['next'] = {label: [t for target in rs for t in resolve(target)] for label, rs in nxt.items()}
            elif 'next' in item:
                item['next'] = [t for target in nxt for t in resolve(target)]
            if 'onError' in item:
                item['onError'] = [t for target in item['onError'] for t in resolve(target)]
            for field in ('call', 'steers', 'after'):
                if field in item:
                    item[field] = (name, item[field]) if body else outer(item[field])
            if 'members' in item:
                item['members'] = [outer(t) for t in item['members']]
            expanded[address] = item
    return {'entry': outer(authored['entry']), 'steps': expanded}, origins, templates


def projection(flow, origins):
    result = {'entry': list(flow['entry']), 'steps': []}
    for address, step in sorted(flow['steps'].items()):
        item = deepcopy(step)
        nxt = item.get('next')
        if isinstance(nxt, dict):
            item['next'] = {k: [list(t) for t in v] for k, v in nxt.items()}
        elif nxt is not None:
            item['next'] = [list(t) for t in nxt]
        if 'onError' in item:
            item['onError'] = [list(t) for t in item['onError']]
        for field in ('call', 'steers', 'after'):
            if field in item:
                item[field] = list(item[field])
        if 'members' in item:
            item['members'] = [list(t) for t in item['members']]
        from reader import pointer
        source, use = origins[address]
        result['steps'].append({'address': list(address), 'step': item,
                                'source': pointer(source), 'invocation': pointer(use) if use else None})
    return result


def selected_step(document, address):
    from reader import SCHEMA, shape
    parts = address if isinstance(address, list) else [address]
    if len(parts) not in (1, 2) or not all(shape(p, SCHEMA['$defs']['Name']) for p in parts):
        return None, ()
    flow, _, _ = expand_document(document, lambda *args: None)
    key = tuple(address) if isinstance(address, list) else (address,)
    return (flow or {}).get('steps', {}).get(key), key
