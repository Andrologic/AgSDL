#!/usr/bin/env python3
"""Check corpus bookkeeping and schema structure, never AgSDL semantics."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIXTURES = ROOT / 'fixtures'
RULES = set('P-SYNTAX P-SHAPE D-IDENTITY D-OWNER D-REFERENCE D-RELATION D-CYCLE D-EXPORT D-AGENT D-DEFERRAL D-DEPENDENCY D-INTEGRITY X-MODE G-TARGET G-PATH G-DATA G-APPROVAL G-RESOLVE R-REQUIREMENT R-SELECTION E-PRESERVE E-LOSS P-PREREQUISITE X-EXECUTION X-FULL-MODEL X-READINESS X-EVIDENCE-ASSESSMENT'.split())
OPERATIONS = {'inspect': ('inspect', None), 'validateD': ('D', 'unresolved-document'), 'validateG': ('G', 'unresolved-document'), 'resolveG': ('G', 'resolved-graph'), 'validateR': ('R', 'unresolved-document'), 'exchange': ('exchange', None), 'lossyExchange': ('exchange', None)}


def require(value, message):
    if not value:
        raise ValueError(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict), 'metadata record must be an object')
    require(set(required) <= set(value) <= set(required) | set(optional), 'unknown/missing metadata fields')


def text(value):
    require(isinstance(value, str) and value, 'metadata text must be nonempty')


def loss(record, input_ids, default=False):
    fields(record, {'input', 'location', 'information', 'permission'} | (set() if default else {'reason'}), {'reason'} if default else ())
    # Supplied losses always include a reason; default expected prose is unspecified.
    require(record['input'] in input_ids and record['permission'] is None, 'loss scope/permission')
    location(record['location'])
    text(record['information'])
    if 'reason' in record:
        text(record['reason'])


def pairs(items):
    out = {}
    for key, value in items:
        require(key not in out, f'duplicate metadata member {key}')
        out[key] = value
    return out


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'), object_pairs_hook=pairs,
                      parse_constant=lambda x: (_ for _ in ()).throw(ValueError(x)))


def pointer(value):
    require(isinstance(value, str) and (value == '' or value.startswith('/')), f'invalid pointer {value!r}')
    require(not re.search(r'~(?![01])', value), f'invalid pointer escape {value!r}')


def location(value):
    require(isinstance(value, dict) and len(value) == 1, 'location must have one member')
    if 'pointer' in value:
        pointer(value['pointer'])
    else:
        require(set(value) == {'byte'} and type(value['byte']) is int and 0 <= value['byte'] <= 9007199254740991, 'invalid byte location')


def artifact(record):
    require(set(record) == {'path', 'sha256'}, 'artifact metadata fields')
    path = (FIXTURES / record['path']).resolve()
    require(path.is_relative_to(FIXTURES) and path.is_file(), f'unsafe/missing artifact {path}')
    require(hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], f'hash mismatch {path}')
    return path


def schema_check(path, full):
    schema = read_json(path)
    require(schema['$schema'] == 'https://json-schema.org/draft/2020-12/schema', f'dialect {path}')
    def walk(node):
        if isinstance(node, dict):
            if '$ref' in node:
                ref = node['$ref']
                require(ref.startswith('#/'), f'nonlocal schema reference {ref}')
                target = schema
                for part in ref[2:].split('/'):
                    target = target[part.replace('~1', '/').replace('~0', '~')]
                require(isinstance(target, (dict, bool)), f'non-schema target {ref}')
            if 'pattern' in node:
                re.compile(node['pattern'])
            if node.get('type') == 'object' and 'properties' in node:
                require(node.get('additionalProperties') is False, f'open record in {path}')
                require(set(node.get('required', [])) <= set(node['properties']), f'unknown required property in {path}')
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)
    walk(schema)
    if full:
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(schema)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--jsonschema', action='store_true', help='also require installed jsonschema and validate Draft 2020-12 metaschemas; no installation or retrieval')
    args = parser.parse_args()
    manifest = read_json(FIXTURES / 'manifest.json')
    fields(manifest, {'format','contract','contractBase','contractSha256','coverage','cases'})
    require(isinstance(manifest['cases'], list), 'cases must be an array')
    require(manifest['format'] == 'agsdl-candidate-corpus-1', 'manifest format')
    require(manifest['contract'] == 'proposal-0012-candidate-2', 'contract edition')
    contract = ROOT.parents[1] / 'proposals/0012-minimal-0.1.0-contract.md'
    require(hashlib.sha256(contract.read_bytes()).hexdigest() == manifest['contractSha256'], 'contract changed; re-review oracles before updating digest')
    require(set(manifest['coverage']) == RULES, 'coverage rule inventory differs')
    cases = manifest['cases']
    names = [c['name'] for c in cases]
    require(len(names) == len(set(names)), 'duplicate case names')
    known = set(names)
    referenced = set()
    witnesses = set()
    by_name = {c['name']: c for c in cases}
    for case in cases:
        fields(case, {'name','status','primary','annexes','operation','source','coverage','reviewWitnesses','expected'}, {'losses','blocker'})
        require(isinstance(case['annexes'], dict), 'annexes must be a map')
        require(isinstance(case['coverage'], list) and isinstance(case['reviewWitnesses'], list), 'case indexes must be arrays')
        name = case['name']
        require(re.fullmatch('[A-Za-z0-9-]+', name), f'invalid case name {name}')
        require(case['operation'] in OPERATIONS, f'operation {name}')
        referenced.add(artifact(case['primary']))
        input_ids = {'primary'}
        for dep_id, record in case['annexes'].items():
            require(isinstance(dep_id, str) and dep_id, f'annex id {name}')
            input_ids.add('annex/' + dep_id)
            referenced.add(artifact(record))
        fields(case['source'], {'document','section'})
        source = (FIXTURES / case['source']['document']).resolve()
        require(source == contract.resolve() and case['source']['section'], f'source {name}')
        require(all(type(n) is int and 1 <= n <= 6 for n in case['reviewWitnesses']), 'review witness domain')
        witnesses.update(case['reviewWitnesses'])
        if 'losses' in case:
            require(case['operation'] == 'lossyExchange' and isinstance(case['losses'], list), 'losses only allowed as an array for lossyExchange')
            for item in case['losses']:
                loss(item, input_ids)
        for item in case['coverage']:
            fields(item, {'rule','variant'})
            require(item['rule'] in RULES, f'unknown coverage rule {name}')
            require(name in manifest['coverage'][item['rule']]['cases'].get(item['variant'], []), f'coverage index missing {name}')
        if case['status'] == 'blocked':
            require(case.get('blocker') and case.get('expected') is None, f'blocked oracle {name}')
            continue
        require(case['status'] == 'ready', f'status {name}')
        expected = case['expected']
        fields(expected, {'results','findings','checks','states','absentStates','opaque','absentOpaque','preservation'}, {'losses'})
        for key in ['results','checks','states','absentStates','opaque','absentOpaque']:
            require(isinstance(expected[key], list), f'{key} must be an array')
        if case['operation'] == 'lossyExchange':
            require(isinstance(expected.get('losses'), list) and expected['losses'], 'expected prospective losses required')
            for item in expected['losses']:
                loss(item, input_ids, default=True)
        else:
            require('losses' not in expected, 'unexpected loss oracle')
        unit, phase = OPERATIONS[case['operation']]
        require(any(r['input'] == 'primary' and (r['unit'], r['phase']) == (unit, phase) for r in expected['results']), f'missing requested result {name}')
        result_keys = []
        for result in expected['results']:
            fields(result, {'input','unit','phase','verdict'})
            allowed = {(unit, phase)}
            if unit in {'G','R'}:
                allowed.add(('D','unresolved-document'))
            if result['input'] != 'primary':
                require(case['operation'] == 'resolveG', f'annex result operation {name}')
                allowed = {('D','unresolved-document'), ('G','resolved-graph')}
            require((result['unit'], result['phase']) in allowed, f'result unit/phase {name}')
            result_keys.append((result['input'],result['unit'],result['phase']))
            require(result['input'] in input_ids, f'result input {name}')
            require(result['verdict'] in {'pass', 'fail', 'unsupported', 'inconclusive'}, f'verdict {name}')
        require(len(result_keys) == len(set(result_keys)), f'duplicate result oracle {name}')
        fields(expected['findings'], {'mode','items'})
        require(isinstance(expected['findings']['items'], list), 'finding items must be an array')
        scopes = {(i,u) for i,u,p in result_keys}
        require(expected['findings']['mode'] in {'contains', 'exact'}, f'finding mode {name}')
        for finding in expected['findings']['items']:
            fields(finding, {'input','unit','rule','location','outcome'})
            require((finding['input'],finding['unit']) in scopes, f'finding unit {name}')
            require(finding['input'] in input_ids and finding['rule'] in RULES, f'finding scope {name}')
            require(finding['outcome'] in {'fail', 'unsupported', 'inconclusive', 'deferred'}, f'outcome {name}')
            location(finding['location'])
        for check in expected['checks']:
            fields(check, {'input','unit','rule','state','locations'})
            require((check['input'],check['unit']) in scopes, f'check unit {name}')
            require(isinstance(check['locations'], list), 'check locations must be an array')
            require(check['input'] in input_ids and check['rule'] in RULES, f'check scope {name}')
            require(check['state'] in {'completed', 'excluded', 'blocked'}, f'check state {name}')
            for loc in check['locations']:
                location(loc)
        for item in expected['states'] + expected['opaque'] + expected['absentOpaque']:
            require(item['input'] in input_ids, f'inventory input {name}')
            pointer(item['pointer'])
        for item in expected['opaque'] + expected['absentOpaque']:
            fields(item, {'input','pointer'})
        for item in expected['states']:
            fields(item, {'input','pointer','state'}, {'detailRequirement'})
            if 'detailRequirement' in item:
                text(item['detailRequirement'])
            require(item['state'] in {'declared','absent','unknown','unchecked'}, f'inventory state {name}')
        for item in expected['absentStates']:
            fields(item, {'input','pointerPrefix'})
            require(item['input'] in input_ids, f'forbidden state input {name}')
            pointer(item['pointerPrefix'])
        require(expected['preservation'] in {'exact-input-boundary', 'no-output'}, f'preservation {name}')
        if expected['preservation'] == 'exact-input-boundary':
            require(case['operation'] == 'exchange', f'preservation operation {name}')
    for rule, coverage in manifest['coverage'].items():
        fields(coverage, {'cases','limits'}, {'notApplicable'})
        text(coverage['limits'])
        require(coverage['cases'], f'no witnesses for {rule}')
        for variant, listed in coverage['cases'].items():
            require(variant in {'positive','negative','unknown','unsupported','inconclusive','deferred','excluded','blocked'}, 'coverage variant')
            require(isinstance(listed, list) and listed, f'empty coverage {rule}/{variant}')
            require(set(listed) <= known and len(listed) == len(set(listed)), f'coverage references {rule}/{variant}')
            for case_name in listed:
                selected = by_name[case_name]
                require(selected['status'] == 'ready', 'blocked case cannot establish coverage')
                if rule in {'P-PREREQUISITE','X-EXECUTION','X-FULL-MODEL','X-READINESS','X-EVIDENCE-ASSESSMENT'}:
                    require(any(c['rule'] == rule and c['state'] == variant for c in selected['expected']['checks']), 'documentary coverage has no matching Check')
                else:
                    require({'rule':rule,'variant':variant} in selected['coverage'], f'reverse coverage association {rule}/{case_name}')
        if rule not in {'E-LOSS','P-PREREQUISITE','X-EXECUTION','X-FULL-MODEL','X-READINESS','X-EVIDENCE-ASSESSMENT'}:
            require({'positive', 'negative'} <= set(coverage['cases']), f'positive/negative coverage absent for {rule}')
    require(witnesses == set(range(1, 7)), 'six review witnesses not indexed')
    on_disk = {p.resolve() for p in FIXTURES.glob('*.json')} - {(FIXTURES / 'manifest.json').resolve()}
    require(referenced == on_disk, 'unreferenced or untracked fixture bytes')
    for unit in ('D','G','R'):
        schema_check(ROOT / 'schemas' / f'{unit}.schema.json', args.jsonschema)
    print(f'{len(cases)} cases: metadata, hashes, source edition, rule coverage and six-review index checked.')
    print('Three schemas: JSON, local references, patterns and closed records checked.' + (' Draft 2020-12 metaschemas checked.' if args.jsonschema else ' Metaschema validation not requested.'))
    print('No AgSDL semantic validation, reader comparison or described-system execution performed.')


if __name__ == '__main__':
    main()
