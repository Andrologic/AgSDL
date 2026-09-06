#!/usr/bin/env python3
"""One offline base64 request on stdin, one lossless JSON response on stdout."""
import base64
import binascii
import sys
from lossless import Parser, SyntaxFailure, dumps
from reader import read


def main():
    try:
        request = Parser(sys.stdin.buffer.read()).parse()
        if not isinstance(request, dict) or not {'operation', 'primary', 'annexes'} <= request.keys() or request.keys() - {'operation', 'primary', 'annexes', 'losses'}:
            raise ValueError('request fields must be operation, primary, annexes and optional losses')
        if not isinstance(request['primary'], str) or not isinstance(request['annexes'], dict) or any(not isinstance(v, str) for v in request['annexes'].values()):
            raise ValueError('primary and annexes must contain base64 strings')
        if 'losses' in request and not isinstance(request['losses'], list):
            raise ValueError('losses must be an array when supplied')
        result = read(request['operation'], base64.b64decode(request['primary'], validate=True),
                      {k: base64.b64decode(v, validate=True) for k, v in request['annexes'].items()}, request.get('losses'))
        result['artifacts'] = {k: base64.b64encode(v).decode('ascii') for k, v in result['artifacts'].items()}
        sys.stdout.write(dumps(result) + '\n')
        return 0
    except (ValueError, TypeError, binascii.Error, SyntaxFailure, RecursionError) as error:
        # Host/request/resource failures are not candidate validation findings.
        sys.stderr.write(type(error).__name__ + ': ' + str(error) + '\n')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
