#!/usr/bin/env python3
"""Report trailing blanks in Markdown, TOML and YAML files without external tools."""
import os
import sys
from pathlib import Path

SUFFIXES = {'.md', '.toml', '.yaml'}
SKIPPED = {'.git', '.venv', '.codex', '__pycache__', 'node_modules'}


def offending_lines(root):
    for directory, names, files in os.walk(root):
        names[:] = sorted(n for n in names if n not in SKIPPED)
        for name in sorted(files):
            path = Path(directory, name)
            if path.suffix not in SUFFIXES:
                continue
            for number, line in enumerate(path.read_bytes().split(b'\n'), 1):
                if line.rstrip(b'\r') != line.rstrip(b'\r').rstrip(b' \t'):
                    yield path.relative_to(root), number


def main():
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('.')
    found = False
    for path, number in offending_lines(root):
        print(f'{path}:{number}: trailing whitespace')
        found = True
    if found:
        print('Trailing whitespace found.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
