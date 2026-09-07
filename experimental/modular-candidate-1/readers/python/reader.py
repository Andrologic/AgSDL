"""Independent, offline modular candidate-1 reader. No described system runs."""
from collections import defaultdict
import hashlib
from grammar import CONTRACT, good, errors, array
from lossless import Parser, SyntaxFailure, pointer, dumps

D_RULES = 'P-SYNTAX P-SHAPE D-IDENTITY D-OWNER D-REFERENCE D-RELATION D-CYCLE D-EXPORT D-AGENT D-DEFERRAL D-DEPENDENCY D-INTEGRITY X-MODE'.split()
G_RULES = 'P-SHAPE X-MODE G-TARGET G-PATH G-DATA G-APPROVAL'.split()
R_RULES = 'P-SHAPE X-MODE R-SELECTION R-BINDING R-TOOL R-CONTENT R-COMPATIBILITY'.split()
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
        self.checks = {}
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

    def complete(self, rule):
        self.checks.setdefault((rule, 'completed'), set())

    def block(self, rule, path='', whole=False):
        self.mark(rule, 'blocked', path, whole)

    def exclude(self, rule, path='', whole=False):
        self.mark(rule, 'excluded', path, whole)

    def find(self, rule, path='', detail='candidate rule violation', outcome='fail', byte=None):
        self.complete(rule)
        loc = ('byte', byte) if byte is not None else ('pointer', path)
        identifier = rule, loc, outcome
        self.findings.setdefault(identifier, set()).add(detail)

    def shape(self, schema, value, path=''):
        self.complete('P-SHAPE')
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
        self.r_states = []
        self.selected_payloads = set()

    def lookup(self, ref, kind, result, rule, path, partial=False):
        identity = key(ref)
        if identity in self.ambiguous or (identity in self.invalid and not partial):
            result.block(rule, path)
            return None
        found = self.index.get(identity)
        if found is None and not self.catalog_complete:
            result.block(rule, path)
            return None
        if found is None:
            result.find(rule, path, 'missing or wrong-kind local target')
            return None
        if kind is not None:
            found_kind = found[0].get('kind') if isinstance(found[0], dict) else None
            if not good('Kind', found_kind):
                result.block(rule, path)
                return None
            if found_kind != kind:
                result.find(rule, path, 'missing or wrong-kind local target')
                return None
        result.complete(rule)
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
        result.complete(rule)
        return dep


def validate_d(doc, annexes):
    result = Result(doc.id, 'D', 'unresolved-document', D_RULES)
    doc.d = result
    if doc.syntax:
        result.find('P-SYNTAX', detail=str(doc.syntax), byte=doc.syntax.offset)
        for rule in D_RULES[1:]:
            result.block(rule, whole=True)
        return result
    result.complete('P-SYNTAX')
    result.shape('Document', doc.tree)
    if not isinstance(doc.tree, dict):
        for rule in D_RULES[2:]:
            result.block(rule, whole=True)
        return result
    root = doc.obj.get('root')
    root_ok = good('Root', root)
    root_key_ok = isinstance(root, dict) and good('Key', root.get('key'))
    seen = set()
    if root_key_ok:
        seen.add(key(root['key'])[:2])
    definitions = items(doc.obj, 'definitions')
    for i, definition in enumerate(definitions):
        path = '/definitions/' + str(i)
        if not good('Definition', definition):
            if not isinstance(definition, dict) or not good('Kind', definition.get('kind')):
                result.block('D-REFERENCE', path)
                result.block('D-AGENT', path)
            elif definition['kind'] == 'Agent' and not good('Key', definition.get('key')):
                result.block('D-AGENT', path)
        if not isinstance(definition, dict):
            for rule in ('D-IDENTITY', 'D-OWNER', 'D-REFERENCE', 'D-AGENT'):
                result.block(rule, path)
            continue
        if good('Key', definition.get('key')):
            result.complete('D-IDENTITY')
            identity = key(definition['key'])
            if identity[:2] in seen:
                result.find('D-IDENTITY', path, 'duplicate scope/id')
            seen.add(identity[:2])
            if root_key_ok and identity[0] != root['key']['scope']:
                result.find('D-IDENTITY', path, 'definition scope differs from root')
            elif not root_key_ok:
                result.block('D-IDENTITY', path)
        else:
            result.block('D-IDENTITY', path)
        if root_key_ok and good('Key', definition.get('owner')):
            result.complete('D-OWNER')
            if definition['owner'] != root['key']:
                result.find('D-OWNER', path, 'owner differs from root')
        else:
            result.block('D-OWNER', path)
    for name, rules in {'definitions': ('D-IDENTITY', 'D-OWNER', 'D-REFERENCE', 'D-AGENT'),
                        'relations': ('D-REFERENCE', 'D-RELATION', 'D-CYCLE'),
                        'exports': ('D-EXPORT',), 'unresolved': ('D-DEFERRAL',),
                        'dependencies': ('D-DEPENDENCY', 'D-INTEGRITY'), 'extensions': ('X-MODE',)}.items():
        if not isinstance(doc.obj.get(name), list):
            for rule in rules:
                result.block(rule, '/' + name if name in doc.obj else '')
        elif not doc.obj[name]:
            for rule in rules:
                result.complete(rule)
    extension_ids = { (x['identity'], x['version']) for x in items(doc.obj, 'extensions') if good('Extension', x)}
    def custom(kind, path):
        result.complete('D-REFERENCE')
        if isinstance(kind, dict) and (kind['extension']['identity'], kind['extension']['version']) not in extension_ids:
            result.find('D-REFERENCE', path, 'custom Kind extension not declared')
    for i, definition in enumerate(definitions):
        if isinstance(definition, dict) and good('Kind', definition.get('kind')):
            custom(definition['kind'], '/definitions/' + str(i))
    seen_rel, edges, counts = set(), defaultdict(list), defaultdict(lambda: defaultdict(list))
    incomplete_relations = not isinstance(doc.obj.get('relations'), list)
    incomplete_cycles = incomplete_relations
    for i, relation in enumerate(items(doc.obj, 'relations')):
        path = '/relations/' + str(i)
        relation_fields_ok = (isinstance(relation, dict)
                              and good('Key', relation.get('source'))
                              and good(('enum', ('actsAs', 'exposes', 'directedBy',
                                                'uses', 'contains')),
                                       relation.get('relation'))
                              and good('Ref', relation.get('target'))
                              and good('Kind', relation.get('expectedKind')))
        if not relation_fields_ok:
            incomplete_relations = True
            incomplete_cycles = True
            for rule in ('D-REFERENCE', 'D-RELATION', 'D-CYCLE'):
                result.block(rule, path)
            continue
        custom(relation['expectedKind'], path)
        result.complete('D-RELATION')
        token = frozen(relation)
        if token in seen_rel:
            result.find('D-RELATION', path, 'duplicate relation')
        seen_rel.add(token)
        source = doc.lookup(relation['source'], None, result, 'D-REFERENCE', path,
                            partial=True)
        target = relation['target']
        if 'dependency' in target:
            doc.external_declaration(target, result, 'D-REFERENCE', path)
        else:
            doc.lookup(target, relation['expectedKind'], result, 'D-REFERENCE', path,
                       partial=True)
        relation_type = relation['relation']
        if relation_type in ('actsAs', 'exposes', 'directedBy'):
            target_kinds = {'actsAs': ['Principal'], 'exposes': ['Interface'], 'directedBy': ['Instructions', 'Role', 'Skill', 'ControlFlow']}[relation_type]
            source_kind = source[0].get('kind') if source else None
            source_kind_readable = (good('Kind', source_kind)
                                    or source_kind in ('System', 'Fragment', 'PackageVersion'))
            if source is None or not source_kind_readable:
                result.block('D-RELATION', path)
            if (source and source_kind_readable
                    and (source_kind != 'Agent' or relation['expectedKind'] not in target_kinds)):
                result.find('D-RELATION', path, 'relation kinds not permitted')
        typed_minimum = ((relation_type == 'actsAs' and relation['expectedKind'] == 'Principal')
                         or (relation_type == 'exposes' and relation['expectedKind'] == 'Interface')
                         or (relation_type == 'directedBy'
                             and relation['expectedKind'] in ('Instructions', 'Role', 'Skill', 'ControlFlow')))
        if typed_minimum:
            counts[key(relation['source'])][relation_type].append(relation)
        if relation_type == 'contains' and 'dependency' not in target:
            if any(k in doc.ambiguous or k in doc.invalid for k in (key(relation['source']), key(target))):
                incomplete_cycles = True
                result.block('D-CYCLE', '/relations')
            else:
                edges[key(relation['source'])].append(('contains', key(target)))
    if not incomplete_cycles:
        result.complete('D-CYCLE')
    if cyclic(edges):
        result.find('D-CYCLE', '/relations', 'containment cycle')
    exports = items(doc.obj, 'exports')
    if root_ok and isinstance(doc.obj.get('exports'), list):
        result.complete('D-EXPORT')
        if (root['kind'] == 'Fragment' and not exports) or (root['kind'] == 'System' and exports):
            result.find('D-EXPORT', '/exports', 'root export constraint')
    elif not root_ok:
        result.block('D-EXPORT', '/exports' if 'exports' in doc.obj else '')
    seen_exports = set()
    for i, export in enumerate(exports):
        path = '/exports/' + str(i)
        if not good('Key', export):
            result.block('D-EXPORT', path)
            continue
        ident = key(export)
        if ident in seen_exports or (root_ok and export == root['key']):
            result.find('D-EXPORT', path, 'duplicate or root export')
        doc.lookup(export, None, result, 'D-EXPORT', path, partial=True)
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
        subject = doc.lookup(entry['subject'], 'Agent', result, 'D-DEFERRAL', path,
                             partial=True)
        c = counts[key(entry['subject'])]
        valid = root_ok and root['kind'] == 'Fragment' and subject and not c['exposes'] and len(c['actsAs']) == 1 and c['directedBy'] and deferral_counts[key(entry['subject'])] == 1
        if incomplete_relations or subject is None or not root_ok:
            result.block('D-DEFERRAL', path)
        elif valid:
            deferred.add(key(entry['subject']))
            result.find('D-DEFERRAL', path, 'Interface relation remains outstanding', 'deferred')
        else:
            result.find('D-DEFERRAL', path, 'invalid or stale deferral')
    if good(array('Definition'), doc.obj.get('definitions')) and not any(d['kind'] == 'Agent' for d in definitions):
        result.complete('D-AGENT')
    for i, definition in enumerate(definitions):
        if (isinstance(definition, dict) and good('Key', definition.get('key'))
                and definition.get('kind') == 'Agent'):
            path, identity = '/definitions/' + str(i), key(definition['key'])
            c = counts[identity]
            if identity not in doc.ambiguous and len(c['actsAs']) > 1:
                result.find('D-AGENT', path, 'Agent relation minimum not met')
            if identity in doc.ambiguous or incomplete_relations:
                result.block('D-AGENT', path)
            else:
                result.complete('D-AGENT')
                if len(c['actsAs']) != 1 or not c['directedBy']:
                    result.find('D-AGENT', path, 'Agent relation minimum not met')
                if not c['exposes'] and identity not in deferred:
                    if root_ok and root['kind'] != 'Fragment':
                        result.find('D-AGENT', path, 'Agent Interface minimum not met')
                    elif not root_ok or not good(array('Deferral'), doc.obj.get('unresolved')):
                        result.block('D-AGENT', path)
                    else:
                        result.find('D-AGENT', path, 'Agent Interface minimum not met')
    dependency_checks(doc, annexes, result)
    extension_checks(doc, result, 'validateD')
    return result


