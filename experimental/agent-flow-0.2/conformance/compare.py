#!/usr/bin/env python3
"""Run contract-authored oracles and compare complete declaration reports."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from cases import ROOT, cases


def decode(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            if k in out:
                raise ValueError('duplicate report member')
            out[k] = v
        return out
    value = json.loads(raw, parse_float=Decimal, parse_int=Decimal, object_pairs_hook=pairs,
                       parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))
    def unicode_scalar(item):
        if isinstance(item, str) and any(0xD800 <= ord(c) <= 0xDFFF for c in item):
            raise ValueError('unpaired report surrogate')
        if isinstance(item, list):
            for child in item:
                unicode_scalar(child)
        if isinstance(item, dict):
            for key, child in item.items():
                unicode_scalar(key)
                unicode_scalar(child)
    unicode_scalar(value)
    return value


def exact(value):
    """Typed, scalar-order comparison key; object order is not semantic."""
    if value is None:
        return ('null',)
    if isinstance(value, bool):
        return ('boolean', value)
    if isinstance(value, (int, Decimal)):
        return ('number', Decimal(value))
    if isinstance(value, str):
        return ('string', value)
    if isinstance(value, list):
        return ('array', tuple(map(exact, value)))
    return ('object', tuple((k, exact(v)) for k, v in sorted(value.items())))


def canonical(report):
    out = dict(report)
    # Human diagnostic text is implementation prose. No semantic field is removed.
    out['findings'] = [dict((k, v) for k, v in f.items() if k != 'message') for f in out['findings']]
    # Report observation arrays are unordered multisets. Duplicate observations
    # remain visible. Arrays inside declarations, routes and requirements retain order.
    for field in ('findings', 'sources', 'support', 'coreNeeds', 'unassessed'):
        if field in out:
            out[field] = sorted(out[field], key=exact)
    if 'expandedFlow' in out:
        out['expandedFlow'] = dict(out['expandedFlow'])
        out['expandedFlow']['steps'] = sorted(out['expandedFlow']['steps'], key=lambda x: exact(x['address']))
    return exact(out)


def observe(report, pointer):
    obj = report
    for token in pointer.split('/')[1:]:
        token = token.replace('~1', '/').replace('~0', '~')
        obj = obj[int(token)] if isinstance(obj, list) else obj[token]
    return obj


def validate(report, case):
    errors = []
    basic = {'contract', 'valid', 'scope', 'executionSupport', 'findings'}
    extras = {'sources', 'support', 'coreNeeds', 'unassessed', 'expandedFlow'}
    if not isinstance(report, dict) or not basic <= report.keys() or report.keys() - basic - extras:
        return ['invalid report fields']
    for field in extras - {'expandedFlow'}:
        if field in report and not isinstance(report[field], list):
            errors.append(f'invalid {field} array')
    if report['contract'] != 'agsdl-exp-flow-0.2-c1' or report['scope'] not in ('document-shape-and-declared-references', 'parse') or report['executionSupport'] != 'not-assessed':
        errors.append('incorrect report identity or scope')
    if type(report['valid']) is not bool or not isinstance(report['findings'], list):
        return errors + ['invalid verdict or findings']
    for f in report['findings']:
        if not isinstance(f, dict) or not {'code', 'path'} <= f.keys() or f.keys() - {'code', 'path', 'message', 'invocation'}:
            errors.append('invalid finding fields')
        elif any(not isinstance(f[k], str) for k in f):
            errors.append('invalid finding primitive')
    if errors:
        return errors
    errors.extend(observation_errors(report))
    actual = sorted(set(f['code'] for f in report['findings']))
    expected_scope = 'parse' if 'PARSE' in actual else 'document-shape-and-declared-references'
    if report['scope'] != expected_scope:
        errors.append('scope inconsistent with parsing outcome')
    if actual != case['codes']:
        errors.append(f'codes {actual!r} != {case["codes"]!r}')
    if report['valid'] != (not case['codes']):
        errors.append('validity contradicts oracle')
    if not set(actual) & {'PARSE', 'SHAPE'} and not (extras - {'expandedFlow'}) <= report.keys():
        errors.append('missing declaration observations')
    for pointer, expected in case['assertions'].items():
        try:
            if exact(observe(report, pointer)) != exact(expected):
                errors.append(f'oracle mismatch at {pointer}')
        except (KeyError, IndexError, TypeError, ValueError):
            errors.append(f'missing oracle observation {pointer}')
    return errors


def observation_errors(report):
    errors = []
    def record(value, required, optional=()):
        return isinstance(value, dict) and set(required) <= value.keys() and not value.keys() - set(required) - set(optional)
    def strings(value, fields):
        return all(isinstance(value.get(k), str) for k in fields)
    for value in report.get('sources', []):
        if not record(value, ('path','baseUri','uri','resolved','status')) or not strings(value, ('path','uri','status')) or any(value[k] is not None and not isinstance(value[k], str) for k in ('baseUri','resolved')) or value['status'] not in ('resolved','unresolved') or (value['resolved'] is None) != (value['status'] == 'unresolved'):
            errors.append('invalid source observation')
    statuses = ('not-requested','unknown','incompatible','declared-supported')
    for value in report.get('support', []):
        if not record(value, ('path','status','requirements'), ('configuration','selection')) or not strings(value, ('path','status')) or value['status'] not in statuses or not isinstance(value['requirements'], list):
            errors.append('invalid support observation')
            continue
        if ('configuration' in value) != ('selection' in value) or 'selection' in value and (not isinstance(value['configuration'], str) or value['selection'] not in ('fixed','conditional')):
            errors.append('invalid support selection')
        for req in value['requirements']:
            if not record(req, ('requirement','status')) or req['status'] not in statuses[1:] or not isinstance(req['requirement'], dict):
                errors.append('invalid requirement assessment')
    for value in report.get('coreNeeds', []):
        if not record(value, ('path','need','status')) or not strings(value, ('path','need')) or value['status'] != 'unassessed':
            errors.append('invalid core need')
    if any(not isinstance(x, str) for x in report.get('unassessed', [])):
        errors.append('invalid unassessed location')
    def address(value):
        return isinstance(value, list) and len(value) in (1, 2) and all(isinstance(x, str) and x for x in value)
    if 'expandedFlow' in report:
        flow = report['expandedFlow']
        if not record(flow, ('entry','steps')) or not address(flow.get('entry')) or not isinstance(flow.get('steps'), list):
            errors.append('invalid expanded flow')
        else:
            seen = []
            for step in flow['steps']:
                if not record(step, ('address','step','source','invocation')) or not address(step.get('address')) or not isinstance(step.get('step'), dict) or not isinstance(step.get('source'), str) or step.get('invocation') is not None and not isinstance(step.get('invocation'), str):
                    errors.append('invalid expanded step')
                elif step['address'] in seen:
                    errors.append('duplicate expanded address')
                else:
                    seen.append(step['address'])
    return errors


def agree(reports):
    try:
        return len(reports) == 2 and canonical(reports['python']) == canonical(reports['javascript'])
    except (KeyError, TypeError, ValueError, AttributeError, RecursionError):
        return False


def run(directory):
    directory.mkdir(parents=True, exist_ok=True)
    if any(directory.iterdir()):
        raise ValueError('reports directory must be empty')
    summary = {'scope': 'candidate-document-declaration-semantics', 'executionSupport': 'not-assessed', 'cases': [], 'failures': 0, 'mismatches': 0}
    repo = ROOT.parents[1]
    summary['sourceHashes'] = {str(p.relative_to(repo)): hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT / 'schema.json', Path(__file__), Path(__file__).with_name('cases.py'), *sorted((repo / 'spec/0.2').glob('*.md')), *sorted(ROOT.glob('*.py')), *sorted((ROOT / 'javascript').glob('*.mjs'))]}
    commands = {'python': [sys.executable, str(ROOT / 'reader.py')],
                'javascript': ['node', str(ROOT / 'javascript/reader.mjs')]}
    for case in cases():
        name = case['name']
        input_path = directory / (name + '.input.json')
        input_path.write_bytes(case['bytes'])
        entry = {'name': name, 'sha256': hashlib.sha256(case['bytes']).hexdigest(), 'source': case['source'], 'expectedCodes': case['codes'], 'assertions': case['assertions'], 'readers': {}}
        reports = {}
        for label, command in commands.items():
            try:
                process = subprocess.run(command + [str(input_path)], capture_output=True, timeout=20)
                (directory / f'{name}.{label}.stdout.json').write_bytes(process.stdout)
                (directory / f'{name}.{label}.stderr.txt').write_bytes(process.stderr)
                report = decode(process.stdout)
                errors = validate(report, case)
                if process.returncode != (0 if report.get('valid') is True else 1):
                    errors.append(f'incorrect exit {process.returncode}')
                reports[label] = report
            except (OSError, ValueError, TypeError, KeyError, AttributeError, RecursionError, subprocess.TimeoutExpired) as e:
                errors = [str(e)]
            entry['readers'][label] = errors
            if errors:
                summary['failures'] += 1
        entry['agreement'] = agree(reports)
        if not entry['agreement']:
            summary['mismatches'] += 1
        summary['cases'].append(entry)
    summary['count'] = len(summary['cases'])
    (directory / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps({k: v for k, v in summary.items() if k not in ('cases', 'sourceHashes')}))
    return bool(summary['failures'] or summary['mismatches'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reports', required=True, type=Path)
    args = parser.parse_args()
    try:
        sys.exit(run(args.reports))
    except (OSError, ValueError) as e:
        parser.exit(2, str(e) + '\n')
