"""Independent, offline candidate-2 reader. No described system is executed."""
from collections import defaultdict
import hashlib
from grammar import CONTRACT, good, errors, array
from lossless import Parser, SyntaxFailure, pointer, dumps

D_RULES = 'P-SYNTAX P-SHAPE D-IDENTITY D-OWNER D-REFERENCE D-RELATION D-CYCLE D-EXPORT D-AGENT D-DEFERRAL D-DEPENDENCY D-INTEGRITY X-MODE'.split()
G_RULES = 'P-SHAPE X-MODE G-TARGET G-PATH G-DATA G-APPROVAL'.split()
R_RULES = 'P-SHAPE X-MODE R-REQUIREMENT R-SELECTION'.split()
OPERATIONS = {'inspect', 'validateD', 'validateG', 'resolveG', 'validateR', 'exchange', 'lossyExchange'}
RANK = {'pass': 0, 'inconclusive': 1, 'unsupported': 2, 'fail': 3}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def key(value):
    return tuple(value[n] for n in ('scope', 'id', 'version'))


def frozen(value):
    if isinstance(value, dict):
        return tuple((k, frozen(v)) for k, v in sorted(value.items()))
    if isinstance(value, list):
        return tuple(frozen(v) for v in value)
    return value


def items(obj, name):
    value = obj.get(name) if isinstance(obj, dict) else None
    return value if isinstance(value, list) else []


def reachable(start, edges, removed=None):
    seen, queue = set(), [start]
    while queue:
        node = queue.pop()
        if node in seen:
            continue
        seen.add(node)
        queue.extend(target for label, target in edges.get(node, []) if (node, label) != removed)
    return seen


def cyclic(edges):
    indegree = {node: 0 for node in edges}
    for successors in edges.values():
        for _, target in successors:
            indegree[target] = indegree.get(target, 0) + 1
    ready = [node for node, count in indegree.items() if count == 0]
    count = 0
    while ready:
        node = ready.pop()
        count += 1
        for _, target in edges.get(node, []):
            indegree[target] -= 1
            if indegree[target] == 0:
                ready.append(target)
    return count != len(indegree)


class Result:
    def __init__(self, input_id, unit, phase, rules):
        self.input, self.unit, self.phase = input_id, unit, phase
        self.findings = {}
        self.checks = {(rule, 'completed'): set() for rule in rules}
        self.parents = []
        if unit in ('D', 'G', 'R'):
            for rule in ('X-EXECUTION', 'X-FULL-MODEL'):
                self.exclude(rule, '', whole=True)
        if unit == 'R':
            for rule in ('X-READINESS', 'X-EVIDENCE-ASSESSMENT'):
                self.exclude(rule, '/runtime', whole=True)

    def mark(self, rule, state, path, whole=False):
        if whole:
            self.checks.pop((rule, 'completed'), None)
        self.checks.setdefault((rule, state), set()).add(path)

    def block(self, rule, path='', whole=False):
        self.mark(rule, 'blocked', path, whole)

    def exclude(self, rule, path='', whole=False):
        self.mark(rule, 'excluded', path, whole)

    def find(self, rule, path='', detail='candidate rule violation', outcome='fail', byte=None):
        loc = ('byte', byte) if byte is not None else ('pointer', path)
        identifier = rule, loc, outcome
        self.findings.setdefault(identifier, set()).add(detail)

    def shape(self, schema, value, path=''):
        found = errors(schema, value, path)
        for location, reason in found:
            self.find('P-SHAPE', location, reason)
        return not found

    def verdict(self):
        values = ['pass'] + [p.verdict() for p in self.parents]
        values += [x[2] for x in self.findings if x[2] != 'deferred']
        if any(state == 'blocked' for _, state in self.checks):
            values.append('inconclusive')
        return max(values, key=RANK.get)

    def export(self):
        return {'input': self.input, 'unit': self.unit, 'phase': self.phase,
                'verdict': self.verdict(),
                'findings': [{'rule': r, 'location': {loc[0]: loc[1]}, 'outcome': outcome,
                              'details': '; '.join(sorted(details))}
                             for (r, loc, outcome), details in sorted(self.findings.items())],
                'checks': [{'rule': rule, 'state': state,
                            'locations': [{'pointer': p} for p in sorted(paths)]}
                           for (rule, state), paths in sorted(self.checks.items())]}


