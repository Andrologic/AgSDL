"""Structural report boundaries; no reader imports or semantic graph checks."""
from copy import deepcopy
from decimal import Decimal
import json
from pathlib import Path
import re

SCHEMA = json.loads((Path(__file__).resolve().parents[1] / 'schema.json').read_text())
NAME = re.compile(r'[A-Za-z][A-Za-z0-9_-]*', re.ASCII)
POINTER = re.compile(r'(?:/(?:[^~]|~[01])*)*')


def name(value):
    return isinstance(value, str) and NAME.fullmatch(value) is not None


def pointer(value):
    return isinstance(value, str) and POINTER.fullmatch(value) is not None


def address(value):
    return isinstance(value, list) and len(value) in (1, 2) and all(map(name, value))


def _equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, Decimal)) and isinstance(b, (int, Decimal)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(_equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(_equal(a[k], b[k]) for k in a)
    return a == b


def shape(value, schema):
    """Check only the schema vocabulary used by embedded declaration records."""
    if isinstance(schema, bool):
        return schema
    if '$ref' in schema:
        return shape(value, SCHEMA['$defs'][schema['$ref'].split('/')[-1]])
    if 'oneOf' in schema and sum(shape(value, s) for s in schema['oneOf']) != 1:
        return False
    if 'anyOf' in schema and not any(shape(value, s) for s in schema['anyOf']):
        return False
    numeric = isinstance(value, (int, Decimal)) and not isinstance(value, bool)
    types = {'null': value is None, 'boolean': type(value) is bool,
             'number': numeric, 'integer': numeric and (not isinstance(value, Decimal) or value == value.to_integral_value()),
             'string': isinstance(value, str), 'array': isinstance(value, list),
             'object': isinstance(value, dict)}
    if 'type' in schema and not types[schema['type']]:
        return False
    if 'const' in schema and not _equal(value, schema['const']):
        return False
    if 'enum' in schema and not any(_equal(value, x) for x in schema['enum']):
        return False
    if numeric and 'minimum' in schema and value < schema['minimum']:
        return False
    if isinstance(value, str):
        if len(value) < schema.get('minLength', 0):
            return False
        if 'pattern' in schema and re.search(schema['pattern'], value) is None:
            return False
    if isinstance(value, list):
        if len(value) < schema.get('minItems', 0):
            return False
        prefix = schema.get('prefixItems', [])
        return all(shape(v, prefix[i] if i < len(prefix) else schema.get('items', True))
                   for i, v in enumerate(value))
    if isinstance(value, dict):
        if len(value) < schema.get('minProperties', 0) or any(k not in value for k in schema.get('required', [])):
            return False
        props = schema.get('properties', {})
        return all(shape(k, schema.get('propertyNames', True)) and
                   shape(v, props[k] if k in props else schema.get('additionalProperties', True))
                   for k, v in value.items())
    return True


def requirement(value):
    return shape(value, SCHEMA['$defs']['Requirement'])


def expanded_step(value, invalid_substitution=False):
    """Adapt Step's reference slots to address arrays, leaving literal data alone.

    Expansion can empty an authored output route, including an approval route.
    An invalid body Agent substitution may be the documented empty string.
    Neither allowance changes the input document schema.
    """
    if not isinstance(value, dict):
        return False
    kind = value.get('type')
    alternatives = SCHEMA['$defs']['Step']['oneOf']
    authored = next((s for s in alternatives if s['properties']['type']['const'] == kind), None)
    if authored is None or kind == 'compose':
        return False
    translated = deepcopy(authored)
    address_schema = {'type': 'array', 'items': SCHEMA['$defs']['Name'], 'minItems': 1}
    # Length is additionally checked below; the bundled vocabulary has no maxItems.
    properties = translated['properties']
    for field in ('call', 'after', 'steers'):
        if field in properties:
            properties[field] = address_schema
    if 'members' in properties:
        properties['members']['items'] = address_schema
    if 'onError' in properties:
        properties['onError']['items'] = address_schema

    def routes(s):
        if 'oneOf' in s:
            for alternative in s['oneOf']:
                routes(alternative)
        elif s.get('type') == 'array':
            s['items'] = address_schema
            if invalid_substitution:
                s['minItems'] = 0
        elif s.get('type') == 'object':
            for child in s.get('properties', {}).values():
                routes(child)
            if isinstance(s.get('additionalProperties'), dict):
                routes(s['additionalProperties'])
    if 'next' in properties:
        routes(properties['next'])
    if kind == 'agent' and invalid_substitution:
        properties['agent'] = {'oneOf': [SCHEMA['$defs']['Name'], {'const': ''}]}
    if not shape(value, translated):
        return False
    targets = [value[f] for f in ('call', 'after', 'steers') if f in value]
    targets += value.get('members', []) + value.get('onError', [])
    next_routes = value.get('next', [])
    targets += (next_routes if isinstance(next_routes, list) else
                [target for route in next_routes.values() for target in route])
    return all(address(target) for target in targets)
