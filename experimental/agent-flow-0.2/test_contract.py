"""Adversarial declarations and supplied records for the proposed modular contract."""
import copy
from decimal import Decimal
import json
from pathlib import Path
import subprocess
import sys
import unittest

from reader import SCHEMA, equal, loads, shape, validate
from check_completion import check_completion
from check_delivery import check_delivery
from check_admission import capture, check_admission
from modular import selected_step
from sources import agent_content, normalize_completion, normalize_message, prepare_message, resolve_uri

ROOT = Path(__file__).parent


def example(name):
    return loads((ROOT / 'examples' / (name + '.json')).read_bytes())


def document_cases():
    result = []
    def case(name, base, mutate, code):
        d = example(base)
        mutate(d)
        result.append((name, d, code))
    for name in ('reusable-checker', 'protected-publication', 'structured-report'):
        result.append((name, example(name), None))
    case('missing-parameter', 'reusable-checker', lambda d: d['flow']['steps']['first']['agents'].clear(), 'COMPOSITION')
    case('extra-parameter', 'reusable-checker', lambda d: d['flow']['steps']['first']['agents'].update(extra='reviewer'), 'COMPOSITION')
    case('parameter-agent-absent', 'reusable-checker', lambda d: d['flow']['steps']['first']['agents'].update(reviewer='absent'), 'REFERENCE')
    case('undeclared-parameter', 'reusable-checker', lambda d: d['compositions']['verify']['steps']['review'].update(agent={'parameter':'absent'}), 'COMPOSITION')
    case('unknown-output', 'reusable-checker', lambda d: d['compositions']['verify']['steps']['condition']['next'].update(true=[{'output':'absent'}]), 'COMPOSITION')
    case('no-output-map', 'reusable-checker', lambda d: d['flow']['steps']['first']['next'].pop('pass'), 'COMPOSITION')
    case('missing-body-entry', 'reusable-checker', lambda d: d['compositions']['verify'].update(entry='absent'), 'REFERENCE')
    case('body-parallel-escape', 'reusable-checker', lambda d: d['compositions']['verify']['steps']['review'].update(next=['check','condition']), 'COMPOSITION')
    case('body-silent-normal-exit', 'reusable-checker', lambda d: d['compositions']['verify']['steps']['review'].pop('next'), 'COMPOSITION')
    case('body-recursion', 'reusable-checker', lambda d: d['compositions']['verify']['steps'].update(recur={'type':'compose','composition':'verify','agents':{},'next':{}}), 'SHAPE')
    case('body-steering', 'reusable-checker', lambda d: d['compositions']['verify']['steps']['review'].update(delivery='steering',steers='review'), 'SHAPE')
    case('body-join', 'reusable-checker', lambda d: d['compositions']['verify']['steps'].update(join={'type':'join','after':'review','members':['check','condition']}), 'SHAPE')
    case('body-error-as-normal', 'reusable-checker', lambda d: d['compositions']['verify']['steps']['check'].update(next=[{'error':True}]), 'SHAPE')
    case('use-independent-limit', 'reusable-checker', lambda d: d['flow']['steps']['first'].update(maxVisits=2), 'SHAPE')
    case('approval-bypass', 'protected-publication', lambda d: d['flow']['steps']['revise'].update(next=['publish']), 'APPROVAL')
    case('approval-target-entry', 'protected-publication', lambda d: d['flow'].update(entry='publish'), 'APPROVAL')
    case('approval-later-entry', 'protected-publication', lambda d: d['flow'].update(entry='release-approval'), 'APPROVAL')
    case('approval-cycle', 'protected-publication', lambda d: d['flow']['steps']['release-approval']['next'].update(approved=['owner-approval']), 'APPROVAL')
    case('approval-multiple-approved', 'protected-publication', lambda d: d['flow']['steps']['release-approval']['next'].update(approved=['publish','revise']), 'APPROVAL')
    case('approval-no-scope', 'protected-publication', lambda d: d['flow']['steps']['publish'].pop('scope'), 'SCOPE')
    case('scope-duplicate', 'protected-publication', lambda d: d['flow']['steps']['publish']['scope']['resources'].append('release-channel'), 'DUPLICATE')
    case('approval-zero-deadline', 'protected-publication', lambda d: d['flow']['steps']['owner-approval'].update(timeoutMs=0), 'SHAPE')
    case('approval-missing-binding', 'protected-publication', lambda d: d['bindings'].pop('authorization'), 'REFERENCE')
    case('approval-wrong-target', 'protected-publication', lambda d: d['flow']['steps']['owner-approval'].update(call='revise'), 'APPROVAL')
    case('unknown-schema-keyword', 'structured-report', lambda d: d['agents']['reviewer']['interface']['results']['report']['valueSchema'].update(pattern='x'), 'SHAPE')
    case('constraint-required-undeclared', 'structured-report', lambda d: d['agents']['reviewer']['interface']['results']['report']['valueSchema']['required'].append('absent'), 'VALUE_SCHEMA')
    case('constraint-enum-wrong-type', 'structured-report', lambda d: d['agents']['reviewer']['interface']['results']['report'].update(valueSchema={'type':'number','enum':[True]}), 'VALUE_SCHEMA')
    case('constraint-enum-equivalent-number', 'structured-report', lambda d: d['agents']['reviewer']['interface']['results']['report'].update(valueSchema={'type':'number','enum':[1,Decimal('1.0')]}), 'VALUE_SCHEMA')
    case('relative-base', 'structured-report', lambda d: d.update(baseUri='relative/'), 'URI')
    case('opaque-base', 'structured-report', lambda d: d.update(baseUri='urn:example:a'), 'URI')
    case('fragment-base', 'structured-report', lambda d: d.update(baseUri='https://example.invalid/#'), 'URI')
    case('bad-uri-escape', 'structured-report', lambda d: d['content']['instructions'].update(uri='bad%2'), 'URI')
    case('ipv6-zone-is-not-rfc3986', 'structured-report', lambda d: d['content']['instructions'].update(uri='https://[fe80::1%eth0]/'), 'URI')
    case('uri-space', 'structured-report', lambda d: d['content']['instructions'].update(uri='a b'), 'URI')
    case('uri-unicode', 'structured-report', lambda d: d['content']['instructions'].update(uri='é'), 'URI')
    case('uri-no-base-visible-unknown', 'structured-report', lambda d: d.pop('baseUri'), None)
    case('duplicate-claim', 'structured-report', lambda d: d['configurations']['review']['claims'].append(copy.deepcopy(d['configurations']['review']['claims'][0])), 'CLAIM')
    case('conflicting-claim', 'structured-report', lambda d: d['configurations']['review']['claims'].append({**d['configurations']['review']['claims'][0],'status':'unsupported'}), 'CLAIM')
    case('duplicate-requirement', 'structured-report', lambda d: d['configurations']['review']['requires'].append(copy.deepcopy(d['configurations']['review']['requires'][0])), 'DUPLICATE')
    return result


