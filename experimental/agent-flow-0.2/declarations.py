"""Bounded value constraints, source observations and scoped declared support."""
from reader import equal, pointer, shape
from sources import normalize_source, valid_base


def constraint_matches(value, constraint):
    # The bundled shape evaluator understands these types. Constraint shape was
    # checked before this call; no user keyword is silently ignored.
    if not shape(value, {'type': constraint['type']}):
        return False
    if 'enum' in constraint and not any(equal(value, v) for v in constraint['enum']):
        return False
    if constraint['type'] == 'array':
        return 'items' not in constraint or all(constraint_matches(v, constraint['items']) for v in value)
    if constraint['type'] == 'object':
        props = constraint.get('properties', {})
        return (all(k in value for k in constraint.get('required', [])) and
                all(constraint_matches(v, props[k]) if k in props else constraint.get('additionalProperties', True)
                    for k, v in value.items()))
    return True


def check_constraint(constraint, path, fail):
    if 'enum' in constraint:
        others = {k: v for k, v in constraint.items() if k != 'enum'}
        for i, value in enumerate(constraint['enum']):
            if any(equal(value, v) for v in constraint['enum'][:i]) or not constraint_matches(value, others):
                fail('VALUE_SCHEMA', path + ['enum', i])
    if constraint['type'] == 'object':
        required = constraint.get('required', [])
        if len(required) != len(set(required)) or not set(required) <= constraint.get('properties', {}).keys():
            fail('VALUE_SCHEMA', path + ['required'])
        for key, child in constraint.get('properties', {}).items():
            check_constraint(child, path + ['properties', key], fail)
    if 'items' in constraint:
        check_constraint(constraint['items'], path + ['items'], fail)


def assess(requirements, claims):
    items = []
    for requirement in requirements:
        claim = next((c for c in claims if equal(c['requirement'], requirement)), None)
        status = 'unknown'
        if claim:
            if claim['status'] == 'unsupported':
                status = 'incompatible'
            elif claim['status'] == 'supported' and 'evidence' in claim:
                status = 'declared-supported'
        items.append({'requirement': requirement, 'status': status})
    aggregate = next((s for s in ('incompatible', 'unknown', 'declared-supported') if any(x['status'] == s for x in items)), 'not-requested')
    return {'status': aggregate, 'requirements': items}


def check_declarations(document, fail):
    sources, support, needs = [], [], []
    base = document.get('baseUri')
    if base is not None:
        try:
            valid_base(base)
        except ValueError:
            fail('URI', ['baseUri'])
            base = None

    def source(value, path):
        if 'ref' in value or 'select' in value or 'source' in value:
            return
        try:
            normalize_source(value, base, pointer(path), sources)
        except ValueError:
            fail('URI', path)

    def content(container, path):
        for i, value in enumerate(container.get('prompt', [])):
            source(value, path + ['prompt', i])
        for key, value in container.get('resources', {}).items():
            source(value, path + ['resources', key])

    def need(path, name):
        needs.append({'path': pointer(path), 'need': name, 'status': 'unassessed'})

    for key, value in document.get('content', {}).items():
        source(value, ['content', key])
    for catalog in ('bindings', 'configurations', 'skills'):
        for name, item in document.get(catalog, {}).items():
            loc = [catalog, name]
            reqs, claims = item.get('requires', []), item.get('claims', [])
            for i, req in enumerate(reqs):
                if any(equal(req, r) for r in reqs[:i]):
                    fail('DUPLICATE', loc + ['requires', i])
            for i, claim in enumerate(claims):
                if any(equal(claim['requirement'], c['requirement']) for c in claims[:i]):
                    fail('CLAIM', loc + ['claims', i])
            if catalog == 'bindings':
                support.append({'path': pointer(loc), **assess(reqs, claims)})
            if catalog == 'skills':
                content(item, loc)
    for name, agent in document['agents'].items():
        loc = ['agents', name]
        content(agent, loc)
        need(loc, 'agent-continuity-and-initialization')
        need(loc, 'content-role-and-media-delivery')
        interface = agent.get('interface', {})
        for field in ('inputMediaTypes', 'outputMediaTypes'):
            if field in interface:
                need(loc + ['interface', field], 'combined-media-path')
        for result, rule in interface.get('results', {}).items():
            path = loc + ['interface', 'results', result]
            need(path, 'required-result-delivery')
            if 'valueSchema' in rule:
                check_constraint(rule['valueSchema'], path + ['valueSchema'], fail)
                need(path + ['valueSchema'], 'structured-result-check')
        selection = agent['configuration']
        alternatives = [selection] if isinstance(selection, str) else sorted(set(selection['cases'].values()))
        if not isinstance(selection, str):
            need(loc + ['configuration'], 'retained-configuration-selection')
        for config_name in alternatives:
            config = document['configurations'].get(config_name)
            if config is None:
                continue
            reqs = list(config.get('requires', []))
            for skill in agent.get('skills', []):
                for req in document.get('skills', {}).get(skill, {}).get('requires', []):
                    if not any(equal(req, old) for old in reqs):
                        reqs.append(req)
            support.append({'path': pointer(loc), 'configuration': config_name,
                            'selection': 'fixed' if isinstance(selection, str) else 'conditional',
                            **assess(reqs, config.get('claims', []))})
    graphs = [(['flow'], document['flow'])] if 'flow' in document else []
    graphs += [(['compositions', n], c) for n, c in document.get('compositions', {}).items()]
    for path, graph in graphs:
        for name, step in graph['steps'].items():
            loc = path + ['steps', name]
            if step['type'] == 'prepare':
                content(step['message'], loc + ['message'])
                for key, resource in step['message'].get('resources', {}).items():
                    if 'source' in resource and 'value' in resource['source']:
                        from reader import SCHEMA
                        literal = resource['source']['value']
                        if not shape(literal, SCHEMA['$defs']['Source']):
                            fail('SOURCE', loc + ['message', 'resources', key])
                        else:
                            source(literal, loc + ['message', 'resources', key, 'source', 'value'])
            elif step['type'] in ('agent', 'call', 'approval', 'compose', 'join'):
                need(loc, {'agent': 'steering' if step.get('delivery') == 'steering' else 'queued-delivery',
                           'call': 'external-call-contract', 'approval': 'actual-invocation-approval',
                           'compose': 'composition-expansion', 'join': 'group-correlation-and-stopping'}[step['type']])
    return {'sources': sources, 'support': support, 'coreNeeds': needs,
            'unassessed': [x['path'] for x in sources if x['status'] == 'unresolved']}