class Document:
    def __init__(self, raw, input_id='primary'):
        self.raw, self.id = raw, input_id
        self.parser, self.syntax, self.tree = Parser(raw), None, None
        try:
            self.tree = self.parser.parse()
        except SyntaxFailure as error:
            self.syntax = error
            self.parser.spans.clear()
        self.obj = self.tree if isinstance(self.tree, dict) else {}
        self.index, self.ambiguous, self.invalid = {}, set(), set()
        scope_ids = defaultdict(list)
        records = [('', self.obj.get('root'))] + [('/definitions/' + str(i), v) for i, v in enumerate(items(self.obj, 'definitions'))]
        for path, value in records:
            if isinstance(value, dict) and good('Key', value.get('key')):
                identity = key(value['key'])
                scope_ids[identity[:2]].append(identity)
                if len(scope_ids[identity[:2]]) > 1:
                    self.ambiguous.update(scope_ids[identity[:2]])
                self.index[identity] = (value, path or '/root')
                if not good('Root' if not path else 'Definition', value):
                    self.invalid.add(identity)
        self.catalog_complete = (isinstance(self.obj.get('root'), dict) and good('Key', self.obj['root'].get('key'))
                                 and isinstance(self.obj.get('definitions'), list)
                                 and all(isinstance(v, dict) and good('Key', v.get('key')) for v in self.obj['definitions']))
        self.dependencies = {}
        self.bad_dependencies = set()
        self.dependency_catalog_complete = (isinstance(self.obj.get('dependencies'), list)
                                            and all(isinstance(v, dict) and good('text', v.get('id')) for v in self.obj['dependencies']))
        for i, dep in enumerate(items(self.obj, 'dependencies')):
            if good('Dependency', dep):
                if dep['id'] in self.dependencies:
                    self.bad_dependencies.add(dep['id'])
                self.dependencies[dep['id']] = (dep, '/dependencies/' + str(i))
            elif isinstance(dep, dict) and good('text', dep.get('id')):
                self.bad_dependencies.add(dep['id'])
        self.d = None
        self.g = None
        self.selected_payloads = set()

    def lookup(self, ref, kind, result, rule, path):
        identity = key(ref)
        if identity in self.ambiguous or identity in self.invalid:
            result.block(rule, path)
            return None
        found = self.index.get(identity)
        if found is None and not self.catalog_complete:
            result.block(rule, path)
            return None
        if found is None or (kind is not None and found[0]['kind'] != kind):
            result.find(rule, path, 'missing or wrong-kind local target')
            return None
        return found

    def external_declaration(self, ref, result, rule, path):
        name = ref['dependency']
        if name in self.bad_dependencies:
            result.block(rule, path)
            return None
        dep = self.dependencies.get(name)
        if dep is None and not self.dependency_catalog_complete:
            result.block(rule, path)
            return None
        if dep is None or dep[0]['rootKey']['scope'] != ref['key']['scope']:
            result.find(rule, path, 'undeclared dependency or target scope mismatch')
            return None
        return dep


def validate_d(doc, annexes):
    result = Result(doc.id, 'D', 'unresolved-document', D_RULES)
    doc.d = result
    if doc.syntax:
        result.find('P-SYNTAX', detail=str(doc.syntax), byte=doc.syntax.offset)
        for rule in D_RULES[1:]:
            result.block(rule, whole=True)
        return result
    result.shape('Document', doc.tree)
    if not isinstance(doc.tree, dict):
        for rule in D_RULES[2:]:
            result.block(rule, whole=True)
        return result
    root = doc.obj.get('root')
    root_ok = good('Root', root)
    seen = set()
    if root_ok:
        seen.add(key(root['key'])[:2])
    definitions = items(doc.obj, 'definitions')
    for i, definition in enumerate(definitions):
        path = '/definitions/' + str(i)
        if not good('Definition', definition):
            for rule in ('D-IDENTITY', 'D-OWNER', 'D-REFERENCE', 'D-AGENT'):
                result.block(rule, path)
            continue
        identity = key(definition['key'])
        if identity[:2] in seen:
            result.find('D-IDENTITY', path, 'duplicate scope/id')
        seen.add(identity[:2])
        if root_ok:
            if identity[0] != root['key']['scope']:
                result.find('D-IDENTITY', path, 'definition scope differs from root')
            if definition['owner'] != root['key']:
                result.find('D-OWNER', path, 'owner differs from root')
        else:
            result.block('D-IDENTITY', path)
            result.block('D-OWNER', path)
    for name, rules in {'definitions': ('D-IDENTITY', 'D-OWNER', 'D-AGENT'),
                        'relations': ('D-REFERENCE', 'D-RELATION', 'D-CYCLE', 'D-AGENT'),
                        'exports': ('D-EXPORT',), 'unresolved': ('D-DEFERRAL',),
                        'dependencies': ('D-DEPENDENCY', 'D-INTEGRITY'), 'extensions': ('X-MODE',)}.items():
        if not isinstance(doc.obj.get(name), list):
            for rule in rules:
                result.block(rule, '/' + name)
    extension_ids = { (x['identity'], x['version']) for x in items(doc.obj, 'extensions') if good('Extension', x)}
    def custom(kind, path):
        if isinstance(kind, dict) and (kind['extension']['identity'], kind['extension']['version']) not in extension_ids:
            result.find('D-REFERENCE', path, 'custom Kind extension not declared')
    for i, definition in enumerate(definitions):
        if good('Definition', definition):
            custom(definition['kind'], '/definitions/' + str(i))
    seen_rel, edges, counts = set(), defaultdict(list), defaultdict(lambda: defaultdict(list))
    incomplete_relations = False
    for i, relation in enumerate(items(doc.obj, 'relations')):
        path = '/relations/' + str(i)
        if not good('Relation', relation):
            incomplete_relations = True
            for rule in ('D-REFERENCE', 'D-RELATION', 'D-CYCLE'):
                result.block(rule, path)
            continue
        custom(relation['expectedKind'], path)
        token = frozen(relation)
        if token in seen_rel:
            result.find('D-RELATION', path, 'duplicate relation')
        seen_rel.add(token)
        source = doc.lookup(relation['source'], None, result, 'D-REFERENCE', path)
        target = relation['target']
        if 'dependency' in target:
            doc.external_declaration(target, result, 'D-REFERENCE', path)
        else:
            doc.lookup(target, relation['expectedKind'], result, 'D-REFERENCE', path)
        relation_type = relation['relation']
        if relation_type in ('actsAs', 'exposes', 'directedBy'):
            target_kinds = {'actsAs': ['Principal'], 'exposes': ['Interface'], 'directedBy': ['Instructions', 'Role', 'Skill', 'ControlFlow']}[relation_type]
            if source and (source[0]['kind'] != 'Agent' or relation['expectedKind'] not in target_kinds):
                result.find('D-RELATION', path, 'relation kinds not permitted')
        if source:
            counts[key(relation['source'])][relation_type].append(relation)
        if relation_type == 'contains' and 'dependency' not in target:
            if key(relation['source']) not in doc.ambiguous and key(target) not in doc.ambiguous:
                edges[key(relation['source'])].append(('contains', key(target)))
    if cyclic(edges):
        result.find('D-CYCLE', '/relations', 'containment cycle')
    exports = items(doc.obj, 'exports')
    if root_ok and isinstance(doc.obj.get('exports'), list):
        if (root['kind'] == 'Fragment' and not exports) or (root['kind'] == 'System' and exports):
            result.find('D-EXPORT', '/exports', 'root export constraint')
    elif not root_ok:
        result.block('D-EXPORT', '/exports')
    seen_exports = set()
    for i, export in enumerate(exports):
        path = '/exports/' + str(i)
        if not good('Key', export):
            result.block('D-EXPORT', path)
            continue
        ident = key(export)
        if ident in seen_exports or (root_ok and export == root['key']):
            result.find('D-EXPORT', path, 'duplicate or root export')
        doc.lookup(export, None, result, 'D-EXPORT', path)
        seen_exports.add(ident)
    deferral_counts = defaultdict(int)
    for entry in items(doc.obj, 'unresolved'):
        if good('Deferral', entry):
            deferral_counts[key(entry['subject'])] += 1
    deferred = set()
    for i, entry in enumerate(items(doc.obj, 'unresolved')):
        path = '/unresolved/' + str(i)
        if not good('Deferral', entry):
            result.block('D-DEFERRAL', path)
            continue
        subject = doc.lookup(entry['subject'], 'Agent', result, 'D-DEFERRAL', path)
        c = counts[key(entry['subject'])]
        valid = root_ok and root['kind'] == 'Fragment' and subject and not c['exposes'] and len(c['actsAs']) == 1 and c['directedBy'] and deferral_counts[key(entry['subject'])] == 1
        if incomplete_relations:
            result.block('D-DEFERRAL', path)
        elif valid:
            deferred.add(key(entry['subject']))
            result.find('D-DEFERRAL', path, 'Interface relation remains outstanding', 'deferred')
        else:
            result.find('D-DEFERRAL', path, 'invalid or stale deferral')
    for i, definition in enumerate(definitions):
        if good('Definition', definition) and definition['kind'] == 'Agent':
            path, identity = '/definitions/' + str(i), key(definition['key'])
            c = counts[identity]
            if identity in doc.ambiguous or incomplete_relations:
                result.block('D-AGENT', path)
            elif len(c['actsAs']) != 1 or not c['directedBy'] or (not c['exposes'] and identity not in deferred):
                result.find('D-AGENT', path, 'Agent relation minimum not met')
    dependency_checks(doc, annexes, result)
    extension_checks(doc, result, 'validateD')
    return result


