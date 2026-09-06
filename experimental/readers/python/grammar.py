"""Candidate-2 closed shape grammar. Semantic rules live in reader.py."""
import re
from lossless import integer, pointer

CONTRACT = 'proposal-0012-candidate-2'
KINDS = 'Agent Principal Interface Instructions Role Skill ControlFlow Action Resource ApprovalRequirement Tool Model Environment Runtime Deployment Policy Memory Knowledge State Topology Protocol'.split()
IDENTITY = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*\Z')
HASH = re.compile(r'[0-9a-f]{64}\Z')
SCHEMAS = {}


def record(**fields):
    return ('record', fields)


def array(item, minimum=0):
    return ('array', item, minimum)


def enum(*items):
    return ('enum', items)


def union(*items):
    return ('union', items)


SCHEMAS.update({
    'Key': record(scope='text', id='text', version='text'),
    'Edition': record(identity='identity', version='text'),
    'Ref': union('Key', record(dependency='text', key='Key')),
    'Kind': union(enum(*KINDS), record(extension='Edition', name='text')),
    'Binding': union(record(input='text'), record(step='text', port='text')),
    'Ports': ('map', enum('string', 'boolean', 'json')),
    'Root': record(key='Key', kind=enum('System', 'Fragment', 'PackageVersion'), **{'payload?': 'any', 'annotations?': 'any'}),
    'Definition': record(key='Key', kind='Kind', owner='Key', payload='any', **{'annotations?': 'any', 'provenance?': 'any'}),
    'Relation': record(source='Key', relation=enum('actsAs', 'exposes', 'directedBy', 'uses', 'contains'), target='Ref', expectedKind='Kind'),
    'Dependency': record(id='text', rootKey='Key', status=enum('included', 'external', 'omitted', 'unavailable'), requiredFor=array(enum('validateD', 'resolveG', 'exchange')), sha256=union('hash', 'null'), **{'location?': 'text'}),
    'Deferral': record(subject='Key', obligation=enum('agent-interface-minimum'), rule=enum('fragment-interface-deferral'), relation=enum('exposes'), expectedKind=enum('Interface'), missingMinimum='one', target=union('Key', 'null'), satisfyBy=enum('typed-exposes-relation'), expiresBefore=enum('resolved-graph')),
    'ExtensionMode': union(enum('required', 'unknown'), record(ignoreRule=enum('annotation-only'))),
    'ExtensionOperations': record(**{x + '?': 'ExtensionMode' for x in ('validateD', 'validateG', 'validateR')}),
    'Extension': record(identity='identity', version='text', operations='ExtensionOperations', payload='any'),
    'Document': record(contract=enum(CONTRACT), root='Root', definitions=array('Definition'), relations=array('Relation'), exports=array('Key'), dependencies=array('Dependency'), unresolved=array('Deferral'), extensions=array('Extension'), **{x + '?': 'any' for x in ('annotations', 'evidence', 'graphs', 'runtime')}),
    'Graph': record(definition='Key', entry='text', inputs='Ports', outputs='Ports', steps=array('Step', 1)),
    'Invoke': record(id='text', kind=enum('invoke'), agent='Ref', interface='Ref', action='Ref', resources=array('Ref', 1), principal='Ref', context='Binding', inputs='Ports', outputs='Ports', bindings=('map', 'Binding'), success='text', failure='text'),
    'Condition': record(id='text', kind=enum('condition'), test='Binding', true='text', false='text', failure='text'),
    'Approval': record(id='text', kind=enum('approval'), requirement='Ref', timeoutMs='positive', approved='text', denied='text', failure='text'),
    'EndSuccess': record(id='text', kind=enum('end'), outcome=enum('success'), bindings=('map', 'Binding')),
    'EndOther': record(id='text', kind=enum('end'), outcome=enum('failure', 'denied'), reason='text'),
    'Interface': record(inputs='Ports', outputs='Ports', action='Ref'),
    'ApprovalRequirement': record(approvers=array('Ref', 1), validForMs='positive'),
    'Runtime': record(requirements=array('Requirement'), **{'selection?': 'Selection'}),
    'Requirement': record(id='text', capability='Edition', subject='Key'),
    'Selection': record(engine='Edition', interface='Edition', evidence=array('EvidenceClaim'), **{'model?': 'Edition', 'provider?': 'identity', 'hosting?': 'Ref'}),
    'EvidenceClaim': record(requirement='text', claim=enum('satisfied', 'unsatisfied', 'indeterminate'), artifact=union('hash', 'null'), **{'location?': 'text'}),
})


def errors(schema, value, path=''):
    if schema == 'Step':
        if isinstance(value, dict):
            kind = value.get('kind')
            name = {'invoke': 'Invoke', 'condition': 'Condition', 'approval': 'Approval'}.get(kind) if isinstance(kind, str) else None
            if value.get('kind') == 'end':
                name = 'EndSuccess' if value.get('outcome') == 'success' else 'EndOther'
            if name:
                return errors(name, value, path)
        return [(path, 'unknown step shape')]
    if isinstance(schema, str):
        if schema in SCHEMAS:
            return errors(SCHEMAS[schema], value, path)
        valid = {'any': lambda: True, 'null': lambda: value is None,
                 'text': lambda: isinstance(value, str) and bool(value),
                 'identity': lambda: isinstance(value, str) and bool(IDENTITY.fullmatch(value)),
                 'hash': lambda: isinstance(value, str) and bool(HASH.fullmatch(value)),
                 'one': lambda: integer(value) == 1,
                 'positive': lambda: integer(value) is not None and integer(value) > 0}[schema]()
        return [] if valid else [(path, 'expected ' + schema)]
    tag = schema[0]
    if tag == 'enum':
        return [] if isinstance(value, str) and value in schema[1] else [(path, 'unexpected literal')]
    if tag == 'union':
        alternatives = [errors(s, value, path) for s in schema[1]]
        return min(alternatives, key=len)
    if tag == 'array':
        if not isinstance(value, list):
            return [(path, 'expected array')]
        result = [] if len(value) >= schema[2] else [(path, 'array minimum')]
        for i, item in enumerate(value):
            result += errors(schema[1], item, pointer(path, i))
        return result
    if not isinstance(value, dict):
        return [(path, 'expected object')]
    result = []
    if tag == 'map':
        for key, item in value.items():
            if not key:
                result.append((pointer(path, key), 'empty map name'))
            result += errors(schema[1], item, pointer(path, key))
        return result
    fields = schema[1]
    allowed = {name.rstrip('?') for name in fields}
    for name, child in fields.items():
        key = name.rstrip('?')
        if key in value:
            result += errors(child, value[key], pointer(path, key))
        elif not name.endswith('?'):
            result.append((path, 'missing ' + key))
    result += [(pointer(path, key), 'unknown member') for key in value if key not in allowed]
    return result


def good(schema, value):
    return not errors(schema, value)
