#!/usr/bin/env python3
"""Render the top-level flow of a valid 0.2.0 document as a Mermaid flowchart.

This is a static, non-normative view of declared connections. It does not
expand compositions, evaluate predicates or describe runtime ordering.
"""
import sys
from pathlib import Path

from reader import loads, validate

SHAPES = {
    'agent': ('["', '"]'),
    'call': ('[["', '"]]'),
    'condition': ('{"', '"}'),
    'prepare': ('[/"', '"/]'),
    'join': ('(("', '"))'),
    'approval': ('{{"', '"}}'),
    'compose': ('[["', '"]]'),
}


def label(text):
    return str(text).replace('&', '#amp;').replace('"', '#quot;').replace('<', '#lt;').replace('>', '#gt;')


def describe(name, step):
    kind = step['type']
    if kind == 'agent':
        detail = f'agent: {step["agent"]}'
    elif kind in ('call', 'approval'):
        detail = f'{kind}: {step["binding"]}'
    elif kind == 'compose':
        detail = f'compose: {step["composition"]}'
    else:
        detail = kind
    return label(name) + '<br/>' + label(detail)


def render(document):
    flow = document.get('flow')
    if flow is None:
        return 'flowchart TD\n  empty["No flow declared"]\n'
    names = list(flow['steps'])
    ids = {name: f's{i}' for i, name in enumerate(names)}
    lines = ['flowchart TD', '  start(("entry"))']
    for name in names:
        step = flow['steps'][name]
        left, right = SHAPES[step['type']]
        lines.append(f'  {ids[name]}{left}{describe(name, step)}{right}')
    lines.append(f'  start --> {ids[flow["entry"]]}')
    for name in names:
        step = flow['steps'][name]
        routes = step.get('next', [])
        if isinstance(routes, dict):
            for outcome, targets in routes.items():
                for target in targets:
                    lines.append(f'  {ids[name]} -- "{label(outcome)}" --> {ids[target]}')
        else:
            for target in routes:
                lines.append(f'  {ids[name]} --> {ids[target]}')
        for target in step.get('onError', []):
            lines.append(f'  {ids[name]} -. "error" .-> {ids[target]}')
        if 'steers' in step:
            lines.append(f'  {ids[name]} -. "steers" .-> {ids[step["steers"]]}')
        if step['type'] == 'approval':
            lines.append(f'  {ids[name]} -. "protects" .-> {ids[step["call"]]}')
    return '\n'.join(lines) + '\n'


def main():
    if len(sys.argv) != 2:
        print('Usage: python3 render_mermaid.py DOCUMENT.json', file=sys.stderr)
        return 2
    try:
        document = loads(Path(sys.argv[1]).read_bytes())
    except OSError as error:
        print(str(error), file=sys.stderr)
        return 2
    except (ValueError, UnicodeError, RecursionError, ArithmeticError):
        print('The document cannot be parsed; run reader.py for its report.', file=sys.stderr)
        return 1
    if not validate(document)['valid']:
        print('The document is invalid; run reader.py for its report.', file=sys.stderr)
        return 1
    sys.stdout.write(render(document))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
