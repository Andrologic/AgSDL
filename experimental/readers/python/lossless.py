"""Strict byte-oriented JSON with source spans and uninterpreted number lexemes."""
from dataclasses import dataclass
import json
import re


@dataclass(frozen=True)
class Number:
    lexeme: str


def integer(value):
    """Return an exact safe uint, or None, without expanding large exponents."""
    if not isinstance(value, Number):
        return None
    match = re.fullmatch(r'(-?)(\d+)(?:\.(\d+))?(?:[eE]([+-]?\d+))?', value.lexeme)
    sign, whole, fraction, exponent = match.groups()
    digits = (whole + (fraction or '')).lstrip('0')
    if not digits:
        return 0
    if sign:
        return None
    exponent = exponent or '0'
    exponent_digits = exponent.lstrip('+-0') or '0'
    # A nonzero safe integer cannot require a decimal shift larger than the
    # entire significand plus the safe-integer width. Compare as strings first.
    bound = str(len(whole) + len(fraction or '') + 16)
    if len(exponent_digits) > len(bound) or (len(exponent_digits) == len(bound) and exponent_digits > bound):
        return None
    normalized_exponent = ('-' if exponent.startswith('-') else '') + exponent_digits
    shift = int(normalized_exponent) - len(fraction or '')
    if shift < 0:
        if -shift > len(digits) or any(c != '0' for c in digits[shift:]):
            return None
        digits = digits[:shift]
    elif len(digits) + shift > 16:
        return None
    else:
        digits += '0' * shift
    if len(digits) > 16:
        return None
    result = int(digits or '0')
    return result if result <= 9007199254740991 else None


def dumps(value):
    if isinstance(value, Number):
        return value.lexeme
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k, ensure_ascii=True) + ':' + dumps(v)
                              for k, v in value.items()) + '}'
    if isinstance(value, (list, tuple)):
        return '[' + ','.join(dumps(v) for v in value) + ']'
    return json.dumps(value, ensure_ascii=True, allow_nan=False, separators=(',', ':'))


def pointer(parent, key):
    return parent + '/' + str(key).replace('~', '~0').replace('/', '~1')


class SyntaxFailure(ValueError):
    def __init__(self, offset, message):
        self.offset = offset
        super().__init__(message)