def dependency_checks(doc, annexes, result, exchange=False):
    seen_ids, roots = set(), set()
    rule = 'E-PRESERVE' if exchange else 'D-DEPENDENCY'
    integrity = 'E-PRESERVE' if exchange else 'D-INTEGRITY'
    for i, dep in enumerate(items(doc.obj, 'dependencies')):
        path = '/dependencies/' + str(i)
        if not good('Dependency', dep):
            result.block(rule, path)
            result.block(integrity, path)
            continue
        if dep['id'] in seen_ids or key(dep['rootKey']) in roots or len(dep['requiredFor']) != len(set(dep['requiredFor'])):
            result.find(rule, path if not exchange else '', 'duplicate dependency declaration')
        seen_ids.add(dep['id'])
        roots.add(key(dep['rootKey']))
        supplied = dep['id'] in annexes
        if (dep['status'] == 'included') != supplied:
            result.find(rule, path if not exchange else '', 'delivery status mismatch')
        if supplied and dep['sha256'] is not None and digest(annexes[dep['id']]) != dep['sha256']:
            result.find(integrity, path, 'content hash mismatch')
        operation = 'exchange' if exchange else 'validateD'
        if operation in dep['requiredFor']:
            if exchange and not supplied:
                result.find(rule, '', 'required exchange dependency absent')
            if dep['sha256'] is None:
                result.find(integrity, path if not exchange else '', 'required hash unknown', 'inconclusive')
    if set(annexes) - seen_ids:
        result.find(rule, '', 'undeclared annex id')


