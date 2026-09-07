import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { spawn, spawnSync } from 'node:child_process';
import { contract, hash, processor } from './core.mjs';
import { run } from './reader.mjs';

const fixture = name => readFileSync(new URL(
  `../../../experimental/modular-candidate-1/fixtures/${name}`,
  import.meta.url,
));
const conformanceFixture = name => readFileSync(new URL(
  `../../../conformance/fixtures/candidate2/${name}`,
  import.meta.url,
));
const officialDocument = (name = 'modular-system.json') => {
  const document = JSON.parse(fixture(name));
  document.contract = contract;
  return document;
};
const bytes = value => Buffer.from(typeof value === 'string' ? value : JSON.stringify(value));
const officialBytes = (name = 'modular-system.json') => bytes(officialDocument(name));
const execute = (operation, value, annexes = {}, losses) => run({
  operation,
  primary: Buffer.isBuffer(value) ? value : bytes(value),
  annexes,
  ...(losses === undefined ? {} : { losses }),
});
const result = (outcome, unit, input = 'primary') =>
  outcome.report.results.find(item => item.input === input && item.unit === unit);
const hasFinding = (outcome, unit, rule, pointer, findingOutcome = 'fail', input = 'primary') =>
  result(outcome, unit, input).findings.some(finding =>
    finding.rule === rule
    && finding.location.pointer === pointer
    && finding.outcome === findingOutcome,
  );
const assertOfficialReport = report => {
  assert.equal(report.contract, contract);
  assert.deepEqual(report.processor, processor);
};

test('all seven official operations retain their distinct result boundaries', () => {
  const raw = officialBytes();
  const expected = new Map([
    ['inspect', ['inspect', null]],
    ['validateD', ['D', 'unresolved-document']],
    ['validateG', ['G', 'unresolved-document']],
    ['resolveG', ['G', 'resolved-graph']],
    ['validateR', ['R', 'unresolved-document']],
    ['exchange', ['exchange', null]],
    ['lossyExchange', ['exchange', null]],
  ]);

  for (const [operation, [unit, phase]] of expected) {
    const outcome = execute(operation, raw);
    assertOfficialReport(outcome.report);
    const requested = result(outcome, unit);
    assert.ok(requested, `${operation} must emit its requested Result`);
    assert.equal(requested.phase, phase);
    if (operation === 'lossyExchange') {
      assert.equal(requested.verdict, 'fail');
      assert.deepEqual(Object.keys(outcome.artifacts), []);
    } else {
      assert.equal(requested.verdict, 'pass', JSON.stringify(requested.findings));
    }
  }
});

test('official validation rejects every foreign document marker', () => {
  const markers = ['proposal-0013-candidate-1', 'proposal-0012-candidate-2', 'agsdl-0.0.2'];
  for (const marker of markers) {
    for (const operation of ['validateD', 'validateG', 'resolveG', 'validateR']) {
      const document = officialDocument();
      document.contract = marker;
      const outcome = execute(operation, document);
      assertOfficialReport(outcome.report);
      assert.equal(result(outcome, 'D').verdict, 'fail');
      assert.ok(hasFinding(outcome, 'D', 'P-SHAPE', '/contract'));
      if (operation !== 'validateD') assert.notEqual(result(outcome, operation === 'validateR' ? 'R' : 'G').verdict, 'pass');
    }
  }
});

test('definitive Agent cardinality failures survive an unreadable relation', () => {
  for (const distinctTarget of [false, true]) {
    const document = officialDocument();
    const secondActsAs = structuredClone(document.relations[0]);
    if (distinctTarget) secondActsAs.target = structuredClone(document.definitions[3].key);
    document.relations.push(secondActsAs, {});

    for (const operation of ['validateD', 'validateG', 'resolveG', 'validateR']) {
      const outcome = execute(operation, document);
      assert.ok(hasFinding(outcome, 'D', 'P-SHAPE', '/relations/9'));
      assert.ok(hasFinding(outcome, 'D', 'D-AGENT', '/definitions/0'));
      if (distinctTarget) {
        assert.equal(hasFinding(outcome, 'D', 'D-RELATION', '/relations/8'), false);
      } else {
        assert.ok(hasFinding(outcome, 'D', 'D-RELATION', '/relations/8'));
      }
    }
  }
});

