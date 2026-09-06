#!/usr/bin/env python3
"""Compare candidate-2 report contracts and corpus assertions, not AgSDL semantics."""
import argparse
import base64
import decimal
import hashlib
import json
import math
import os
from pathlib import Path
import re
import signal
import subprocess
import sys

CONTRACT = 'proposal-0012-candidate-2'
UINT_MAX = 9007199254740991
EDITION = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')
SAFE = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]*\Z')
OPERATIONS = {'inspect': ('inspect', None), 'validateD': ('D', 'unresolved-document'), 'validateG': ('G', 'unresolved-document'), 'resolveG': ('G', 'resolved-graph'), 'validateR': ('R', 'unresolved-document'), 'exchange': ('exchange', None), 'lossyExchange': ('exchange', None)}
D_RULES = set('P-SYNTAX P-SHAPE D-IDENTITY D-OWNER D-REFERENCE D-RELATION D-CYCLE D-EXPORT D-AGENT D-DEFERRAL D-DEPENDENCY D-INTEGRITY X-MODE'.split())
G_RULES = set('P-SHAPE X-MODE G-TARGET G-PATH G-DATA G-APPROVAL'.split())
R_RULES = {'P-SHAPE', 'X-MODE', 'R-REQUIREMENT', 'R-SELECTION'}
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


def array(value):
    demand(isinstance(value, list), 'expected array')


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


def location(loc, input_id, source, parsed, existing=True):
    demand(isinstance(loc, dict) and len(loc) == 1, 'closed Location')
    if 'pointer' in loc:
        pointer(loc['pointer'])
        if existing:
            demand(parsed[input_id] is not None and loc['pointer'] in parsed[input_id].spans, 'location is not a source value')
    else:
        record(loc, 'byte')
        demand(uint(loc['byte']) <= len(source[input_id]), 'byte location outside input')


def missing_id(state, tree):
    """Recover only an unambiguous named Requirement id, not its meaning."""
    runtime = tree.get('runtime') if isinstance(tree, dict) else None
    reqs = runtime.get('requirements', []) if isinstance(runtime, dict) else []
    ids = {r['id'] for r in reqs if isinstance(r, dict) and isinstance(r.get('id'), str)} if isinstance(reqs, list) else set()
    detail = state['detail']
    if detail in ids: return detail
    matched = [i for i in ids if json.dumps(i, ensure_ascii=False) in detail or re.search(r'(?<![\w/.-])' + re.escape(i) + r'(?![\w/.-])', detail)]
    demand(len(matched) == 1, 'missing-claim detail does not name one unambiguous Requirement id')
    return matched[0]


def state_key(state, tree):
    out = {k: state[k] for k in ('input','pointer','state')}
    if state['state'] == 'absent' and state['pointer'] == '/runtime/selection/evidence':
        out['requirement'] = missing_id(state, tree)
    return out


def rules_for(result, operation):
    unit = result['unit']
    if unit == 'D': return D_RULES
    if unit == 'G':
        if result['input'] != 'primary': return {'P-SHAPE','G-TARGET'}
        return G_RULES | ({'G-RESOLVE'} if operation == 'resolveG' else set())
    if unit == 'R': return R_RULES
    return {'P-SYNTAX'} if unit == 'inspect' else {'E-LOSS'} if operation == 'lossyExchange' else {'E-PRESERVE'}


