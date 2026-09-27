"""Static validator for agsdl-exp-0016-c2; no execution or transformation."""
import hashlib
import importlib.util
from pathlib import Path
import re
import sys
from collections import Counter, defaultdict

# Reuse only the official lexical parser, never its semantic implementation.
_LEXICAL_PATH = Path(__file__).resolve().parents[4] / 'tooling/readers/python/agsdl_reader/lossless.py'
_spec = importlib.util.spec_from_file_location('_kiss_python_lossless', _LEXICAL_PATH)
lexical = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = lexical
_spec.loader.exec_module(lexical)

EDITION = 'agsdl-exp-0016-c2'
PROCESSOR = {'identity': 'agsdl-experimental/python-kiss', 'version': '2'}
UNITS = ('syntax', 'core', 'flow', 'configuration', 'compatibility', 'external')
SUBJECTS = ('', '', '/graphs', '/configurations', '/selected', '/extensions')
CATALOGS = ('principals', 'instructions', 'interfaces', 'agents', 'tools', 'graphs')
MISSING = object()
ptr = lexical.pointer


def field(obj, name, default=MISSING):
    return obj.get(name, default) if isinstance(obj, dict) else default


def is_id(value):
    return isinstance(value, str) and re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]*', value) is not None


def edition(value):
    # Identity projection: extra-key SHAPE failures do not hide readable fields.
    return all(isinstance(field(value, k), str) and field(value, k)
               for k in ('identity', 'version'))


def edition_key(value):
    return (value['identity'], value['version'])


def ref_id(value):
    target = field(value, 'ref')
    return target if is_id(target) else None


def step_kind(step):
    kind = field(step, 'kind')
    return kind if kind in ('invoke', 'approval', 'end') else None


def record(required, optional=None):
    return ('record', required, optional or {})


def array(item, minimum=0):
    return ('array', item, minimum)


def mapping(item, minimum=0):
    return ('map', item, minimum)


def enum(*values):
    return ('enum', values)


E = record({'identity': 'text', 'version': 'text'})
REF = record({'ref': 'id'})
PORTS = mapping(enum('string', 'boolean', 'json'))
INSTRUCTIONS = record({'target': enum('Agent'), 'at': enum('before-invoke'),
                       'format': E, 'body': 'text'})
OPERATION = record({'direction': enum('inbound', 'outbound', 'bidirectional'),
                    'mode': enum('request-response'), 'inputs': PORTS, 'outputs': PORTS,
                    'effects': enum('none', 'external', 'unknown')})
INTERFACE = record({'operations': mapping(OPERATION, 1)})
AGENT = record({'instructions': array(record({'id': 'id', 'content': ('choice', INSTRUCTIONS)}), 1),
                'interface': ('choice', INTERFACE)}, {'principal': REF, 'tools': array(REF)})
TOOL = record({'inputs': PORTS, 'outputs': PORTS, 'effects': enum('none', 'external', 'unknown'),
               'failures': array('text'), 'requires': array(E)})
CLAIM = record({'capability': E, 'status': enum('supported', 'unsupported', 'unknown'),
                'evidence': ('nullable', 'hash')})
SCOPE = record({'action': 'text', 'resources': array('text', 1), 'context': 'binding'})
INVOKE = record({'id': 'id', 'kind': enum('invoke'), 'agent': REF, 'operation': 'id',
                 'bindings': mapping('binding'), 'success': 'id', 'failure': 'id'}, {'scope': SCOPE})
APPROVAL = record({'id': 'id', 'kind': enum('approval'), 'call': 'id', 'approvers': array(REF, 1),
                   'validForMs': 'positive', 'timeoutMs': 'positive', 'approved': 'id',
                   'denied': 'id', 'failure': 'id'})
SUCCESS = record({'id': 'id', 'kind': enum('end'), 'outcome': enum('success'),
                  'bindings': mapping('binding')})
FAILURE = record({'id': 'id', 'kind': enum('end'), 'outcome': enum('failure', 'denied'), 'reason': 'text'})
GRAPH = record({'entry': 'id', 'inputs': PORTS, 'outputs': PORTS, 'steps': array('step', 1)})
APPLICATION = record({'slot': 'id', 'adapter': E, 'parameters': 'json'})
TOOL_BINDING = record({'tool': REF, 'implementation': ('nullable', E), 'parameters': 'json',
                       'claims': array(CLAIM)})
AGENT_BINDING = record({'agent': REF, 'engine': ('nullable', E), 'parameters': 'json',
                        'requires': array(E), 'claims': array(CLAIM),
                        'applications': array(APPLICATION), 'tools': array(TOOL_BINDING)},
                       {'settings': record({'format': E, 'value': 'json'})})
CONFIGURATION = record({'graph': REF, 'agents': array(AGENT_BINDING)})
EXTENSION = record({'edition': E, 'use': enum('required', 'annotation'), 'payload': 'json'})
CORE_FIELDS = {'edition': enum(EDITION), 'agents': mapping(AGENT)}
CORE_OPTIONAL = {'principals': mapping(record({'description': 'text'})),
                 'instructions': mapping(INSTRUCTIONS), 'interfaces': mapping(INTERFACE),
                 'tools': mapping(TOOL), 'annotations': 'json', 'graphs': 'json',
                 'configurations': 'json', 'selected': 'json', 'extensions': 'json'}


