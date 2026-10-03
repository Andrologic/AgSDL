"""Explicit URI origin handling. This module never opens a URI or a file."""
from copy import deepcopy
import ipaddress
import re

_PARTS = re.compile(r'^(?:([A-Za-z][A-Za-z0-9+.-]*):)?(?://([^/?#]*))?([^?#]*)(?:\?([^#]*))?(?:#(.*))?$', re.ASCII)
_ATOM = r"(?:[A-Za-z0-9._~!$&'()*+,;=:@-]|%[0-9A-Fa-f]{2})"


def parts(uri):
    if not isinstance(uri, str) or not uri.isascii():
        raise ValueError('URI requires ASCII syntax.')
    match = _PARTS.fullmatch(uri)
    if not match:
        raise ValueError('Invalid URI syntax.')
    scheme, authority, path, query, fragment = match.groups()
    if not re.fullmatch('(?:' + _ATOM + '|/)*', path):
        raise ValueError('Invalid URI path.')
    if any(v is not None and not re.fullmatch('(?:' + _ATOM + '|[/?])*', v) for v in (query, fragment)):
        raise ValueError('Invalid URI query or fragment.')
    if scheme is None and authority is None and ':' in path.split('/')[0]:
        raise ValueError('Relative URI first segment cannot contain a colon.')
    if authority is not None:
        user, sep, hostport = authority.rpartition('@')
        if sep and (not re.fullmatch(r"(?:[A-Za-z0-9._~!$&'()*+,;=:-]|%[0-9A-Fa-f]{2})*", user)):
            raise ValueError('Invalid URI user info.')
        hostport = hostport if sep else authority
        if hostport.startswith('['):
            closing = hostport.find(']')
            if closing == -1:
                raise ValueError('Invalid URI IP literal.')
            host, port = hostport[1:closing], hostport[closing + 1:]
            if not re.fullmatch(r"[vV][0-9A-Fa-f]+\.[A-Za-z0-9._~!$&'()*+,;=:-]+", host):
                if not re.fullmatch('[0-9A-Fa-f:.]+', host):
                    raise ValueError('Invalid IPv6 literal.')
                ipaddress.IPv6Address(host)
            if port and not re.fullmatch(r':[0-9]*', port):
                raise ValueError('Invalid URI port.')
        else:
            host, sep, port = hostport.partition(':')
            if not re.fullmatch(r"(?:[A-Za-z0-9._~!$&'()*+,;=-]|%[0-9A-Fa-f]{2})*", host) or sep and not re.fullmatch('[0-9]*', port):
                raise ValueError('Invalid URI host or port.')
    return scheme, authority, path, query, fragment


def valid_base(base):
    scheme, authority, path, _, fragment = parts(base)
    if scheme is None or fragment is not None or not (authority is not None or path.startswith('/')):
        raise ValueError('Base must be absolute and hierarchical, without fragment.')


def remove_dots(path):
    output = ''
    while path:
        if path.startswith('../'):
            path = path[3:]
        elif path.startswith('./'):
            path = path[2:]
        elif path.startswith('/./') or path == '/.':
            path = '/' + path[3:]
        elif path.startswith('/../') or path == '/..':
            path = '/' + path[4:]
            output = output.rsplit('/', 1)[0] if '/' in output else ''
        elif path in ('.', '..'):
            path = ''
        else:
            end = path.find('/', 1 if path.startswith('/') else 0)
            if end == -1:
                output += path
                path = ''
            else:
                output += path[:end]
                path = path[end:]
    return output


def resolve_uri(uri, base=None):
    s, a, p, q, f = parts(uri)
    if s is not None:
        return (s + ':' + ('//' + a if a is not None else '') + remove_dots(p) +
                ('?' + q if q is not None else '') + ('#' + f if f is not None else ''))
    if base is None:
        return None
    valid_base(base)
    bs, ba, bp, bq, _ = parts(base)
    if a is not None:
        p = remove_dots(p)
    else:
        a = ba
        if not p:
            p, q = bp, bq if q is None else q
        else:
            if not p.startswith('/'):
                p = ('/' if ba is not None and not bp else bp.rsplit('/', 1)[0] + '/' if '/' in bp else '') + p
            p = remove_dots(p)
    return bs + ':' + ('//' + a if a is not None else '') + p + ('?' + q if q is not None else '') + ('#' + f if f is not None else '')