test('only a typed Interface exposure satisfies the official Agent minimum', () => {
  const outcome = execute('validateD', conformanceFixture('relation-kind-contract.json'));
  assert.ok(hasFinding(outcome, 'D', 'D-REFERENCE', '/relations/1'));
  assert.ok(hasFinding(outcome, 'D', 'D-RELATION', '/relations/1'));
  assert.ok(hasFinding(outcome, 'D', 'D-AGENT', '/definitions/0'));
});

test('official exchange preserves foreign-edition bytes without relabelling them', () => {
  const historical = fixture('modular-system.json');
  const outcome = execute('exchange', historical);
  assertOfficialReport(outcome.report);
  assert.equal(result(outcome, 'exchange').verdict, 'pass');
  assert.deepEqual(outcome.artifacts.primary, historical);
  assert.equal(outcome.report.inventory.tree.contract, 'proposal-0013-candidate-1');
  assert.equal(outcome.report.outputs[0].sha256, hash(historical));
});

test('G ignores runtime and R does not adopt G path semantics', () => {
  const badRuntime = officialDocument();
  badRuntime.runtime = 17;
  assert.equal(result(execute('validateG', badRuntime), 'G').verdict, 'pass');

  const badPath = officialDocument();
  badPath.graphs[0].entry = 'missing-step';
  assert.equal(result(execute('validateG', badPath), 'G').verdict, 'fail');
  assert.equal(result(execute('validateR', badPath), 'R').verdict, 'pass');
});

test('resolveG validates direct official annexes and refuses a foreign annex marker', () => {
  const document = officialDocument();
  const face = structuredClone(document.definitions[4]);
  const actions = document.definitions.slice(5, 7).map(value => structuredClone(value));
  const annex = {
    contract,
    root: { key: { scope: 'mvp', id: 'package', version: '1' }, kind: 'PackageVersion' },
    definitions: [face, ...actions],
    relations: [],
    exports: [face.key, ...actions.map(action => action.key)],
    dependencies: [],
    unresolved: [],
    extensions: [],
  };
  for (const definition of annex.definitions) definition.owner = annex.root.key;
  document.definitions.splice(4, 3);
  const external = key => ({ dependency: 'ui', key });
  for (const step of document.graphs[0].steps.filter(step => step.kind === 'invoke')) {
    const action = step.action;
    step.interface = external(face.key);
    step.action = external(action);
  }
  for (const relation of document.relations.filter(relation => relation.relation === 'exposes')) {
    relation.target = external(face.key);
  }

  let annexBytes = bytes(annex);
  document.dependencies = [{
    id: 'ui',
    rootKey: annex.root.key,
    status: 'included',
    requiredFor: [],
    sha256: hash(annexBytes),
  }];
  let outcome = execute('resolveG', document, { ui: annexBytes });
  assert.equal(result(outcome, 'G').verdict, 'pass', JSON.stringify(outcome.report.results));
  assert.equal(result(outcome, 'D', 'annex/ui').verdict, 'pass');
  assert.equal(result(outcome, 'G', 'annex/ui').verdict, 'pass');

  annex.contract = 'proposal-0013-candidate-1';
  annexBytes = bytes(annex);
  document.dependencies[0].sha256 = hash(annexBytes);
  outcome = execute('resolveG', document, { ui: annexBytes });
  assert.equal(result(outcome, 'D', 'annex/ui').verdict, 'fail');
  assert.ok(hasFinding(outcome, 'D', 'P-SHAPE', '/contract', 'fail', 'annex/ui'));
  assert.equal(result(outcome, 'G').verdict, 'fail');
});