def shape_errors(value, schema, path=''):
    """Yield candidate SHAPE locations; opaque Number wrappers are not objects."""
    if schema == 'json':
        return
    if schema == 'step':
        kind = step_kind(value)
        if kind is None:
            yield path
            if isinstance(value, dict) and 'id' in value:
                yield from shape_errors(value['id'], 'id', ptr(path, 'id'))
            return
        if kind == 'end' and field(value, 'outcome') not in ('success', 'failure', 'denied'):
            yield path
            if 'id' in value:
                yield from shape_errors(value['id'], 'id', ptr(path, 'id'))
            return
        schema = INVOKE if kind == 'invoke' else APPROVAL if kind == 'approval' else (
            SUCCESS if value['outcome'] == 'success' else FAILURE)
    if schema == 'binding':
        if not isinstance(value, dict) or ('input' in value) == ('step' in value):
            yield path
            return
        schema = record({'input': 'id'}) if 'input' in value else record({'step': 'id', 'port': 'id'})
    if isinstance(schema, str):
        good = False
        if schema == 'text':
            good = isinstance(value, str) and bool(value)
        elif schema == 'id':
            good = is_id(value)
        elif schema == 'hash':
            good = isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None
        elif schema == 'positive':
            number = lexical.integer(value)
            good = number is not None and number > 0
        if not good:
            yield path
        return
    tag = schema[0]
    if tag == 'nullable':
        if value is not None:
            yield from shape_errors(value, schema[1], path)
    elif tag == 'enum':
        if not isinstance(value, str) or value not in schema[1]:
            yield path
    elif tag == 'choice':
        if not isinstance(value, dict) or ('ref' in value) == ('value' in value):
            yield path
        else:
            selected = REF if 'ref' in value else record({'value': schema[1]})
            yield from shape_errors(value, selected, path)
    elif tag == 'record':
        if not isinstance(value, dict):
            yield path
            return
        required, optional = schema[1:]
        if any(k not in value for k in required):
            yield path
        fields = dict(required, **optional)
        for name, item in value.items():
            if name not in fields:
                yield ptr(path, name)
            else:
                yield from shape_errors(item, fields[name], ptr(path, name))
    elif tag in ('array', 'map'):
        expected = list if tag == 'array' else dict
        if not isinstance(value, expected):
            yield path
            return
        if len(value) < schema[2]:
            yield path
        entries = enumerate(value) if tag == 'array' else value.items()
        for key, item in entries:
            if tag == 'map' and not is_id(key):
                yield ptr(path, key)
            yield from shape_errors(item, schema[1], ptr(path, key))


def shaped(value, schema):
    return not any(True for _ in shape_errors(value, schema))