def dependency_checks(doc, annexes, result, exchange=False):
    seen_ids, roots = set(), set()
    rule = 'E-PRESERVE' if exchange else 'D-DEPENDENCY'
    integrity = 'E-PRESERVE' if exchange else 'D-INTEGRITY'
    if isinstance(doc.obj.get('dependencies'), list) and not doc.obj['dependencies']:
        result.complete(rule)
        result.complete(integrity)
    for i, dep in enumerate(items(doc.obj, 'dependencies')):
        path = '/dependencies/' + str(i)
        if not isinstance(dep, dict):
            result.block(rule, path)
            result.block(integrity, path)
            continue
        id_ok = good('text', dep.get('id'))
        root_ok = good('Key', dep.get('rootKey'))
        required_ok = good(array(('enum', ('validateD', 'resolveG', 'exchange'))),
                           dep.get('requiredFor'))
        required = items(dep, 'requiredFor')
        readable_required = [v for v in required if v in ('validateD', 'resolveG', 'exchange')]
        status_ok = good(('enum', ('included', 'external', 'omitted', 'unavailable')),
                         dep.get('status'))
        hash_ok = good(('union', ('hash', 'null')), dep.get('sha256'))
        if id_ok and root_ok and required_ok and status_ok:
            result.complete(rule)
        else:
            result.block(rule, path)
        if id_ok and required_ok and hash_ok:
            result.complete(integrity)
        else:
            result.block(integrity, path)
        duplicate = len(readable_required) != len(set(readable_required))
        if id_ok:
            duplicate |= dep['id'] in seen_ids
            seen_ids.add(dep['id'])
        if root_ok:
            duplicate |= key(dep['rootKey']) in roots
            roots.add(key(dep['rootKey']))
        if duplicate:
            result.find(rule, path if not exchange else '', 'duplicate dependency declaration')
        supplied = id_ok and dep['id'] in annexes
        if id_ok and status_ok and (dep['status'] == 'included') != supplied:
            result.find(rule, path if not exchange else '', 'delivery status mismatch')
        if supplied and good('hash', dep.get('sha256')) and digest(annexes[dep['id']]) != dep['sha256']:
            result.find(integrity, path, 'content hash mismatch')
        operation = 'exchange' if exchange else 'validateD'
        if operation in readable_required:
            if exchange and id_ok and not supplied:
                result.find(rule, '', 'required exchange dependency absent')
            if 'sha256' in dep and dep['sha256'] is None:
                result.find(integrity, path if not exchange else '', 'required hash unknown', 'inconclusive')
    if set(annexes) - seen_ids:
        if doc.dependency_catalog_complete:
            result.find(rule, '', 'undeclared annex id')
        else:
            result.block(rule, '')


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
        result.block('X-MODE', '/extensions' if 'extensions' in doc.obj else '')
    elif not doc.obj['extensions']:
        result.complete('X-MODE')
    for i, ext in enumerate(items(doc.obj, 'extensions')):
        path = '/extensions/' + str(i)
        if not good('Extension', ext):
            result.block('X-MODE', path)
            continue
        result.complete('X-MODE')
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
    """Validate the modular static configuration without resolving R annexes."""
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
        for rule in R_RULES[2:]:
            result.block(rule, '/runtime')
        return result

    states = doc.r_states

    def state(path, value, detail=None):
        states.append({'input': doc.id, 'pointer': path, 'state': value,
                       'detail': value if detail is None else detail})

    def duplicates(values, rule, path, detail):
        seen, duplicate = set(), False
        for value in values:
            token = frozen(value)
            if token in seen:
                result.find(rule, path, detail)
                duplicate = True
            seen.add(token)
        return duplicate

    def ref_target(ref, kinds, rule, path, excluded_path=None, state_path=None):
        if not good('Ref', ref):
            result.block(rule, path)
            return None
        if 'dependency' in ref:
            if doc.external_declaration(ref, result, rule, path):
                result.exclude(rule, excluded_path or path)
                external_state_path = state_path or path
                if state_path is not False and not external_state_path.startswith('/relations/'):
                    state(external_state_path, 'unchecked', 'external target excluded')
                return ('external', ref, path)
            return None
        found = doc.lookup(ref, None, result, rule, path)
        if found and (not isinstance(found[0]['kind'], str)
                      or found[0]['kind'] not in kinds):
            result.find(rule, path, 'wrong-kind local target')
            return None
        return (doc, found[0], found[1]) if found else None

    configurations_value = runtime.get('configurations')
    if not isinstance(configurations_value, list):
        for rule in R_RULES[2:]:
            result.block(rule, '/runtime')
        return result
    configurations = configurations_value
    if not configurations:
        for rule in ('R-SELECTION', 'R-BINDING', 'R-TOOL', 'R-CONTENT'):
            result.complete(rule)

    by_id = defaultdict(list)
    configuration_records = []
    binding_entries = []
    configuration_catalog_readable = True
    for i, configuration in enumerate(configurations):
        path = '/runtime/configurations/' + str(i)
        if isinstance(configuration, dict) and good('text', configuration.get('id')):
            by_id[configuration['id']].append((configuration, path))
            if len(by_id[configuration['id']]) > 1:
                result.find('R-SELECTION', path, 'duplicate configuration id')
        else:
            configuration_catalog_readable = False
        if not isinstance(configuration, dict):
            for rule in ('R-SELECTION', 'R-BINDING', 'R-TOOL', 'R-CONTENT'):
                result.block(rule, path)
            continue
        configuration_records.append((configuration, path))
        if good('Configuration', configuration):
            state(path, 'declared')
        if good('text', configuration.get('id')):
            result.complete('R-SELECTION')
        else:
            result.block('R-SELECTION', path)
        if not good('Key', configuration.get('graph')):
            result.block('R-SELECTION', path)
        bindings_value = configuration.get('agents')
        if not isinstance(bindings_value, list):
            for rule in ('R-BINDING', 'R-TOOL', 'R-CONTENT'):
                result.block(rule, path)
            continue
        if not bindings_value:
            for rule in ('R-BINDING', 'R-TOOL', 'R-CONTENT'):
                result.complete(rule)
        for j, binding in enumerate(bindings_value):
            bp = path + '/agents/' + str(j)
            if not isinstance(binding, dict):
                for rule in ('R-BINDING', 'R-TOOL', 'R-CONTENT'):
                    result.block(rule, bp)
                continue

            agent_ok = good('Ref', binding.get('agent'))
            engine_ok = ('engine' in binding
                         and (binding['engine'] is None or good('Edition', binding['engine'])))
            requires_value = binding.get('requires')
            requires_ok = isinstance(requires_value, list)
            requirements = [item for item in requires_value if good('Edition', item)] if requires_ok else []
            requires_complete = requires_ok and len(requirements) == len(requires_value)
            claims_value = binding.get('claims')
            claims_ok = isinstance(claims_value, list)
            claim_identities = ([item for item in claims_value
                                 if isinstance(item, dict)
                                 and good('Edition', item.get('capability'))]
                                if claims_ok else [])
            claims = [item for item in claim_identities
                      if good(('enum', ('supported', 'unsupported', 'unknown')),
                              item.get('status'))]
            claims_complete = (claims_ok
                               and all(good('CapabilityClaim', item)
                                       for item in claims_value))
            tools_value = binding.get('tools')
            tools_ok = isinstance(tools_value, list)
            tool_bindings = [(tool, bp + '/tools/' + str(k)) for k, tool in enumerate(tools_value)
                             if isinstance(tool, dict)] if tools_ok else []
            tools_complete = tools_ok and len(tool_bindings) == len(tools_value)
            applications_value = binding.get('applications')
            applications_ok = isinstance(applications_value, list)
            application_slots = [(application, bp + '/applications/' + str(k))
                                 for k, application in enumerate(applications_value)] if applications_ok else []
            applications = [(application, ap) for application, ap in application_slots
                            if isinstance(application, dict)
                            if good('Ref', application.get('content'))]
            applications_complete = (applications_ok
                                     and all(good('Application', application)
                                             for application, _ in application_slots))
            application_catalog_complete = (applications_ok
                                            and len(applications) == len(applications_value))

            if not all((agent_ok, engine_ok, requires_complete, claims_complete)):
                result.block('R-BINDING', bp)
            if not tools_complete:
                result.block('R-TOOL', bp)
            if not applications_complete:
                result.block('R-CONTENT', bp)
            if good('AgentBinding', binding):
                state(bp + '/engine', 'absent' if binding['engine'] is None else 'declared')
            duplicate_requirements = duplicates(requirements, 'R-BINDING', bp,
                                                'duplicate engine requirement')
            duplicate_claims = duplicates([claim['capability'] for claim in claim_identities], 'R-BINDING', bp,
                                          'duplicate engine capability claim')
            for k, claim in enumerate(claims_value if claims_ok else []):
                if good('CapabilityClaim', claim) and claim['evidence'] is None:
                    state(bp + '/claims/' + str(k) + '/evidence', 'unknown')
            if any((agent_ok, engine_ok, requires_ok, claims_ok)):
                result.complete('R-BINDING')

            agent_target = (ref_target(binding['agent'], {'Agent'}, 'R-BINDING', bp,
                                       bp, bp + '/agent') if agent_ok else None)
            binding_entries.append({
                'configuration': configuration, 'binding': binding, 'path': bp,
                'agent_ok': agent_ok, 'agent_target': agent_target,
                'engine_ok': engine_ok, 'requirements': requirements,
                'requires_complete': requires_complete,
                'claims': claims, 'claims_complete': claims_complete,
                'duplicate_claims': duplicate_claims,
                'duplicate_requirements': duplicate_requirements,
                'tool_bindings': tool_bindings, 'tools_complete': tools_complete,
                'tool_catalog_complete': (tools_complete
                                          and all(good('Ref', tool.get('tool'))
                                                  for tool, _ in tool_bindings)),
                'applications': applications, 'applications_complete': applications_complete,
                'application_slots': application_slots,
                'application_catalog_complete': application_catalog_complete,
                'binding_shape_ok': good('AgentBinding', binding),
            })

    selected_present = 'selected' in runtime
    selected = runtime.get('selected')
    if not selected_present:
        if good('Runtime', runtime):
            state('/runtime/selected', 'absent')
        result.complete('R-SELECTION')
        result.exclude('R-COMPATIBILITY', '/runtime', whole=True)
    elif good('text', selected):
        if good('Runtime', runtime):
            state('/runtime/selected', 'declared')
    else:
        result.block('R-SELECTION', '/runtime')
        result.block('R-COMPATIBILITY', '/runtime', whole=True)

    selected_record = None
    if selected_present and good('text', selected):
        matches = by_id.get(selected, [])
        if not matches:
            if configuration_catalog_readable:
                result.find('R-SELECTION', '/runtime', 'selected configuration does not exist')
            else:
                result.block('R-SELECTION', '/runtime')
            result.block('R-COMPATIBILITY', '/runtime', whole=True)
        elif len(matches) > 1:
            result.block('R-COMPATIBILITY', '/runtime', whole=True)
        else:
            selected_record = matches[0]

    graphs = doc.obj.get('graphs')
    graph_index = defaultdict(list)
    graph_index_readable = isinstance(graphs, list)
    for graph in graphs if isinstance(graphs, list) else []:
        if not isinstance(graph, dict) or not good('Key', graph.get('definition')):
            graph_index_readable = False
        else:
            graph_index[key(graph['definition'])].append(graph)

    configuration_blocked = {}
    ambiguous_agent_bindings = set()
    for configuration, path in configuration_records:
        graph_key_ok = good('Key', configuration.get('graph'))
        graph_matches = graph_index.get(key(configuration['graph']), []) if graph_key_ok else []
        graph = None
        selection_blocked = False
        if not graph_key_ok:
            result.block('R-SELECTION', path)
            selection_blocked = True
        elif not graph_index_readable:
            result.block('R-SELECTION', path)
            selection_blocked = True
        elif len(graph_matches) > 1:
            result.block('R-SELECTION', path)
            selection_blocked = True
        elif not graph_matches:
            result.find('R-SELECTION', path, 'configuration graph does not exist')
            selection_blocked = True
        else:
            graph = graph_matches[0]
            if doc.lookup(configuration['graph'], 'ControlFlow', result,
                          'R-SELECTION', path) is None:
                selection_blocked = True

        required_agents = []
        projection_readable = graph is not None and isinstance(graph.get('steps'), list)
        if projection_readable:
            for step in graph['steps']:
                if (not isinstance(step, dict)
                        or step.get('kind') not in ('invoke', 'condition', 'approval', 'end')):
                    projection_readable = False
                    break
                if step['kind'] == 'invoke':
                    if not good('Ref', step.get('agent')):
                        projection_readable = False
                        break
                    if frozen(step['agent']) not in {frozen(item) for item in required_agents}:
                        required_agents.append(step['agent'])
        projection_blocked = graph is None or not projection_readable
        if graph is not None and not projection_readable:
            result.block('R-BINDING', path)
        elif graph is not None:
            bindings = configuration.get('agents')
            if not isinstance(bindings, list):
                result.block('R-BINDING', path)
            else:
                readable_bindings = [(binding, path + '/agents/' + str(i))
                                     for i, binding in enumerate(bindings)
                                     if isinstance(binding, dict) and good('Ref', binding.get('agent'))]
                binding_catalog_complete = len(readable_bindings) == len(bindings)
                binding_groups = defaultdict(list)
                for binding, bp in readable_bindings:
                    binding_groups[frozen(binding['agent'])].append(bp)
                for group in binding_groups.values():
                    if len(group) > 1:
                        ambiguous_agent_bindings.update(group)
                for ref in required_agents:
                    matches = [(binding, bp) for binding, bp in readable_bindings
                               if binding['agent'] == ref]
                    if len(matches) > 1:
                        for _, bp in matches[1:]:
                            result.find('R-BINDING', bp, 'missing or duplicate AgentBinding')
                    elif not matches and not binding_catalog_complete:
                        result.block('R-BINDING', path)
                    elif not matches:
                        result.find('R-BINDING', path, 'missing or duplicate AgentBinding')
                for binding, bp in readable_bindings:
                    if binding['agent'] not in required_agents:
                        result.find('R-BINDING', bp, 'unused AgentBinding')
                result.complete('R-BINDING')
        configuration_blocked[id(configuration)] = selection_blocked or projection_blocked
        if selected_record and configuration is selected_record[0] and configuration_blocked[id(configuration)]:
            result.block('R-COMPATIBILITY', path)

    def agent_relations(agent_ref, relation_name, expected):
        if not good('Ref', agent_ref):
            return [], False
        if 'dependency' in agent_ref:
            return [], True
        if not isinstance(doc.obj.get('relations'), list):
            return [], False
        refs, readable = [], True
        for i, relation in enumerate(doc.obj['relations']):
            if not good('Relation', relation):
                readable = False
            elif (relation['source'] == agent_ref and relation['relation'] == relation_name
                  and relation['expectedKind'] == expected):
                refs.append((relation['target'], '/relations/' + str(i) + '/target'))
        return refs, readable

    def assess(requirements, claims, supplied, path, unknown=False, blocked=False,
               not_provided=False, emit_state=True):
        statuses = []
        claim_groups = defaultdict(list)
        for claim in claims:
            claim_groups[frozen(claim['capability'])].append(claim)
        for requirement in requirements:
            matching = claim_groups.get(frozen(requirement), [])
            if len(matching) > 1:
                continue
            claim = matching[0] if matching else None
            if not supplied:
                statuses.append('not-provided')
            elif claim and claim['status'] == 'unsupported':
                statuses.append('incompatible')
            elif (not claim or claim['status'] == 'unknown'
                  or not good('hash', claim.get('evidence'))):
                statuses.append('unknown')
            else:
                statuses.append('declared-supported')
        if not requirements:
            statuses.append('declared-supported' if supplied else 'not-provided')
        if unknown:
            statuses.append('unknown')
        if not_provided:
            statuses.append('not-provided')
        status = ('blocked' if blocked else
                  min(statuses, key={'incompatible': 0, 'not-provided': 1,
                                    'unknown': 2, 'declared-supported': 3}.get))
        if 'incompatible' in statuses:
            result.find('R-COMPATIBILITY', path, 'declared incompatible requirement')
        if any(item in ('not-provided', 'unknown') for item in statuses):
            result.find('R-COMPATIBILITY', path,
                        'required capability or choice not established', 'inconclusive')
        result.complete('R-COMPATIBILITY')
        if blocked:
            result.block('R-COMPATIBILITY', path)
        state_value = {'incompatible': 'declared', 'not-provided': 'absent',
                       'unknown': 'unknown', 'declared-supported': 'unchecked',
                       'blocked': 'unchecked'}[status]
        if emit_state:
            state(path, state_value, status)

    selected_assessments = 0
    selected_assessment_blocked = bool(selected_record and
                                       configuration_blocked.get(id(selected_record[0]), True))

    for entry in binding_entries:
        configuration, binding, bp = entry['configuration'], entry['binding'], entry['path']
        assess_selected = bool(selected_record and configuration is selected_record[0])
        agent_target = entry['agent_target']
        external_agent = bool(agent_target and agent_target[0] == 'external')
        agent_prerequisite_blocked = entry['agent_ok'] and agent_target is None
        if not entry['agent_ok']:
            agent_prerequisite_blocked = True

        content_root_records, content_relations_ok = agent_relations(binding.get('agent'),
                                                                    'directedBy', 'Instructions')
        skill_root_records, skill_relations_ok = agent_relations(binding.get('agent'),
                                                                'directedBy', 'Skill')
        tool_root_records, tool_relations_ok = agent_relations(binding.get('agent'),
                                                              'uses', 'Tool')
        required_content_records = content_root_records + skill_root_records
        required_content = [ref for ref, _ in required_content_records]
        tool_roots = [ref for ref, _ in tool_root_records]
        applications = entry['applications']
        content_records, content_edges = {}, defaultdict(list)
        skill_tools = defaultdict(list)
        external_content = external_agent
        content_blocked = not (content_relations_ok and skill_relations_ok
                               and entry['applications_complete'])
        content_closure_complete = content_relations_ok and skill_relations_ok
        tool_closure_complete = content_closure_complete and tool_relations_ok
        missing_content = False
        if external_agent:
            result.exclude('R-CONTENT', bp)
            result.exclude('R-TOOL', bp)
        elif not tool_relations_ok:
            result.block('R-TOOL', bp)

        queue = ([(ref, path.rsplit('/', 1)[0], path.rsplit('/', 1)[0], path)
                  for ref, path in required_content_records]
                 + [(application['content'], ap, ap, ap + '/content')
                    for application, ap in applications])
        visited = set()
        while queue:
            ref, request_path, excluded_path, ref_state_path = queue.pop(0)
            token = frozen(ref)
            if token in visited:
                ref_target(ref, {'Instructions', 'Skill'}, 'R-CONTENT', request_path,
                           excluded_path, ref_state_path)
                continue
            visited.add(token)
            local_identity = (key(ref) if good('Ref', ref) and 'dependency' not in ref else None)
            known_missing = (local_identity is not None
                             and local_identity not in doc.ambiguous
                             and local_identity not in doc.invalid and doc.catalog_complete
                             and (local_identity not in doc.index
                                  or doc.index[local_identity][0]['kind']
                                  not in ('Instructions', 'Skill')))
            target = ref_target(ref, {'Instructions', 'Skill'}, 'R-CONTENT', request_path,
                                excluded_path, ref_state_path)
            if target is None:
                if known_missing:
                    missing_content = True
                else:
                    content_blocked = True
                    content_closure_complete = False
                    tool_closure_complete = False
                continue
            if target[0] == 'external':
                external_content = True
                content_closure_complete = False
                tool_closure_complete = False
                continue
            _, definition, dp = target
            schema = ('InstructionsPayload' if definition['kind'] == 'Instructions'
                      else 'SkillPayload')
            payload_path = dp + '/payload'
            doc.selected_payloads.add(payload_path)
            payload_ok = result.shape(schema, definition['payload'], payload_path)
            if not isinstance(definition['payload'], dict):
                result.block('R-CONTENT', payload_path)
                content_blocked = True
                content_closure_complete = False
                tool_closure_complete = False
                continue
            payload = definition['payload']
            content_records[token] = (ref, definition, dp, payload, payload_ok)
            if not payload_ok:
                result.block('R-CONTENT', payload_path)
                content_blocked = True

            requires_value = payload.get('requires')
            if isinstance(requires_value, list):
                duplicates([item for item in requires_value if good('Edition', item)],
                           'R-CONTENT', payload_path, 'duplicate content requirement')
            else:
                content_blocked = True

            if definition['kind'] == 'Skill':
                dependencies_value = payload.get('dependencies')
                if not isinstance(dependencies_value, list):
                    content_blocked = True
                    content_closure_complete = False
                    tool_closure_complete = False
                else:
                    valid_dependencies = [dep for dep in dependencies_value if good('Ref', dep)]
                    duplicates(valid_dependencies, 'R-CONTENT', payload_path,
                               'duplicate Skill dependency')
                    if len(valid_dependencies) != len(dependencies_value):
                        content_blocked = True
                        content_closure_complete = False
                        tool_closure_complete = False
                    for i, dep in enumerate(dependencies_value):
                        if good('Ref', dep):
                            content_edges[token].append(frozen(dep))
                            queue.append((dep, payload_path, payload_path,
                                          payload_path + '/dependencies/' + str(i)))

                tools_value = payload.get('tools')
                if not isinstance(tools_value, list):
                    content_blocked = True
                    tool_closure_complete = False
                else:
                    valid_tools = [tool for tool in tools_value if good('Ref', tool)]
                    duplicates(valid_tools, 'R-CONTENT', payload_path,
                               'duplicate Skill tool')
                    if len(valid_tools) != len(tools_value):
                        content_blocked = True
                        tool_closure_complete = False
                    for i, tool in enumerate(tools_value):
                        if not good('Ref', tool):
                            continue
                        target = ref_target(tool, {'Tool'}, 'R-CONTENT', payload_path,
                                            payload_path, payload_path + '/tools/' + str(i))
                        if target is None:
                            tool_closure_complete = False
                        elif target[0] == 'external':
                            external_content = True
                            skill_tools[token].append(tool)
                        else:
                            skill_tools[token].append(tool)

        content_graph = {token: [('dependency', successor) for successor in successors]
                         for token, successors in content_edges.items()}
        for token, (_, definition, dp, _, _) in content_records.items():
            if definition['kind'] != 'Skill':
                continue
            if any(token in reachable(successor, content_graph)
                   for successor in content_edges.get(token, [])):
                result.find('R-CONTENT', dp + '/payload', 'Skill dependency cycle')

        required_tokens = set()
        for ref in required_content:
            required_tokens.update(reachable(frozen(ref), content_graph))
        application_tokens = [(frozen(application['content'])
                               if isinstance(application, dict)
                               and good('Ref', application.get('content')) else None)
                              for application, _ in entry['application_slots']]
        if entry['application_catalog_complete']:
            for token in required_tokens:
                if token not in application_tokens:
                    result.find('R-CONTENT', bp, 'required content Application missing')
        application_positions = {ap: i for i, (_, ap) in enumerate(entry['application_slots'])}
        for application, ap in applications:
            i = application_positions[ap]
            token = frozen(application['content'])
            if token not in required_tokens and not external_agent:
                if content_closure_complete:
                    result.find('R-CONTENT', ap, 'Application content is not reachable')
                else:
                    result.block('R-CONTENT', ap)
            target = ref_target(application['content'], {'Instructions', 'Skill'},
                                'R-CONTENT', ap, ap, ap + '/content')
            if target and target[0] != 'external':
                record = content_records.get(token)
                if record and record[1]['kind'] == 'Skill':
                    dependencies_value = record[3].get('dependencies')
                    if isinstance(dependencies_value, list):
                        earlier = application_tokens[:i]
                        if any(frozen(dep) not in earlier for dep in dependencies_value
                               if good('Ref', dep)):
                            if None in earlier:
                                result.block('R-CONTENT', ap)
                            else:
                                result.find('R-CONTENT', ap,
                                            'Skill dependency Application must be earlier')
                    else:
                        result.block('R-CONTENT', ap)
        result.complete('R-CONTENT')

        required_tools = []
        for ref, path in tool_root_records:
            if frozen(ref) not in {frozen(item) for item in required_tools}:
                required_tools.append(ref)
            ref_target(ref, {'Tool'}, 'R-TOOL', path.rsplit('/', 1)[0],
                       path.rsplit('/', 1)[0], path)
        for token in required_tokens:
            for tool in skill_tools.get(token, []):
                if frozen(tool) not in {frozen(item) for item in required_tools}:
                    required_tools.append(tool)

        observed_tools = {}

        def observe_tool(ref, request_path, state_path):
            token = frozen(ref)
            target = ref_target(ref, {'Tool'}, 'R-TOOL', request_path,
                                request_path, state_path)
            if token in observed_tools:
                return observed_tools[token]
            payload, requirements, unknown, blocked = None, [], False, False
            if target and target[0] == 'external':
                unknown = True
            elif target:
                _, definition, dp = target
                payload_path = dp + '/payload'
                doc.selected_payloads.add(payload_path)
                payload_ok = result.shape('ToolPayload', definition['payload'], payload_path)
                if isinstance(definition['payload'], dict):
                    payload = definition['payload']
                    blocked = not payload_ok
                    requires_value = payload.get('requires')
                    if isinstance(requires_value, list):
                        requirements = [item for item in requires_value if good('Edition', item)]
                        if len(requirements) != len(requires_value):
                            blocked = True
                        duplicates(requirements, 'R-TOOL', payload_path,
                                   'duplicate Tool requirement')
                    else:
                        blocked = True
                    failures_value = payload.get('failures')
                    if isinstance(failures_value, list):
                        duplicates([item for item in failures_value if good('text', item)],
                                   'R-TOOL', payload_path, 'duplicate Tool failure')
                    else:
                        blocked = True
                    if good('Ref', payload.get('action')):
                        if ref_target(payload['action'], {'Action'}, 'R-TOOL', payload_path,
                                      payload_path, payload_path + '/action') is None:
                            blocked = True
                    else:
                        blocked = True
                else:
                    blocked = True
            else:
                blocked = True
            observed_tools[token] = (payload, requirements, unknown, blocked)
            return observed_tools[token]

        for ref in required_tools:
            observe_tool(ref, bp, False)

        required_tool_tokens = {frozen(ref) for ref in required_tools}
        readable_tool_bindings = []
        for tool, tp in entry['tool_bindings']:
            if good('Ref', tool.get('tool')):
                readable_tool_bindings.append((tool, tp))
            else:
                result.block('R-TOOL', tp)
        tool_groups = defaultdict(list)
        for tool, tp in readable_tool_bindings:
            tool_groups[frozen(tool['tool'])].append(tp)
        ambiguous_tool_bindings = {tp for group in tool_groups.values() if len(group) > 1
                                   for tp in group}
        for ref in required_tools:
            matches = [(tool, tp) for tool, tp in readable_tool_bindings
                       if tool['tool'] == ref]
            if len(matches) > 1:
                for _, tp in matches[1:]:
                    result.find('R-TOOL', tp, 'missing or duplicate required ToolBinding')
            elif not matches and entry['tool_catalog_complete']:
                result.find('R-TOOL', bp, 'missing or duplicate required ToolBinding')
            elif not matches:
                result.block('R-TOOL', bp)
        if not entry['tool_catalog_complete']:
            result.block('R-TOOL', bp)

        for tool, tp in entry['tool_bindings']:
            tool_shape_ok = good('ToolBinding', tool)
            if tool_shape_ok:
                state(tp + '/selected', 'declared' if 'selected' in tool else 'absent')
            tool_ref_ok = good('Ref', tool.get('tool'))
            if tool_ref_ok and frozen(tool['tool']) not in required_tool_tokens and not external_agent:
                if tool_closure_complete:
                    result.find('R-TOOL', tp, 'unused ToolBinding')
                else:
                    result.block('R-TOOL', tp)

            payload, tool_requirements, tool_unknown, tool_blocked = (None, [], False, True)
            if tool_ref_ok:
                payload, tool_requirements, tool_unknown, tool_blocked = observe_tool(
                    tool['tool'], tp, tp + '/tool')

            choices_value = tool.get('choices')
            choices_ok = isinstance(choices_value, list)
            choices = [(choice, tp + '/choices/' + str(j))
                       for j, choice in enumerate(choices_value if choices_ok else [])
                       if isinstance(choice, dict) and good('text', choice.get('id'))]
            choices_complete = choices_ok and len(choices) == len(choices_value)
            if not choices_complete:
                result.block('R-TOOL', tp)
            choice_ids = defaultdict(list)
            ambiguous_choices = set()
            choice_claims = {}
            choice_complete = {}
            for choice, cp in choices:
                choice_ids[choice['id']].append((choice, cp))
                if len(choice_ids[choice['id']]) > 1:
                    result.find('R-TOOL', cp, 'duplicate Implementation id')
                    ambiguous_choices.add(choice['id'])
                claims_value = choice.get('claims')
                claim_identities = ([claim for claim in claims_value
                                     if isinstance(claim, dict)
                                     and good('Edition', claim.get('capability'))]
                                    if isinstance(claims_value, list) else [])
                valid_claims = [claim for claim in claim_identities
                                if good(('enum', ('supported', 'unsupported', 'unknown')),
                                        claim.get('status'))]
                complete = (isinstance(claims_value, list)
                            and all(good('CapabilityClaim', claim)
                                    for claim in claims_value)
                            and good('Edition', choice.get('implementation'))
                            and 'parameters' in choice)
                choice_claims[cp] = valid_claims
                choice_complete[cp] = complete
                if not complete:
                    result.block('R-TOOL', cp)
                if duplicates([claim['capability'] for claim in claim_identities],
                              'R-TOOL', cp,
                              'duplicate implementation capability claim'):
                    ambiguous_choices.add(choice['id'])
                if isinstance(claims_value, list):
                    for k, claim in enumerate(claims_value):
                        if good('CapabilityClaim', claim) and claim['evidence'] is None:
                            state(cp + '/claims/' + str(k) + '/evidence', 'unknown')

            selected_choice_present = 'selected' in tool
            selected_choice = tool.get('selected')
            selected_choice_valid = not selected_choice_present or good('text', selected_choice)
            chosen = (choice_ids.get(selected_choice, [])
                      if selected_choice_present and good('text', selected_choice) else [])
            if selected_choice_present and good('text', selected_choice) and not chosen:
                if choices_complete:
                    result.find('R-TOOL', tp,
                                'selected Implementation does not exist')
                else:
                    result.block('R-TOOL', tp)
            elif len(chosen) > 1:
                result.block('R-TOOL', tp)
            elif not selected_choice_valid:
                result.block('R-TOOL', tp)
            result.complete('R-TOOL')

            if assess_selected:
                chosen_claims = choice_claims.get(chosen[0][1], []) if len(chosen) == 1 else []
                selection_blocked = (not selected_choice_valid or len(chosen) > 1
                                     or (selected_choice_present and not chosen))
                supplied = len(chosen) == 1
                assess(tool_requirements, chosen_claims, supplied, tp,
                       unknown=tool_unknown or bool(payload and payload.get('effects') == 'unknown'),
                       blocked=(configuration_blocked.get(id(configuration), True)
                                or agent_prerequisite_blocked
                                or bp in ambiguous_agent_bindings
                                or tp in ambiguous_tool_bindings
                                or selection_blocked or tool_blocked
                                or not tool_ref_ok or not choices_complete
                                or (bool(chosen) and not choice_complete.get(chosen[0][1], False))
                                or selected_choice in ambiguous_choices),
                       emit_state=tool_shape_ok)
                selected_assessments += 1

        engine_requirements = list(entry['requirements'])
        for token, (_, definition, _, payload, _) in content_records.items():
            if token not in required_tokens:
                continue
            requires_value = payload.get('requires')
            if isinstance(requires_value, list):
                engine_requirements.extend(item for item in requires_value
                                           if good('Edition', item))
            if definition['kind'] == 'Instructions' and good('Edition', payload.get('format')):
                engine_requirements.append(payload['format'])
        engine_requirements.extend(application['adapter'] for application, _ in applications
                                   if good('Edition', application.get('adapter')))
        missing_application = (entry['application_catalog_complete']
                               and any(token not in application_tokens
                                       for token in required_tokens))
        if assess_selected:
            engine = binding.get('engine') if entry['engine_ok'] else None
            assess(engine_requirements, entry['claims'], engine is not None, bp,
                   unknown=external_content,
                   blocked=(configuration_blocked.get(id(configuration), True)
                            or agent_prerequisite_blocked or bp in ambiguous_agent_bindings
                            or content_blocked
                            or not entry['engine_ok'] or not entry['requires_complete']
                            or not entry['claims_complete'] or entry['duplicate_claims']
                            or entry['duplicate_requirements']),
                   not_provided=missing_application or missing_content,
                   emit_state=entry['binding_shape_ok'])
            selected_assessments += 1

    if (selected_record is None and selected_present
            and ('R-COMPATIBILITY', 'blocked') not in result.checks):
        result.block('R-COMPATIBILITY', '/runtime', whole=True)
    elif selected_record is not None and not selected_assessments and not selected_assessment_blocked:
        result.complete('R-COMPATIBILITY')
    for rule in ('R-BINDING', 'R-TOOL', 'R-CONTENT'):
        if rule not in {name for name, _ in result.checks}:
            result.complete(rule)
    return result