def validate_report(response, case, source):
    record(response, 'report artifacts')
    r = response['report']; op = case['operation']; unit, phase = OPERATIONS[op]
    record(r, 'contract processor operation inputs results inventory losses outputs')
    demand(r['contract'] == CONTRACT and r['operation'] == op, 'report edition/operation mismatch')
    edition(r['processor'])
    for k in ('inputs','results','losses','outputs'): array(r[k])
    input_order = ['primary'] + sorted(k for k in source if k != 'primary')
    demand(len(r['inputs']) == len(source), 'input boundary size mismatch')
    for item in r['inputs'] + r['outputs']:
        record(item, 'id sha256'); text(item['id']); text(item['sha256'])
        demand(HASH.fullmatch(item['sha256']), 'invalid hash spelling')
    demand(r['inputs'] == [{'id': i, 'sha256': digest(source[i])} for i in input_order], 'input order/hash/boundary mismatch')
    parsed = {}
    for i, data in source.items():
        try: parsed[i] = JsonSource(data)
        except (ValueError, UnicodeError, decimal.InvalidOperation, RecursionError): parsed[i] = None
    results = r['results']; demand(results, 'missing Result')
    result_ids = []
    for result in results:
        record(result, 'input unit phase verdict findings checks')
        demand(result['input'] in source, 'unknown Result input')
        demand(result['verdict'] in RANK, 'unknown verdict')
        array(result['findings']); array(result['checks'])
        result_ids.append((result['input'],result['unit'],result['phase']))
    demand(len(set(result_ids)) == len(result_ids), 'duplicate Result')
    requested = ('primary', unit, phase)
    demand(result_ids[-1] == requested, 'requested Result missing or not last')
    if unit not in {'G','R'}:
        demand(result_ids == [requested], 'unrequested Result')
    else:
        demand(result_ids[0] == ('primary','D','unresolved-document'), 'missing primary D prerequisite')
        middle = result_ids[1:-1]
        if op != 'resolveG': demand(not middle, 'unexpected annex Results')
        annex_d = [i for i,u,p in middle if u == 'D' and p == 'unresolved-document' and i != 'primary']
        annex_g = [i for i,u,p in middle if u == 'G' and p == 'resolved-graph' and i != 'primary']
        demand(len(annex_d) + len(annex_g) == len(middle), 'invalid Result unit/phase')
        demand(annex_d == sorted(annex_d), 'annex D Results not sorted')
        demand(middle == [(i,'D','unresolved-document') for i in annex_d] + [(i,'G','resolved-graph') for i in annex_g], 'annex Result stage order')
        demand(set(annex_g) <= set(annex_d), 'annex G missing D prerequisite')
    # Check scope, duplicates, ordering and verdict bookkeeping, never graph validity.
    for result in results:
        input_id = result['input']; executed = rules_for(result, op)
        boundaries = dict(BOUNDARY) if result['unit'] in {'D','G','R'} else {}
        if result['unit'] == 'R': boundaries.update(R_BOUNDARY)
        prior = []
        if result['unit'] in {'G','R'}:
            if input_id == 'primary': prior = [x for x in results[:-1] if x['unit'] in {'D','G'}]
            else: prior = [x for x in results if x['unit'] == 'D' and x['input'] == input_id]
        d_failed = input_id == 'primary' and result['unit'] in {'G','R'} and any(x['unit'] == 'D' and x['verdict'] != 'pass' for x in prior)
        allowed = executed | set(boundaries) | ({'P-PREREQUISITE'} if d_failed else set())
        seen = []
        for check in result['checks']:
            record(check, 'rule state locations'); text(check['rule']); array(check['locations'])
            demand(check['rule'] in allowed and check['state'] in {'completed','blocked','excluded'}, 'Check rule/state outside requested scope')
            seen.append((check['rule'],check['state']))
            for loc in check['locations']:
                location(loc,input_id,source,parsed,existing=False)
                if 'pointer' in loc and loc['pointer'] not in {'','/graphs','/runtime','/runtime/selection'}:
                    demand(parsed[input_id] is not None and loc['pointer'] in parsed[input_id].spans, 'Check location is not an observed record')
            unique(check['locations'], 'Check location')
            demand(check['locations'] == sorted(check['locations'],key=loc_key), 'Check locations not sorted')
            demand(check['locations'] == [] if check['state'] == 'completed' else bool(check['locations']), 'Check locations/state mismatch')
            if check['rule'] in boundaries:
                demand(check == {'rule':check['rule'],'state':'excluded','locations':[{'pointer':boundaries[check['rule']]}]}, 'documentary exclusion mismatch')
            if check['rule'] == 'P-PREREQUISITE':
                demand(check['state'] == 'blocked' and check['locations'] == [{'pointer':''}], 'invalid prerequisite Check')
        demand(len(seen) == len(set(seen)), 'duplicate Check rule/state')
        demand(seen == sorted(seen), 'Checks not sorted by rule/state')
        demand({rule for rule,state in seen} == allowed, 'missing rule coverage in Result')
        findings = result['findings']; keys = []
        for f in findings:
            record(f, 'rule location outcome details'); text(f['details'])
            demand(f['rule'] in executed, 'Finding rule outside executed scope')
            outcomes = {'fail'}
            if f['rule'] in {'D-INTEGRITY','E-PRESERVE'}: outcomes.add('inconclusive')
            if f['rule'] in {'X-MODE','G-RESOLVE'}: outcomes |= {'unsupported','inconclusive'}
            if f['rule'] == 'D-DEFERRAL': outcomes.add('deferred')
            demand(f['outcome'] in outcomes, 'Finding outcome outside rule contract')
            location(f['location'], input_id, source, parsed, existing=f['rule'] not in {'E-LOSS','E-PRESERVE'})
            demand(('byte' in f['location']) == (f['rule'] == 'P-SYNTAX'), 'Finding location kind')
            demand((f['rule'],'completed') in seen, 'Finding has no completed rule Check')
            keys.append((f['rule'],canonical(f['location'])))
        demand(len(keys) == len(set(keys)), 'duplicate Finding tuple')
        rank = max([0] + [RANK[f['outcome']] for f in findings if f['outcome'] != 'deferred'] + [RANK[x['verdict']] for x in prior] + [1 for rule,state in seen if state == 'blocked'])
        demand(RANK[result['verdict']] == rank, 'Result verdict disagrees with findings/checks/prerequisites')
    inventory = r['inventory']; record(inventory, 'tree states opaque'); array(inventory['states']); array(inventory['opaque'])
    demand(canonical(inventory['tree']) == canonical(parsed['primary'].tree if parsed['primary'] else None), 'inventory tree differs from exact source JSON')
    observed_inputs={'primary'} | {x['input'] for x in results if x['unit']=='D' and op=='resolveG'}
    state_keys = []
    for state in inventory['states']:
        record(state, 'input pointer state detail'); text(state['detail']); pointer(state['pointer'])
        demand(state['input'] in observed_inputs and state['state'] in {'absent','unknown','declared','unchecked'}, 'State scope/domain')
        state_keys.append(state_key(state, inventory['tree']))
    unique(state_keys, 'State tuple')
    for input_id in observed_inputs:
        src=parsed[input_id]
        if src and isinstance(src.tree,dict):
            for field in ('graphs','runtime'):
                selected=input_id=='primary' and (field=='graphs' and unit=='G' or field=='runtime' and unit=='R')
                expected_state='absent' if field not in src.tree else 'declared' if selected else 'unchecked'
                entries=[s for s in inventory['states'] if s['input']==input_id and s['pointer']=='/'+field]
                demand(len(entries)==1 and entries[0]['state']==expected_state, 'container State missing or inconsistent')
    if op in {'inspect','exchange','lossyExchange'}:
        entries=[s for s in inventory['states'] if s['input']=='primary' and s['pointer']=='/dependencies']
        demand(len(entries)==1, 'dependency inventory State missing')
        src=parsed['primary']
        if src and isinstance(src.tree,dict) and 'dependencies' not in src.tree:
            demand(entries[0]['state']=='absent', 'absent dependency inventory mismatch')
        elif not src or not isinstance(src.tree,dict) or not isinstance(src.tree.get('dependencies'),list):
            demand(entries[0]['state']=='unchecked', 'unreadable dependency inventory mismatch')
    demand(all(x['input'] in observed_inputs for x in inventory['opaque']), 'Slice outside observed unit inputs')
    validate_slices(inventory['opaque'], source, parsed, op)
    for state in inventory['states']:
        for part in inventory['opaque']:
            if part['pointer'] and state['input']==part['input']:
                demand(not state['pointer'].startswith(part['pointer']+'/'), 'State discovered inside opaque Slice')
        for parent in inventory['states']:
            if parent['input']==state['input'] and parent['state']=='absent' and parent['pointer']!='/runtime/selection/evidence':
                demand(not state['pointer'].startswith(parent['pointer']+'/'), 'State below absent parent')
    for loss in r['losses']:
        record(loss, 'input location information reason permission')
        demand(op == 'lossyExchange' and loss['input'] in source and loss['permission'] is None, 'Loss outside operation/boundary')
        text(loss['information']); text(loss['reason'])
        location(loss['location'],loss['input'],source,parsed,existing=False)
    unique(r['losses'], 'Loss')
    demand(bool(r['losses']) == (op == 'lossyExchange'), 'missing or unexpected Loss records')
    demand(isinstance(response['artifacts'],dict), 'artifacts must be a map')
    artifacts = {}
    for i, encoded in response['artifacts'].items():
        text(i); text(encoded, empty=True)
        artifacts[i] = base64.b64decode(encoded,validate=True)
    unique([x['id'] for x in r['outputs']], 'OutputRecord id')
    demand({x['id']:x['sha256'] for x in r['outputs']} == {i:digest(data) for i,data in artifacts.items()}, 'output hashes or boundary differ from delivered bytes')
    return parsed, artifacts


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