class Validator:
    def __init__(self, raw):
        self.raw = raw
        self.doc = None
        self.diagnostics = {u: set() for u in UNITS}
        self.gaps = {u: defaultdict(set) for u in UNITS}
        self.presence = {u: 'undetermined' for u in UNITS}
        self.presence['syntax'] = 'present'
        self.catalog = defaultdict(list)
        self.catalog_complete = True

    def fail(self, unit, code, path, outcome='fail'):
        self.diagnostics[unit].add((code, path, outcome))

    def gap(self, unit, code, path, cause='shape'):
        self.gaps[unit][code, path].add(cause)

    def shape(self, unit, value, schema, path):
        for bad in shape_errors(value, schema, path):
            self.fail(unit, 'SHAPE', bad)

    def lookup(self, ref, kind):
        target = ref_id(ref)
        if target is None:
            return None, None, 'shape'
        if not self.catalog_complete:
            return None, None, 'reference'
        entries = self.catalog.get(target, [])
        if len(entries) != 1:
            return None, None, 'reference'
        cat, path, value = entries[0]
        if cat != kind:
            return None, None, 'reference'
        return value, path, None

    def check_ref(self, unit, ref, kind, path):
        target = ref_id(ref)
        if target is None:
            self.gap(unit, 'REF', path)
        elif not self.catalog_complete or len(self.catalog.get(target, [])) > 1:
            self.gap(unit, 'REF', path, 'reference')
        elif not self.catalog.get(target) or self.catalog[target][0][0] != kind:
            self.fail(unit, 'REF', path)

    def choice(self, value, kind, path):
        if not isinstance(value, dict) or ('ref' in value) == ('value' in value):
            return None, path, 'shape'
        if 'ref' in value:
            return self.lookup(value, kind)
        return value['value'], ptr(path, 'value'), None

    def unique(self, unit, value, schema, path, key=lambda x: x):
        if not shaped(value, array(schema)):
            self.gap(unit, 'UNIQUE', path)
        elif len({key(v) for v in value}) != len(value):
            self.fail(unit, 'UNIQUE', path)

    def refs(self, unit, value, kind, path):
        if not isinstance(value, list):
            self.gap(unit, 'REF', path)
        else:
            for i, item in enumerate(value):
                self.check_ref(unit, item, kind, ptr(path, i))

    def core(self):
        d = self.doc
        self.shape('core', d, record(CORE_FIELDS, CORE_OPTIONAL), '')
        for cat in CATALOGS:
            values = d.get(cat, MISSING if cat == 'agents' else {})
            if not isinstance(values, dict):
                self.catalog_complete = False
                self.gap('core', 'ID', ptr('', cat) if cat in d else '')
                continue
            for name, value in values.items():
                path = ptr(ptr('', cat), name)
                if not is_id(name):
                    self.catalog_complete = False
                    self.gap('core', 'ID', path)
                else:
                    self.catalog[name].append((cat, path, value))
        for entries in self.catalog.values():
            if len(entries) > 1:
                for _, path, _ in entries:
                    self.fail('core', 'ID', path)
        agents = d.get('agents', MISSING)
        if not isinstance(agents, dict):
            path = '/agents' if 'agents' in d else ''
            for code in ('REF', 'SLOT-ID', 'UNIQUE'):
                self.gap('core', code, path)
        else:
            for name, agent in agents.items():
                p = ptr('/agents', name)
                if not isinstance(agent, dict):
                    for code in ('REF', 'SLOT-ID', 'UNIQUE'):
                        self.gap('core', code, p)
                    continue
                slots = agent.get('instructions', MISSING)
                sp = ptr(p, 'instructions') if slots is not MISSING else p
                if not isinstance(slots, list):
                    self.gap('core', 'SLOT-ID', sp)
                    self.gap('core', 'REF', sp)
                else:
                    ids = [field(s, 'id') for s in slots]
                    known = [x for x in ids if is_id(x)]
                    if len(known) != len(ids):
                        self.gap('core', 'SLOT-ID', sp)
                    if len(set(known)) != len(known):
                        self.fail('core', 'SLOT-ID', sp)
                    for i, slot in enumerate(slots):
                        cp = ptr(ptr(sp, i), 'content') if isinstance(slot, dict) and 'content' in slot else ptr(sp, i)
                        self.choice_ref(field(slot, 'content'), 'instructions', cp)
                ip = ptr(p, 'interface') if 'interface' in agent else p
                self.choice_ref(agent.get('interface', MISSING), 'interfaces', ip)
                if 'principal' in agent:
                    self.check_ref('core', agent['principal'], 'principals', ptr(p, 'principal'))
                if 'tools' in agent:
                    self.refs('core', agent['tools'], 'tools', ptr(p, 'tools'))
                    self.unique('core', agent['tools'], REF, ptr(p, 'tools'), ref_id)
        tools = d.get('tools', {})
        if not isinstance(tools, dict):
            self.gap('core', 'UNIQUE', '/tools')
        else:
            for name, tool in tools.items():
                p = ptr('/tools', name)
                for key, schema, projector in (('requires', E, edition_key), ('failures', 'text', lambda x: x)):
                    value = field(tool, key)
                    self.unique('core', value, schema, ptr(p, key) if value is not MISSING else p, projector)

    def choice_ref(self, value, kind, path):
        if not isinstance(value, dict) or ('ref' in value) == ('value' in value):
            self.gap('core', 'REF', path)
        elif 'ref' in value:
            self.check_ref('core', value, kind, path)

    def external(self):
        if 'extensions' not in self.doc:
            return
        values = self.doc['extensions']
        self.shape('external', values, array(EXTENSION), '/extensions')
        if not isinstance(values, list):
            for code in ('UNIQUE', 'REQUIRED'):
                self.gap('external', code, '/extensions')
            return
        identities = []
        for i, value in enumerate(values):
            p = ptr('/extensions', i)
            identity = field(value, 'edition')
            if edition(identity):
                identities.append(edition_key(identity))
            else:
                self.gap('external', 'UNIQUE', '/extensions')
            use = field(value, 'use')
            if not edition(identity) or use not in ('required', 'annotation'):
                self.gap('external', 'REQUIRED', p)
            elif use == 'required':
                self.fail('external', 'REQUIRED', p, 'unsupported')
                self.gap('external', 'REQUIRED', p, 'unsupported')
        if len(set(identities)) != len(identities):
            self.fail('external', 'UNIQUE', '/extensions')

    def report(self):
        results = []
        for unit, subject in zip(UNITS, SUBJECTS):
            ds = self.diagnostics[unit]
            gs = self.gaps[unit]
            outcomes = {d[2] for d in ds}
            if gs:
                outcomes.add('inconclusive')
            if any('unsupported' in causes for causes in gs.values()):
                outcomes.add('unsupported')
            outcome = next((x for x in ('fail', 'unsupported', 'inconclusive') if x in outcomes),
                           'not-applicable' if self.presence[unit] == 'absent' else 'pass')
            results.append({'unit': unit, 'phase': 'local', 'subject': subject,
                            'presence': self.presence[unit], 'outcome': outcome,
                            'diagnostics': [{'code': c, 'location': p, 'outcome': o} for c, p, o in sorted(ds)],
                            'incomplete': [{'code': c, 'location': p, 'causes': sorted(causes)}
                                           for (c, p), causes in sorted(gs.items())]})
        return {'edition': EDITION, 'processor': dict(PROCESSOR), 'operation': 'validate',
                'input': {'id': 'primary', 'sha256': hashlib.sha256(self.raw).hexdigest()}, 'results': results}

    def operation(self, step, path, diagnose=True):
        agent, ap, cause = self.lookup(field(step, 'agent'), 'agents')
        if cause:
            if diagnose:
                self.gap('flow', 'OPERATION', path, cause)
            return None, agent, cause
        interface, _, cause = self.choice(field(agent, 'interface'), 'interfaces', ptr(ap, 'interface'))
        operations = field(interface, 'operations')
        name = field(step, 'operation')
        if cause or not isinstance(operations, dict) or not all(is_id(k) for k in operations) or not is_id(name):
            cause = cause or 'shape'
            if diagnose:
                self.gap('flow', 'OPERATION', path, cause)
            return None, agent, cause
        if name not in operations:
            if diagnose:
                self.fail('flow', 'OPERATION', path)
            return None, agent, 'reference'
        op = operations[name]
        direction = field(op, 'direction')
        if direction not in ('inbound', 'outbound', 'bidirectional'):
            if diagnose:
                self.gap('flow', 'OPERATION', path)
        elif direction == 'outbound':
            if diagnose:
                self.fail('flow', 'OPERATION', path)
            return None, agent, 'reference'
        return op, agent, None

    def flow(self):
        if 'graphs' not in self.doc:
            return
        graphs = self.doc['graphs']
        self.shape('flow', graphs, mapping(GRAPH), '/graphs')
        if not isinstance(graphs, dict):
            self.flow_container_gaps('/graphs')
            return
        for name, graph in graphs.items():
            p = ptr('/graphs', name)
            GraphChecks(self, graph, p).run()

    def flow_container_gaps(self, path):
        for code in ('REF', 'STEP-ID', 'PATH', 'OPERATION', 'DATA', 'ACTOR', 'APPROVAL', 'APPROVAL-DATA', 'UNIQUE'):
            self.gap('flow', code, path)

    def run(self):
        try:
            self.doc = lexical.Parser(self.raw).parse()
        except lexical.SyntaxFailure:
            self.fail('syntax', 'SYNTAX', '')
            for unit in UNITS[1:]:
                self.gap(unit, 'CHECKS', '')
            return self.report()
        if not isinstance(self.doc, dict):
            self.fail('core', 'SHAPE', '')
            for unit in UNITS[1:]:
                self.gap(unit, 'CHECKS', '')
            return self.report()
        self.presence.update(core='present',
                             flow='present' if 'graphs' in self.doc else 'absent',
                             configuration='present' if 'configurations' in self.doc or 'selected' in self.doc else 'absent',
                             compatibility='present' if 'selected' in self.doc else 'absent',
                             external='present' if 'extensions' in self.doc else 'absent')
        self.core()
        if self.doc.get('edition') != EDITION:
            for unit in UNITS[2:]:
                self.gap(unit, 'CHECKS', '')
            return self.report()
        self.flow()
        ConfigurationChecks(self).run()
        self.external()
        return self.report()


