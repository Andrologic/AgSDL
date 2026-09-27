#!/usr/bin/env python3
"""Read one artifact path and write one candidate report; no execution."""
import json
from pathlib import Path
import sys

from reader import validate


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print('usage: cli.py ARTIFACT', file=sys.stderr)
        return 2
    try:
        report = validate(Path(args[0]).read_bytes())
        output = json.dumps(report, ensure_ascii=True, allow_nan=False)
    except (OSError, MemoryError, RecursionError) as error:
        print('Unable to produce report: ' + str(error), file=sys.stderr)
        return 2
    print(output)
    return 0


if __name__ == '__main__':
    sys.exit(main())
