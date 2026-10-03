"""Contract-authored cases, independent of either semantic reader.

Expected codes are exhaustive. Additional pointer assertions pin important
report observations; the comparator also compares every report field.
"""
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EDITION = {'identity': 'example/test', 'version': '1'}
BINDING = {'contract': EDITION, 'implementation': EDITION}
BASE = {'contract': 'agsdl-exp-flow-0.2-c1', 'id': 'independent',
        'bindings': {'engine': BINDING}, 'configurations': {'main': {'engine': 'engine'}},
        'agents': {'worker': {'configuration': 'main'}}}
SCOPE = {'action': 'publish', 'resources': ['repository'], 'context': {'value': {}}}
PREDICATE = {'equals': [{'value': True}, {'value': True}]}


def cases():
    result = []

    def add(name, doc=None, codes=(), assertions=None, source='Static checks and evidence limits', raw=None):
        result.append({'name': name, 'bytes': raw if raw is not None else
                       (json.dumps(doc, ensure_ascii=False, separators=(',', ':')) + '\n').encode(),
                       'codes': sorted(codes), 'assertions': assertions or {}, 'source': source})

    def mutate(name, fn, codes=(), assertions=None, source='Document and content'):
        doc = deepcopy(BASE)
        fn(doc)
        add(name, doc, codes, assertions, source)

    add('minimal', BASE)
    for path in sorted((ROOT / 'examples').glob('*.json')):
        add('example-' + path.stem, raw=path.read_bytes(), source='Read or check an example')
    mutate('literal-nonreferences', lambda d: d.update(content={'literal': {'value': {
        'ref': 'missing', 'uri': 'bad uri', 'baseUri': False, 'agent': 'missing',
        '__proto__': {'polluted': True}, 'constructor': {}, 'toString': None}}}))
    mutate('unknown-configuration', lambda d: d['agents']['worker'].update(configuration='missing'), ['REFERENCE'])
    mutate('unknown-engine', lambda d: d['configurations']['main'].update(engine='missing'), ['REFERENCE'])
    mutate('unknown-content', lambda d: d['agents']['worker'].update(prompt=[{'ref': 'missing'}]), ['REFERENCE'])
    mutate('unknown-tool', lambda d: d['configurations']['main'].update(tools={'test': 'missing'}), ['REFERENCE'])
    mutate('duplicate-skill', lambda d: (d.update(skills={'guide': {}}), d['agents']['worker'].update(skills=['guide', 'guide'])), ['DUPLICATE'])
    mutate('resource-collision', lambda d: (d.update(skills={'guide': {'resources': {'x': {'value': 1}}}}),
        d['agents']['worker'].update(skills=['guide'], resources={'x': {'value': 2}})), ['RESOURCE_COLLISION'])
    mutate('result-format', lambda d: d['agents']['worker'].update(interface={'outputMediaTypes': ['text/plain'],
        'results': {'report': {'mediaTypes': ['application/json']}}}), ['OUTPUT_FORMAT'])
    mutate('constraint-invalid-required', lambda d: d['agents']['worker'].update(interface={'results': {'r': {
        'mediaTypes': ['application/json'], 'valueSchema': {'type': 'object', 'required': ['missing']}}}}), ['VALUE_SCHEMA'])
    mutate('constraint-enum-number-boolean', lambda d: d['agents']['worker'].update(interface={'results': {'r': {
        'mediaTypes': ['application/json'], 'valueSchema': {'type': 'integer', 'enum': [True]}}}}), ['VALUE_SCHEMA'])
    mutate('constraint-enum-equal-decimals', lambda d: d['agents']['worker'].update(interface={'results': {'r': {
        'mediaTypes': ['application/json'], 'valueSchema': {'type': 'number', 'enum': [1, 1.0]}}}}), ['VALUE_SCHEMA'])
    mutate('constraint-special-property', lambda d: d['agents']['worker'].update(interface={'results': {'r': {
        'mediaTypes': ['application/json'], 'valueSchema': {'type': 'object', 'properties': {
        '__proto__': {'type': 'integer'}, 'constructor': {'type': 'boolean'}},
        'required': ['__proto__'], 'enum': [{'__proto__': 2, 'constructor': False}]}}}}))
    mutate('uri-resolved', lambda d: d.update(baseUri='https://example.invalid/a/b', content={'x': {'uri': '../c?#'}}),
        assertions={'/sources/0/resolved': 'https://example.invalid/c?#'})
    mutate('uri-unresolved', lambda d: d.update(content={'x': {'uri': '../c'}}),
        assertions={'/sources/0/status': 'unresolved', '/sources/0/resolved': None})
    mutate('uri-absolute-dots', lambda d: d.update(content={'x': {'uri': 'custom:/a/../b/%2e?x#'}}),
        assertions={'/sources/0/resolved': 'custom:/b/%2e?x#'})
    mutate('uri-invalid', lambda d: d.update(content={'x': {'uri': 'bad uri'}}), ['URI'])
    mutate('base-invalid', lambda d: d.update(baseUri='relative/base'), ['URI'])
    mutate('literal-source-invalid', lambda d: d.update(flow={'entry': 'p', 'steps': {'p': {'type': 'prepare',
        'message': {'resources': {'x': {'source': {'value': {'ref': 'missing'}}}}}}}}), ['SOURCE'])
    mutate('literal-source-uri', lambda d: d.update(baseUri='https://example.invalid/a/',flow={'entry': 'p', 'steps': {'p': {
        'type': 'prepare', 'message': {'resources': {'x': {'source': {'value': {'uri': 'x'}}}}}}}}))
    requirement = {'contract': EDITION, 'parameters': {'a': 1, 'nested': {'b': True}}}
    def claims(d, status='supported', evidence=True):
        d['configurations']['main'].update(requires=[requirement], claims=[{'requirement': deepcopy(requirement),
            'status': status, **({'evidence': 'a' * 64} if evidence else {})}])
    mutate('support-known', claims, assertions={'/support/1/status': 'declared-supported'})
    mutate('support-incompatible', lambda d: claims(d, 'unsupported'), assertions={'/support/1/status': 'incompatible'})
    mutate('support-no-evidence', lambda d: claims(d, evidence=False), assertions={'/support/1/status': 'unknown'})
    mutate('support-parameter-mismatch', lambda d: (claims(d), d['configurations']['main']['claims'][0]['requirement'].update(parameters={})),
        assertions={'/support/1/status': 'unknown'})
    mutate('support-absent-empty-parameters', lambda d: d['configurations']['main'].update(requires=[{'contract': EDITION}],
        claims=[{'requirement': {'contract': EDITION, 'parameters': {}}, 'status': 'supported', 'evidence': 'a'*64}]),
        assertions={'/support/1/status': 'unknown'})
    mutate('duplicate-claim', lambda d: (claims(d), d['configurations']['main']['claims'].append(deepcopy(d['configurations']['main']['claims'][0]))), ['CLAIM'])
    mutate('duplicate-requirement', lambda d: d['bindings']['engine'].update(requires=[requirement, deepcopy(requirement)]), ['DUPLICATE'])
    mutate('dynamic-alternatives', lambda d: (d['configurations'].update(other={'engine': 'engine'}), d['agents']['worker'].update(
        configuration={'select': {'path': ['mode']}, 'cases': {'a': 'main', 'b': 'other'}})))
    mutate('condition-routes', lambda d: d.update(flow={'entry': 'c', 'steps': {'c': {'type': 'condition', 'test': PREDICATE,
        'next': {'true': ['a'], 'false': ['a']}}, 'a': {'type': 'agent', 'agent': 'worker'}}}))
    mutate('condition-missing-route', lambda d: d.update(flow={'entry': 'c', 'steps': {'c': {'type': 'condition',
        'test': PREDICATE, 'next': {'true': []}}}}), ['SHAPE'])
    mutate('decision-route-mismatch', lambda d: d.update(flow={'entry': 'a', 'steps': {'a': {'type': 'agent', 'agent': 'worker',
        'decision': {'binding': 'engine', 'choices': ['yes']}, 'next': {'no': []}}}}), ['ROUTES'])
    mutate('duplicate-destination', lambda d: d.update(flow={'entry': 'a', 'steps': {'a': {'type': 'agent', 'agent': 'worker',
        'next': ['b', 'b']}, 'b': {'type': 'agent', 'agent': 'worker'}}}), ['DUPLICATE'])
    mutate('unreachable-step', lambda d: d.update(flow={'entry': 'a', 'steps': {'a': {'type': 'agent', 'agent': 'worker'},
        'b': {'type': 'agent', 'agent': 'worker'}}}), ['UNREACHABLE'])
    def steering(d):
        d['flow']={'entry': 'fork', 'steps': {'fork': {'type': 'prepare', 'message': {}, 'next': ['a', 's']},
            'a': {'type': 'agent', 'agent': 'worker'}, 's': {'type': 'agent', 'agent': 'worker', 'delivery': 'steering', 'steers': 'a'}}}
    mutate('steering-owner', steering)
    mutate('steering-continuation', lambda d: (steering(d), d['flow']['steps']['s'].update(next=['a'])), ['STEERING'])
    mutate('queued-steers', lambda d: (steering(d), d['flow']['steps']['s'].update(delivery='queue')), ['STEERING'])
    def join(d):
        d['flow']={'entry': 'fork','steps': {'fork': {'type': 'prepare','message': {},'next': ['a','b']},
            'a': {'type': 'agent','agent': 'worker','next': ['join']}, 'b': {'type': 'agent','agent': 'worker','next': ['join']},
            'join': {'type': 'join','after': 'fork','members': ['a','b']}}}
    mutate('join-all', join)
    mutate('join-first', lambda d: (join(d), d['flow']['steps']['join'].update(mode='first',accept=PREDICATE)))
    mutate('join-policy', lambda d: (join(d), d['flow']['steps']['join'].update(mode='first')), ['JOIN_POLICY'])
    mutate('join-member-error', lambda d: (join(d), d['flow']['steps']['a'].update(onError=['fork'])), ['JOIN_GROUP'])
    def composition(d):
        d['compositions']={'part': {'entry':'a','outputs':['done'],'agentParameters':['actor'], 'steps': {
            'a': {'type':'agent','agent':{'parameter':'actor'},'next':[{'output':'done'}]}}}}
        d['flow']={'entry':'use','steps':{'use':{'type':'compose','composition':'part','agents':{'actor':'worker'},'next':{'done':[]}}}}
    mutate('composition-origin', composition, assertions={'/expandedFlow/entry': ['use','a'],
        '/expandedFlow/steps/0/source':'/compositions/part/steps/a','/expandedFlow/steps/0/invocation':'/flow/steps/use',
        '/expandedFlow/steps/0/step/agent':'worker'})
    mutate('composition-parameter', lambda d: (composition(d),d['flow']['steps']['use'].update(agents={})), ['COMPOSITION','REFERENCE'])
    mutate('composition-output', lambda d: (composition(d),d['flow']['steps']['use'].update(next={'other':[]})), ['COMPOSITION'])
    mutate('composition-serial', lambda d: (composition(d),d['compositions']['part']['steps']['a'].update(next=[{'output':'done'},{'output':'done'}])), ['COMPOSITION','DUPLICATE'])
    mutate('unused-body-reference', lambda d: (composition(d),d.pop('flow'),d['compositions']['part']['steps']['a'].update(agent='missing')), ['REFERENCE'])
    def approval(d):
        d['flow']={'entry':'gate','steps':{'gate':{'type':'approval','binding':'engine','call':'act','timeoutMs':1,'validForMs':2,
            'next':{'approved':['act'],'denied':[]}},'act':{'type':'call','binding':'engine','scope':deepcopy(SCOPE)}}}
    mutate('approval-valid', approval)
    mutate('approval-scope', lambda d: (approval(d),d['flow']['steps']['act'].pop('scope')), ['SCOPE'])
    mutate('approval-bypass', lambda d: (approval(d),d['flow']['steps']['gate']['next'].update(denied=['act'])), ['APPROVAL'])
    mutate('effect-scope', lambda d: (d['bindings']['engine'].update(effects='external'),d.update(flow={'entry':'act','steps':{
        'act':{'type':'call','binding':'engine'}}})), ['SCOPE'])
    mutate('unknown-field', lambda d: d.update(unexpected=True), ['SHAPE'])
    mutate('boolean-integer', lambda d: d.update(flow={'entry':'a','steps':{'a':{'type':'agent','agent':'worker','maxVisits':True}}}), ['SHAPE'])
    mutate('large-integer', lambda d: d.update(flow={'entry':'a','steps':{'a':{'type':'agent','agent':'worker','maxVisits':9007199254740993}}}))
    mutate('steering-empty-next', lambda d: (steering(d), d['flow']['steps']['s'].update(next=[])), ['STEERING'])
    mutate('steering-entry', lambda d: (steering(d), d['flow'].update(entry='s'), d['flow']['steps']['s'].update(onError=['fork'])), ['STEERING'])
    mutate('steering-wrong-agent', lambda d: (steering(d), d['agents'].update(other={'configuration':'main'}),
        d['flow']['steps']['s'].update(agent='other')), ['STEERING'])
    mutate('unknown-destination', lambda d: d.update(flow={'entry':'a','steps':{'a':{'type':'agent','agent':'worker','next':['missing']}}}), ['REFERENCE'])
    mutate('unknown-flow-entry', lambda d: d.update(flow={'entry':'missing','steps':{'a':{'type':'agent','agent':'worker'}}}), ['REFERENCE','UNREACHABLE'])
    mutate('join-duplicate-member', lambda d: (join(d),d['flow']['steps']['join'].update(members=['a','a'])), ['JOIN_GROUP'])
    mutate('join-foreign-incoming', lambda d: (join(d),d['flow']['steps']['fork']['next'].append('join')), ['JOIN_GROUP'])
    mutate('join-steering-member', lambda d: (join(d),d['flow']['steps']['b'].update(delivery='steering',steers='a')), ['STEERING'])
    mutate('scope-duplicate-resources', lambda d: (approval(d),d['flow']['steps']['act']['scope'].update(resources=['x','x'])), ['DUPLICATE'])
    def gates(d):
        approval(d)
        d['flow']['steps']['gate']['next']['approved']=['gateTwo']
        d['flow']['steps']['gateTwo']={'type':'approval','binding':'engine','call':'act','timeoutMs':1,'validForMs':2,
            'next':{'approved':['act'],'denied':['gate']}}
    mutate('approval-chain', gates)
    mutate('approval-chain-bypass', lambda d: (gates(d),d['flow']['steps']['gate']['next'].update(denied=['act'])), ['APPROVAL'])
    mutate('approval-chain-cycle', lambda d: (gates(d),d['flow']['steps']['gateTwo']['next'].update(approved=['gate'])), ['APPROVAL','UNREACHABLE'])
    mutate('approval-missing-target', lambda d: (approval(d),d['flow']['steps']['gate'].update(call='missing')), ['APPROVAL'])
    mutate('approval-bad-approved-target', lambda d: (approval(d),d['flow']['steps']['gate']['next'].update(approved=['gate'])), ['APPROVAL','UNREACHABLE'])
    mutate('composition-missing-body', lambda d: (composition(d),d['flow']['steps']['use'].update(composition='absent')), ['REFERENCE'])
    mutate('composition-duplicate-parameters', lambda d: (composition(d),d['compositions']['part'].update(agentParameters=['actor','actor'])), ['DUPLICATE'])
    mutate('composition-missing-normal-route', lambda d: (composition(d),d['compositions']['part']['steps']['a'].pop('next')), ['COMPOSITION'])
    mutate('composition-unexported-output', lambda d: (composition(d),d['compositions']['part'].update(outputs=['done','other']),
        d['flow']['steps']['use']['next'].update(other=[])), ['COMPOSITION'])
    mutate('composition-template-reference', lambda d: (composition(d),d['compositions']['part']['steps']['a'].update(agent='missing')), ['REFERENCE'])
    mutate('composition-error-export', lambda d: (composition(d),d['compositions']['part']['steps']['a'].update(onError=[{'error':True}]),
        d['flow']['steps']['use'].update(onError=['recover']),d['flow']['steps'].update(recover={'type':'prepare','message':{}})))
    mutate('binding-prototype-name', lambda d: d['configurations']['main'].update(engine='constructor'), ['REFERENCE'])
    mutate('unicode-pointer', lambda d: d['agents']['worker'].update(interface={'results':{'r':{'mediaTypes':['application/json'],
        'valueSchema':{'type':'object','properties':{'\ue000':{'type':'integer','enum':[False]},'𐀀':{'type':'integer','enum':[False]},
        '~/':{'type':'integer','enum':[False]}}}}}}), ['VALUE_SCHEMA'])
    mutate('exact-enum-large-distinct', lambda d: d['agents']['worker'].update(interface={'results':{'r':{'mediaTypes':['application/json'],
        'valueSchema':{'type':'integer','enum':[9007199254740992,9007199254740993]}}}}))
    mutate('constraint-nested-array', lambda d: d['agents']['worker'].update(interface={'results':{'r':{'mediaTypes':['application/json'],
        'valueSchema':{'type':'array','items':{'type':'object','properties':{'x':{'type':'boolean'}},'required':['x'],'additionalProperties':False},
            'enum':[[{'x':1}]]}}}}), ['VALUE_SCHEMA'])
    mutate('support-conflicting-claims', lambda d: (claims(d),d['configurations']['main']['claims'].append(
        {'requirement':deepcopy(requirement),'status':'unsupported'})), ['CLAIM'])
    mutate('support-independent-unknown', lambda d: (claims(d,'unsupported'),d['configurations']['main']['requires'].append({'contract':{'identity':'example/other','version':'1'}})),
        assertions={'/support/1/status':'incompatible','/support/1/requirements/1/status':'unknown'})
    mutate('dynamic-same-alternative', lambda d: d['agents']['worker'].update(configuration={'select':{'path':['mode']},'cases':{'one':'main','two':'main'}}))
    mutate('base-invalid-with-source', lambda d: d.update(baseUri='relative',content={'x':{'uri':'asset'}}), ['URI'])
    mutate('uri-ipv6', lambda d: d.update(content={'x':{'uri':'https://[2001:db8::1]:443/a'}}))
    mutate('uri-invalid-ipv6', lambda d: d.update(content={'x':{'uri':'https://[not-ip]/a'}}), ['URI'])
    mutate('uri-fragment-base', lambda d: d.update(baseUri='https://example.invalid/#'), ['URI'])
    mutate('duplicate-skill-requirement', lambda d: d.update(skills={'guide':{'requires':[requirement,deepcopy(requirement)]}}), ['DUPLICATE'])
    def join_composition(d, anchor=False):
        join(d)
        d['compositions']={'part':{'entry':'inside','outputs':['done'],'steps':{
            'inside':{'type':'prepare','message':{},'next':[{'output':'done'}]}}}}
        name='fork' if anchor else 'a'
        d['flow']['steps'][name]={'type':'compose','composition':'part','agents':{},'next':{'done':['a','b'] if anchor else ['join']}}
    mutate('join-composition-member', join_composition, ['COMPOSITION'])
    mutate('join-composition-anchor', lambda d: join_composition(d, True))
    def expanded_reference(d):
        composition(d)
        d['compositions']['part']['steps']['a']['next']=['missing']
    mutate('composition-expanded-reference', expanded_reference, ['COMPOSITION','REFERENCE'])
    mutate('composition-repeated-scope', lambda d: (composition(d),d['compositions']['part']['steps']['a'].update(scope={'action':'x','resources':['x','x'],'context':{'value':None}})), ['DUPLICATE'])
    mutate('composition-template-content', lambda d: (composition(d),d['compositions']['part']['steps'].update(a={'type':'prepare',
        'message':{'prompt':[{'ref':'missing'}]},'next':[{'output':'done'}]})), ['REFERENCE'])
    raw=json.dumps(BASE,separators=(',',':')).encode()
    add('duplicate-key',raw=raw.replace(b'"id":"independent"',b'"id":"independent","id":"second"'),codes=['PARSE'])
    add('unpaired-surrogate',raw=raw.replace(b'"independent"',b'"\\ud800"'),codes=['PARSE'])
    add('invalid-utf8',raw=raw.replace(b'"independent"',b'"\xff"'),codes=['PARSE'])
    add('nan',raw=raw.replace(b'"independent"',b'NaN'),codes=['PARSE'])
    exact=deepcopy(BASE);exact['flow']={'entry':'a','steps':{'a':{'type':'agent','agent':'worker','maxVisits':'NUMBER'}}}
    for name,num,codes in [('fraction-large','9007199254740992.1',['SHAPE']),('integer-exponent','1e30',[]),('fraction-small','1e-30',['SHAPE'])]:
        add(name,raw=json.dumps(exact).replace('"NUMBER"',num).encode(),codes=codes)
    return result
