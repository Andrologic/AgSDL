"""Observable candidate cases, including cross-reference and grouping failures."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from reader import SCHEMA, equal, loads, shape, validate
from check_completion import check_completion

ROOT = Path(__file__).parent


def example(name):
    return loads((ROOT / 'examples' / (name + '.json')).read_bytes())


def cases():
    """Named cases with independently written expected verdicts and rule codes."""
    result = []
    for path in sorted((ROOT / 'examples').glob('*.json')):
        result.append((path.stem, loads(path.read_bytes()), None))

    def case(name, base, mutate, code):
        value = example(base)
        mutate(value)
        result.append((name, value, code))

    case('wrong-edition', 'conversation', lambda d: d.update(contract='agsdl-0.1.0'), 'SHAPE')
    case('undeclared-field', 'conversation', lambda d: d.update(runtimeReset=True), 'SHAPE')
    case('configuration-missing', 'conversation', lambda d: d['configurations'].clear(), 'REFERENCE')
    case('engine-missing', 'conversation', lambda d: d['bindings'].clear(), 'REFERENCE')
    case('configuration-choice', 'conversation', lambda d: d['agents']['helper'].update(configuration={'select':{'path':['data','mode']},'cases':{'review':'project'}}), None)
    case('configuration-choice-missing-target', 'conversation', lambda d: d['agents']['helper'].update(configuration={'select':{'path':['data','mode']},'cases':{'review':'missing'}}), 'REFERENCE')
    case('configuration-choice-no-alternatives', 'conversation', lambda d: d['agents']['helper'].update(configuration={'select':{'path':['data','mode']},'cases':{}}), 'SHAPE')
    case('no-default-engine', 'conversation', lambda d: d['configurations']['project'].clear(), 'SHAPE')
    case('binding-needs-implementation', 'conversation', lambda d: d['bindings']['coding'].pop('implementation'), 'SHAPE')
    case('unknown-engine-parameters-retained', 'conversation', lambda d: d['bindings']['coding'].update(settings={'vendorSpecific': {'flag': True}}), None)
    case('tool-reference-missing', 'test-loop', lambda d: d['bindings'].pop('edit'), 'REFERENCE')
    case('agent-reference-missing', 'test-loop', lambda d: d['agents'].clear(), 'REFERENCE')
    case('entry-missing', 'test-loop', lambda d: d['flow'].update(entry='absent'), 'REFERENCE')
    case('route-target-missing', 'test-loop', lambda d: d['flow']['steps']['develop'].update(next=['absent']), 'REFERENCE')
    case('duplicate-activation', 'test-loop', lambda d: d['flow']['steps']['develop'].update(next=['tests','tests']), 'DUPLICATE')
    case('zero-visit-limit', 'test-loop', lambda d: d['flow']['steps']['develop'].update(maxVisits=0), 'SHAPE')
    case('boolean-visit-limit', 'test-loop', lambda d: d['flow']['steps']['develop'].update(maxVisits=True), 'SHAPE')
    case('positive-visit-limit', 'test-loop', lambda d: d['flow']['steps']['develop'].update(maxVisits=3), None)
    case('dead-step', 'test-loop', lambda d: d['flow']['steps'].update(unused={'type':'call','binding':'tests'}), 'UNREACHABLE')
    case('call-binding-missing', 'test-loop', lambda d: d['bindings'].pop('tests'), 'REFERENCE')
    case('condition-needs-both-routes', 'test-loop', lambda d: d['flow']['steps']['passed']['next'].pop('false'), 'SHAPE')
    case('negative-array-index', 'test-loop', lambda d: d['flow']['steps']['passed']['test'].update(equals=[{'path':[-1]}, {'value':0}]), 'SHAPE')
    case('unmapped-decision', 'parallel-reviews', lambda d: d['flow']['steps']['code']['next'].pop('changes_needed'), 'ROUTES')
    case('decision-binding-missing', 'parallel-reviews', lambda d: d['bindings'].pop('review-choice'), 'REFERENCE')
    case('duplicate-choice', 'parallel-reviews', lambda d: d['flow']['steps']['code']['decision']['choices'].append('accepted'), 'DUPLICATE')
    case('choice-map-without-decision', 'parallel-reviews', lambda d: d['flow']['steps']['code'].pop('decision'), 'ROUTES')
    case('failed-anchor-cannot-start-group-members', 'parallel-reviews', lambda d: d['flow']['steps']['develop'].update(onError=['code']), 'JOIN_GROUP')
    case('join-anchor-missing', 'parallel-reviews', lambda d: d['flow']['steps']['reviews'].update(after='absent'), 'JOIN_GROUP')
    case('join-expects-missing-member', 'parallel-reviews', lambda d: d['flow']['steps']['reviews']['members'].append('absent'), 'JOIN_GROUP')
    case('join-duplicate-member', 'parallel-reviews', lambda d: d['flow']['steps']['reviews']['members'].append('code'), 'JOIN_GROUP')
    case('join-entry-cannot-receive-unrelated-input', 'parallel-reviews', lambda d: d['flow'].update(entry='reviews'), 'JOIN_GROUP')
    case('member-entry-bypasses-anchor', 'parallel-reviews', lambda d: d['flow'].update(entry='code'), 'JOIN_GROUP')
    case('negative-review-must-still-join', 'parallel-reviews', lambda d: d['flow']['steps']['code']['next'].update(changes_needed=[]), 'JOIN_GROUP')
    case('sibling-cannot-start-correction-early', 'parallel-reviews', lambda d: d['flow']['steps']['code']['next'].update(changes_needed=['correction']), 'JOIN_GROUP')
    case('content-reference-missing', 'multimedia-and-reuse', lambda d: d['content'].clear(), 'REFERENCE')
    case('skill-reference-missing', 'multimedia-and-reuse', lambda d: d['skills'].clear(), 'REFERENCE')
    case('duplicate-skill', 'multimedia-and-reuse', lambda d: d['agents']['reviewer']['skills'].append('review'), 'DUPLICATE')
    case('output-contract-conflicts-with-permitted-formats', 'multimedia-and-reuse', lambda d: d['agents']['reviewer']['interface'].update(outputMediaTypes=['text/plain']), 'OUTPUT_FORMAT')
    case('source-cannot-contain-uri-and-inline-value', 'multimedia-and-reuse', lambda d: d['content']['review-rules'].update(value='ambiguous'), 'SHAPE')
    case('literal-object-is-not-a-reference', 'conversation', lambda d: d['agents']['helper'].update(prompt=[{'value':{'ref':'unresolved-as-data'}}]), None)
    case('newline-name-rejected', 'conversation', lambda d: d['agents'].update({'bad\n':{'configuration':'project'}}), 'SHAPE')

    def collision(d):
        d['skills']['review']['resources']={'recording':{'value':'a different recording'}}
    case('skill-resource-collision', 'multimedia-and-reuse', collision, 'RESOURCE_COLLISION')
    # These accepted directions are deliberately not implemented by bounded c1.
    case('steering-not-silently-accepted', 'conversation', lambda d: d['agents']['helper'].update(messageMode='steering'), 'SHAPE')
    case('first-needs-acceptance-rule', 'parallel-reviews', lambda d: d['flow']['steps']['reviews'].update(mode='first'), 'JOIN_POLICY')
    case('all-does-not-accept-first-policy', 'parallel-reviews', lambda d: d['flow']['steps']['reviews'].update(remaining='finish'), 'JOIN_POLICY')
    case('first-can-explicitly-let-losers-finish', 'first-review', lambda d: d['flow']['steps']['reviews'].update(remaining='finish'), None)
    case('first-can-explicitly-wait-for-stop', 'first-review', lambda d: d['flow']['steps']['reviews'].update(remaining='stop-and-wait'), None)
    case('unknown-stop-policy', 'first-review', lambda d: d['flow']['steps']['reviews'].update(remaining='pretend-stopped'), 'SHAPE')
    case('first-member-missing', 'first-review', lambda d: d['flow']['steps']['reviews']['members'].append('absent'), 'JOIN_GROUP')
    return result


class CandidateTests(unittest.TestCase):
    def test_examples_and_adverse_documents(self):
        for name, document, expected in cases():
            with self.subTest(case=name):
                original = copy.deepcopy(document)
                report = validate(document)
                self.assertEqual(report['executionSupport'], 'not-assessed')
                self.assertEqual(report['valid'], expected is None, report)
                if expected:
                    self.assertIn(expected, [x['code'] for x in report['findings']])
                self.assertEqual(document, original, 'Static validation must not transform input')

    def test_required_output_can_be_corrected_without_text(self):
        document = example('output-correction')
        missing = check_completion(document, 'develop', {'text': 'Work completed.'})
        self.assertFalse(missing['valid'])
        self.assertEqual(missing['error']['code'], 'OUTPUT_CONSTRAINT')
        self.assertEqual(missing['error']['details'][0]['path'], '/results/report')
        corrected = check_completion(document, 'develop', {
            'results': {'report': {'value': 'Completed changes and checks.', 'mediaType': 'text/plain'}}})
        self.assertTrue(corrected['valid'])
        self.assertEqual(corrected['executionSupport'], 'not-assessed')

    def test_output_constraints_are_conditional_not_text_required(self):
        document = example('output-correction')
        document['agents']['developer']['interface']['results']['report']['required'] = False
        self.assertTrue(check_completion(document, 'develop', {})['valid'])
        wrong_format = {'results': {'report': {'value': {}, 'mediaType': 'application/json'}}}
        self.assertFalse(check_completion(document, 'develop', wrong_format)['valid'])
        self.assertFalse(check_completion(document, 'develop', {'results': {'report': {'value': 'Untyped'}}})['valid'])

    def test_recorded_file_reference_does_not_claim_availability(self):
        document = example('output-correction')
        record = {'results': {'report': {'uri': 'file:///not-fetched/report.txt', 'mediaType': 'text/plain'}}}
        report = check_completion(document, 'develop', record)
        self.assertTrue(report['valid'])
        self.assertEqual(report['scope'], 'recorded-output-constraints')
        self.assertEqual(report['executionSupport'], 'not-assessed')

    def test_required_decision_is_checked_without_changing_visible_text(self):
        document = example('parallel-reviews')
        result = {'text': 'I quoted accepted in an example.'}
        self.assertFalse(check_completion(document, 'code', result)['valid'])
        result['choice'] = 'accepted'
        before = copy.deepcopy(result)
        self.assertTrue(check_completion(document, 'code', result)['valid'])
        self.assertEqual(result, before)
        result['choice'] = 'unmapped'
        self.assertFalse(check_completion(document, 'code', result)['valid'])

    def test_undeclared_decision_is_not_accepted_as_control_data(self):
        document = example('test-loop')
        step = document['flow']['entry']
        result = {'text': 'accepted'}
        self.assertTrue(check_completion(document, step, result)['valid'])
        result['choice'] = 'accepted'
        report = check_completion(document, step, result)
        self.assertFalse(report['valid'])
        self.assertEqual(report['error']['code'], 'INVALID_RECORD')

    def test_bad_record_or_request_is_not_an_agent_output_to_repair(self):
        document = example('output-correction')
        self.assertEqual(check_completion(document, 'develop', {'text': 12})['error']['code'], 'INVALID_RECORD')
        self.assertEqual(check_completion(document, 'classify-error', {})['error']['code'], 'INVALID_REQUEST')
        self.assertEqual(check_completion(document, 'absent', {})['error']['code'], 'INVALID_REQUEST')

    def test_overall_output_formats_cover_public_text_and_artifacts(self):
        document = example('output-correction')
        document['agents']['developer']['interface'] = {'outputMediaTypes': ['image/png']}
        self.assertFalse(check_completion(document, 'develop', {'text': 'Not an image'})['valid'])
        self.assertFalse(check_completion(document, 'develop', {'results': {'x': {'value': 'untyped'}}})['valid'])
        image = {'results': {'image': {'uri': 'file:///image.png', 'mediaType': 'image/png'}}}
        self.assertTrue(check_completion(document, 'develop', image)['valid'])

    def test_completion_cli_emits_recoverable_diagnostic(self):
        command = [sys.executable, str(ROOT/'check_completion.py'),
                   str(ROOT/'examples'/'output-correction.json'), 'develop']
        with tempfile.TemporaryDirectory() as folder:
            record = Path(folder)/'result.json'
            record.write_text('{"text":"I finished."}')
            run = subprocess.run(command+[str(record)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 1, run.stderr)
            self.assertEqual(json.loads(run.stdout)['error']['code'], 'OUTPUT_CONSTRAINT')
            record.write_text('{"results":{"report":{"value":"Changes and checks","mediaType":"text/plain"}}}')
            run = subprocess.run(command+[str(record)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertTrue(json.loads(run.stdout)['valid'])

    def test_parse_rejects_ambiguous_or_non_json_inputs(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}',
                    b'{"x":"\\ud800"}', b'\xff', b'{} {}'):
            with self.subTest(raw=raw), self.assertRaises((ValueError, UnicodeError)):
                loads(raw)

    def test_fractional_lexeme_is_not_rounded_to_integer(self):
        document = example('test-loop')
        document['flow']['steps']['develop']['maxVisits'] = loads(b'1.00000000000000000000000001')
        self.assertFalse(validate(document)['valid'])
        document['flow']['steps']['develop']['maxVisits'] = loads(b'1.0')
        self.assertTrue(validate(document)['valid'])

    def test_json_boolean_is_not_numeric_equality(self):
        self.assertFalse(equal(True, 1))
        self.assertFalse(equal({'a':[False]}, {'a':[0]}))
        self.assertTrue(equal(1, loads(b'1.0')))

    def test_cli_exit_codes_and_no_execution_claim(self):
        command=[sys.executable, str(ROOT/'reader.py')]
        run=subprocess.run(command+[str(ROOT/'examples'/'conversation.json')],capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        self.assertEqual(json.loads(run.stdout)['executionSupport'],'not-assessed')
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'invalid.json'
            path.write_text('{"contract":')
            run=subprocess.run(command+[str(path)],capture_output=True,text=True)
            self.assertEqual(run.returncode,1)
            self.assertEqual(json.loads(run.stdout)['findings'][0]['code'],'PARSE')
            run=subprocess.run(command+[str(Path(folder)/'absent.json')],capture_output=True,text=True)
            self.assertEqual(run.returncode,2)


def check_schema_library():
    """Separate implementation of shape checks, not an independent semantic reader."""
    import jsonschema
    jsonschema.Draft202012Validator.check_schema(SCHEMA)
    independent=jsonschema.Draft202012Validator(SCHEMA)
    for name, document, _ in cases():
        assert shape(document,SCHEMA) == independent.is_valid(document), name
    completion_schema = {**SCHEMA, '$ref': '#/$defs/Completion'}
    completions = [{}, {'text': ''}, {'text': 1},
                   {'results': {'report': {'value': 'ok', 'mediaType': 'text/plain'}}},
                   {'results': {'report': {'uri': 'file:///report.txt'}}},
                   {'results': {'report': {'uri': 'file:///report.txt', 'value': 'bad'}}},
                   {'choice': 'accepted'}, {'choice': 'bad\n'}, {'unknown': True}]
    library = jsonschema.Draft202012Validator(completion_schema)
    for record in completions:
        assert shape(record, completion_schema) == library.is_valid(record), record
    print(f'Schema-library agreement on {len(cases())} documents and {len(completions)} completion records; no execution claim.')


if __name__ == '__main__':
    if sys.argv[1:] == ['--schema']:
        check_schema_library()
    else:
        unittest.main()
