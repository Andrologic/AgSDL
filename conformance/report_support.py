"""Official comparator utilities copied without semantic changes from candidate-2.

Only the JSON, report-boundary and process helpers used by the official tools
are retained. Historical comparators keep their own implementation.
"""
import decimal
import hashlib
import json
import os
import re
import signal
import subprocess

UINT_MAX = 9007199254740991

EDITION = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*\Z')

HASH = re.compile(r'[0-9a-f]{64}\Z')

OPERATIONS = {'inspect': ('inspect', None), 'validateD': ('D', 'unresolved-document'), 'validateG': ('G', 'unresolved-document'), 'resolveG': ('G', 'resolved-graph'), 'validateR': ('R', 'unresolved-document'), 'exchange': ('exchange', None), 'lossyExchange': ('exchange', None)}

D_RULES = set('P-SYNTAX P-SHAPE D-IDENTITY D-OWNER D-REFERENCE D-RELATION D-CYCLE D-EXPORT D-AGENT D-DEFERRAL D-DEPENDENCY D-INTEGRITY X-MODE'.split())

G_RULES = set('P-SHAPE X-MODE G-TARGET G-PATH G-DATA G-APPROVAL'.split())

BOUNDARY = {'X-EXECUTION': '', 'X-FULL-MODEL': ''}

R_BOUNDARY = {'X-READINESS': '/runtime', 'X-EVIDENCE-ASSESSMENT': '/runtime'}

RANK = {'pass': 0, 'inconclusive': 1, 'unsupported': 2, 'fail': 3}

def demand(condition, message):
    if not condition:
        raise ValueError(message)

def record(value, fields):
    demand(isinstance(value, dict) and set(value) == set(fields.split()), 'closed record fields: ' + fields)

def text(value, empty=False):
    demand(isinstance(value, str) and (empty or bool(value)), 'expected text')
    demand(not any(0xD800 <= ord(c) <= 0xDFFF for c in value), 'invalid Unicode scalar')

class WideNumber:
    # Decimal has an implementation exponent ceiling; JSON opaque values do not.
    def __init__(self, lexeme):
        self.lexeme = lexeme

def number_parts(value):
    if isinstance(value, WideNumber):
        word = value.lexeme.lower()
        coefficient, _, exponent = word.partition('e')
        power = 0
        for digit in exponent.lstrip('+-'):
            power = power * 10 + ord(digit) - 48
        if exponent.startswith('-'): power = -power
        sign = int(coefficient.startswith('-'))
        integer, dot, fractional = coefficient.lstrip('-').partition('.')
        digits = (integer + fractional).lstrip('0')
        power -= len(fractional)
    else:
        number = decimal.Decimal(value)
        demand(number.is_finite(), 'nonfinite number')
        sign, coefficient, power = number.as_tuple()
        digits = ''.join(str(d) for d in coefficient).lstrip('0')
    if not digits: return (0, '0', 0)
    trimmed = digits.rstrip('0')
    return (sign, trimmed, power + len(digits) - len(trimmed))

def uint(value):
    demand(not isinstance(value, bool) and isinstance(value, (int, decimal.Decimal, WideNumber)), 'expected uint')
    sign, digits, power = number_parts(value)
    demand(not sign and power >= 0 and len(digits) + power <= 16, 'uint outside domain')
    integer = int(digits) * 10 ** power
    demand(integer <= UINT_MAX, 'uint outside domain')
    return integer

def edition(value):
    record(value, 'identity version')
    text(value['identity']); text(value['version'])
    demand(EDITION.fullmatch(value['identity']), 'invalid Edition identity')

def digest(data):
    return hashlib.sha256(data).hexdigest()

def pointer(value):
    text(value, empty=True)
    demand((not value or value.startswith('/')) and not re.search(r'~(?![01])', value), 'invalid JSON Pointer')

def escape(value):
    return value.replace('~', '~0').replace('/', '~1')

class JsonSource:
    """Strict JSON syntax and exact value spans. No AgSDL record interpretation."""
    def __init__(self, data):
        self.data = data
        self.s = data.decode('utf-8', errors='strict')
        self.at = 0
        self.spans = {}
        # Character-to-UTF-8 offsets keep escaped and multibyte strings exact.
        self.offsets = [0]
        for ch in self.s:
            self.offsets.append(self.offsets[-1] + len(ch.encode('utf-8')))
        self.tree = self.value('')
        self.ws()
        demand(self.at == len(self.s), 'trailing JSON content')

    def ws(self):
        while self.at < len(self.s) and self.s[self.at] in ' \t\r\n':
            self.at += 1

    def string(self):
        demand(self.at < len(self.s) and self.s[self.at] == '"', 'expected JSON string')
        value, end = json.JSONDecoder().raw_decode(self.s, self.at)
        text(value, empty=True)
        self.at = end
        return value

    def value(self, path):
        self.ws(); start = self.at
        demand(start < len(self.s), 'unexpected JSON EOF')
        ch = self.s[self.at]
        if ch == '{':
            self.at += 1; result = {}; self.ws()
            if self.at < len(self.s) and self.s[self.at] == '}':
                self.at += 1
            else:
                while True:
                    self.ws(); key = self.string()
                    demand(key not in result, 'duplicate JSON member')
                    self.ws(); demand(self.at < len(self.s) and self.s[self.at] == ':', 'expected colon')
                    self.at += 1; result[key] = self.value(path + '/' + escape(key)); self.ws()
                    demand(self.at < len(self.s), 'unexpected JSON EOF')
                    ch = self.s[self.at]; self.at += 1
                    if ch == '}': break
                    demand(ch == ',', 'expected object separator')
        elif ch == '[':
            self.at += 1; result = []; self.ws()
            if self.at < len(self.s) and self.s[self.at] == ']':
                self.at += 1
            else:
                while True:
                    result.append(self.value(path + '/' + str(len(result)))); self.ws()
                    demand(self.at < len(self.s), 'unexpected JSON EOF')
                    ch = self.s[self.at]; self.at += 1
                    if ch == ']': break
                    demand(ch == ',', 'expected array separator')
        elif ch == '"':
            result = self.string()
        else:
            token = re.match(r'(?:true|false|null|-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)', self.s[self.at:])
            demand(token is not None, 'invalid JSON value')
            word = token.group(); self.at += len(word)
            if word in {'true','false','null'}:
                result = {'true': True, 'false': False, 'null': None}[word]
            else:
                try: result = decimal.Decimal(word)
                except decimal.InvalidOperation: result = WideNumber(word)
        self.spans[path] = (self.offsets[start], self.offsets[self.at])
        return result