def validate_slices(slices, source, parsed, operation):
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
        if parsed[i] and (i=='primary' or parts):
            _,required=opaque_boundaries(parsed[i],operation,i)
            demand(required <= {p for _,_,p in parts}, 'missing maximal opaque boundary')


def finding_rows(report):
    return [dict(input=r['input'],unit=r['unit'],phase=r['phase'],rule=f['rule'],location=f['location'],outcome=f['outcome']) for r in report['results'] for f in r['findings']]


def check_rows(report):
    return [dict(input=r['input'],unit=r['unit'],phase=r['phase'],**c) for r in report['results'] for c in r['checks']]


def observe(case, response, source):
    try:
        _, artifacts = validate_report(response,case,source)
        expected=case['expected']; r=response['report']; errors=[]
        actual=[{k:v[k] for k in ('input','unit','phase','verdict')} for v in r['results']]
        if any(not contains(actual,x) for x in expected['results']): errors.append('required Result differs from oracle')
        findings=finding_rows(r); ef=expected['findings']; wanted=ef['items']
        if ef['mode']=='exact':
            # The manifest's exact tuple shape omits phase; no field is silently defaulted.
            keys=('input','unit','rule','location','outcome')
            if {canonical({k:x[k] for k in keys}) for x in findings} != {canonical(x) for x in wanted}: errors.append('findings differ from exact oracle')
        elif any(not contains(findings,x) for x in wanted): errors.append('required Finding missing')
        for target in expected['checks']:
            metadata={k:v for k,v in target.items() if k!='locations'}
            matches=[c for c in check_rows(r) if contains([c],metadata)]
            if not any({canonical(x) for x in target['locations']} <= {canonical(x) for x in c['locations']} for c in matches): errors.append('required Check or location missing: '+target['rule'])
        states=r['inventory']['states']
        for target in expected['states']:
            metadata={k:v for k,v in target.items() if k!='detailRequirement'}
            matches=[s for s in states if contains([s],metadata)]
            if not matches or ('detailRequirement' in target and not any(missing_id(s,r['inventory']['tree'])==target['detailRequirement'] for s in matches)): errors.append('required State missing: '+target['pointer'])
        for target in expected['absentStates']:
            if any(s['input']==target['input'] and s['pointer'].startswith(target['pointerPrefix']) for s in states): errors.append('forbidden State: '+target['pointerPrefix'])
        for target in expected['opaque']:
            if not contains(r['inventory']['opaque'],target): errors.append('required opaque Slice missing: '+target['pointer'])
        for target in expected['absentOpaque']:
            if contains(r['inventory']['opaque'],target): errors.append('forbidden opaque Slice: '+target['pointer'])
        if expected['preservation']=='exact-input-boundary':
            if artifacts != source: errors.append('output bytes or boundary changed')
        elif artifacts or r['outputs']: errors.append('unexpected output')
        if 'losses' in expected:
            if len(r['losses'])!=len(expected['losses']) or any(not contains(r['losses'],x) for x in expected['losses']): errors.append('prospective losses differ from oracle')
        return errors
    except (ValueError,TypeError,KeyError,IndexError,OverflowError,RecursionError,decimal.InvalidOperation) as exc:
        return ['invalid response: '+str(exc)]