class GraphChecks:
    def __init__(self, validator, graph, path):
        self.v, self.graph, self.path = validator, graph, path
        self.steps = field(graph, 'steps')
        self.index = defaultdict(list)
        self.complete_ids = True
        self.edges = {}
        self.path_ok = False
        self.operations = {}

    def gap(self, code, path, cause='shape'):
        self.v.gap('flow', code, path, cause)

    def fail(self, code, path):
        self.v.fail('flow', code, path)

    def sp(self, i):
        return ptr(ptr(self.path, 'steps'), i)

    def find_step(self, name):
        if not is_id(name):
            return None, None, 'shape'
        if not self.complete_ids:
            return None, None, 'reference'
        entries = self.index.get(name, [])
        if len(entries) != 1:
            return None, None, 'reference'
        i = entries[0]
        return self.steps[i], i, None

    def reachable(self, start, remove=None):
        seen = set()
        pending = [start]
        while pending:
            node = pending.pop()
            if node in seen:
                continue
            seen.add(node)
            for label, target in self.edges.get(node, []):
                if remove != (node, label):
                    pending.append(target)
        return seen

    def path_check(self):
        p = self.path
        entry = field(self.graph, 'entry')
        if not is_id(entry) or not self.complete_ids or any(len(xs) != 1 for xs in self.index.values()):
            self.gap('PATH', p)
            return
        good = True
        for step in self.steps:
            kind, name = step_kind(step), step['id']
            labels = ('success', 'failure') if kind == 'invoke' else (
                ('approved', 'denied', 'failure') if kind == 'approval' else ())
            if kind is None or (kind == 'end' and field(step, 'outcome') not in ('success', 'failure', 'denied')):
                good = False
            edges = []
            for label in labels:
                target = field(step, label)
                if not is_id(target):
                    good = False
                else:
                    edges.append((label, target))
            self.edges[name] = edges
        if not good:
            self.gap('PATH', p)
            return
        if entry not in self.index or any(t not in self.index for edges in self.edges.values() for _, t in edges):
            self.fail('PATH', p)
            return
        # Kahn's algorithm avoids Python recursion for long valid graphs.
        incoming = Counter(t for edges in self.edges.values() for _, t in edges)
        ready = [n for n in self.index if incoming[n] == 0]
        visited = 0
        while ready:
            node = ready.pop()
            visited += 1
            for _, target in self.edges[node]:
                incoming[target] -= 1
                if incoming[target] == 0:
                    ready.append(target)
        if visited != len(self.index) or self.reachable(entry) != set(self.index):
            self.fail('PATH', p)
        else:
            self.path_ok = True

    def data_binding(self, binding, expected, consumer, path, code):
        if not shaped(binding, 'binding'):
            self.gap(code, path)
            return
        if 'input' in binding:
            ports = field(self.graph, 'inputs')
            if not isinstance(ports, dict) or not all(is_id(k) for k in ports):
                self.gap(code, path)
            elif binding['input'] not in ports:
                self.fail(code, path)
            else:
                actual = ports[binding['input']]
                if actual not in ('string', 'boolean', 'json'):
                    self.gap(code, path)
                elif expected is not None and actual != expected:
                    self.fail(code, path)
            return
        producer, i, cause = self.find_step(binding['step'])
        if cause:
            if self.complete_ids and binding['step'] not in self.index:
                self.fail(code, path)
            else:
                self.gap(code, path, cause)
        elif step_kind(producer) is None:
            self.gap(code, path, 'reference')
        elif step_kind(producer) != 'invoke':
            self.fail(code, path)
        else:
            op, _, cause = self.operations[i]
            outputs = field(op, 'outputs')
            if cause:
                self.gap(code, path, cause)
            elif not isinstance(outputs, dict) or not all(is_id(k) for k in outputs):
                self.gap(code, path)
            elif binding['port'] not in outputs:
                self.fail(code, path)
            else:
                actual = outputs[binding['port']]
                if actual not in ('string', 'boolean', 'json'):
                    self.gap(code, path)
                elif expected is not None and actual != expected:
                    self.fail(code, path)
        if not self.path_ok:
            self.gap(code, path, 'path')
        elif consumer in self.reachable(self.graph['entry'], (binding['step'], 'success')):
            self.fail(code, path)

    def data(self, i, consumer=None, path=None, code='DATA'):
        step = self.steps[i]
        p = path or self.sp(i)
        consumer = consumer if consumer is not None else field(step, 'id')
        if step_kind(step) == 'invoke':
            op, _, cause = self.operations[i]
            ports = field(op, 'inputs')
        else:
            ports, cause = field(self.graph, 'outputs'), None
        bindings = field(step, 'bindings')
        if cause:
            self.gap(code, p, cause)
        keys_readable = isinstance(ports, dict) and all(is_id(k) for k in ports)
        bindings_readable = isinstance(bindings, dict) and all(is_id(k) for k in bindings)
        if not keys_readable and not cause:
            self.gap(code, p)
        if not bindings_readable:
            self.gap(code, p)
        if keys_readable and bindings_readable and set(ports) != set(bindings):
            self.fail(code, p)
        if isinstance(bindings, dict):
            for name, binding in bindings.items():
                expected = ports.get(name, MISSING) if keys_readable else MISSING
                if expected is MISSING:
                    expected = None
                elif expected not in ('string', 'boolean', 'json'):
                    self.gap(code, p)
                    expected = None
                self.data_binding(binding, expected, consumer, p, code)
        if step_kind(step) == 'invoke' and 'scope' in step:
            scope = step['scope']
            context = field(scope, 'context')
            self.data_binding(context, 'json', consumer, p, code)
        elif code == 'APPROVAL-DATA':
            self.gap(code, p)

    def actor(self, i):
        step, p = self.steps[i], self.sp(i)
        op, agent, cause = self.operations[i]
        triggers = ['scope' in step]
        unavailable = set()
        effects = field(op, 'effects')
        if cause:
            unavailable.add(cause)
        elif effects not in ('none', 'external', 'unknown'):
            unavailable.add('shape')
        else:
            triggers.append(effects != 'none')
        if not isinstance(agent, dict):
            unavailable.add(cause or 'shape')
        else:
            tools = agent.get('tools', [])
            if not isinstance(tools, list):
                unavailable.add('shape')
            else:
                for ref in tools:
                    tool, _, tc = self.v.lookup(ref, 'tools')
                    te = field(tool, 'effects')
                    if tc:
                        unavailable.add(tc)
                    elif te not in ('none', 'external', 'unknown'):
                        unavailable.add('shape')
                    else:
                        triggers.append(te != 'none')
        for other in self.steps:
            kind = step_kind(other)
            if kind is None:
                unavailable.add('shape')
            elif kind == 'approval':
                call = field(other, 'call')
                if not is_id(call):
                    unavailable.add('shape')
                elif call == field(step, 'id'):
                    triggers.append(True)
        if any(triggers):
            if 'scope' not in step:
                self.fail('ACTOR', p)
            elif not shaped(step['scope'], SCOPE):
                self.gap('ACTOR', p)
            if not isinstance(agent, dict):
                self.gap('ACTOR', p, cause or 'shape')
            elif 'principal' not in agent:
                self.fail('ACTOR', p)
            else:
                _, _, pc = self.v.lookup(agent['principal'], 'principals')
                if pc:
                    self.gap('ACTOR', p, pc)
        elif unavailable:
            for c in unavailable:
                self.gap('ACTOR', p, c)

    def approvals(self):
        groups = defaultdict(list)
        for i, step in enumerate(self.steps):
            if step_kind(step) != 'approval':
                continue
            p = self.sp(i)
            call = field(step, 'call')
            target, ti, cause = self.find_step(call)
            missing = cause and is_id(call) and self.complete_ids and call not in self.index
            wrong_kind = not cause and step_kind(target) in ('approval', 'end')
            if missing or wrong_kind:
                self.fail('APPROVAL', p)
                self.gap('APPROVAL-DATA', p, 'reference')
                continue
            approvers = field(step, 'approvers')
            if shaped(approvers, array(REF, 1)):
                if len({ref_id(x) for x in approvers}) != len(approvers):
                    self.fail('APPROVAL', p)
            else:
                self.gap('APPROVAL', p)
            if cause:
                self.gap('APPROVAL', p, cause)
                self.gap('APPROVAL-DATA', p, cause)
                continue
            if step_kind(target) is None:
                self.gap('APPROVAL', p)
                self.gap('APPROVAL-DATA', p, 'reference')
                continue
            groups[call].append(i)
            self.data(ti, field(step, 'id'), p, 'APPROVAL-DATA')
        for call, indices in groups.items():
            if not self.path_ok:
                for i in indices:
                    self.gap('APPROVAL', self.sp(i), 'path')
                continue
            if not all(shaped(self.steps[i], APPROVAL) for i in indices):
                for i in indices:
                    self.gap('APPROVAL', self.sp(i))
                continue
            names = {self.steps[i]['id'] for i in indices}
            successors = {self.steps[i]['id']: self.steps[i]['approved'] for i in indices}
            incoming = defaultdict(list)
            for source, edges in self.edges.items():
                for label, target in edges:
                    incoming[target].append((source, label))
            firsts = names - set(successors.values())
            bad = len(firsts) != 1
            chain = []
            if not bad:
                current = next(iter(firsts))
                while current in names and current not in chain:
                    chain.append(current)
                    current = successors[current]
                bad = current != call or set(chain) != names
            if not bad:
                if incoming[call] != [(chain[-1], 'approved')]:
                    bad = True
                for pos, name in enumerate(chain):
                    if pos and incoming[name] != [(chain[pos - 1], 'approved')]:
                        bad = True
                    if pos == 0:
                        for source, label in incoming[name]:
                            source_step = self.steps[self.index[source][0]]
                            if step_kind(source_step) == 'approval' and label == 'approved':
                                source_call = field(source_step, 'call')
                                if not is_id(source_call):
                                    for i in indices:
                                        self.gap('APPROVAL', self.sp(i))
                                elif source_call != call:
                                    bad = True
                    gate = self.steps[self.index[name][0]]
                    forbidden = set(chain[pos + 1:]) | {call}
                    if any(self.reachable(gate[label]) & forbidden for label in ('denied', 'failure')):
                        bad = True
                if self.graph['entry'] in set(chain[1:]) | {call}:
                    bad = True
            if bad:
                for i in indices:
                    self.fail('APPROVAL', self.sp(i))

    def run(self):
        if not isinstance(self.graph, dict) or not isinstance(self.steps, list):
            location = ptr(self.path, 'steps') if isinstance(self.graph, dict) and 'steps' in self.graph else self.path
            self.v.flow_container_gaps(location)
            return
        for i, step in enumerate(self.steps):
            name = field(step, 'id')
            if is_id(name):
                self.index[name].append(i)
            else:
                self.complete_ids = False
        if not self.complete_ids:
            self.gap('STEP-ID', ptr(self.path, 'steps'))
        if any(len(xs) > 1 for xs in self.index.values()):
            self.fail('STEP-ID', ptr(self.path, 'steps'))
        self.path_check()
        for i, step in enumerate(self.steps):
            p, kind = self.sp(i), step_kind(step)
            if kind is None:
                for code in ('REF', 'OPERATION', 'DATA', 'ACTOR', 'APPROVAL', 'APPROVAL-DATA', 'UNIQUE'):
                    self.gap(code, p)
            elif kind == 'invoke':
                rp = ptr(p, 'agent') if 'agent' in step else p
                self.v.check_ref('flow', field(step, 'agent'), 'agents', rp)
                self.operations[i] = self.v.operation(step, p)
                if 'scope' in step:
                    scope = step['scope']
                    resources = field(scope, 'resources')
                    if not isinstance(resources, list):
                        self.gap('UNIQUE', ptr(p, 'scope'))
                    elif not shaped(resources, array('text', 1)):
                        self.gap('UNIQUE', ptr(ptr(p, 'scope'), 'resources'))
                    else:
                        self.v.unique('flow', resources, 'text', ptr(ptr(p, 'scope'), 'resources'))
            elif kind == 'approval':
                loc = ptr(p, 'approvers') if 'approvers' in step else p
                self.v.refs('flow', field(step, 'approvers'), 'principals', loc)
            elif field(step, 'outcome') not in ('success', 'failure', 'denied'):
                self.gap('DATA', p)
        for i, step in enumerate(self.steps):
            kind = step_kind(step)
            if kind == 'invoke':
                self.data(i)
                self.actor(i)
            elif kind == 'end' and field(step, 'outcome') == 'success':
                self.data(i)
        self.approvals()