test('syntax diagnostics and official-byte slices keep exact offsets', () => {
  for (const [hex, expectedByte] of [
    ['225c756438303022', 1],
    ['22c3a9e25822', 4],
    ['22e282', 3],
  ]) {
    const outcome = execute('inspect', Buffer.from(hex, 'hex'));
    assert.equal(result(outcome, 'inspect').findings[0].location.byte, expectedByte);
  }

  const raw = officialBytes();
  const outcome = execute('validateR', raw);
  const pointer = '/definitions/9/payload/failures/0';
  const slice = outcome.report.inventory.opaque.find(item => item.pointer === pointer);
  const expected = Buffer.from('"unavailable"');
  assert.ok(slice);
  assert.equal(slice.start, raw.indexOf(expected));
  assert.equal(slice.end, slice.start + expected.length);
  assert.deepEqual(raw.subarray(slice.start, slice.end), expected);
});

test('application omissions preserve independent incompatibility evidence', () => {
  const document = officialDocument('missing-application-keeps-incompatibility.json');
  const outcome = execute('validateR', document);
  const runtimeResult = result(outcome, 'R');
  const pointer = '/runtime/configurations/0/agents/0';

  assert.ok(runtimeResult.findings.some(finding =>
    finding.rule === 'R-CONTENT' && finding.location.pointer === pointer,
  ));
  assert.deepEqual(
    new Set(runtimeResult.findings
      .filter(finding => finding.rule === 'R-COMPATIBILITY' && finding.location.pointer === pointer)
      .map(finding => finding.outcome)),
    new Set(['fail', 'inconclusive']),
  );
  assert.ok(outcome.report.inventory.states.some(state =>
    state.pointer === pointer && state.detail === 'incompatible',
  ));
});

test('Application order diagnostics remain attached to the dependent record', () => {
  const outcome = execute('validateR', officialDocument('skill-dependency-after-dependent.json'));
  assert.ok(result(outcome, 'R').findings.some(finding =>
    finding.rule === 'R-CONTENT'
    && finding.location.pointer === '/runtime/configurations/0/agents/0/applications/0'
    && finding.details.includes('appear earlier'),
  ));
});

test('CLI host errors are distinct from validation failures', () => {
  const cli = fileURLToPath(new URL('./cli.mjs', import.meta.url));
  const malformed = spawnSync(process.execPath, [cli], {
    input: JSON.stringify({ operation: 'validateD', primary: '*', annexes: {} }),
    encoding: 'utf8',
  });
  assert.equal(malformed.status, 2);
  assert.equal(malformed.stdout, '');
  assert.match(malformed.stderr, /^host request error:/);

  const foreign = fixture('modular-system.json');
  const handled = spawnSync(process.execPath, [cli], {
    input: JSON.stringify({
      operation: 'validateD',
      primary: foreign.toString('base64'),
      annexes: {},
    }),
    encoding: 'utf8',
  });
  assert.equal(handled.status, 0, handled.stderr);
  assert.equal(handled.stderr, '');
  const response = JSON.parse(handled.stdout);
  assert.equal(response.report.contract, contract);
  assert.equal(result(response, 'D').verdict, 'fail');
  assert.deepEqual(response.artifacts, {});
});

test('CLI decodes a UTF-8 character split across stdin chunks exactly once', async () => {
  const cli = fileURLToPath(new URL('./cli.mjs', import.meta.url));
  const request = {
    operation: 'lossyExchange',
    primary: 'e30=',
    annexes: {},
    losses: [{
      input: 'primary',
      location: { pointer: '' },
      information: 'métadonnées',
      reason: 'demandé',
      permission: null,
    }],
  };
  const raw = Buffer.from(JSON.stringify(request));
  const cut = raw.indexOf(Buffer.from('é')) + 1;
  const child = spawn(process.execPath, [cli]);
  child.stdout.setEncoding('utf8');
  child.stderr.setEncoding('utf8');
  let stdout = '';
  let stderr = '';
  child.stdout.on('data', chunk => { stdout += chunk; });
  child.stderr.on('data', chunk => { stderr += chunk; });
  child.stdin.write(raw.subarray(0, cut));
  await new Promise(resolve => setTimeout(resolve, 50));
  child.stdin.end(raw.subarray(cut));
  const status = await new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('close', resolve);
  });

  assert.equal(status, 0, stderr);
  assert.equal(stderr, '');
  const response = JSON.parse(stdout);
  assert.equal(response.report.losses[0].information, request.losses[0].information);
  assert.equal(response.report.losses[0].reason, request.losses[0].reason);
});