def extension_checks(doc, result, operation):
    used = set()
    for definition in items(doc.obj, 'definitions'):
        if good('Definition', definition) and isinstance(definition['kind'], dict):
            used.add(frozen(definition['kind']['extension']))
    for relation in items(doc.obj, 'relations'):
        if good('Relation', relation) and isinstance(relation['expectedKind'], dict):
            used.add(frozen(relation['expectedKind']['extension']))
    seen = set()
    if not isinstance(doc.obj.get('extensions'), list):
        result.block('X-MODE', '/extensions')
    for i, ext in enumerate(items(doc.obj, 'extensions')):
        path = '/extensions/' + str(i)
        if not good('Extension', ext):
            result.block('X-MODE', path)
            continue
        identity = frozen({x: ext[x] for x in ('identity', 'version')})
        if identity in seen:
            result.find('X-MODE', path, 'duplicate extension Edition')
        seen.add(identity)
        mode = ext['operations'].get(operation, 'unknown')
        if operation == 'validateD' and identity in used and mode != 'required':
            result.find('X-MODE', path, 'custom Kind requires required classification')
        elif mode == 'required':
            result.find('X-MODE', path, 'semantic extension interpreter unavailable', 'unsupported')
        elif mode == 'unknown':
            result.find('X-MODE', path, 'extension applicability unknown', 'inconclusive')


def validate_r(doc):
    result = Result(doc.id, 'R', 'unresolved-document', R_RULES)
    if doc.syntax:
        for rule in R_RULES:
            result.block(rule, whole=True)
        return result
    extension_checks(doc, result, 'validateR')
    if 'runtime' not in doc.obj:
        for rule in R_RULES:
            if rule != 'X-MODE':
                result.exclude(rule, '/runtime', whole=True)
        return result
    runtime = doc.obj['runtime']
    result.shape('Runtime', runtime, '/runtime')
    if not isinstance(runtime, dict):
        for rule in ('R-REQUIREMENT', 'R-SELECTION'):
            result.block(rule, '/runtime')
        return result
    seen, pairs = set(), set()
    requirements_readable = good(array('Requirement'), runtime.get('requirements'))
    if not isinstance(runtime.get('requirements'), list):
        result.block('R-REQUIREMENT', '/runtime')
    for i, requirement in enumerate(items(runtime, 'requirements')):
        path = '/runtime/requirements/' + str(i)
        if not good('Requirement', requirement):
            result.block('R-REQUIREMENT', path)
            continue
        pair = frozen(requirement['capability']), key(requirement['subject'])
        if requirement['id'] in seen or pair in pairs:
            result.find('R-REQUIREMENT', path, 'duplicate requirement')
        seen.add(requirement['id'])
        pairs.add(pair)
        target = doc.lookup(requirement['subject'], None, result, 'R-REQUIREMENT', path)
        if target and target[1] == '/root':
            result.find('R-REQUIREMENT', path, 'requirement subject is root')
    if 'selection' not in runtime:
        if good('Runtime', runtime):
            result.exclude('R-SELECTION', '/runtime/selection', whole=True)
        else:
            result.block('R-SELECTION', '/runtime')
        return result
    selection = runtime['selection']
    if not isinstance(selection, dict):
        result.block('R-SELECTION', '/runtime/selection')
        return result
    if 'hosting' in selection:
        hosting = selection['hosting']
        if not good('Ref', hosting):
            result.block('R-SELECTION', '/runtime/selection')
        elif 'dependency' in hosting:
            doc.external_declaration(hosting, result, 'R-SELECTION', '/runtime/selection')
        else:
            doc.lookup(hosting, 'Environment', result, 'R-SELECTION', '/runtime/selection')
    seen_claims = set()
    if not isinstance(selection.get('evidence'), list):
        result.block('R-SELECTION', '/runtime/selection')
    for i, claim in enumerate(items(selection, 'evidence')):
        path = '/runtime/selection/evidence/' + str(i)
        if not good('EvidenceClaim', claim):
            result.block('R-SELECTION', path)
            continue
        if claim['requirement'] in seen_claims:
            result.find('R-SELECTION', path, 'duplicate requirement claim')
        if claim['requirement'] not in seen:
            if requirements_readable:
                result.find('R-SELECTION', path, 'missing requirement claim target')
            else:
                result.block('R-SELECTION', path)
        seen_claims.add(claim['requirement'])
    return result