def load(value):
    return JsonSource(value.encode('utf-8') if isinstance(value, str) else value).tree

def canonical(value):
    if value is None: return ('null',)
    if isinstance(value, bool): return ('bool', value)
    if isinstance(value, (int, decimal.Decimal, WideNumber)):
        return ('number', number_parts(value))
    if isinstance(value, str): return ('string', value)
    if isinstance(value, list): return ('array', tuple(canonical(x) for x in value))
    demand(isinstance(value, dict), 'unsupported JSON host type')
    return ('object', tuple(sorted((k, canonical(v)) for k, v in value.items())))

def unique(items, label):
    keys = [canonical(x) for x in items]
    demand(len(keys) == len(set(keys)), 'duplicate ' + label)

def contains(items, wanted):
    return any(all(k in item and canonical(item[k]) == canonical(v) for k,v in wanted.items()) for item in items)

def loc_key(loc):
    return (0, loc['pointer']) if 'pointer' in loc else (1, uint(loc['byte']))

def opaque_boundaries(parsed, operation, input_id):
    """Possible and obligatory documentary boundaries; no Ref lookup or resolution."""
    tree = parsed.tree
    if not isinstance(tree,dict):
        return ({''}, {''}) if operation in {'inspect','exchange','lossyExchange'} else (set(),set())
    possible, required = set(), set()
    def opaque(parent, names):
        value = tree if parent == '' else at_pointer(tree,parent)
        if isinstance(value,dict):
            for name in names:
                if name in value:
                    p = parent + '/' + escape(name); possible.add(p); required.add(p)
    opaque('', ['annotations','evidence'])
    opaque('/root', ['payload','annotations']) if 'root' in tree else None
    for container, names in [('definitions',['payload','annotations','provenance']),('extensions',['payload'])]:
        entries = tree.get(container)
        if isinstance(entries,list):
            for index, entry in enumerate(entries):
                path = '/' + container + '/' + str(index); opaque(path,names)
                if container == 'definitions' and operation in {'validateG','resolveG'} and isinstance(entry,dict) and entry.get('kind') in ('Interface','ApprovalRequirement'):
                    # Selection is reader work. The payload is either wholly opaque or interpreted.
                    required.discard(path+'/payload')
    for container in ('graphs','runtime'):
        interpreted = input_id == 'primary' and (container == 'graphs' and operation in {'validateG','resolveG'} or container == 'runtime' and operation == 'validateR')
        if not interpreted: opaque('',[container])
    if operation in {'inspect','exchange','lossyExchange'} and 'dependencies' in tree:
        # Readability is a shape probe performed by the reader, not inferred here.
        possible.add('/dependencies')
    return possible, required

def at_pointer(tree, path):
    value = tree
    for component in path.split('/')[1:]:
        name = component.replace('~1','/').replace('~0','~')
        value = value[int(name)] if isinstance(value,list) else value[name]
    return value

def validate_slices(slices, source, parsed, operation, observed_inputs):
    keys=[]; by_input={i:[] for i in source}
    for part in slices:
        record(part, 'input pointer start end')
        i=part['input']; demand(i in source and parsed[i] is not None, 'Slice input unparseable/unknown'); pointer(part['pointer'])
        start,end=uint(part['start']),uint(part['end'])
        demand(parsed[i].spans.get(part['pointer']) == (start,end), 'Slice is not the exact source value span')
        possible,_=opaque_boundaries(parsed[i],operation,i)
        demand(part['pointer'] in possible, 'Slice is interpreted or nonmaximal')
        keys.append((i,part['pointer']));by_input[i].append((start,end,part['pointer']))
    demand(len(keys)==len(set(keys)), 'duplicate Slice')
    for i, parts in by_input.items():
        ordered=sorted(parts)
        demand(all(a[1] <= b[0] for a,b in zip(ordered,ordered[1:])), 'overlapping opaque slices')
        # Annex inventory is limited to observed/selected annexes, not every supplied file.
        if parsed[i] and i in observed_inputs:
            _,required=opaque_boundaries(parsed[i],operation,i)
            demand(required <= {p for _,_,p in parts}, 'missing maximal opaque boundary')

def run_reader(command, request, timeout):
    proc=subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True)
    try:
        stdout,stderr=proc.communicate(request,timeout=timeout)
        return proc.returncode,stdout,stderr,None
    except subprocess.TimeoutExpired:
        # Only the launched reader process group is terminated; partial output is retained.
        try: os.killpg(proc.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        stdout,stderr=proc.communicate()
        return proc.returncode,stdout,stderr,'reader timeout'