class ConfigurationChecks:
    def __init__(self, validator):
        self.v = validator
        self.selected = None

    def gap(self, code, path, cause='shape', unit='configuration'):
        self.v.gap(unit, code, path, cause)

    def fail(self, code, path, outcome='fail', unit='configuration'):
        self.v.fail(unit, code, path, outcome)

    def projection(self, values, field_name):
        if not isinstance(values, list):
            return [], False, set()
        ids = [ref_id(field(x, field_name)) for x in values]
        counts = Counter(x for x in ids if x is not None)
        return ids, all(x is not None for x in ids), {x for x, n in counts.items() if n > 1}

    def slot_projection(self, agent):
        slots = field(agent, 'instructions')
        if not isinstance(slots, list):
            return [], 'shape'
        names = [field(x, 'id') for x in slots]
        if not all(is_id(x) for x in names):
            return [], 'shape'
        if len(set(names)) != len(names):
            return names, 'reference'
        return names, None

    def content(self, binding, agent, path, parent_cause, selected):
        names, cause = self.slot_projection(agent)
        cause = parent_cause or cause
        applications = field(binding, 'applications')
        supplied = [field(x, 'slot') for x in applications] if isinstance(applications, list) else []
        if not isinstance(applications, list) or not all(is_id(x) for x in supplied):
            cause = cause or 'shape'
        if cause:
            self.gap('CONTENT', path, cause)
            if selected:
                self.gap('ENGINE', path, cause, 'compatibility')
        elif names != supplied:
            self.fail('CONTENT', path)
            if selected:
                self.gap('ENGINE', path, 'reference', 'compatibility')

    def tool_coverage(self, binding, agent, path, parent_cause, selected):
        required = field(agent, 'tools', []) if isinstance(agent, dict) else MISSING
        supplied = field(binding, 'tools')
        required_ids = [ref_id(x) for x in required] if isinstance(required, list) else []
        provided, complete, duplicates = self.projection(supplied, 'tool')
        cause = parent_cause
        if not isinstance(required, list) or any(x is None for x in required_ids) or not complete:
            cause = cause or 'shape'
        if cause:
            self.gap('TOOLS', path, cause)
            if selected:
                self.gap('TOOL', path, cause, 'compatibility')
        elif set(required_ids) != set(provided) or duplicates:
            self.fail('TOOLS', path)
            if selected:
                self.gap('TOOL', path, 'reference', 'compatibility')
        return duplicates

    def requirements(self, value, path, code):
        if not isinstance(value, list):
            self.gap(code, path, unit='compatibility')
            return set()
        output = set()
        for requirement in value:
            if edition(requirement):
                output.add(edition_key(requirement))
            else:
                self.gap(code, path, unit='compatibility')
        return output

    def assess(self, requirements, selection, claims, code, path):
        if selection is None:
            self.fail(code, path, 'inconclusive', 'compatibility')
            return
        if not edition(selection):
            self.gap(code, path, unit='compatibility')
            return
        # Claims are a lookup prerequisite, not an independent assessment.
        # Callers retain gaps for any unreadable requirement subsets.
        if not requirements:
            return
        if not isinstance(claims, list) or not all(edition(field(x, 'capability')) for x in claims):
            self.gap(code, path, unit='compatibility')
            return
        index = defaultdict(list)
        for claim in claims:
            index[edition_key(claim['capability'])].append(claim)
        for requirement in requirements:
            matching = index.get(requirement, [])
            if len(matching) > 1:
                self.gap(code, path, 'reference', 'compatibility')
            elif not matching:
                self.fail(code, path, 'inconclusive', 'compatibility')
            else:
                claim = matching[0]
                status, evidence = field(claim, 'status'), field(claim, 'evidence')
                if status == 'unsupported':
                    self.fail(code, path, 'fail', 'compatibility')
                elif status == 'unknown':
                    self.fail(code, path, 'inconclusive', 'compatibility')
                elif status != 'supported':
                    self.gap(code, path, unit='compatibility')
                elif evidence is None:
                    self.fail(code, path, 'inconclusive', 'compatibility')
                elif not shaped(evidence, 'hash'):
                    self.gap(code, path, unit='compatibility')

    def engine(self, binding, agent, ap, path, parent_cause):
        if parent_cause:
            self.gap('ENGINE', path, parent_cause, 'compatibility')
            return
        requirements = self.requirements(field(binding, 'requires'), path, 'ENGINE')
        slots = field(agent, 'instructions')
        if not isinstance(slots, list):
            self.gap('ENGINE', path, unit='compatibility')
        else:
            for i, slot in enumerate(slots):
                content, _, cause = self.v.choice(field(slot, 'content'), 'instructions', ptr(ptr(ptr(ap, 'instructions'), i), 'content'))
                fmt = field(content, 'format')
                if cause:
                    self.gap('ENGINE', path, cause, 'compatibility')
                elif edition(fmt):
                    requirements.add(edition_key(fmt))
                else:
                    self.gap('ENGINE', path, unit='compatibility')
        applications = field(binding, 'applications')
        if not isinstance(applications, list):
            self.gap('ENGINE', path, unit='compatibility')
        else:
            for app in applications:
                adapter = field(app, 'adapter')
                if edition(adapter):
                    requirements.add(edition_key(adapter))
                else:
                    self.gap('ENGINE', path, unit='compatibility')
        if isinstance(binding, dict) and 'settings' in binding:
            fmt = field(binding['settings'], 'format')
            if edition(fmt):
                requirements.add(edition_key(fmt))
            else:
                self.gap('ENGINE', path, unit='compatibility')
        self.assess(requirements, field(binding, 'engine'), field(binding, 'claims'), 'ENGINE', path)

    def tool(self, binding, path, parent_cause, duplicates):
        name = ref_id(field(binding, 'tool'))
        cause = parent_cause or ('shape' if name is None else 'reference' if name in duplicates else None)
        tool, _, lookup_cause = self.v.lookup(field(binding, 'tool'), 'tools')
        cause = cause or lookup_cause
        if cause:
            self.gap('TOOL', path, cause, 'compatibility')
            return
        requirements = self.requirements(field(tool, 'requires'), path, 'TOOL')
        effect = field(tool, 'effects')
        if effect == 'unknown':
            self.fail('TOOL', path, 'inconclusive', 'compatibility')
        elif effect not in ('none', 'external'):
            self.gap('TOOL', path, unit='compatibility')
        self.assess(requirements, field(binding, 'implementation'), field(binding, 'claims'), 'TOOL', path)

    def assign(self, config, path):
        graph, _, cause = self.v.lookup(field(config, 'graph'), 'graphs')
        steps = field(graph, 'steps')
        agents = field(config, 'agents')
        ids, complete, duplicates = self.projection(agents, 'agent')
        required = []
        if not isinstance(steps, list):
            cause = cause or 'shape'
        else:
            for step in steps:
                kind = step_kind(step)
                if kind is None:
                    cause = cause or 'shape'
                elif kind == 'invoke':
                    name = ref_id(field(step, 'agent'))
                    if name is None:
                        cause = cause or 'shape'
                    else:
                        required.append(name)
        if not complete:
            cause = cause or 'shape'
        if cause:
            self.gap('ASSIGN', path, cause)
        elif set(ids) != set(required) or duplicates:
            self.fail('ASSIGN', path)
        return duplicates

    def bindings(self, config, path, selected, duplicates):
        bindings = field(config, 'agents')
        bp = ptr(path, 'agents') if isinstance(config, dict) and 'agents' in config else path
        if not isinstance(bindings, list):
            for code in ('REF', 'CONTENT', 'TOOLS', 'UNIQUE'):
                self.gap(code, bp)
            if selected:
                for code in ('ENGINE', 'TOOL'):
                    self.gap(code, bp, unit='compatibility')
            return
        for i, binding in enumerate(bindings):
            p = ptr(bp, i)
            agent_ref = field(binding, 'agent')
            rp = ptr(p, 'agent') if isinstance(binding, dict) and 'agent' in binding else p
            self.v.check_ref('configuration', agent_ref, 'agents', rp)
            name = ref_id(agent_ref)
            agent, ap, cause = self.v.lookup(agent_ref, 'agents')
            cause = ('reference' if name is not None and name in duplicates else cause)
            if not isinstance(agent, dict) and cause is None:
                cause = 'shape'
            self.content(binding, agent, p, cause, selected)
            tool_duplicates = self.tool_coverage(binding, agent, p, cause, selected)
            for f, schema, key in (('requires', E, edition_key), ('claims', CLAIM, lambda x: edition_key(x['capability']))):
                value = field(binding, f)
                location = ptr(p, f) if isinstance(binding, dict) and f in binding else p
                self.v.unique('configuration', value, schema, location, key)
            if selected:
                self.engine(binding, agent, ap, p, cause)
            tools = field(binding, 'tools')
            tp = ptr(p, 'tools') if isinstance(binding, dict) and 'tools' in binding else p
            if not isinstance(tools, list):
                self.gap('REF', tp)
                self.gap('UNIQUE', tp)
                if selected:
                    self.gap('TOOL', tp, unit='compatibility')
            else:
                for j, tb in enumerate(tools):
                    loc = ptr(tp, j)
                    rp = ptr(loc, 'tool') if isinstance(tb, dict) and 'tool' in tb else loc
                    self.v.check_ref('configuration', field(tb, 'tool'), 'tools', rp)
                    cp = ptr(loc, 'claims') if isinstance(tb, dict) and 'claims' in tb else loc
                    self.v.unique('configuration', field(tb, 'claims'), CLAIM, cp, lambda x: edition_key(x['capability']))
                    if selected:
                        self.tool(tb, loc, cause, tool_duplicates)

    def run(self):
        d = self.v.doc
        configs = d.get('configurations', {})
        if 'configurations' in d:
            self.v.shape('configuration', configs, mapping(CONFIGURATION), '/configurations')
        if 'selected' in d:
            selected = d['selected']
            self.v.shape('configuration', selected, 'id', '/selected')
            if not is_id(selected) or not isinstance(configs, dict) or not all(is_id(k) for k in configs):
                self.gap('SELECTION', '/selected')
                self.gap('CHECKS', '/selected', unit='compatibility')
            elif selected not in configs:
                self.fail('SELECTION', '/selected')
                self.gap('CHECKS', '/selected', 'reference', 'compatibility')
            else:
                self.selected = selected
        if not isinstance(configs, dict):
            for code in ('REF', 'ASSIGN', 'CONTENT', 'TOOLS', 'UNIQUE'):
                self.gap(code, '/configurations')
            return
        for name, config in configs.items():
            p = ptr('/configurations', name)
            rp = ptr(p, 'graph') if isinstance(config, dict) and 'graph' in config else p
            self.v.check_ref('configuration', field(config, 'graph'), 'graphs', rp)
            duplicates = self.assign(config, p)
            self.bindings(config, p, name == self.selected, duplicates)


def validate(primary_bytes):
    """Return one complete static candidate Report for bytes, or raise an API error.

    Findings do not raise. TypeError is host misuse; MemoryError/RecursionError
    are resource failures with no report. No other inputs or external lookups.
    """
    if not isinstance(primary_bytes, bytes):
        raise TypeError('validate expects bytes')
    return Validator(primary_bytes).run()