def admission_record(document=None, address='publish'):
    d = document or example('protected-publication')
    current = {'resources': {'artifact': {'value': 'release-content'}}}
    invocation = capture(d, address, 'work-1', 'entry', current)
    record = {'occurrence':'work-1','origin':'entry','input':current,'invocation':invocation,
              'admittedAt':500,'decisions':[]}
    for gate, entered, decided in [('owner-approval',0,100),('release-approval',100,200)]:
        record['decisions'].append({'gate':[gate],'occurrence':'work-1','invocation':copy.deepcopy(invocation),
            'binding':copy.deepcopy(d['bindings']['authorization']), 'enteredAt':entered,'decidedAt':decided,
            'decision':'approved','authorityConfirmed':True})
    return record


def schema_records():
    record = admission_record()
    claim = example('structured-report')['configurations']['review']['claims'][0]
    return {
        'ValueConstraint': [
            {'type':'null'}, {'type':'integer'}, {'type':'number','enum':[1,2]},
            {'type':'object','properties':{'a':{'type':'boolean'}},'required':['a'],'additionalProperties':False},
            {'type':'array','items':{'type':'object'}}, {'type':'string','pattern':'a'},
            {'type':'object','additionalProperties':{'type':'string'}}, {'type':'array','enum':[]},
            {'type':'string','properties':{}}, {'enum':[1]}],
        'AdmissionRecord': [record, {**record,'admittedAt':False}, {**record,'admittedAt':-1},
                            {**record,'unknown':True}, {**record,'decisions':[{'text':'approved'}]}],
        'ApprovalDecision': [record['decisions'][0], {**record['decisions'][0],'decision':'denied'},
                             {**record['decisions'][0],'authorityConfirmed':False},
                             {**record['decisions'][0],'enteredAt':0.5}],
        'Claim': [claim, {**claim,'evidence':'A'*64}, {**claim,'status':'ready'},
                  {k:v for k,v in claim.items() if k!='evidence'}],
        'Completion': [{'baseUri':'https://example.invalid/','results':{'x':{'uri':'x'}}},
                        {'baseUri':None}],
        'Message': [{'baseUri':'https://example.invalid/','prompt':[{'uri':'x'}]},
                     {'baseUri':True}]
    }