def normalize_source(source, base, path, observations):
    result = deepcopy(source)
    if 'uri' not in source:
        return result
    resolved = resolve_uri(source['uri'], base)
    observations.append({'path': path, 'baseUri': base, 'uri': source['uri'],
                         'resolved': resolved, 'status': 'resolved' if resolved is not None else 'unresolved'})
    if resolved is not None:
        result['uri'] = resolved
    return result


def normalize_message(message, document):
    """Expand catalog references using their document origin, never the receiver."""
    from reader import pointer
    if 'baseUri' in message:
        valid_base(message['baseUri'])
    result, observations = {}, []
    for field in ('prompt', 'resources'):
        if field not in message:
            continue
        original = message[field]
        values = [] if field == 'prompt' else {}
        for key, source in (enumerate(original) if field == 'prompt' else original.items()):
            if 'ref' in source:
                path = pointer(['content', source['ref']])
                value = document.get('content', {})[source['ref']]
                base = document.get('baseUri')
            else:
                path, value, base = pointer([field, key]), source, message.get('baseUri')
            value = normalize_source(value, base, path, observations)
            if isinstance(values, list):
                values.append(value)
            else:
                values[key] = value
        result[field] = values
    return result, observations


def normalize_completion(completion):
    if 'baseUri' in completion:
        valid_base(completion['baseUri'])
    from reader import pointer
    result, observations = deepcopy(completion), []
    result.pop('baseUri', None)
    if 'results' in completion:
        result['results'] = {k: normalize_source(v, completion.get('baseUri'), pointer(['results', k]), observations)
                             for k, v in completion['results'].items()}
    return result, observations


def prepare_message(document, step, current, source_bases=None):
    """Inspect deterministic preparation from supplied data, with explicit source provenance.

    source_bases maps JSON Pointers in current input to their original bases;
    a missing entry means unresolved origin, never the document's base.
    """
    from reader import SCHEMA, pointer, shape
    from check_delivery import operand_value
    message = deepcopy(step['message'])
    observations = []
    # Authored content originates in the document, before selecting dynamic Sources.
    message['baseUri'] = document['baseUri'] if 'baseUri' in document else None
    if message['baseUri'] is None:
        message.pop('baseUri')
    dynamic = {}
    for key, resource in list(message.get('resources', {}).items()):
        if 'select' in resource:
            dynamic[key] = {'value': operand_value(resource['select'], current)}
            if 'mediaType' in resource:
                dynamic[key]['mediaType'] = resource['mediaType']
            del message['resources'][key]
        elif 'source' in resource:
            operand = resource['source']
            source = operand_value(operand, current)
            if not shape(source, SCHEMA['$defs']['Source']):
                raise ValueError('Source selection requires a Source.')
            path = pointer(operand['path']) if 'path' in operand else ''
            base = (source_bases or {}).get(path) if 'path' in operand else document.get('baseUri')
            dynamic[key] = normalize_source(source, base, path, observations)
            del message['resources'][key]
    normalized, authored = normalize_message(message, document)
    if dynamic:
        normalized.setdefault('resources', {}).update(dynamic)
    return normalized, authored + observations


def agent_content(document, agent_name):
    """Expand initialization content only, without selecting or starting an Engine."""
    agent = document['agents'][agent_name]
    message = {'prompt': [], 'resources': {}}
    if 'baseUri' in document:
        message['baseUri'] = document['baseUri']
    for container in [document.get('skills', {})[name] for name in agent.get('skills', [])] + [agent]:
        message['prompt'].extend(deepcopy(container.get('prompt', [])))
        for name, source in container.get('resources', {}).items():
            if name in message['resources']:
                raise ValueError('Resource collision during skill expansion.')
            message['resources'][name] = deepcopy(source)
    return normalize_message(message, document)
