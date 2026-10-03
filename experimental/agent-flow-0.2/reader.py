"""Static reader for the bounded persistent-Agent candidate; never executes bindings."""
import json
from decimal import Decimal
import math
import re
import sys
from pathlib import Path

SCHEMA = json.loads(Path(__file__).with_name('schema.json').read_text())
MARKER = 'agsdl-exp-flow-0.2-c1'


def equal(a, b):
    """JSON equality, including numeric equality but never bool/number coercion."""
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (float, int, Decimal)) and isinstance(b, (float, int, Decimal)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(equal(v, b[k]) for k, v in a.items())
    if isinstance(a, list):
        return len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    return a == b


def shape(value, schema):
    """Evaluate only the schema vocabulary used by this bundled candidate."""
    if isinstance(schema, bool):
        return schema
    if '$ref' in schema:
        return shape(value, SCHEMA['$defs'][schema['$ref'].split('/')[-1]])
    if 'anyOf' in schema and not any(shape(value, s) for s in schema['anyOf']):
        return False
    if 'oneOf' in schema and sum(shape(value, s) for s in schema['oneOf']) != 1:
        return False
    if 'const' in schema and not equal(value, schema['const']):
        return False
    if 'enum' in schema and not any(equal(value, x) for x in schema['enum']):
        return False
    kind = schema.get('type')
    kinds = {'object': isinstance(value, dict), 'array': isinstance(value, list),
             'string': isinstance(value, str), 'boolean': isinstance(value, bool),
             'integer': (type(value) is int or isinstance(value, Decimal) and value == value.to_integral_value() or type(value) is float and value.is_integer())}
    if kind is not None and not kinds[kind]:
        return False
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            return False
        if 'pattern' in schema and re.search(schema['pattern'], value) is None:
            return False
    if type(value) in (int, float, Decimal) and value < schema.get('minimum', -math.inf):
        return False
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            return False
        prefix = schema.get('prefixItems', [])
        return all(shape(x, prefix[i] if i < len(prefix) else schema.get('items', {}))
                   for i, x in enumerate(value))
    if isinstance(value, dict):
        if len(value) < schema.get('minProperties', 0):
            return False
        if not all(k in value for k in schema.get('required', [])):
            return False
        props = schema.get('properties', {})
        return all(shape(k, schema.get('propertyNames', {})) and
                   shape(v, props.get(k, schema.get('additionalProperties', {})))
                   for k, v in value.items())
    return True


def pointer(parts):
    return ''.join('/' + str(p).replace('~', '~0').replace('/', '~1') for p in parts)


def validate(document):
    findings = []

    def fail(code, location):
        item = {'code': code, 'path': pointer(location)}
        if item not in findings:
            findings.append(item)

    if not shape(document, SCHEMA):
        fail('SHAPE', [])
    else:
        bindings = document['bindings']
        configs = document['configurations']
        agents = document['agents']
        skills = document.get('skills', {})
        content = document.get('content', {})

        def reference(catalog, name, location):
            if name not in catalog:
                fail('REFERENCE', location)

        def sources(container, location):
            for field in ('prompt', 'resources'):
                values = container.get(field, [] if field == 'prompt' else {})
                iterator = enumerate(values) if isinstance(values, list) else values.items()
                for k, source in iterator:
                    if 'ref' in source:
                        reference(content, source['ref'], location + [field, k, 'ref'])

        for name, config in configs.items():
            reference(bindings, config['engine'], ['configurations', name, 'engine'])
            for tool, binding in config.get('tools', {}).items():
                reference(bindings, binding, ['configurations', name, 'tools', tool])
        for name, skill in skills.items():
            sources(skill, ['skills', name])
        for name, agent in agents.items():
            loc = ['agents', name]
            selection = agent['configuration']
            if isinstance(selection, str):
                reference(configs, selection, loc + ['configuration'])
            else:
                for choice, config in selection['cases'].items():
                    reference(configs, config, loc + ['configuration', 'cases', choice])
            sources(agent, loc)
            selected = agent.get('skills', [])
            if len(selected) != len(set(selected)):
                fail('DUPLICATE', loc + ['skills'])
            resource_names = set(agent.get('resources', {}))
            for skill in selected:
                reference(skills, skill, loc + ['skills'])
                for resource in skills.get(skill, {}).get('resources', {}):
                    if resource in resource_names:
                        fail('RESOURCE_COLLISION', loc + ['skills'])
                    resource_names.add(resource)
            interface = agent.get('interface', {})
            allowed = interface.get('outputMediaTypes')
            for result, constraint in interface.get('results', {}).items():
                if allowed is not None and not set(constraint['mediaTypes']) <= set(allowed):
                    fail('OUTPUT_FORMAT', loc + ['interface', 'results', result])

        flow = document.get('flow')
        if flow:
            steps = flow['steps']
            reference(steps, flow['entry'], ['flow', 'entry'])

            def routes(step):
                nxt = step.get('next', [])
                return list(nxt.values()) if isinstance(nxt, dict) else [nxt]

            incoming = {k: set() for k in steps}
            for name, step in steps.items():
                loc = ['flow', 'steps', name]
                for targets in routes(step) + [step.get('onError', [])]:
                    if len(targets) != len(set(targets)):
                        fail('DUPLICATE', loc)
                    for target in targets:
                        reference(steps, target, loc)
                        if target in incoming:
                            incoming[target].add(name)
                if step['type'] == 'agent':
                    reference(agents, step['agent'], loc + ['agent'])
                    steering = step.get('delivery', 'queue') == 'steering'
                    if steering:
                        target = steps.get(step.get('steers'))
                        grouped = {member for item in steps.values() if item['type'] == 'join'
                                   for member in item['members']}
                        if (target is None or target['type'] != 'agent' or
                            target.get('delivery', 'queue') != 'queue' or
                            target.get('agent') != step['agent'] or
                            name == flow['entry'] or 'next' in step or 'decision' in step or
                            name in grouped):
                            fail('STEERING', loc)
                    elif 'steers' in step:
                        fail('STEERING', loc + ['steers'])
                    decision = step.get('decision')
                    if decision:
                        reference(bindings, decision['binding'], loc + ['decision', 'binding'])
                        choices = decision['choices']
                        if len(choices) != len(set(choices)):
                            fail('DUPLICATE', loc + ['decision', 'choices'])
                        if not isinstance(step.get('next'), dict) or set(step['next']) != set(choices):
                            fail('ROUTES', loc + ['next'])
                    elif isinstance(step.get('next'), dict):
                        fail('ROUTES', loc + ['next'])
                elif step['type'] == 'call':
                    reference(bindings, step['binding'], loc + ['binding'])
                elif step['type'] == 'prepare':
                    sources(step['message'], loc + ['message'])

            for name, step in steps.items():
                if step['type'] != 'join':
                    continue
                loc = ['flow', 'steps', name]
                mode = step.get('mode', 'all')
                if mode == 'first' and 'accept' not in step:
                    fail('JOIN_POLICY', loc)
                if mode == 'all' and ('accept' in step or 'remaining' in step):
                    fail('JOIN_POLICY', loc)
                members = step['members']
                anchor = steps.get(step['after'])
                # c1 deliberately implements the direct fork-and-join shape only.
                if (len(set(members)) != len(members) or name == flow['entry'] or
                    step['after'] in members or name in members or
                    anchor is None or not isinstance(anchor.get('next'), list) or
                    set(anchor['next']) != set(members) or
                    any(member in anchor.get('onError', []) for member in members) or
                    incoming[name] != set(members)):
                    fail('JOIN_GROUP', loc)
                for member in members:
                    source = steps.get(member)
                    if (source is None or source['type'] == 'join' or
                        incoming.get(member) != {step['after']} or
                        any(targets != [name] for targets in routes(source)) or
                        source.get('onError') or member == flow['entry']):
                        fail('JOIN_GROUP', loc)

            reachable = set()
            todo = [flow['entry']]
            while todo:
                name = todo.pop()
                if name in reachable or name not in steps:
                    continue
                reachable.add(name)
                step = steps[name]
                for targets in routes(step) + [step.get('onError', [])]:
                    todo.extend(targets)
            for name in steps.keys() - reachable:
                fail('UNREACHABLE', ['flow', 'steps', name])

    return {'contract': MARKER, 'valid': not findings,
            'scope': 'document-shape-and-declared-references',
            'executionSupport': 'not-assessed',
            'findings': sorted(findings, key=lambda x: (x['path'], x['code']))}


def loads(raw):
    def pairs(entries):
        result = {}
        for key, value in entries:
            if key in result:
                raise ValueError('Duplicate object member')
            result[key] = value
        return result

    def constant(value):
        raise ValueError('Non-JSON numeric constant')

    def check(value):
        if isinstance(value, str):
            value.encode('utf-8')  # Reject unpaired surrogate code points.
        elif isinstance(value, (float, Decimal)) and not (value.is_finite() if isinstance(value, Decimal) else math.isfinite(value)):
            raise ValueError('Number exceeds supported finite representation')
        elif isinstance(value, dict):
            for key, item in value.items():
                check(key)
                check(item)
        elif isinstance(value, list):
            for item in value:
                check(item)

    value = json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant, parse_float=Decimal)
    check(value)
    return value


def main():
    if len(sys.argv) != 2:
        print('Usage: python3 reader.py DOCUMENT.json', file=sys.stderr)
        return 2
    try:
        result = validate(loads(Path(sys.argv[1]).read_bytes()))
    except (ValueError, UnicodeError, RecursionError, ArithmeticError):
        print(json.dumps({'contract': MARKER, 'valid': False, 'scope': 'parse',
                          'executionSupport': 'not-assessed',
                          'findings': [{'code': 'PARSE', 'path': ''}]}))
        return 1
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