class GraphValidation:
    def __init__(self, primary, annexes, resolve=False):
        self.primary, self.annexes, self.resolve = primary, annexes, resolve
        self.result = Result(primary.id, 'G', 'resolved-graph' if resolve else 'unresolved-document', G_RULES + (['G-RESOLVE'] if resolve else []))
        self.loaded, self.annex_results, self.selections = {}, {}, {}
        self.selection_uses = defaultdict(set)
        self.extra_states = []

    def dependency(self, name):
        if name in self.loaded:
            return self.loaded[name]
        self.loaded[name] = None
        record = self.primary.dependencies.get(name)
        if record is None or name in self.primary.bad_dependencies:
            self.result.block('G-RESOLVE', '')
            return None
        dep, path = record
        raw = self.annexes.get(name)
        if raw is None or dep['status'] != 'included':
            self.result.find('G-RESOLVE', path, 'required annex unavailable')
            return None
        if dep['sha256'] is None:
            self.result.find('G-RESOLVE', path, 'required declared hash unknown', 'inconclusive')
        elif digest(raw) != dep['sha256']:
            self.result.find('G-RESOLVE', path, 'required annex hash mismatch')
        doc = Document(raw, 'annex/' + name)
        self.loaded[name] = doc
        validate_d(doc, {})
        if doc.syntax or not good('Root', doc.obj.get('root')) or doc.obj['root']['key'] != dep['rootKey'] or doc.obj.get('contract') != CONTRACT:
            self.result.find('G-RESOLVE', path, 'invalid annex or root key')
        self.result.parents.append(doc.d)
        return doc

    def annex_result(self, doc):
        if doc is self.primary:
            return self.result
        if doc.id not in self.annex_results:
            r = Result(doc.id, 'G', 'resolved-graph', ['P-SHAPE', 'G-TARGET'])
            r.parents.append(doc.d)
            self.annex_results[doc.id] = r
            self.result.parents.append(r)
        return self.annex_results[doc.id]

    def ref(self, ref, expected, owner, consumer, field_path, report=None, affected=None):
        report = report or self.result
        affected = affected or consumer
        if not good('Ref', ref):
            report.block('G-TARGET', affected)
            return None
        external = 'dependency' in ref
        if external:
            if not owner.external_declaration(ref, report, 'G-TARGET', affected):
                return None
            if owner is not self.primary:
                self.result.find('G-RESOLVE', consumer, 'transitive selected reference unsupported', 'unsupported')
                report.block('G-TARGET', affected)
                return None
            if not self.resolve:
                report.exclude('G-TARGET', consumer)
                self.extra_states.append({'input': owner.id, 'pointer': field_path, 'state': 'unchecked', 'detail': 'external target excluded'})
                return None
            doc = self.dependency(ref['dependency'])
            if doc is None or doc.syntax:
                return None
            identity = ref['key']
            if not good(array('Key'), doc.obj.get('exports')):
                self.result.block('G-RESOLVE', consumer)
                return None
            if identity not in items(doc.obj, 'exports'):
                self.result.find('G-RESOLVE', consumer, 'target not exported')
                return None
        else:
            doc, identity = owner, ref
        if key(identity) in doc.ambiguous or key(identity) in doc.invalid:
            report.block('G-TARGET', affected)
            return None
        target = doc.index.get(key(identity))
        if target is None and not doc.catalog_complete:
            report.block('G-TARGET', affected)
            return None
        if target is None or target[0]['kind'] != expected:
            report.find('G-TARGET' if not external else 'G-RESOLVE', affected if not external else consumer, 'missing or wrong-kind target')
            return None
        if self.resolve:
            previous = self.selections.get(key(identity))
            if previous is not None and previous != doc.id:
                self.result.find('G-RESOLVE', consumer, 'selected key in multiple document boundaries')
            self.selections[key(identity)] = doc.id
            self.selection_uses[key(identity)].add(consumer)
        return doc, target[0], target[1]

    def check_collisions(self):
        if not self.resolve:
            return
        boundaries = [self.primary] + [doc for doc in self.loaded.values() if doc is not None]
        for identity, consumers in self.selection_uses.items():
            if sum(identity in doc.index for doc in boundaries) > 1:
                for consumer in consumers:
                    self.result.find('G-RESOLVE', consumer, 'selected key appears in multiple document boundaries')

    def payload(self, selected, schema):
        if selected is None:
            return None
        doc, definition, path = selected
        doc.selected_payloads.add(path + '/payload')
        result = self.annex_result(doc)
        if result.shape(schema, definition['payload'], path + '/payload'):
            return definition['payload']
        result.block('G-TARGET', path + '/payload')
        return None

    @staticmethod
    def same(left, right):
        return left and right and left[1]['key'] == right[1]['key']

    def check(self):
        doc, result = self.primary, self.result
        if doc.syntax:
            for rule in G_RULES + (['G-RESOLVE'] if self.resolve else []):
                result.block(rule, whole=True)
            return
        extension_checks(doc, result, 'validateG')
        if self.resolve:
            for dep, _ in doc.dependencies.values():
                if 'resolveG' in dep['requiredFor']:
                    self.dependency(dep['id'])
        if 'graphs' not in doc.obj:
            for rule in G_RULES:
                if rule != 'X-MODE':
                    result.exclude(rule, '/graphs', whole=True)
            if self.resolve:
                result.exclude('G-RESOLVE', '/graphs')
            return
        graphs = doc.obj['graphs']
        result.shape(array('Graph'), graphs, '/graphs')
        if not isinstance(graphs, list):
            for rule in G_RULES[2:]:
                result.block(rule, '/graphs')
            if self.resolve:
                result.block('G-RESOLVE', '/graphs')
            return
        graph_keys = set()
        for i, graph in enumerate(graphs):
            path = '/graphs/' + str(i)
            if not isinstance(graph, dict):
                for rule in G_RULES[2:]:
                    result.block(rule, path)
                continue
            definition = graph.get('definition')
            if good('Key', definition):
                self.ref(definition, 'ControlFlow', doc, path, path + '/definition')
                if key(definition) in graph_keys:
                    result.find('G-TARGET', path, 'duplicate graph ControlFlow')
                graph_keys.add(key(definition))
            else:
                result.block('G-TARGET', path)
            self.graph(graph, path)

    def graph(self, graph, path):
        result, doc = self.result, self.primary
        steps_list = items(graph, 'steps')
        steps, edges, records, ambiguous = {}, {}, [], set()
        index_readable = isinstance(graph.get('steps'), list)
        path_shape = isinstance(graph.get('steps'), list) and good('text', graph.get('entry'))
        path_bad = not steps_list
        for i, step in enumerate(steps_list):
            sp = path + '/steps/' + str(i)
            if isinstance(step, dict):
                records.append((step.get('id'), step, sp))
            if not isinstance(step, dict) or not good('text', step.get('id')):
                index_readable = False
                path_shape = False
                result.block('G-PATH', path)
                continue
            sid = step['id']
            if sid in steps:
                path_bad = True
                ambiguous.add(sid)
            steps[sid] = step
            labels = {'invoke': ('success', 'failure'), 'condition': ('true', 'false', 'failure'), 'approval': ('approved', 'denied', 'failure'), 'end': ()}.get(step.get('kind')) if isinstance(step.get('kind'), str) else None
            if labels is None or any(not good('text', step.get(label)) for label in labels):
                path_shape = False
                edges[sid] = []
            else:
                edges[sid] = [(label, step[label]) for label in labels]
        if path_shape:
            path_bad = path_bad or graph['entry'] not in steps or any(t not in steps for links in edges.values() for _, t in links)
            path_bad = path_bad or cyclic(edges) or reachable(graph['entry'], edges) != set(steps)
            path_bad = path_bad or any(not edges[sid] and steps[sid].get('kind') != 'end' for sid in steps)
            if path_bad:
                result.find('G-PATH', path, 'invalid graph paths, ids or cycles')
        else:
            result.block('G-PATH', path)
        paths_ok = path_shape and not path_bad

        def binding(binding_value, expected, consumer_id, consumer_path):
            if not good('Binding', binding_value):
                result.block('G-DATA', consumer_path)
                return
            if 'input' in binding_value:
                if not good('Ports', graph.get('inputs')):
                    result.block('G-DATA', consumer_path)
                elif graph['inputs'].get(binding_value['input']) != expected:
                    result.find('G-DATA', consumer_path, 'graph input missing or wrong type')
            else:
                producer = steps.get(binding_value['step'])
                if binding_value['step'] in ambiguous or (producer is None and not index_readable):
                    result.block('G-DATA', consumer_path)
                elif producer is None:
                    result.find('G-DATA', consumer_path, 'binding producer missing')
                elif producer.get('kind') not in ('invoke', 'condition', 'approval', 'end'):
                    result.block('G-DATA', consumer_path)
                elif producer['kind'] != 'invoke':
                    result.find('G-DATA', consumer_path, 'binding producer is not invoke')
                elif not good('Ports', producer.get('outputs')):
                    result.block('G-DATA', consumer_path)
                elif producer['outputs'].get(binding_value['port']) != expected:
                    result.find('G-DATA', consumer_path, 'producer output missing or wrong type')
                if not paths_ok:
                    result.block('G-DATA', consumer_path)
                elif consumer_id in reachable(graph['entry'], edges, (binding_value['step'], 'success')):
                    result.find('G-DATA', consumer_path, 'output available without producer success')

        def input_bindings(step, consumer_id, consumer_path):
            if good('Ports', step.get('inputs')) and good(('map', 'Binding'), step.get('bindings')):
                if set(step['inputs']) != set(step['bindings']):
                    result.find('G-DATA', consumer_path, 'invoke bindings differ from input names')
                for port, b in step['bindings'].items():
                    if port in step['inputs']:
                        binding(b, step['inputs'][port], consumer_id, consumer_path)
            else:
                result.block('G-DATA', consumer_path)
            binding(step.get('context'), 'json', consumer_id, consumer_path)

        for sid, step, sp in records:
            kind = step.get('kind')
            if kind == 'invoke':
                input_bindings(step, sid, sp)
                targets = {}
                for field, expected in (('agent', 'Agent'), ('interface', 'Interface'), ('action', 'Action'), ('principal', 'Principal')):
                    targets[field] = self.ref(step.get(field), expected, doc, sp, sp + '/' + field)
                seen = set()
                for j, ref in enumerate(items(step, 'resources')):
                    if good('Ref', ref):
                        if frozen(ref) in seen:
                            result.find('G-TARGET', sp, 'duplicate resource reference')
                        seen.add(frozen(ref))
                    self.ref(ref, 'Resource', doc, sp, sp + '/resources/' + str(j))
                agent = targets['agent']
                if agent:
                    owner, definition, dp = agent
                    exposure, principals = [], []
                    for j, relation in enumerate(items(owner.obj, 'relations')):
                        if not good('Relation', relation) or relation['source'] != definition['key']:
                            continue
                        relpath = '/relations/' + str(j)
                        if relation['relation'] in ('exposes', 'actsAs'):
                            target = self.ref(relation['target'], 'Interface' if relation['relation'] == 'exposes' else 'Principal', owner, sp, relpath + '/target', self.annex_result(owner), relpath)
                            (exposure if relation['relation'] == 'exposes' else principals).append(target)
                    comparisons = ((exposure, targets['interface']), (principals, targets['principal']))
                    for available, expected in comparisons:
                        if expected is not None and all(v is not None for v in available):
                            if not any(self.same(v, expected) for v in available):
                                result.find('G-TARGET', sp, 'Agent exposure or Principal mismatch')
                        elif not self.resolve:
                            result.exclude('G-TARGET', sp)
                payload = self.payload(targets['interface'], 'Interface')
                if payload is not None:
                    owner, _, dp = targets['interface']
                    action = self.ref(payload['action'], 'Action', owner, sp, dp + '/payload/action', self.annex_result(owner), dp + '/payload')
                    if action is not None and targets['action'] is not None and not self.same(action, targets['action']):
                        result.find('G-TARGET', sp, 'Interface action mismatch')
                    if good('Ports', step.get('inputs')) and good('Ports', step.get('outputs')):
                        if payload['inputs'] != step['inputs'] or payload['outputs'] != step['outputs']:
                            result.find('G-DATA', sp, 'Interface port maps differ')
                    else:
                        result.block('G-DATA', sp)
                elif targets['interface'] is None and not self.resolve and good('Ref', step.get('interface')) and 'dependency' in step['interface']:
                    result.exclude('G-DATA', sp)
                else:
                    result.block('G-DATA', sp)
            elif kind == 'condition':
                binding(step.get('test'), 'boolean', sid, sp)
            elif kind == 'end' and step.get('outcome') == 'success':
                if good('Ports', graph.get('outputs')) and good(('map', 'Binding'), step.get('bindings')):
                    if set(graph['outputs']) != set(step['bindings']):
                        result.find('G-DATA', sp, 'terminal bindings differ from graph outputs')
                    for port, b in step['bindings'].items():
                        if port in graph['outputs']:
                            binding(b, graph['outputs'][port], sid, sp)
                else:
                    result.block('G-DATA', sp)
            elif kind == 'approval':
                target = self.ref(step.get('requirement'), 'ApprovalRequirement', doc, sp, sp + '/requirement')
                payload = self.payload(target, 'ApprovalRequirement')
                if payload is not None:
                    owner, _, dp = target
                    seen = set()
                    for j, ref in enumerate(payload['approvers']):
                        ar = self.annex_result(owner)
                        if frozen(ref) in seen:
                            ar.find('G-TARGET', dp + '/payload', 'duplicate approver')
                        seen.add(frozen(ref))
                        self.ref(ref, 'Principal', owner, sp, dp + '/payload/approvers/' + str(j), ar, dp + '/payload')
                approved = step.get('approved')
                protected = steps.get(approved) if isinstance(approved, str) else None
                if not good('text', approved) or approved in ambiguous or (protected is None and not index_readable):
                    result.block('G-APPROVAL', sp)
                elif protected is not None and protected.get('kind') not in ('invoke', 'condition', 'approval', 'end'):
                    result.block('G-APPROVAL', sp)
                elif protected is None or protected.get('kind') != 'invoke':
                    result.find('G-APPROVAL', sp, 'approved successor is not invoke')
                else:
                    input_bindings(protected, sid, sp)
                if paths_ok:
                    incoming = [(s, label) for s, links in edges.items() for label, t in links if t == approved]
                    if incoming != [(sid, 'approved')] or approved in reachable(step['denied'], edges) or approved in reachable(step['failure'], edges):
                        result.find('G-APPROVAL', sp, 'protected invoke reachable without approval')
                else:
                    result.block('G-APPROVAL', sp)
            elif not good('Step', step):
                result.block('G-TARGET', sp)
                result.block('G-DATA', sp)


