import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { read } from './reader.mjs';
import { parse, equal, shape, satisfies, NumberToken } from './values.mjs';
import { resolveUri } from './declarations.mjs';

const base = () => ({
  contract: 'agsdl-exp-flow-0.2-c1',
  id: 'test',
  bindings: {
    engine: {
      contract: { identity: 'example/e', version: '1' },
      implementation: { identity: 'example/e', version: '1' },
    },
  },
  configurations: { main: { engine: 'engine' } },
  agents: { worker: { configuration: 'main' } },
});
const report = (doc) => read(Buffer.from(JSON.stringify(doc)));
const number = (raw) => new NumberToken(raw);

test('all maintained examples pass the independent declaration reader', () => {
  const dir = new URL('../examples/', import.meta.url);
  for (const name of readdirSync(dir).filter((n) => n.endsWith('.json'))) {
    const result = read(readFileSync(new URL(name, dir)));
    assert.equal(
      result.valid,
      true,
      `${name}: ${JSON.stringify(result.findings)}`,
    );
    assert.equal(result.executionSupport, 'not-assessed');
  }
});
test('numbers are exact, mathematical integers and distinct from booleans', () => {
  assert.equal(equal(number('1'), number('1.0e0')), true);
  assert.equal(
    equal(number('9007199254740992'), number('9007199254740993')),
    false,
  );
  assert.equal(equal(number('1'), true), false);
  assert.equal(shape(number('9007199254740992.1'), { type: 'integer' }), false);
  assert.equal(shape(number('1e30'), { type: 'integer', minimum: 1 }), true);
  assert.equal(shape(number('1e-30'), { type: 'integer' }), false);
  assert.equal(equal(number('-0.000e999999'), number('0')), true);
  assert.equal(equal(number('1e999999'), number('10e999998')), true);
});
test('duplicate keys, invalid UTF-8 and unpaired Unicode fail parsing', () => {
  for (const bytes of [
    Buffer.from('{"x":1,"\\u0078":2}'),
    Buffer.from('"\\ud800"'),
    Buffer.from([34, 0xff, 34]),
    Buffer.from('NaN'),
  ]) {
    const result = read(bytes);
    assert.equal(result.valid, false);
    assert.deepEqual(result.findings, [{ code: 'PARSE', path: '' }]);
  }
  assert.equal(parse(Buffer.from('"\\ud800\\udc00"')).tree, '𐀀');
});
test('prototype and Unicode property names are ordinary literal data', () => {
  const doc = base();
  doc.content = {
    literal: {
      value: JSON.parse(
        '{"__proto__":{"ref":"missing"},"constructor":{"uri":"bad uri"},"toString":1,"\ue000":0,"\ud800\udc00":1}',
      ),
    },
  };
  assert.equal(report(doc).valid, true);
  assert.equal({}.ref, undefined);
  const c = {
    type: 'object',
    properties: JSON.parse('{"__proto__":{"type":"integer"}}'),
    required: ['__proto__'],
    additionalProperties: false,
  };
  assert.equal(satisfies(parse(Buffer.from('{"__proto__":1}')).tree, c), true);
  assert.equal(satisfies({}, c), false);
});
test('RFC 3986 resolution preserves explicit empty components and encoded dots', () => {
  const base = 'http://a/b/c/d;p?q';
  for (const [ref, expected] of [
    ['g', 'http://a/b/c/g'],
    ['../g', 'http://a/b/g'],
    ['../../../g', 'http://a/g'],
    ['?', 'http://a/b/c/d;p?'],
    ['#', 'http://a/b/c/d;p?q#'],
    ['g?y/./x', 'http://a/b/c/g?y/./x'],
    ['http:g', 'http:g'],
    ['g/../h', 'http://a/b/c/h'],
    ['/%2e/g', 'http://a/%2e/g'],
  ])
    assert.equal(resolveUri(ref, base), expected);
  assert.equal(resolveUri('relative', null), null);
  assert.throws(() => resolveUri('bad uri', base));
  assert.throws(() => resolveUri('x', 'not-a-base'));
});
test('conditions do not discover references inside operand values', () => {
  const doc = base();
  doc.flow = {
    entry: 'c',
    steps: {
      c: {
        type: 'condition',
        test: {
          equals: [
            { value: { ref: 'missing' } },
            { value: { ref: 'missing' } },
          ],
        },
        next: { true: ['a'], false: [] },
      },
      a: { type: 'agent', agent: 'worker' },
    },
  };
  assert.equal(report(doc).valid, true);
});
test('claims match the full requirement including omitted parameters', () => {
  const doc = base(),
    requirement = { contract: { identity: 'example/r', version: '1' } };
  doc.configurations.main.requires = [requirement];
  doc.configurations.main.claims = [
    {
      requirement: { ...requirement, parameters: {} },
      status: 'supported',
      evidence: 'a'.repeat(64),
    },
  ];
  assert.equal(report(doc).support.at(-1).status, 'unknown');
  delete doc.configurations.main.claims[0].requirement.parameters;
  assert.equal(report(doc).support.at(-1).status, 'declared-supported');
});
test('composition addresses and origins remain separate from names', () => {
  const doc = base();
  doc.compositions = {
    part: {
      entry: 'inside',
      outputs: ['done'],
      agentParameters: ['actor'],
      steps: {
        inside: {
          type: 'agent',
          agent: { parameter: 'actor' },
          next: [{ output: 'done' }],
        },
      },
    },
  };
  doc.flow = {
    entry: 'use',
    steps: {
      use: {
        type: 'compose',
        composition: 'part',
        agents: { actor: 'worker' },
        next: { done: ['use-inside'] },
      },
      'use-inside': { type: 'agent', agent: 'worker' },
    },
  };
  const result = report(doc);
  assert.equal(result.valid, true);
  const inside = result.expandedFlow.steps.find((x) => x.address.length === 2);
  assert.deepEqual(inside.address, ['use', 'inside']);
  assert.deepEqual(inside.step.next, [['use-inside']]);
  assert.equal(inside.source, '/compositions/part/steps/inside');
  assert.equal(inside.invocation, '/flow/steps/use');
});
test('approval rejection cannot bypass the first gate', () => {
  const doc = base();
  doc.flow = {
    entry: 'gate',
    steps: {
      gate: {
        type: 'approval',
        binding: 'engine',
        call: 'act',
        timeoutMs: 1,
        validForMs: 2,
        next: { approved: ['act'], denied: ['act'] },
      },
      act: {
        type: 'call',
        binding: 'engine',
        scope: {
          action: 'publish',
          resources: ['repository'],
          context: { value: {} },
        },
      },
    },
  };
  assert.ok(report(doc).findings.some((x) => x.code === 'APPROVAL'));
  doc.flow.steps.gate.next.denied = ['gate'];
  assert.equal(report(doc).valid, true);
});

test('duplicate decision choices fail once without inventing a route mismatch', () => {
  const doc = base();
  doc.flow = {
    entry: 'a',
    steps: {
      a: {
        type: 'agent',
        agent: 'worker',
        decision: { binding: 'engine', choices: ['yes', 'yes'] },
        next: { yes: [] },
      },
    },
  };
  assert.deepEqual(report(doc).findings, [
    { code: 'DUPLICATE', path: '/flow/steps/a/decision/choices' },
  ]);
});

test('omitted composition catalogs never expose inherited object members', () => {
  for (const missing of ['constructor', 'toString']) {
    const doc = base();
    doc.flow = {
      entry: 'use',
      steps: {
        use: {
          type: 'compose',
          composition: missing,
          agents: {},
          next: { done: [] },
        },
      },
    };
    const omitted = report(doc);
    doc.compositions = {};
    assert.deepEqual(omitted, report(doc));
    assert.equal(omitted.valid, false);
    assert.deepEqual(
      omitted.findings.map((x) => x.code),
      ['REFERENCE', 'REFERENCE'],
    );
  }
});
