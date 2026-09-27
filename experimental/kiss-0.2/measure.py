#!/usr/bin/env python3
"""Mechanical example sizes, not equivalent-capability or quality scores."""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]


def members(value):
    if isinstance(value, dict):
        return len(value) + sum(members(child) for child in value.values())
    if isinstance(value, list):
        return sum(members(child) for child in value)
    return 0


def measure(label, data):
    value = json.loads(data)
    return dict(input=label, sha256=hashlib.sha256(data).hexdigest(),
                objectMembersRecursive=members(value),
                compactUtf8Bytes=len(json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()),
                topLevelFields=len(value), topLevelNames=list(value))


def measurements():
    paths = ['examples/0.1.0/single-agent.json', 'examples/0.1.0/two-agent-sequence.json']
    paths += ['experimental/kiss-0.2/examples/' + name + '.json' for name in
              ('agent-embedded', 'agent-named', 'two-agent-sequence', 'two-configurations', 'governed-call')]
    rows = [measure(path, (ROOT / path).read_bytes()) for path in paths]
    path = 'docs/research/0.2-design-examples.md'
    sketches = re.findall(r'^```json\n(.*?)^```', (ROOT / path).read_text(), re.M | re.S)
    for index, sketch in enumerate(sketches[:2], 1):
        rows.append(measure(path + '#json-sketch-' + str(index), sketch.encode()))
    return rows


if __name__ == '__main__':
    print(json.dumps(measurements(), indent=2))
