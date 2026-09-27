#!/usr/bin/env python3
"""Bounded c2 comparison. No reader code supplies expectations or validation."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EDITION = 'agsdl-exp-0016-c2'
SUBJECTS = dict(syntax='', core='', flow='/graphs', configuration='/configurations',
                compatibility='/selected', external='/extensions')
CODES = {
    'syntax': {'SYNTAX'},
    'core': {'SHAPE', 'ID', 'REF', 'SLOT-ID', 'UNIQUE'},
    'flow': {'SHAPE', 'REF', 'OPERATION', 'STEP-ID', 'PATH', 'DATA', 'ACTOR',
             'APPROVAL', 'APPROVAL-DATA', 'UNIQUE'},
    'configuration': {'SHAPE', 'REF', 'SELECTION', 'ASSIGN', 'CONTENT', 'TOOLS', 'UNIQUE'},
    'compatibility': {'ENGINE', 'TOOL'},
    'external': {'SHAPE', 'UNIQUE', 'REQUIRED'},
}
READERS = {
    'python': [sys.executable, str(HERE / 'readers/python/cli.py')],
    'javascript': ['node', str(HERE / 'readers/javascript/cli.mjs')],
}
READER_COMMITS = {'python': '04bd276dd75470a05761496b5dc45932e3437873',
                  'javascript': 'ffc81611a76284dd3fcce05496de3671dc04a197'}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(data):
    def pairs(items):
        obj = {}
        for key, value in items:
            require(key not in obj, 'duplicate JSON member: ' + key)
            obj[key] = value
        return obj

    def bad_constant(value):
        raise ValueError('non-JSON constant: ' + value)

    def scalar_strings(value):
        if isinstance(value, str):
            require(not any(0xd800 <= ord(c) <= 0xdfff for c in value),
                    'non-scalar Unicode string')
        elif isinstance(value, dict):
            for key, child in value.items():
                scalar_strings(key)
                scalar_strings(child)
        elif isinstance(value, list):
            for child in value:
                scalar_strings(child)

    value = json.loads(data.decode('utf-8'), object_pairs_hook=pairs,
                       parse_constant=bad_constant)
    scalar_strings(value)
    return value


def record(value, fields, optional=()):
    require(isinstance(value, dict), 'expected object')
    require(set(fields) <= value.keys() <= set(fields) | set(optional),
            'missing or extra fields: ' + repr(list(value)))


def text(value):
    require(isinstance(value, str) and bool(value), 'expected nonempty text')


def member(value, choices):
    require(isinstance(value, str) and value in choices, 'invalid enum: ' + repr(value))


def pointer(value):
    require(isinstance(value, str) and re.fullmatch(r'(?:/(?:[^~]|~[01])*)*', value),
            'invalid JSON Pointer: ' + repr(value))


def aggregate(presence, diagnostics, gaps):
    contributions = {d['outcome'] for d in diagnostics}
    contributions.update('unsupported' if 'unsupported' in g['causes'] else 'inconclusive'
                         for g in gaps)
    for outcome in ('fail', 'unsupported', 'inconclusive'):
        if outcome in contributions:
            return outcome
    return 'not-applicable' if presence == 'absent' else 'pass'


def normalize(data, sha256):
    """Validate the closed report before removing only processor and messages."""
    report = strict_json(data)
    record(report, {'edition', 'processor', 'operation', 'input', 'results'})
    require(report['edition'] == EDITION and report['operation'] == 'validate',
            'wrong edition or operation')
    record(report['processor'], {'identity', 'version'})
    for value in report['processor'].values():
        text(value)
    record(report['input'], {'id', 'sha256'})
    require(report['input']['id'] == 'primary', 'wrong input id')
    value = report['input']['sha256']
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value)
            and value == sha256, 'wrong input hash')
    results = report['results']
    require(isinstance(results, list) and len(results) == 6, 'expected six results')
    seen = set()
    for result in results:
        record(result, {'unit', 'phase', 'subject', 'presence', 'outcome',
                        'diagnostics', 'incomplete'})
        unit = result['unit']
        member(unit, SUBJECTS)
        require(unit not in seen, 'duplicate unit')
        seen.add(unit)
        require(result['phase'] == 'local' and result['subject'] == SUBJECTS[unit],
                'wrong result phase or subject')
        member(result['presence'], {'present', 'absent', 'undetermined'})
        member(result['outcome'], {'pass', 'fail', 'unsupported', 'inconclusive', 'not-applicable'})
        diagnostics, gaps = result['diagnostics'], result['incomplete']
        require(isinstance(diagnostics, list) and isinstance(gaps, list), 'expected arrays')
        keys = set()
        for diagnostic in diagnostics:
            record(diagnostic, {'code', 'location', 'outcome'}, {'message'})
            member(diagnostic['code'], CODES[unit])
            pointer(diagnostic['location'])
            member(diagnostic['outcome'], {'fail', 'unsupported', 'inconclusive'})
            if 'message' in diagnostic:
                text(diagnostic.pop('message'))
            key = tuple(diagnostic[k] for k in ('code', 'location', 'outcome'))
            require(key not in keys, 'duplicate diagnostic')
            keys.add(key)
        keys = set()
        for gap in gaps:
            record(gap, {'code', 'location', 'causes'})
            member(gap['code'], CODES[unit] | ({'CHECKS'} if unit != 'syntax' else set()))
            pointer(gap['location'])
            key = (gap['code'], gap['location'])
            require(key not in keys, 'duplicate gap')
            keys.add(key)
            causes = gap['causes']
            require(isinstance(causes, list) and causes, 'expected nonempty causes')
            for cause in causes:
                member(cause, {'shape', 'reference', 'path', 'unsupported'})
            require(len(set(causes)) == len(causes), 'duplicate cause')
            gap['causes'] = sorted(causes)
        require(result['presence'] != 'undetermined' or gaps, 'undetermined without gap')
        require(result['outcome'] == aggregate(result['presence'], diagnostics, gaps),
                'incorrect aggregate outcome')
        result['diagnostics'] = sorted(diagnostics, key=lambda d: (d['code'], d['location'], d['outcome']))
        result['incomplete'] = sorted(gaps, key=lambda g: (g['code'], g['location']))
    del report['processor']
    report['results'] = sorted(results, key=lambda r: r['unit'])
    return report


def expected_report(case):
    """Expand hand-authored tuples; never inspect reader output or input semantics."""
    require(set(case['presence']) == set(SUBJECTS), 'oracle needs all six presences')
    require(all(d[0] in SUBJECTS for d in case['diagnostics']), 'unknown diagnostic unit')
    require(all(g[0] in SUBJECTS for g in case['gaps']), 'unknown gap unit')
    results = []
    for unit, subject in SUBJECTS.items():
        diagnostics = [dict(code=c, location=l, outcome=o)
                       for u, c, l, o in case['diagnostics'] if u == unit]
        gaps = [dict(code=c, location=l, causes=a)
                for u, c, l, a in case['gaps'] if u == unit]
        presence = case['presence'][unit]
        results.append(dict(unit=unit, subject=subject, phase='local', presence=presence,
                            outcome=aggregate(presence, diagnostics, gaps),
                            diagnostics=diagnostics, incomplete=gaps))
    return dict(edition=EDITION, processor=dict(identity='hand-authored-oracle', version=EDITION),
                operation='validate', input=dict(id='primary', sha256=case['sha256']), results=results)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def write_json(path, value):
    path.write_bytes(encoded(value))


def load_cases():
    raw = (HERE / 'corpus/expectations.json').read_bytes()
    manifest = strict_json(raw)
    require(manifest['edition'] == EDITION, 'wrong corpus edition')
    candidate = ROOT / 'proposals/0016-kiss-experiment-0.2.md'
    require(digest(candidate.read_bytes()) == manifest['candidateSha256'], 'candidate changed')
    cases = manifest['cases']
    require(len(cases) == 38, 'expected the reviewed 38-case corpus')
    names = set()
    for case in cases:
        require(re.fullmatch('[a-z0-9-]+', case['name']) and case['name'] not in names,
                'invalid or duplicate case name')
        names.add(case['name'])
        path = (HERE / case['input']).resolve()
        require(HERE in path.parents, 'input outside experiment')
        require(digest(path.read_bytes()) == case['sha256'], 'input changed: ' + case['name'])
        normalize(encoded(expected_report(case)), case['sha256'])
    return manifest, raw


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def run_case(case, directory, commands, timeout=30):
    directory.mkdir()
    primary = directory / 'primary.input'
    data = (HERE / case['input']).read_bytes()
    require(digest(data) == case['sha256'], 'input changed: ' + case['name'])
    primary.write_bytes(data)
    primary.chmod(0o444)
    oracle = normalize(encoded(expected_report(case)), case['sha256'])
    write_json(directory / 'expected.json', oracle)
    result = {'name': case['name'], 'sha256': case['sha256'], 'readers': {}}
    normalized = {}
    for name, command in commands.items():
        argv = [*command, str(primary)]
        status = {'argv': argv, 'returncode': None, 'validReport': False, 'oracleMatch': False}
        stdout = stderr = b''
        try:
            require(primary.read_bytes() == data, 'input modified before reader')
            completed = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=timeout,
                                       env=None, check=False)
            stdout, stderr = completed.stdout, completed.stderr
            status['returncode'] = completed.returncode
            require(completed.returncode == 0, 'reader process failed')
            require(primary.read_bytes() == data, 'input modified by reader')
            actual = normalize(stdout, case['sha256'])
            normalized[name] = actual
            status['validReport'] = True
            status['oracleMatch'] = actual == oracle
            if actual != oracle:
                status['error'] = 'exact oracle mismatch; compare expected.json and normalized output'
            write_json(directory / (name + '.normalized.json'), actual)
        except subprocess.TimeoutExpired as error:
            stdout, stderr = error.stdout or b'', error.stderr or b''
            status['error'] = 'reader timeout'
        except (ValueError, OSError, RecursionError) as error:
            status['error'] = str(error)
        (directory / (name + '.stdout')).write_bytes(stdout)
        (directory / (name + '.stderr')).write_bytes(stderr)
        result['readers'][name] = status
    result['agreement'] = (len(normalized) == 2 and len(commands) == 2
                           and len({json.dumps(r, sort_keys=True) for r in normalized.values()}) == 1)
    result['passed'] = result['agreement'] and all(r['oracleMatch'] for r in result['readers'].values())
    write_json(directory / 'result.json', result)
    return result


def compare(output):
    output = output.resolve()
    require(output != ROOT and ROOT not in output.parents, 'evidence must be outside checkout')
    manifest, raw = load_cases()
    # Refuse even an empty existing directory. Never clean or overwrite evidence.
    output.mkdir(parents=True, exist_ok=False)
    (output / 'expectations.json').write_bytes(raw)
    metadata = dict(commit=git('rev-parse', 'HEAD'), dirty=git('status', '--porcelain'),
                    candidateSha256=manifest['candidateSha256'], oracleSha256=digest(raw),
                    reviewedReaderCommits=READER_COMMITS, python=sys.version, node=None,
                    sourceSha256={})
    source_paths = list(HERE.rglob('*')) + [
        ROOT / 'tooling/readers/python/agsdl_reader/lossless.py',
        ROOT / 'tooling/readers/javascript/json.mjs',
    ]
    for path in sorted(source_paths):
        if path.is_file() and '__pycache__' not in path.parts:
            metadata['sourceSha256'][str(path.relative_to(ROOT))] = digest(path.read_bytes())
    try:
        metadata['node'] = subprocess.check_output(['node', '--version'], text=True).strip()
    except (OSError, subprocess.CalledProcessError) as error:
        metadata['node'] = str(error)
    write_json(output / 'metadata.json', metadata)
    cases = [run_case(c, output / c['name'], READERS) for c in manifest['cases']]
    summary = dict(cases=len(cases), passed=sum(c['passed'] for c in cases),
                   invalidReports=sum(not r['validReport'] for c in cases for r in c['readers'].values()),
                   oracleMismatches=sum(r['validReport'] and not r['oracleMatch']
                                        for c in cases for r in c['readers'].values()),
                   readerMismatches=sum(not c['agreement'] and all(r['validReport'] for r in c['readers'].values())
                                        for c in cases),
                   results=cases)
    write_json(output / 'summary.json', summary)
    print(json.dumps({k: v for k, v in summary.items() if k != 'results'}))
    print('Evidence:', output)
    return 0 if summary['passed'] == len(cases) else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path, help='new evidence directory outside checkout')
    args = parser.parse_args()
    try:
        return compare(args.output)
    except (ValueError, OSError, subprocess.CalledProcessError, RecursionError) as error:
        print('Comparison failed: ' + str(error), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