def inventory(doc, operation, extra_states=(), primary=True):
    states, opaque_paths = [], set()
    graph_mode = operation in ('validateG', 'resolveG') and primary
    runtime_mode = operation == 'validateR' and primary
    copy_mode = operation in ('inspect', 'exchange', 'lossyExchange')

    def state(path, value, detail=''):
        states.append({'input': doc.id, 'pointer': path, 'state': value, 'detail': detail or value})

    def opaque(path):
        if path in doc.parser.spans:
            opaque_paths.add(path)

    obj = doc.obj
    if isinstance(doc.tree, dict) and doc.syntax is None:
        for name, interpreted in (('graphs', graph_mode), ('runtime', runtime_mode)):
            state('/' + name, 'absent' if name not in obj else 'declared' if interpreted else 'unchecked')
            if name in obj and not interpreted:
                opaque('/' + name)
        for field in ('annotations', 'evidence'):
            opaque('/' + field)
        for field in ('payload', 'annotations'):
            opaque('/root/' + field)
        for i, definition in enumerate(items(obj, 'definitions')):
            path = '/definitions/' + str(i)
            if isinstance(definition, dict):
                if path + '/payload' not in doc.selected_payloads:
                    opaque(path + '/payload')
                for field in ('annotations', 'provenance'):
                    opaque(path + '/' + field)
        for i, extension in enumerate(items(obj, 'extensions')):
            if isinstance(extension, dict):
                opaque('/extensions/' + str(i) + '/payload')
        for i, relation in enumerate(items(obj, 'relations')):
            if good('Relation', relation) and 'dependency' in relation['target']:
                state('/relations/' + str(i) + '/target', 'unchecked')
    elif doc.syntax is None:
        opaque('')
    deps_ok = good(array('Dependency'), obj.get('dependencies'))
    if copy_mode:
        if doc.syntax or not isinstance(doc.tree, dict):
            state('/dependencies', 'unchecked')
        elif 'dependencies' not in obj:
            state('/dependencies', 'absent')
        elif deps_ok:
            state('/dependencies', 'declared')
        else:
            state('/dependencies', 'unchecked')
            opaque('/dependencies')
    if not copy_mode or deps_ok:
        for i, dep in enumerate(items(obj, 'dependencies')):
            if good('Dependency', dep) and dep['sha256'] is None:
                state('/dependencies/' + str(i) + '/sha256', 'unknown')
    runtime = obj.get('runtime')
    if runtime_mode and good('Runtime', runtime):
        if 'selection' not in runtime:
            state('/runtime/selection', 'absent')
        else:
            selection = runtime['selection']
            state('/runtime/selection', 'declared')
            for name in ('model', 'provider', 'hosting'):
                state('/runtime/selection/' + name, 'declared' if name in selection else 'absent')
            state('/runtime/selection/engine', 'unchecked', 'engine support unassessed')
            if 'hosting' in selection and 'dependency' in selection['hosting']:
                state('/runtime/selection/hosting', 'unchecked', 'target content unobserved')
            seen = set()
            for i, claim in enumerate(selection['evidence']):
                seen.add(claim['requirement'])
                path = '/runtime/selection/evidence/' + str(i)
                state(path, 'unchecked', 'evidence assessment excluded')
                if claim['artifact'] is None:
                    state(path + '/artifact', 'unknown')
            for requirement in runtime['requirements']:
                if requirement['id'] not in seen:
                    state('/runtime/selection/evidence', 'absent', requirement['id'])
    states.extend(x for x in extra_states if x['input'] == doc.id)
    # Parent slices subsume any nested slice; byte coordinates are never reserialized.
    selected = []
    for path in sorted(opaque_paths, key=lambda p: (p.count('/'), p)):
        if not any(path == parent or (parent == '' or path.startswith(parent + '/')) for parent in selected):
            selected.append(path)
    slices = [{'input': doc.id, 'pointer': p, 'start': doc.parser.spans[p][0], 'end': doc.parser.spans[p][1]} for p in sorted(selected)]
    unique = {}
    for item in states:
        unique[(item['input'], item['pointer'], item['state'], item['detail'])] = item
    return list(unique.values()), slices


