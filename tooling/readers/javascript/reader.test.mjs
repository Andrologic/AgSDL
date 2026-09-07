import test from 'node:test';
import assert from 'node:assert/strict';
import { copyFileSync, mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { spawn, spawnSync } from 'node:child_process';
import { contract, hash, processor } from './core.mjs';
import { run, stringify } from './reader.mjs';

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

// The distribution must work with only this directory and Node's standard library.
test('API and CLI run all seven operations without the repository or experimental', async () => {
  const directory = mkdtempSync(join(tmpdir(), 'agsdl-javascript-'));
  try {
    const source = fileURLToPath(new URL('.', import.meta.url));
    for (const name of readdirSync(source)) {
      if (name.endsWith('.mjs') && !name.endsWith('.test.mjs')) {
        copyFileSync(join(source, name), join(directory, name));
      }
    }
    const isolated = await import(pathToFileURL(join(directory, 'reader.mjs')));
    for (const operation of ['inspect', 'validateD', 'validateG', 'resolveG', 'validateR', 'exchange', 'lossyExchange']) {
      const primary = officialBytes();
      const request = { operation, primary, annexes: {} };
      const expected = run(request);
      assert.equal(isolated.stringify(isolated.run(request)), stringify(expected), operation);
      const cli = spawnSync(process.execPath, [join(directory, 'cli.mjs')], {
        cwd: directory,
        input: JSON.stringify({ ...request, primary: primary.toString('base64') }),
        encoding: 'utf8',
      });
      assert.equal(cli.status, 0, cli.stderr);
      assert.equal(cli.stderr, '');
      const response = JSON.parse(cli.stdout);
      assert.deepEqual(response.report, JSON.parse(stringify(expected.report)), operation);
      assert.deepEqual(response.artifacts, Object.fromEntries(
        Object.entries(expected.artifacts).map(([id, bytes]) => [id, bytes.toString('base64')]),
      ), operation);
    }
  } finally {
    rmSync(directory, { recursive: true, force: true });
  }
});

const diagnosticDocument = () => JSON.parse(readFileSync(new URL(
  '../../../examples/0.1.0/general-purpose-system.json', import.meta.url,
)));
const check = (outcome, unit, rule, state) => result(outcome, unit).checks.find(
  item => item.rule === rule && item.state === state,
);
const blockedPointers = (outcome, unit, rule) =>
  check(outcome, unit, rule, 'blocked')?.locations.map(location => location.pointer) || [];

// spec/reports.md: observed work and known empty domains complete independently
// of blocked portions; spec/document.md: root form and per-export lookup differ.
test('empty exports complete independently of missing root kind or identity', () => {
  for (const field of ['kind', 'key']) {
    const document = diagnosticDocument();
    delete document.root[field];
    const outcome = execute('validateD', document);
    assert.ok(hasFinding(outcome, 'D', 'P-SHAPE', '/root'));
    assert.deepEqual(check(outcome, 'D', 'D-EXPORT', 'completed')?.locations, []);
    assert.deepEqual(blockedPointers(outcome, 'D', 'D-EXPORT'), field === 'kind' ? ['/exports'] : []);
  }
  const document = diagnosticDocument();
  delete document.root.kind;
  delete document.exports;
  const outcome = execute('validateD', document);
  assert.equal(check(outcome, 'D', 'D-EXPORT', 'completed'), undefined);
  assert.deepEqual(blockedPointers(outcome, 'D', 'D-EXPORT'), ['']);
});

// spec/reports.md, Runtime rule execution: an absent required enumeration is
// blocked at its existing parent, and is not an observed empty domain.
test('missing configurations block selection without inventing completed work', () => {
  const document = diagnosticDocument();
  delete document.runtime.configurations;
  const outcome = execute('validateR', document);
  assert.ok(hasFinding(outcome, 'R', 'P-SHAPE', '/runtime'));
  assert.equal(result(outcome, 'R').verdict, 'fail');
  assert.equal(check(outcome, 'R', 'R-SELECTION', 'completed'), undefined);
  for (const rule of ['R-SELECTION', 'R-BINDING', 'R-TOOL', 'R-CONTENT', 'R-COMPATIBILITY']) {
    assert.deepEqual(blockedPointers(outcome, 'R', rule), ['/runtime']);
  }
  assert.equal(outcome.report.inventory.states.some(item => item.pointer.startsWith('/runtime/')), false);
  document.runtime.configurations = [];
  const empty = execute('validateR', document);
  assert.deepEqual(check(empty, 'R', 'R-SELECTION', 'completed')?.locations, []);
  assert.ok(hasFinding(empty, 'R', 'R-SELECTION', '/runtime'));
});

// spec/runtime.md, Configuration selection and assignments, and spec/reports.md:
// id uniqueness and selected lookup block separately; readable graph checks run.
test('missing configuration id blocks its record and selected lookup', () => {
  const document = diagnosticDocument();
  delete document.runtime.configurations[0].id;
  const outcome = execute('validateR', document);
  assert.ok(hasFinding(outcome, 'R', 'P-SHAPE', '/runtime/configurations/0'));
  assert.deepEqual(blockedPointers(outcome, 'R', 'R-SELECTION'), ['/runtime', '/runtime/configurations/0']);
  assert.deepEqual(check(outcome, 'R', 'R-SELECTION', 'completed')?.locations, []);
  assert.equal(hasFinding(outcome, 'R', 'R-SELECTION', '/runtime'), false);
  document.runtime.configurations[1].graph.id = 'missing-graph';
  const independent = execute('validateR', document);
  assert.ok(hasFinding(independent, 'R', 'R-SELECTION', '/runtime/configurations/1'));
});

// spec/runtime.md requires exact Agent/Tool coverage in every configuration.
// Missing Agent identity hides membership, but not readable sibling claims.
// The dossier's group E aggregate ambiguity is deliberately not an exact oracle.
test('missing Agent identity blocks coverage and supplied Tool membership', () => {
  const cp = '/runtime/configurations/0', ap = `${cp}/agents/0`;
  for (const selected of [true, false]) {
    const document = diagnosticDocument();
    delete document.runtime.configurations[0].agents[0].agent;
    if (!selected) delete document.runtime.selected;
    const outcome = execute('validateR', document);
    assert.ok(hasFinding(outcome, 'R', 'P-SHAPE', ap));
    assert.deepEqual(blockedPointers(outcome, 'R', 'R-BINDING'), [cp, ap]);
    assert.deepEqual(blockedPointers(outcome, 'R', 'R-TOOL'), [ap, `${ap}/tools/0`]);
    assert.deepEqual(check(outcome, 'R', 'R-BINDING', 'completed')?.locations, []);
    assert.deepEqual(check(outcome, 'R', 'R-TOOL', 'completed')?.locations, []);
    assert.equal(hasFinding(outcome, 'R', 'R-BINDING', cp), false);
    assert.equal(hasFinding(outcome, 'R', 'R-TOOL', ap), false);
  }
  const document = diagnosticDocument();
  delete document.runtime.configurations[0].agents[0].agent;
  for (const claim of document.runtime.configurations[0].agents[1].claims) claim.status = 'unsupported';
  const outcome = execute('validateR', document);
  assert.ok(hasFinding(outcome, 'R', 'R-COMPATIBILITY', `${cp}/agents/1`));
});

// Stabilized F witness: official/missing-engine.json. Only engine is absent;
// the nested ToolBinding is well-shaped and explicitly selects its sole choice.
const inventoryWitness = () => {
  const key = (id) => ({ scope: 'native', id, version: '1' });
  const edition = (name) => ({ identity: `native/${name}`, version: '1' });
  const claim = (name) => ({
    capability: edition(name),
    status: 'supported',
    evidence: 'a'.repeat(64),
  });
  const definition = (id, kind, payload = {}) => ({
    key: key(id),
    kind,
    owner: key('system'),
    payload,
  });
  return {
    contract,
    root: { key: key('system'), kind: 'System' },
    definitions: [
      definition('agent', 'Agent'),
      definition('principal', 'Principal'),
      definition('interface', 'Interface', {
        operations: [
          {
            id: 'call',
            direction: 'inbound',
            mode: 'request-response',
            action: key('action'),
            inputs: {},
            outputs: {},
          },
        ],
      }),
      definition('flow', 'ControlFlow'),
      definition('action', 'Action'),
      definition('resource', 'Resource'),
      definition('instructions', 'Instructions', {
        target: 'Agent',
        at: 'before-invoke',
        format: edition('text'),
        body: 'Do the declared work.',
        requires: [],
      }),
      definition('tool', 'Tool', {
        action: key('action'),
        inputs: {},
        outputs: {},
        effects: 'none',
        failures: [],
        requires: [],
      }),
    ],
    relations: [
      ['actsAs', 'principal', 'Principal'],
      ['exposes', 'interface', 'Interface'],
      ['directedBy', 'instructions', 'Instructions'],
      ['uses', 'tool', 'Tool'],
    ].map(([relation, target, expectedKind]) => ({
      source: key('agent'),
      relation,
      target: key(target),
      expectedKind,
    })),
    exports: [],
    dependencies: [],
    unresolved: [],
    extensions: [],
    graphs: [
      {
        definition: key('flow'),
        entry: 'call',
        inputs: { context: 'json' },
        outputs: {},
        steps: [
          {
            id: 'call',
            kind: 'invoke',
            operation: 'call',
            agent: key('agent'),
            interface: key('interface'),
            action: key('action'),
            resources: [key('resource')],
            principal: key('principal'),
            context: { input: 'context' },
            inputs: {},
            outputs: {},
            bindings: {},
            success: 'done',
            failure: 'failed',
          },
          { id: 'done', kind: 'end', outcome: 'success', bindings: {} },
          { id: 'failed', kind: 'end', outcome: 'failure', reason: 'Failed' },
        ],
      },
    ],
    runtime: {
      selected: 'selected',
      configurations: [
        {
          id: 'selected',
          graph: key('flow'),
          agents: [
            {
              agent: key('agent'),
              parameters: {},
              requires: [],
              claims: [claim('text'), claim('adapter')],
              tools: [
                {
                  tool: key('tool'),
                  choices: [
                    {
                      id: 'only',
                      implementation: edition('tool'),
                      parameters: {},
                      claims: [],
                    },
                  ],
                  selected: 'only',
                },
              ],
              applications: [
                {
                  content: key('instructions'),
                  adapter: edition('adapter'),
                  parameters: {},
                },
              ],
            },
          ],
        },
      ],
    },
  };
};

// spec/reports.md, Runtime inventory: each State requires its own well-shaped
// parent record. Missing runtime selection never creates assessment States.
test('runtime inventory observes shaped ToolBindings beneath an incomplete AgentBinding', () => {
  const ap = '/runtime/configurations/0/agents/0',
    tp = `${ap}/tools/0`;
  for (const selectedConfiguration of [true, false]) {
    for (const selectedTool of [true, false]) {
      const document = inventoryWitness();
      if (!selectedConfiguration) delete document.runtime.selected;
      if (!selectedTool)
        delete document.runtime.configurations[0].agents[0].tools[0].selected;
      const outcome = execute('validateR', document);
      const states = outcome.report.inventory.states;
      assert.ok(hasFinding(outcome, 'R', 'P-SHAPE', ap));
      assert.equal(
        states.some(
          (item) => item.pointer === ap || item.pointer === `${ap}/engine`,
        ),
        false,
      );
      assert.equal(
        states.some((item) => item.pointer === '/runtime/selected'),
        false,
      );
      assert.deepEqual(
        states.filter((item) => item.pointer === `${tp}/selected`),
        [
          {
            input: 'primary',
            pointer: `${tp}/selected`,
            state: selectedTool ? 'declared' : 'absent',
            detail: selectedTool ? 'declared' : 'absent',
          },
        ],
      );
      const assessments = states.filter((item) =>
        [ap, tp].includes(item.pointer),
      );
      assert.deepEqual(
        assessments,
        selectedConfiguration
          ? [
              {
                input: 'primary',
                pointer: tp,
                state: selectedTool ? 'unchecked' : 'absent',
                detail: selectedTool ? 'declared-supported' : 'not-provided',
              },
            ]
          : [],
      );
      if (selectedConfiguration)
        assert.ok(
          blockedPointers(outcome, 'R', 'R-COMPATIBILITY').includes(ap),
        );
      else
        assert.deepEqual(
          check(outcome, 'R', 'R-COMPATIBILITY', 'excluded')?.locations,
          [{ pointer: '/runtime' }],
        );
    }
  }
  const document = inventoryWitness();
  delete document.runtime.configurations[0].agents[0].tools[0].choices;
  const outcome = execute('validateR', document);
  assert.ok(hasFinding(outcome, 'R', 'P-SHAPE', tp));
  assert.equal(
    outcome.report.inventory.states.some((item) =>
      [tp, `${tp}/selected`].includes(item.pointer),
    ),
    false,
  );
});