class GraphValidation:
    def __init__(self, primary, annexes, resolve=False):
        self.primary, self.annexes, self.resolve = primary, annexes, resolve
        self.result = Result(primary.id, 'G', 'resolved-graph' if resolve else 'unresolved-document', G_RULES + (['G-RESOLVE'] if resolve else []))
        self.loaded, self.annex_results, self.selections = {}, {}, {}
        self.selection_uses = defaultdict(set)
        self.extra_states = []
        self.agreements = []

    def dependency(self, name):
        if name in self.loaded:
            return self.loaded[name]
        self.loaded[name] = None
        record = self.primary.dependencies.get(name)
        if record is None or name in self.primary.bad_dependencies:
            self.result.block('G-RESOLVE', '')
            return None
        dep, path = record
        self.result.complete('G-RESOLVE')
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
                report.exclude('G-TARGET', affected)
                return None
            if not self.resolve:
                report.exclude('G-TARGET', consumer)
                self.extra_states.append({'input': owner.id, 'pointer': field_path, 'state': 'unchecked', 'detail': 'external target excluded'})
                return None
            doc = self.dependency(ref['dependency'])
            if doc is None or doc.syntax:
                report.block('G-TARGET', affected)
                self.result.block('G-RESOLVE', consumer)
                return None
            identity = ref['key']
            if not good(array('Key'), doc.obj.get('exports')):
                self.result.block('G-RESOLVE', consumer)
                report.block('G-TARGET', affected)
                return None
            if identity not in items(doc.obj, 'exports'):
                self.result.find('G-RESOLVE', consumer, 'target not exported')
                report.block('G-TARGET', affected)
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
        report.complete('G-TARGET')
        if self.resolve:
            self.result.complete('G-RESOLVE')
            previous = self.selections.get(key(identity))
            if previous is not None and previous != doc.id:
                self.result.find('G-RESOLVE', consumer, 'selected key in multiple document boundaries')
            self.selections[key(identity)] = doc.id
            self.selection_uses[key(identity)].add(consumer)
        return doc, target[0], target[1]

    def finish(self):
        # All required boundaries are known before identity-dependent agreements.
        boundaries = [self.primary] + [doc for doc in self.loaded.values() if doc is not None]
        collisions = {identity for identity in self.selection_uses
                      if sum(identity in doc.index for doc in boundaries) > 1}
        for identity in collisions:
            for consumer in self.selection_uses[identity]:
                self.result.find('G-RESOLVE', consumer, 'selected key appears in multiple document boundaries')
                self.result.block('G-TARGET', consumer)
        for available, expected, context, consumer, detail, readable in self.agreements:
            if any(key(selected[1]['key']) in collisions for selected in [*available, expected, context]):
                self.result.block('G-TARGET', consumer)
            else:
                self.result.complete('G-TARGET')
                if not any(self.same(selected, expected) for selected in available):
                    if readable:
                        self.result.find('G-TARGET', consumer, detail)
                    else:
                        self.result.block('G-TARGET', consumer)

    def payload(self, selected, schema):
        if selected is None:
            return None
        doc, definition, path = selected
        doc.selected_payloads.add(path + '/payload')
        result = self.annex_result(doc)
        payload = definition['payload']
        result.shape(schema, payload, path + '/payload')
        if isinstance(payload, dict):
            return payload
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
            if good(array('Dependency'), doc.obj.get('dependencies')):
                result.complete('G-RESOLVE')
            else:
                result.block('G-RESOLVE', '/dependencies' if 'dependencies' in doc.obj else '')
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
        if not graphs:
            for rule in G_RULES[2:]:
                result.complete(rule)
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
            if not isinstance(step, dict) or step.get('kind') not in ('invoke', 'condition', 'approval', 'end'):
                for rule in ('G-TARGET', 'G-DATA', 'G-APPROVAL'):
                    result.block(rule, sp)
            if isinstance(step, dict) and step.get('kind') == 'end' and step.get('outcome') not in ('success', 'failure', 'denied'):
                result.block('G-DATA', sp)
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
            result.complete('G-PATH')
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
                else:
                    result.complete('G-DATA')
                    if graph['inputs'].get(binding_value['input']) != expected:
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
                else:
                    result.complete('G-DATA')
                    if producer['outputs'].get(binding_value['port']) != expected:
                        result.find('G-DATA', consumer_path, 'producer output missing or wrong type')
                if not paths_ok:
                    result.block('G-DATA', consumer_path)
                elif consumer_id in reachable(graph['entry'], edges, (binding_value['step'], 'success')):
                    result.find('G-DATA', consumer_path, 'output available without producer success')

        def input_bindings(step, consumer_id, consumer_path):
            if good('Ports', step.get('inputs')) and good(('map', 'Binding'), step.get('bindings')):
                result.complete('G-DATA')
                if set(step['inputs']) != set(step['bindings']):
                    result.find('G-DATA', consumer_path, 'invoke bindings differ from input names')
                for port, b in step['bindings'].items():
                    if port in step['inputs']:
                        binding(b, step['inputs'][port], consumer_id, consumer_path)
            else:
                result.block('G-DATA', consumer_path)
            binding(step.get('context'), 'json', consumer_id, consumer_path)

        if isinstance(graph.get('steps'), list) and all(isinstance(v, dict) and v.get('kind') in ('invoke', 'condition', 'approval', 'end') for v in steps_list):
            if not any(v['kind'] == 'approval' for v in steps_list):
                result.complete('G-APPROVAL')
            if not any(v['kind'] in ('invoke', 'condition', 'approval') or (v['kind'] == 'end' and v.get('outcome') == 'success') for v in steps_list):
                result.complete('G-DATA')
        elif not isinstance(graph.get('steps'), list):
            for rule in ('G-TARGET', 'G-DATA', 'G-APPROVAL'):
                result.block(rule, path)
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
                            target = self.ref(relation['target'], 'Interface' if relation['relation'] == 'exposes' else 'Principal', owner, sp, relpath + '/target', self.annex_result(owner), sp if owner is doc else relpath)
                            (exposure if relation['relation'] == 'exposes' else principals).append(target)
                    comparisons = ((exposure, targets['interface']), (principals, targets['principal']))
                    for available, expected in comparisons:
                        if expected is not None and all(v is not None for v in available):
                            self.agreements.append((available, expected, agent, sp,
                                                    'Agent exposure or Principal mismatch',
                                                    good(array('Relation'), owner.obj.get('relations'))))
                        elif not self.resolve and any(good('Ref', step.get(f)) and 'dependency' in step[f] for f in ('agent', 'interface', 'principal')):
                            result.exclude('G-TARGET', sp)
                        else:
                            result.block('G-TARGET', sp)
                elif not (not self.resolve and good('Ref', step.get('agent')) and 'dependency' in step['agent']):
                    result.block('G-TARGET', sp)
                payload = self.payload(targets['interface'], 'Interface')
                if payload is not None:
                    owner, _, dp = targets['interface']
                    owner_result = self.annex_result(owner)
                    operations = items(payload, 'operations')
                    by_id = defaultdict(list)
                    id_catalog_readable = isinstance(payload.get('operations'), list)
                    if not id_catalog_readable:
                        result.block('G-TARGET', sp)
                        result.block('G-DATA', sp)
                    for i, operation in enumerate(operations):
                        op_path = dp + '/payload/operations/' + str(i)
                        if isinstance(operation, dict) and good('text', operation.get('id')):
                            by_id[operation['id']].append((operation, op_path))
                            if len(by_id[operation['id']]) > 1:
                                owner_result.find('G-TARGET', op_path, 'duplicate operation id')
                        else:
                            id_catalog_readable = False
                    operation_selection_ok = good('text', step.get('operation'))
                    selected = (by_id.get(step['operation'], [])
                                if operation_selection_ok else [])
                    if not selected:
                        if not operation_selection_ok or not id_catalog_readable:
                            result.block('G-TARGET', sp)
                        else:
                            result.find('G-TARGET', sp, 'selected Interface operation does not exist')
                        result.block('G-DATA', sp)
                    elif len(selected) > 1:
                        result.block('G-TARGET', sp)
                        result.block('G-DATA', sp)
                    else:
                        operation, op_path = selected[0]
                        operation_ok = good('Operation', operation)
                        if not operation_ok:
                            # P-SHAPE owns the complete record.  G keeps checking
                            # each independently readable field below.
                            result.block('G-TARGET', sp)
                            result.block('G-DATA', sp)
                        if good(('enum', ('inbound', 'outbound', 'bidirectional')),
                                operation.get('direction')):
                            result.complete('G-TARGET')
                            if operation['direction'] == 'outbound':
                                result.find('G-TARGET', sp, 'outbound operation cannot be invoked')
                        else:
                            result.block('G-TARGET', sp)
                        if good('Ref', operation.get('action')):
                            action = self.ref(operation['action'], 'Action', owner, sp,
                                              op_path + '/action', owner_result, op_path)
                            if action is not None and targets['action'] is not None:
                                self.agreements.append(([action], targets['action'], targets['interface'], sp,
                                                        'Interface operation action mismatch', True))
                            elif 'dependency' in operation['action']:
                                result.exclude('G-TARGET', sp)
                            else:
                                result.block('G-TARGET', sp)
                        else:
                            result.block('G-TARGET', sp)
                        for field in ('inputs', 'outputs'):
                            if good('Ports', operation.get(field)) and good('Ports', step.get(field)):
                                result.complete('G-DATA')
                                if operation[field] != step[field]:
                                    result.find('G-DATA', sp, 'Interface operation port maps differ')
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
                    result.complete('G-DATA')
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
                    if not good(array('Ref'), payload.get('approvers')):
                        self.annex_result(owner).block('G-TARGET', dp + '/payload')
                    elif not payload['approvers']:
                        self.annex_result(owner).complete('G-TARGET')
                    for j, ref in enumerate(items(payload, 'approvers')):
                        ar = self.annex_result(owner)
                        if frozen(ref) in seen:
                            ar.find('G-TARGET', dp + '/payload', 'duplicate approver')
                        seen.add(frozen(ref))
                        self.ref(ref, 'Principal', owner, sp, dp + '/payload/approvers/' + str(j), ar, dp + '/payload')
                call_id = step.get('call')
                call = steps.get(call_id) if isinstance(call_id, str) else None
                if not good('text', call_id) or call_id in ambiguous or (call is None and not index_readable):
                    result.block('G-APPROVAL', sp)
                elif call is None:
                    result.find('G-APPROVAL', sp, 'approval call is not an invoke')
                elif not good(('enum', ('invoke', 'condition', 'approval', 'end')),
                              call.get('kind')):
                    result.block('G-APPROVAL', sp)
                elif call['kind'] != 'invoke':
                    result.find('G-APPROVAL', sp, 'approval call is not an invoke')
                else:
                    result.complete('G-APPROVAL')
                    input_bindings(call, sid, sp)
            elif not good('Step', step):
                result.block('G-TARGET', sp)
                result.block('G-DATA', sp)

        approvals = [(sid, step, sp) for sid, step, sp in records if step.get('kind') == 'approval']
        by_call = defaultdict(list)
        call_catalog_complete = True
        for sid, step, sp in approvals:
            call_ok = good('text', step.get('call'))
            if call_ok:
                by_call[step['call']].append((sid, step, sp))
            else:
                call_catalog_complete = False
            approved_id = step.get('approved')
            if not good('text', approved_id) or approved_id in ambiguous:
                result.block('G-APPROVAL', sp)
                continue
            successor = steps.get(approved_id)
            if successor is None:
                if index_readable:
                    result.find('G-APPROVAL', sp, 'approved successor is missing')
                else:
                    result.block('G-APPROVAL', sp)
            else:
                successor_kind = successor.get('kind')
                kind_ok = good(('enum', ('invoke', 'condition', 'approval', 'end')),
                               successor_kind)
                if not kind_ok:
                    result.block('G-APPROVAL', sp)
                elif successor_kind == 'approval':
                    if call_ok and good('text', successor.get('call')):
                        if successor['call'] != step['call']:
                            result.find('G-APPROVAL', sp, 'approval chain changes call')
                    else:
                        result.block('G-APPROVAL', sp)
                elif successor_kind == 'invoke':
                    if call_ok:
                        if approved_id != step['call']:
                            result.find('G-APPROVAL', sp, 'approved invoke differs from call')
                    else:
                        result.block('G-APPROVAL', sp)
                else:
                    result.find('G-APPROVAL', sp,
                                'approved successor is not a gate or call')

        if approvals and paths_ok:
            incoming = defaultdict(list)
            for source, links in edges.items():
                for label, target in links:
                    incoming[target].append((source, label))
            approval_paths = {sid: sp for sid, _, sp in approvals}
            for call_id, gates in by_call.items():
                call = steps.get(call_id)
                if not call or call.get('kind') != 'invoke':
                    continue
                final = [entry for entry in gates if entry[1].get('approved') == call_id]
                if len(final) > 1:
                    for _, _, sp in final:
                        result.find('G-APPROVAL', sp,
                                    'call must have one final approved gate')
                definitely_bad_incoming = []
                for source, label in incoming[call_id]:
                    source_step = steps.get(source)
                    source_call = (source_step.get('call')
                                   if isinstance(source_step, dict) else None)
                    if label != 'approved':
                        definitely_bad_incoming.append((source, label))
                    elif source in approval_paths and good('text', source_call) and source_call != call_id:
                        definitely_bad_incoming.append((source, label))
                if definitely_bad_incoming:
                    for _, _, sp in final:
                        result.find('G-APPROVAL', sp,
                                    'call must have one final approved gate')
                gate_ids = {sid for sid, _, _ in gates}
                for sid, step, sp in gates:
                    approved_predecessors = [(source, label) for source, label in incoming[sid]
                                             if source in gate_ids and label == 'approved']
                    if len(approved_predecessors) > 1:
                        result.find('G-APPROVAL', sp,
                                    'gate has multiple approved predecessors')
                    elif approved_predecessors and incoming[sid] != approved_predecessors:
                        result.find('G-APPROVAL', sp,
                                    'later gate has another incoming edge')
                    known_later = set()
                    cursor = step.get('approved')
                    while cursor in gate_ids and cursor not in known_later:
                        known_later.add(cursor)
                        cursor = steps[cursor].get('approved')
                    forbidden = known_later | {call_id}
                    if (reachable(step['denied'], edges) & forbidden
                            or reachable(step['failure'], edges) & forbidden):
                        result.find('G-APPROVAL', sp,
                                    'denied or failure path bypasses approval')
            if not call_catalog_complete:
                for _, _, sp in approvals:
                    result.block('G-APPROVAL', sp)
            else:
                for call_id, gates in by_call.items():
                    call = steps.get(call_id)
                    if not call or call.get('kind') != 'invoke':
                        continue
                    gate_ids = {sid for sid, _, _ in gates}
                    final = [entry for entry in gates if entry[1].get('approved') == call_id]
                    final_incoming_ok = (len(final) == 1
                                         and incoming[call_id] == [(final[0][0], 'approved')])
                    if not final_incoming_ok:
                        for _, _, sp in final or gates:
                            result.find('G-APPROVAL', sp, 'call must have one final approved gate')
                    for sid, step, sp in gates:
                        approved_predecessors = [(source, label) for source, label in incoming[sid]
                                                 if source in gate_ids and label == 'approved']
                        if len(approved_predecessors) > 1:
                            result.find('G-APPROVAL', sp, 'gate has multiple approved predecessors')
                        elif approved_predecessors and incoming[sid] != approved_predecessors:
                            result.find('G-APPROVAL', sp, 'later gate has another incoming edge')
                        later = set()
                        cursor = step.get('approved')
                        while cursor in gate_ids and cursor not in later:
                            later.add(cursor)
                            cursor = steps[cursor].get('approved')
                        if cursor != call_id:
                            result.find('G-APPROVAL', sp, 'approved chain does not reach call')
                        forbidden = later | {call_id}
                        if (reachable(step['denied'], edges) & forbidden
                                or reachable(step['failure'], edges) & forbidden):
                            result.find('G-APPROVAL', sp,
                                        'denied or failure path bypasses approval')
                    starts = [sid for sid, _, _ in gates
                              if not any(source in gate_ids and label == 'approved'
                                         for source, label in incoming[sid])]
                    if len(starts) != 1:
                        for _, _, sp in gates:
                            result.find('G-APPROVAL', sp,
                                        'gates do not form one ordered chain')
            result.complete('G-APPROVAL')
        elif approvals:
            for _, _, sp in approvals:
                result.block('G-APPROVAL', sp)


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
    if runtime_mode and isinstance(runtime, dict) and isinstance(runtime.get('configurations'), list):
        for i, configuration in enumerate(runtime['configurations']):
            cp = '/runtime/configurations/' + str(i)
            if not isinstance(configuration, dict) or not isinstance(configuration.get('agents'), list):
                continue
            if good('Configuration', configuration):
                state(cp, 'declared')
            for j, binding in enumerate(configuration['agents']):
                bp = cp + '/agents/' + str(j)
                if not isinstance(binding, dict):
                    continue
                opaque(bp + '/parameters')
                for k, tool in enumerate(items(binding, 'tools')):
                    tp = bp + '/tools/' + str(k)
                    if not isinstance(tool, dict):
                        continue
                    for n, choice in enumerate(items(tool, 'choices')):
                        ip = tp + '/choices/' + str(n)
                        if not isinstance(choice, dict):
                            continue
                        opaque(ip + '/parameters')
                for k, application in enumerate(items(binding, 'applications')):
                    if not isinstance(application, dict):
                        continue
                    opaque(bp + '/applications/' + str(k) + '/parameters')
                if not good('AgentBinding', binding):
                    continue
                for k, claim in enumerate(binding['claims']):
                    if claim['evidence'] is None:
                        state(bp + '/claims/' + str(k) + '/evidence', 'unknown')
                for k, tool in enumerate(binding['tools']):
                    for n, choice in enumerate(tool['choices']):
                        for m, claim in enumerate(choice['claims']):
                            if claim['evidence'] is None:
                                state(bp + '/tools/' + str(k) + '/choices/' + str(n)
                                      + '/claims/' + str(m) + '/evidence', 'unknown')
        for i, definition in enumerate(items(obj, 'definitions')):
            dp = '/definitions/' + str(i)
            if dp + '/payload' not in doc.selected_payloads or not isinstance(definition, dict):
                continue
            payload = definition.get('payload')
            if not isinstance(payload, dict):
                continue
            if definition.get('kind') == 'Tool':
                for j, _ in enumerate(items(payload, 'failures')):
                    opaque(dp + '/payload/failures/' + str(j))
            elif definition.get('kind') == 'Instructions':
                opaque(dp + '/payload/body')
            elif definition.get('kind') == 'Skill':
                opaque(dp + '/payload/preconditions')
                opaque(dp + '/payload/completion')
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
        r.complete('P-SYNTAX')
        if doc.syntax:
            r.find('P-SYNTAX', detail=str(doc.syntax), byte=doc.syntax.offset)
        results.append(r)
    elif operation in ('exchange', 'lossyExchange'):
        r = Result('primary', 'exchange', None, ['E-PRESERVE' if operation == 'exchange' else 'E-LOSS'])
        if operation == 'lossyExchange':
            r.find('E-LOSS', '', 'candidate edition permits no lossy exchange')
            loss_records = losses or [{'input': 'primary', 'location': {'pointer': ''}, 'information': 'unspecified requested loss', 'reason': 'no omission permission in modular candidate-1', 'permission': None}]
        else:
            r.complete('E-PRESERVE')
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
            extra_states = doc.r_states
        elif operation in ('validateG', 'resolveG'):
            g = GraphValidation(doc, annexes, operation == 'resolveG')
            g.check()
            g.finish()
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
    report = {'contract': CONTRACT, 'processor': {'identity': 'agsdl-experimental/python-modular-reader', 'version': 'candidate-1.0'},
              'operation': operation, 'inputs': [{'id': name, 'sha256': digest(raw)} for name, raw in input_bytes.items()],
              'results': [r.export() for r in results], 'inventory': {'tree': doc.tree, 'states': states, 'opaque': slices},
              'losses': loss_records, 'outputs': [{'id': name, 'sha256': digest(raw)} for name, raw in artifacts.items()]}
    return {'report': report, 'artifacts': artifacts}
