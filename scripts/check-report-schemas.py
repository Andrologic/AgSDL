#!/usr/bin/env python3
"""Validate every expected official comparator response against Draft 2020-12."""
import argparse
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reports', type=Path, help='official comparator report directory')
    args = parser.parse_args()
    schema = json.loads((ROOT / 'schemas/report.schema.json').read_text())
    document = json.loads((ROOT / 'schemas/agsdl.schema.json').read_text())
    Draft202012Validator.check_schema(schema)
    registry = Registry().with_resource('agsdl.schema.json', Resource.from_contents(document))
    validator = Draft202012Validator(schema, registry=registry)
    manifest = json.loads((ROOT / 'conformance/fixtures/manifest.json').read_text())
    summary = json.loads((args.reports / 'summary.json').read_text())
    if summary['cases'] != len(manifest['cases']) or summary['blocked']:
        raise ValueError('Official comparison must cover the complete unblocked corpus')
    readers = summary['readers']
    if len(readers) < 2 or len(set(readers)) != len(readers):
        raise ValueError('At least two distinct reader labels are required')
    expected = {f"{case['name']}.{label}.stdout" for case in manifest['cases'] for label in readers}
    actual = {p.name for p in args.reports.glob('*.stdout')}
    if actual != expected:
        raise ValueError(f'Report set differs: missing {sorted(expected - actual)}, extra {sorted(actual - expected)}')
    for name in sorted(expected):
        response = json.loads((args.reports / name).read_text())
        validator.validate(response['report'])
    print(f'{len(expected)} official reports validated against Draft 2020-12')


if __name__ == '__main__':
    main()