def loss_key(loss):
    if loss['input']=='primary' and loss['location']=={'pointer':''} and loss['information']=='unspecified requested loss':
        return {k:v for k,v in loss.items() if k!='reason'}
    return loss


def comparison(response):
    r=response['report']
    return {
        'contract':r['contract'], 'operation':r['operation'],
        'inputs':canonical(r['inputs']),
        'results':frozenset(canonical({k:v[k] for k in ('input','unit','phase','verdict')}) for v in r['results']),
        'findings':frozenset(canonical(x) for x in finding_rows(r)),
        'checks':frozenset(canonical(x) for x in check_rows(r)),
        'states':frozenset(canonical(state_key(s,r['inventory']['tree'])) for s in r['inventory']['states']),
        'opaque':frozenset(canonical(x) for x in r['inventory']['opaque']),
        'tree':canonical(r['inventory']['tree']),
        'losses':frozenset(canonical(loss_key(x)) for x in r['losses']),
        'outputs':frozenset(canonical(x) for x in r['outputs']),
        'artifacts':tuple(sorted((i,base64.b64decode(v,validate=True)) for i,v in response['artifacts'].items()))}


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


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('manifest',type=Path,nargs='?',default=Path(__file__).resolve().parent/'fixtures/manifest.json')
    ap.add_argument('--reader',action='append',required=True,help='JSON array [safe label, executable, arguments...]')
    ap.add_argument('--reports',type=Path,required=True)
    ap.add_argument('--timeout',type=float,default=30,help='seconds per reader/case, default 30, maximum 300')
    ap.add_argument('--case',action='append',dest='case_names',help='run only this named case; repeatable')
    args=ap.parse_args(argv)
    readers=[]
    try:
        demand(math.isfinite(args.timeout) and 0<args.timeout<=300,'timeout must be in (0,300]')
        for raw in args.reader:
            entry=json.loads(raw)
            demand(isinstance(entry,list) and len(entry)>=2 and all(isinstance(x,str) and x for x in entry),'reader requires label and argv')
            demand(SAFE.fullmatch(entry[0]),'unsafe reader label')
            readers.append(entry)
        demand(len(readers)>=2,'at least two readers required')
        demand(len({r[0] for r in readers})==len(readers),'duplicate reader label')
        manifest=load(args.manifest.read_bytes())
        demand(manifest['contract']==CONTRACT and manifest['format']=='agsdl-candidate-corpus-1','wrong corpus edition/format')
        names=[c['name'] for c in manifest['cases']]
        demand(len(set(names))==len(names) and all(SAFE.fullmatch(n) for n in names),'unsafe or duplicate case name')
        demand(not args.case_names or set(args.case_names)<=set(names),'unknown selected case')
        # New/empty destination prevents accidental overwrite of previous evidence.
        args.reports.mkdir(parents=True,exist_ok=True)
        demand(not any(args.reports.iterdir()),'reports directory must be empty')
    except (ValueError,TypeError,KeyError,OSError) as exc:
        ap.error(str(exc))
    failures=[]; blocked=[]; completed=0
    for case in manifest['cases']:
        if args.case_names and case['name'] not in args.case_names: continue
        name=case['name']
        if case['status']=='blocked':
            blocked.append({'case':name,'blocker':case.get('blocker','unspecified')});continue
        observations={}
        try:
            demand(case['status']=='ready','unknown case status')
            def read_artifact(metadata):
                path=(args.manifest.parent/metadata['path']).resolve()
                demand(path.is_relative_to(args.manifest.parent.resolve()),'artifact escapes manifest directory')
                data=path.read_bytes();demand(digest(data)==metadata['sha256'],'fixture hash mismatch');return data
            primary=read_artifact(case['primary']);annexes={k:read_artifact(v) for k,v in case['annexes'].items()}
            source={'primary':primary,**{'annex/'+k:v for k,v in annexes.items()}}
            request={'operation':case['operation'],'primary':base64.b64encode(primary).decode(),'annexes':{k:base64.b64encode(v).decode() for k,v in annexes.items()}}
            if 'losses' in case:
                # Manifest loss byte offsets decode as Decimal; convert exact bounded integers only.
                request['losses']=case['losses']
            wire=json.dumps(request,ensure_ascii=False,default=lambda x:uint(x)).encode('utf-8')
        except (ValueError,TypeError,KeyError,OSError) as exc:
            failures.append({'case':name,'issue':str(exc)});continue
        for label,*command in readers:
            stdout=b'';stderr=b''
            try:
                code,stdout,stderr,error=run_reader(command,wire,args.timeout)
                if error: raise ValueError(error)
                demand(code==0,'reader exit '+str(code))
                response=load(stdout)
                errors=observe(case,response,source)
                failures.extend({'case':name,'reader':label,'issue':e} for e in errors)
                if not errors: observations[label]=comparison(response)
            except (ValueError,TypeError,KeyError,OSError,decimal.InvalidOperation,RecursionError) as exc:
                failures.append({'case':name,'reader':label,'issue':str(exc)})
            finally:
                (args.reports/(name+'.'+label+'.stdout')).write_bytes(stdout)
                (args.reports/(name+'.'+label+'.stderr')).write_bytes(stderr)
        if len(observations)==len(readers):
            first=readers[0][0]
            for label in [r[0] for r in readers[1:]]:
                for key,value in observations[first].items():
                    if value!=observations[label][key]:failures.append({'case':name,'reader':label,'issue':'cross-reader mismatch: '+key})
        completed+=1
    summary={'cases':completed,'readers':[r[0] for r in readers],'blocked':blocked,'failures':failures,'scope':'report contract and corpus assertions; no AgSDL semantic validation'}
    (args.reports/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return int(bool(failures or blocked))


if __name__=='__main__':
    sys.exit(main())