class Parser:
    def __init__(self, raw):
        self.raw, self.i, self.spans = raw, 0, {}

    def error(self, message, offset=None):
        raise SyntaxFailure(self.i if offset is None else offset, message)

    def whitespace(self):
        while self.i < len(self.raw) and self.raw[self.i] in b' \t\r\n':
            self.i += 1

    def parse(self):
        self.whitespace()
        value = self.value('')
        self.whitespace()
        if self.i != len(self.raw):
            self.error('trailing content')
        return value

    def value(self, path):
        self.whitespace()
        start = self.i
        if self.i >= len(self.raw):
            self.error('unexpected end of input')
        char = self.raw[self.i]
        if char == 34:
            result = self.string()
        elif char in (123, 91):
            object_mode = char == 123
            result = {} if object_mode else []
            self.i += 1
            self.whitespace()
            close = 125 if object_mode else 93
            if self.i < len(self.raw) and self.raw[self.i] == close:
                self.i += 1
            else:
                while True:
                    self.whitespace()
                    if object_mode:
                        quote = self.i
                        if self.i >= len(self.raw) or self.raw[self.i] != 34:
                            self.error('expected member name')
                        key = self.string()
                        if key in result:
                            self.error('duplicate decoded member name', quote)
                        self.whitespace()
                        if self.i >= len(self.raw) or self.raw[self.i] != 58:
                            self.error('expected colon')
                        self.i += 1
                        result[key] = self.value(pointer(path, key))
                    else:
                        result.append(self.value(pointer(path, len(result))))
                    self.whitespace()
                    if self.i >= len(self.raw):
                        self.error('unexpected end of container')
                    if self.raw[self.i] == close:
                        self.i += 1
                        break
                    if self.raw[self.i] != 44:
                        self.error('expected comma or closing delimiter')
                    self.i += 1
        elif char == 45 or 48 <= char <= 57:
            # Scan one token and diagnose the first missing digit, not its start.
            if char == 45:
                self.i += 1
            if self.i >= len(self.raw) or not 48 <= self.raw[self.i] <= 57:
                self.error('expected digit')
            if self.raw[self.i] == 48:
                self.i += 1
            else:
                while self.i < len(self.raw) and 48 <= self.raw[self.i] <= 57:
                    self.i += 1
            if self.i < len(self.raw) and self.raw[self.i] == 46:
                self.i += 1
                self.digits()
            if self.i < len(self.raw) and self.raw[self.i] in b'eE':
                self.i += 1
                if self.i < len(self.raw) and self.raw[self.i] in b'+-':
                    self.i += 1
                self.digits()
            result = Number(self.raw[start:self.i].decode('ascii'))
        else:
            candidates = {116: (b'true', True), 102: (b'false', False), 110: (b'null', None)}
            if char not in candidates:
                self.error('unexpected value')
            token, result = candidates[char]
            for c in token:
                if self.i >= len(self.raw) or self.raw[self.i] != c:
                    self.error('invalid literal')
                self.i += 1
        self.spans[path] = (start, self.i)
        return result

    def digits(self):
        start = self.i
        while self.i < len(self.raw) and 48 <= self.raw[self.i] <= 57:
            self.i += 1
        if self.i == start:
            self.error('expected digit')

    def hex4(self):
        value = 0
        for _ in range(4):
            if self.i >= len(self.raw):
                self.error('incomplete Unicode escape')
            c = self.raw[self.i]
            if c not in b'0123456789abcdefABCDEF':
                self.error('invalid Unicode escape')
            value = value * 16 + int(chr(c), 16)
            self.i += 1
        return value

    def string(self):
        self.i += 1
        chars = []
        while True:
            if self.i >= len(self.raw):
                self.error('unterminated string')
            c = self.raw[self.i]
            if c == 34:
                self.i += 1
                return ''.join(chars)
            if c < 32:
                self.error('unescaped control character')
            if c == 92:
                escape = self.i
                self.i += 1
                if self.i >= len(self.raw):
                    self.error('incomplete escape')
                c = self.raw[self.i]
                self.i += 1
                escapes = {34: '"', 92: '\\', 47: '/', 98: '\b', 102: '\f', 110: '\n', 114: '\r', 116: '\t'}
                if c in escapes:
                    chars.append(escapes[c])
                elif c == 117:
                    code = self.hex4()
                    if 0xD800 <= code <= 0xDBFF:
                        if self.raw[self.i:self.i + 2] != b'\\u':
                            self.error('unpaired high surrogate', escape)
                        self.i += 2
                        low = self.hex4()
                        if not 0xDC00 <= low <= 0xDFFF:
                            self.error('unpaired high surrogate', escape)
                        code = 0x10000 + ((code - 0xD800) << 10) + low - 0xDC00
                    elif 0xDC00 <= code <= 0xDFFF:
                        self.error('unpaired low surrogate', escape)
                    chars.append(chr(code))
                else:
                    self.error('invalid escape', self.i - 1)
            elif c < 128:
                chars.append(chr(c))
                self.i += 1
            else:
                length = 2 if 0xC2 <= c <= 0xDF else 3 if 0xE0 <= c <= 0xEF else 4 if 0xF0 <= c <= 0xF4 else 0
                if not length:
                    self.error('invalid UTF-8')
                chunk = self.raw[self.i:self.i + length]
                try:
                    chars.append(chunk.decode('utf-8', errors='strict'))
                except UnicodeDecodeError as error:
                    self.error('invalid UTF-8', self.i + error.start)
                self.i += length