def read(operation, primary, annexes=None, losses=None):
    """Return report and byte artifacts. Caller supplies all bytes, without retrieval."""
    annexes = {} if annexes is None else annexes
    if operation not in OPERATIONS or not isinstance(primary, bytes) or not isinstance(annexes, dict) or any(not isinstance(k, str) or not k or not isinstance(v, bytes) for k, v in annexes.items()):
        raise ValueError('invalid experimental request')
    if losses is not None and operation != 'lossyExchange':
        raise ValueError('losses only permitted for lossyExchange')
    if losses is not None:
        if not isinstance(losses, list):
            raise ValueError('losses must be an array')
        for loss in losses:
            if not isinstance(loss, dict) or set(loss) != {'input', 'location', 'information', 'reason', 'permission'} or loss['permission'] is not None or any(not good('text', loss[x]) for x in ('input', 'information', 'reason')):
                raise ValueError('invalid loss record')
            loc = loss['location']
            from lossless import integer
            if not isinstance(loc, dict) or not ((set(loc) == {'pointer'} and isinstance(loc['pointer'], str)) or (set(loc) == {'byte'} and ((type(loc['byte']) is int and 0 <= loc['byte'] <= 9007199254740991) or integer(loc['byte']) is not None))):
                raise ValueError('invalid loss location')
    doc = Document(primary)
    input_bytes = {'primary': primary, **{'annex/' + name: raw for name, raw in sorted(annexes.items())}}
    results, artifacts, loss_records, annex_docs, extra_states = [], {}, [], [], []
    if operation == 'inspect':
        r = Result('primary', 'inspect', None, ['P-SYNTAX'])
        if doc.syntax:
            r.find('P-SYNTAX', detail=str(doc.syntax), byte=doc.syntax.offset)
        results.append(r)
    elif operation in ('exchange', 'lossyExchange'):
        r = Result('primary', 'exchange', None, ['E-PRESERVE' if operation == 'exchange' else 'E-LOSS'])
        if operation == 'lossyExchange':
            r.find('E-LOSS', '', 'candidate edition permits no lossy exchange')
            loss_records = losses or [{'input': 'primary', 'location': {'pointer': ''}, 'information': 'unspecified requested loss', 'reason': 'no omission permission in candidate-2', 'permission': None}]
        else:
            if good(array('Dependency'), doc.obj.get('dependencies')):
                dependency_checks(doc, annexes, r, exchange=True)
            if r.verdict() == 'pass':
                artifacts = dict(input_bytes)
        results.append(r)
    else:
        d = validate_d(doc, annexes)
        results.append(d)
        if operation == 'validateR':
            r = validate_r(doc)
            r.parents.append(d)
            if d.verdict() != 'pass':
                r.block('P-PREREQUISITE', whole=True)
            results.append(r)
        elif operation in ('validateG', 'resolveG'):
            g = GraphValidation(doc, annexes, operation == 'resolveG')
            g.check()
            g.check_collisions()
            r = g.result
            r.parents.append(d)
            if d.verdict() != 'pass':
                r.block('P-PREREQUISITE', whole=True)
            annex_docs = [v for _, v in sorted(g.loaded.items()) if v is not None]
            results += [v.d for v in annex_docs]
            results += [v for _, v in sorted(g.annex_results.items())]
            results.append(r)
            extra_states = g.extra_states
    states, slices = inventory(doc, operation, extra_states)
    for annex in annex_docs:
        a, b = inventory(annex, 'resolveG', extra_states, primary=False)
        states.extend(a)
        slices.extend(b)
    report = {'contract': CONTRACT, 'processor': {'identity': 'agsdl-experimental/python-reader', 'version': 'candidate-2.1'},
              'operation': operation, 'inputs': [{'id': name, 'sha256': digest(raw)} for name, raw in input_bytes.items()],
              'results': [r.export() for r in results], 'inventory': {'tree': doc.tree, 'states': states, 'opaque': slices},
              'losses': loss_records, 'outputs': [{'id': name, 'sha256': digest(raw)} for name, raw in artifacts.items()]}
    return {'report': report, 'artifacts': artifacts}