class ContractTests(unittest.TestCase):
    def test_adverse_declarations_and_unchanged_input(self):
        for name, d, code in document_cases():
            with self.subTest(name=name):
                before = copy.deepcopy(d)
                result = validate(d)
                self.assertEqual(result['valid'], code is None, result)
                if code:
                    self.assertIn(code, [f['code'] for f in result['findings']], result)
                self.assertEqual(d, before)

    def test_expansion_keeps_agent_identity_addresses_and_limits(self):
        d = example('reusable-checker')
        d['compositions']['verify']['steps']['review']['maxVisits'] = 3
        d['flow']['steps']['first-review'] = {'type':'prepare','message':{}}
        d['flow']['steps']['third']['next']['pass'] = ['first-review']
        report = validate(d)
        self.assertTrue(report['valid'], report)
        projected = {tuple(s['address']):s for s in report['expandedFlow']['steps']}
        self.assertEqual(projected[('first','review')]['step']['agent'], 'reviewer')
        self.assertEqual(projected[('second','review')]['step']['agent'], 'reviewer')
        self.assertEqual(projected[('third','review')]['step']['agent'], 'other-reviewer')
        self.assertIn(('first-review',), projected)
        self.assertEqual(projected[('first','review')]['step']['maxVisits'], 3)
        self.assertEqual(projected[('second','review')]['step']['maxVisits'], 3)
        self.assertEqual(projected[('first','check')]['step']['onError'], [['failure']])
        self.assertEqual(projected[('first','condition')]['step']['next']['true'], [['second','review']])
        self.assertTrue(check_completion(d, ['second','review'], {'text':'done'})['valid'])
        d['compositions']['verify']['steps']['review']['agent'] = 'missing'
        findings = validate(d)['findings']
        self.assertTrue(any(f.get('invocation') == '/flow/steps/second' and f['path'] == '/compositions/verify/steps/review/agent' for f in findings))

    def test_unused_body_still_validated_and_join_member_rejected(self):
        d = example('reusable-checker')
        d['compositions']['unused'] = copy.deepcopy(d['compositions']['verify'])
        d['compositions']['unused']['steps']['check']['binding'] = 'absent'
        self.assertFalse(validate(d)['valid'])
        d = example('parallel-reviews')
        d['compositions'] = example('reusable-checker')['compositions']
        d['bindings']['checker'] = d['bindings']['coding']
        d['flow']['steps']['code'] = {'type':'compose','composition':'verify','agents':{'reviewer':'code-reviewer'},'next':{'pass':['reviews'],'revise':['reviews']}}
        self.assertIn('COMPOSITION', [f['code'] for f in validate(d)['findings']])

    def test_protected_action_inside_composition_checked_after_expansion(self):
        d = example('protected-publication')
        body = copy.deepcopy(d['flow']['steps'])
        body.pop('revise'); body.pop('failure')
        for gate in ('owner-approval','release-approval'):
            body[gate]['next']['denied'] = [{'output':'denied'}]
        body['publish']['next'] = [{'output':'done'}]
        body['publish']['onError'] = [{'error':True}]
        d['compositions'] = {'publication':{'entry':'owner-approval','outputs':['done','denied'],'steps':body}}
        d['flow'] = {'entry':'use','steps':{'use':{'type':'compose','composition':'publication','agents':{},'next':{'done':[],'denied':[]}}}}
        self.assertTrue(validate(d)['valid'], validate(d))
        invocation = capture(d, ['use','publish'], 'work-1', 'entry', {'resources':{'artifact':{'value':'a'}}})
        record = {'occurrence':'work-1','origin':'entry','input':{'resources':{'artifact':{'value':'a'}}},'invocation':invocation,'admittedAt':400,'decisions':[]}
        for gate,t in [('owner-approval',0),('release-approval',100)]:
            record['decisions'].append({'gate':['use',gate],'occurrence':'work-1','invocation':copy.deepcopy(invocation),'binding':d['bindings']['authorization'],'enteredAt':t,'decidedAt':t+50,'decision':'approved','authorityConfirmed':True})
        self.assertTrue(check_admission(d,['use','publish'],record)['valid'])
        d['flow']['steps']['bypass'] = {'type':'prepare','message':{},'next':['use']}
        d['flow']['entry'] = 'bypass'
        self.assertTrue(validate(d)['valid'])
        d['compositions']['publication']['entry'] = 'publish'
        self.assertFalse(validate(d)['valid'])

    def test_approval_records_reject_stale_mismatched_expired_and_opinion(self):
        d = example('protected-publication')
        record = admission_record(d)
        self.assertTrue(check_admission(d,'publish',record)['valid'])
        mutations = [
            lambda r:r.update(occurrence='work-2'),
            lambda r:r.update(admittedAt=1100),
            lambda r:r['decisions'][0].update(decidedAt=1000),
            lambda r:r['decisions'][1].update(enteredAt=99),
            lambda r:r['decisions'][0].update(authorityConfirmed=False),
            lambda r:r['decisions'][0].update(decision='denied'),
            lambda r:r['decisions'].reverse(),
            lambda r:r['decisions'].pop(),
            lambda r:r['invocation']['arguments'].update(artifact='different'),
            lambda r:r['decisions'][0]['binding']['implementation'].update(version='2'),
            lambda r:r['input']['resources']['artifact'].update(value='different'),
            lambda r:r['decisions'][0]['invocation']['scope'].update(action='another action')]
        for mutation in mutations:
            with self.subTest(mutation=mutation):
                other = copy.deepcopy(record); mutation(other)
                self.assertFalse(check_admission(d,'publish',other)['valid'])
        self.assertEqual(check_admission(d,'publish',{'text':'approved'})['error']['code'],'INVALID_RECORD')
        changed = copy.deepcopy(d); changed['bindings']['publisher']['implementation']['version']='2'
        self.assertFalse(check_admission(changed,'publish',record)['valid'])

    def test_protected_agent_configuration_before_initialization_and_queue_expiry(self):
        d = example('protected-publication')
        d['configurations'] = {'a':{'engine':'publisher'},'b':{'engine':'authorization'}}
        d['agents'] = {'worker':{'configuration':{'select':{'path':['resources','artifact','value']},'cases':{'release-content':'a','another':'b'}}}}
        target = d['flow']['steps']['publish']
        target.pop('binding'); target.pop('arguments'); target.update(type='agent',agent='worker')
        record = admission_record(d)
        self.assertEqual(record['invocation']['configuration'],'a')
        self.assertTrue(check_admission(d,'publish',record)['valid'])
        record['admittedAt']=1100
        self.assertFalse(check_admission(d,'publish',record)['valid'])
        record=admission_record(d); record['retainedConfiguration']='b'
        self.assertFalse(check_admission(d,'publish',record)['valid'])
        # A new input need not repeat a selector when the instance retains its config.
        current={}; invocation=capture(d,'publish','later','entry',current,'a')
        self.assertEqual(invocation['configuration'],'a')
        self.assertNotIn('initialization',invocation)

    def test_effects_do_not_imply_a_gate_but_need_scope_when_declared(self):
        d=example('protected-publication')
        d['flow']['steps']={'publish':d['flow']['steps']['publish']}
        d['flow']['steps']['publish'].pop('onError');d['flow']['entry']='publish'
        self.assertTrue(validate(d)['valid'])
        d['flow']['steps']['publish'].pop('scope')
        self.assertFalse(validate(d)['valid'])
        d['bindings']['publisher']['effects']='none'
        self.assertTrue(validate(d)['valid'])

    def test_structured_results_exact_types_and_unassessed_uri(self):
        d=example('structured-report')
        record={'results':{'report':{'value':{'accepted':True,'issues':[]},'mediaType':'application/json'}}}
        self.assertTrue(check_completion(d,'review',record)['valid'])
        for value in ({'accepted':1,'issues':[]},{'accepted':True},{'accepted':True,'issues':[1]},'{"accepted":true,"issues":[]}',{'accepted':True,'issues':[],'extra':0}):
            record['results']['report']['value']=value
            self.assertEqual(check_completion(d,'review',record)['error']['code'],'OUTPUT_CONSTRAINT')
        record={'baseUri':'https://output.invalid/run/','results':{'report':{'uri':'report.json','mediaType':'application/json'}}}
        result=check_completion(d,'review',record)
        self.assertTrue(result['valid']);self.assertEqual(result['constraintAssessment'],'unassessed')
        self.assertEqual(result['unassessed'],['/results/report'])
        self.assertEqual(result['normalizedResults']['report']['uri'],'https://output.invalid/run/report.json')
        rule=d['agents']['reviewer']['interface']['results']['report'];rule['valueSchema']={'type':'integer'}
        for value,valid in [(loads(b'9007199254740993.0'),True),(loads(b'9007199254740993.1'),False),(True,False),(None,False)]:
            record={'results':{'report':{'value':value,'mediaType':'application/json'}}}
            self.assertEqual(check_completion(d,'review',record)['valid'],valid)
        rule['valueSchema']={'type':'number','enum':[loads(b'9007199254740993.1')]}
        self.assertTrue(check_completion(d,'review',{'results':{'report':{'value':loads(b'9007199254740993.10'),'mediaType':'application/json'}}})['valid'])

    def test_uri_rfc_resolution_and_origin_never_receiver_or_cwd(self):
        base='http://a/b/c/d;p?q'
        cases={'g':'http://a/b/c/g','./g':'http://a/b/c/g','g/':'http://a/b/c/g/','/g':'http://a/g','//g':'http://g','?y':'http://a/b/c/d;p?y','#s':'http://a/b/c/d;p?q#s','g?y#s':'http://a/b/c/g?y#s','.':'http://a/b/c/','..':'http://a/b/','../g':'http://a/b/g','../../g':'http://a/g','../../../g':'http://a/g','/./g':'http://a/g','g/../h':'http://a/b/c/h','g?y/../x':'http://a/b/c/g?y/../x','%2e%2e/g':'http://a/b/c/%2e%2e/g','?':'http://a/b/c/d;p?','#':'http://a/b/c/d;p?q#'}
        for uri,expected in cases.items():
            self.assertEqual(resolve_uri(uri,base),expected,uri)
        self.assertEqual(resolve_uri('g','custom:/a/b/'),'custom:/a/b/g')
        self.assertIsNone(resolve_uri('g'))
        d=example('structured-report')
        initial,initial_sources=agent_content(d,'reviewer')
        self.assertEqual(initial['prompt'][0]['uri'],'https://example.invalid/project/instructions/review.txt')
        self.assertEqual(initial['resources']['input']['uri'],'https://example.invalid/project/data/input.json')
        message={'baseUri':'https://message.invalid/in/','prompt':[{'ref':'instructions'}],'resources':{'local':{'uri':'same'},'literal':{'value':{'uri':'same','baseUri':'not interpreted'}}}}
        normalized,observations=normalize_message(message,d)
        self.assertEqual(normalized['prompt'][0]['uri'],'https://example.invalid/project/instructions/review.txt')
        self.assertEqual(normalized['resources']['local']['uri'],'https://message.invalid/in/same')
        self.assertEqual(normalized['resources']['literal'],message['resources']['literal'])
        record={'origin':'entry','input':message,'message':normalized,'configuration':'review'}
        self.assertTrue(check_delivery(d,'reviewer',record)['valid'])
        record['message']=copy.deepcopy(message);record['message']['baseUri']='https://wrong.invalid/'
        self.assertFalse(check_delivery(d,'reviewer',record)['valid'])
        completion={'baseUri':'https://source.invalid/run/','results':{'image':{'uri':'same','mediaType':'image/png'}}}
        current,obs=normalize_completion(completion)
        step={'message':{'prompt':[{'ref':'instructions'}],'resources':{'image':{'source':{'path':['results','image']}}}}}
        prepared,obs=prepare_message(d,step,current)
        self.assertEqual(prepared['resources']['image']['uri'],'https://source.invalid/run/same')
        raw=copy.deepcopy(completion);raw.pop('baseUri')
        prepared,obs=prepare_message(d,step,raw)
        self.assertEqual(prepared['resources']['image']['uri'],'same')
        self.assertIn('unresolved',[x['status'] for x in obs])
        prepared,obs=prepare_message(d,step,raw,{'/results/image':'https://explicit.invalid/'})
        self.assertEqual(prepared['resources']['image']['uri'],'https://explicit.invalid/same')
        nested={'members':{'one':raw}}
        nested_step={'message':{'resources':{'image':{'source':{'path':['members','one','results','image']}}}}}
        prepared,obs=prepare_message(d,nested_step,nested,{'/members/one/results/image':'https://member.invalid/run/'})
        self.assertEqual(prepared['resources']['image']['uri'],'https://member.invalid/run/same')

    def test_support_exact_scope_parameters_conflicts_and_core_needs(self):
        d=example('structured-report')
        def assessment():return next(x for x in validate(d)['support'] if x.get('configuration')=='review')
        self.assertEqual(assessment()['status'],'declared-supported')
        claim=d['configurations']['review']['claims'][0]
        claim['requirement']=copy.deepcopy(claim['requirement']);claim['requirement']['parameters']['mediaTypes'].append('image/png')
        self.assertEqual(assessment()['status'],'unknown')
        claim['requirement']=copy.deepcopy(d['configurations']['review']['requires'][0]);claim.pop('evidence')
        self.assertEqual(assessment()['status'],'unknown')
        claim['status']='unsupported'
        self.assertEqual(assessment()['status'],'incompatible')
        d['configurations']['review']['requires'].append({'contract':{'identity':'other','version':'1'}})
        self.assertEqual(assessment()['status'],'incompatible')
        self.assertIn('unknown',[x['status'] for x in assessment()['requirements']])
        d['bindings']['engine']['claims']=d['configurations']['review'].pop('claims')
        self.assertEqual(assessment()['status'],'unknown')
        d['configurations']['unused']={'engine':'engine','claims':[]}
        self.assertFalse(any(x.get('configuration')=='unused' for x in validate(d)['support']))
        d['agents']['reviewer']['configuration']={'select':{'path':['data']},'cases':{'a':'review','b':'unused'}}
        configs=[x for x in validate(d)['support'] if 'configuration' in x]
        self.assertEqual({x['selection'] for x in configs},{'conditional'})
        self.assertEqual(validate(d)['executionSupport'],'not-assessed')
        self.assertTrue(all(x['status']=='unassessed' for x in validate(d)['coreNeeds']))

    def test_support_absent_parameters_are_not_empty_parameters(self):
        d=example('conversation')
        req={'contract':{'identity':'example/access','version':'1'}}
        d['configurations']['project']['requires']=[req]
        d['configurations']['project']['claims']=[{'requirement':{**req,'parameters':{}},'status':'supported','evidence':'0'*64}]
        assessment=next(x for x in validate(d)['support'] if x.get('configuration')=='project')
        self.assertEqual(assessment['status'],'unknown')

    def test_admission_origin_consistency_for_call_and_agent_targets(self):
        invalid = [
            ('agent', {'text':'A','responseMessages':[['B']]}),
            ('agent', {'baseUri':'relative/','results':{}}),
            ('agent', {'results':{'report':{'uri':'bad%zz'}}}),
            ('entry', {'prompt':[{'ref':'missing'}]}),
            ('prepare', {'resources':{'report':{'ref':'missing'}}}),
            ('entry', {'prompt':[{'uri':'bad%zz'}]}),
            ('entry', {'baseUri':'relative/'}),
        ]
        for kind in ('call', 'agent'):
            d=example('protected-publication')
            target=d['flow']['steps']['publish']
            if kind=='call':
                target['arguments']={'artifact':{'value':'fixed'}}
            else:
                target.pop('binding');target.pop('arguments')
                target.update(type='agent',agent='worker')
                d['agents']={'worker':{'configuration':'fixed'}}
                d['configurations']={'fixed':{'engine':'publisher'}}
            for origin,current in invalid:
                with self.subTest(kind=kind,origin=origin,current=current):
                    record=admission_record(d)
                    record.update(origin=origin,input=current)
                    self.assertEqual(check_admission(d,'publish',record)['error']['code'],'INVALID_RECORD')
                    with self.assertRaises((KeyError,ValueError)):
                        capture(d,'publish','work-1',origin,current)
                    if kind=='agent':
                        delivery={'origin':origin,'input':current,'configuration':'fixed','message':{}}
                        self.assertEqual(check_delivery(d,'worker',delivery)['error']['code'],'INVALID_RECORD')
        # Check consistency, not completeness of response history or content access.
        d=example('protected-publication')
        d['flow']['steps']['publish']['arguments']={}
        opaque={'uri':'bad%zz','baseUri':'relative/','ref':'missing','text':'A','responseMessages':[['B']]}
        values=[('entry',{'resources':{'data':{'value':opaque}}}),
                ('call',{'data':opaque}),
                ('agent',{'text':'AB','responseMessages':[['A','B']]}),
                ('agent',{'results':{'report':{'value':opaque}}}),
                ('join',{'members':{'one':{'text':'A','responseMessages':[['B']]}}}),
                ('error',{'error':{'code':'CALL_FAILED','message':'failed','details':[{'path':'','rule':'external','expected':opaque}]}})]
        for origin,current in values:
            with self.subTest(opaque_origin=origin):
                record=admission_record(d)
                record.update(origin=origin,input=current)
                invocation=capture(d,'publish','work-1',origin,current)
                record['invocation']=invocation
                for decision in record['decisions']:
                    decision['invocation']=copy.deepcopy(invocation)
                self.assertTrue(check_admission(d,'publish',record)['valid'])

    def test_absolute_uri_dot_segments_queries_and_fragments(self):
        cases={
            'https://a/b/../c':'https://a/c',
            'x:/a/../b':'x:/b',
            'https://a/b/./c/../d?x=/../#f/./':'https://a/b/d?x=/../#f/./',
            'https://a/b/../c?#':'https://a/c?#',
            'https://a/b/../c?':'https://a/c?',
            'https://a/b/../c#':'https://a/c#',
            'https://a/%2e/%2E%2e/c':'https://a/%2e/%2E%2e/c',
        }
        for uri,expected in cases.items():
            for base in (None,'https://base.invalid/a/'):
                with self.subTest(uri=uri,base=base):
                    self.assertEqual(resolve_uri(uri,base),expected)
        normalized,_=normalize_completion({'results':{'report':{'uri':'https://a/b/../c?#'}}})
        self.assertEqual(normalized['results']['report']['uri'],'https://a/c?#')

    def test_composition_as_join_anchor_requires_one_expanded_step(self):
        d=example('parallel-reviews')
        d['compositions']={'anchor':{'entry':'start','outputs':['done'],'steps':{
            'start':{'type':'prepare','message':{},'next':[{'output':'done'}]}}}}
        d['flow']['steps']['develop']={'type':'compose','composition':'anchor','agents':{},'next':{'done':['code','tests']}}
        # Read the existing member names rather than inventing a different Join.
        d['flow']['steps']['develop']['next']['done']=d['flow']['steps']['reviews']['members'][:]
        self.assertTrue(validate(d)['valid'],validate(d))
        body=d['compositions']['anchor']['steps']
        body['start']['next']=['finish']
        body['finish']={'type':'prepare','message':{},'next':[{'output':'done'}]}
        self.assertIn('JOIN_GROUP',[x['code'] for x in validate(d)['findings']])

    def test_record_addresses_and_large_integer_deadlines(self):
        d=example('protected-publication')
        for address in ([], [['publish']], {}, ['publish', 'extra', 'extra']):
            self.assertEqual(check_admission(d,address,{})['error']['code'],'INVALID_REQUEST')
            self.assertEqual(check_completion(d,address,{})['error']['code'],'INVALID_REQUEST')
        record=admission_record(d)
        offset=10**80
        record['admittedAt']=Decimal(offset+500)
        for decision in record['decisions']:
            decision['enteredAt']=Decimal(offset+decision['enteredAt'])
            decision['decidedAt']=Decimal(offset+decision['decidedAt'])
        self.assertTrue(check_admission(d,'publish',record)['valid'])
        record['admittedAt']=Decimal(offset+1100)
        self.assertFalse(check_admission(d,'publish',record)['valid'])

    def test_gate_cannot_silently_target_composition_entry(self):
        d=example('reusable-checker')
        d['flow']['steps']['gate']={'type':'approval','call':'first','binding':'checker','timeoutMs':100,'validForMs':100,'next':{'approved':['first'],'denied':[]}}
        d['flow']['entry']='gate'
        d['compositions']['verify']['steps']['review']['scope']={'action':'review','resources':['document'],'context':{'path':[]}}
        self.assertIn('APPROVAL',[x['code'] for x in validate(d)['findings']])

    def test_cli_expanded_address_and_exact_json_output(self):
        run=subprocess.run([sys.executable,str(ROOT/'reader.py'),str(ROOT/'examples'/'reusable-checker.json')],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertTrue(json.loads(run.stdout)['expandedFlow']['steps'])
