import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, mkdtempSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { validate, EDITION, PROCESSOR } from './reader.mjs';
const example = name => JSON.parse(readFileSync(new URL(`../../examples/${name}.json`, import.meta.url), 'utf8'));
const report = obj => validate(Buffer.from(JSON.stringify(obj)));
const minimal = () => ({ edition: EDITION, agents: {} });
const result = (r, u) => r.results.find(x => x.unit === u);
const observations = r => r.results.flatMap(x => [
  ...x.diagnostics.map(d => ['D', x.unit, d.code, d.location, d.outcome]),
  ...x.incomplete.map(g => ['G', x.unit, g.code, g.location, [...g.causes].sort().join(',')]),
]).map(x => x.join('|')).sort();
const D = (u, c, p, o = 'fail') => ['D', u, c, p, o].join('|');
const G = (u, c, p, cause = 'shape') => ['G', u, c, p, cause.split(',').sort().join(',')].join('|');
const exact = (v, expected) => assert.deepEqual(observations(report(v)), expected.sort());
const includes = (r, ...items) => items.forEach(x => assert.ok(observations(r).includes(x), x));
const C = '/configurations/primary', B = `${C}/agents/0`, P = '/graphs/pipeline', E = { identity: 'test/unknown', version: '1' };

// Expectations below are authored from proposal 0016 sections 1–7, not a reader.
for (const name of ['agent-embedded', 'agent-named', 'two-agent-sequence', 'two-configurations', 'governed-call']) {
  test(`positive ${name}: all present units pass`, () => {
    const r = report(example(name)); assert.equal(r.results.length, 6); assert.deepEqual(observations(r), []);
    r.results.forEach(x => assert.equal(x.outcome, x.presence === 'absent' ? 'not-applicable' : 'pass'));
  });
}
test('all deliberate example findings and gaps', () => {
  exact(example('tool-incompatible'), [D('compatibility', 'TOOL', `${B}/tools/0`)]);
  exact(example('governed-missing-actor'), [D('flow', 'ACTOR', '/graphs/release/steps/2')]);
  exact(example('required-extension'), [D('external', 'REQUIRED', '/extensions/0', 'unsupported'), G('external', 'REQUIRED', '/extensions/0', 'unsupported')]);
  exact(example('missing-reference'), [D('core', 'REF', '/agents/writer/instructions/0/content')]);
  exact(example('ambiguous-reference'), [D('core', 'ID', '/instructions/draft'), D('core', 'ID', '/principals/draft'), G('core', 'REF', '/agents/writer/instructions/0/content', 'reference')]);
  exact(example('unknown-support'), [D('compatibility', 'ENGINE', B, 'inconclusive')]);
  exact(example('application-order-conflict'), [D('configuration', 'CONTENT', '/configurations/ordered/agents/0'), G('compatibility', 'ENGINE', '/configurations/ordered/agents/0', 'reference')]);
  exact(example('conflicting-bindings'), [D('configuration', 'ASSIGN', C), ...[0, 2].flatMap(i => [G('configuration', 'CONTENT', `${C}/agents/${i}`, 'reference'), G('configuration', 'TOOLS', `${C}/agents/${i}`, 'reference'), G('compatibility', 'ENGINE', `${C}/agents/${i}`, 'reference'), G('compatibility', 'TOOL', `${C}/agents/${i}`, 'reference')])]);
  const r = report(example('independent-errors'));
  includes(r, D('core', 'REF', '/agents/writer/instructions/0/content'), D('external', 'REQUIRED', '/extensions/0', 'unsupported'));
  assert.ok(result(r, 'core').diagnostics.some(x => x.code === 'SHAPE' && x.location.endsWith('/mode')));
});

test('section 5 mixed Binding branches: exactly shape and DATA gap', () => {
  const v = example('two-agent-sequence'); v.graphs.pipeline.steps[1].bindings.text = { input: 'text', step: 'draft-call', port: 'text' };
  exact(v, [D('flow', 'SHAPE', `${P}/steps/1/bindings/text`), G('flow', 'DATA', `${P}/steps/1`)]);
});
test('section 5 missing binding identity preserves sibling incompatibility', () => {
  const v = example('two-configurations'); delete v.configurations.primary.agents[0].agent; v.configurations.primary.agents[1].claims[0].status = 'unsupported';
  exact(v, [D('configuration', 'SHAPE', B), G('configuration', 'REF', B), G('configuration', 'ASSIGN', C), G('configuration', 'CONTENT', B), G('configuration', 'TOOLS', B), G('compatibility', 'ENGINE', B), G('compatibility', 'TOOL', B), D('compatibility', 'ENGINE', `${C}/agents/1`)]);
});
test('section 5 malformed sibling claim does not hide unsupported claim', () => {
  const v = example('two-configurations'), b = v.configurations.primary.agents[0]; b.claims[0].status = 'unsupported'; b.claims[1].status = 17;
  exact(v, [D('configuration', 'SHAPE', `${B}/claims/1/status`), G('configuration', 'UNIQUE', `${B}/claims`), D('compatibility', 'ENGINE', B), G('compatibility', 'ENGINE', B)]);
});
test('section 5 missing Applications retain intrinsic formats', () => {
  const v = example('two-configurations'); v.configurations.primary.agents[0].applications = [];
  exact(v, [D('configuration', 'CONTENT', B), G('compatibility', 'ENGINE', B, 'reference')]);
});
test('section 5 missing ToolBinding creates parent coverage, no fabricated child', () => {
  const v = example('tool-incompatible'); v.configurations.primary.agents[0].tools = [];
  exact(v, [D('configuration', 'TOOLS', B), G('compatibility', 'TOOL', B, 'reference')]);
});
test('section 5 missing kind exact observations', () => {
  const v = example('two-agent-sequence'); delete v.graphs.pipeline.steps[0].kind;
  exact(v, [D('flow', 'SHAPE', `${P}/steps/0`), ...['REF', 'OPERATION', 'DATA', 'ACTOR', 'APPROVAL', 'APPROVAL-DATA', 'UNIQUE'].map(c => G('flow', c, `${P}/steps/0`)), G('flow', 'PATH', P), G('flow', 'DATA', `${P}/steps/1`, 'reference,path'), G('flow', 'DATA', `${P}/steps/2`, 'path'), G('flow', 'ACTOR', `${P}/steps/1`)]);
});
test('section 5 missing approval call exact observations', () => {
  const v = example('governed-call'); v.graphs.release.steps[0].call = 'missing';
  exact(v, [D('flow', 'APPROVAL', '/graphs/release/steps/0'), G('flow', 'APPROVAL-DATA', '/graphs/release/steps/0', 'reference'), D('flow', 'APPROVAL', '/graphs/release/steps/1')]);
});

for (const bytes of ['null', '[]', '"text"', '123456789012345678901234567890', 'true', 'false']) test(`nonobject ${bytes}`, () => {
  const r = validate(Buffer.from(bytes)); assert.equal(result(r, 'syntax').outcome, 'pass');
  assert.deepEqual(observations(r), [D('core', 'SHAPE', ''), ...['core', 'flow', 'configuration', 'compatibility', 'external'].map(u => G(u, 'CHECKS', ''))].sort());
  r.results.slice(1).forEach(x => assert.equal(x.presence, 'undetermined'));
});
test('strict JSON primitives are lexical failures, not host errors', () => {
  for (const bytes of ['{"a":0,"\\u0061":1}', '"\\ud800"', '\ufeff{}', '{}x', '{"a":NaN}', '[1,]', '01', '"\\udc00"', Buffer.from([34, 0xc0, 0x80, 34])]) {
    const r = validate(Buffer.from(bytes));
    assert.deepEqual(observations(r), [D('syntax', 'SYNTAX', ''), ...['core', 'flow', 'configuration', 'compatibility', 'external'].map(u => G(u, 'CHECKS', ''))].sort());
  }
});
test('opaque huge numbers never become objects or rounded floats', () => {
  const bytes = Buffer.from(`{"edition":"${EDITION}","agents":{},"annotations":{"n":9007199254740993,"huge":1e999999}}`);
  assert.deepEqual(observations(validate(bytes)), []);
  assert.equal(validate(bytes).input.sha256, createHash('sha256').update(bytes).digest('hex'));
  const numericAgents = validate(Buffer.from(`{"edition":"${EDITION}","agents":1e999}`));
  includes(numericAgents, D('core', 'SHAPE', '/agents'), G('core', 'ID', '/agents'));
});
test('mathematical positive integer guards approval timing without rounding', () => {
  const v = example('governed-call'); const raw = JSON.stringify(v).replace('120000', '9007199254740991.1');
  includes(validate(Buffer.from(raw)), D('flow', 'SHAPE', '/graphs/release/steps/0/validForMs'));
  const valid = JSON.stringify(v).replace('120000', '12e4'); assert.deepEqual(observations(validate(Buffer.from(valid))), []);
});
test('API types, source identity and report identity', () => {
  assert.throws(() => validate('{}'), TypeError);
  const bytes = Buffer.from(JSON.stringify(minimal()));
  const r = validate(new Uint8Array(bytes)); assert.deepEqual(r.processor, PROCESSOR); assert.equal(r.edition, EDITION);
  assert.notEqual(r.input.sha256, validate(Buffer.concat([bytes, Buffer.from(' ')])).input.sha256);
});
test('absent is distinct from present empty containers and invalid selection', () => {
  const r = report(minimal()); ['flow', 'configuration', 'compatibility', 'external'].forEach(u => assert.equal(result(r, u).outcome, 'not-applicable'));
  const empty = report({ ...minimal(), graphs: {}, configurations: {}, extensions: [] }); ['flow', 'configuration', 'external'].forEach(u => assert.equal(result(empty, u).outcome, 'pass'));
  exact({ ...minimal(), selected: 'nope' }, [D('configuration', 'SELECTION', '/selected'), G('compatibility', 'CHECKS', '/selected', 'reference')]);
});
test('wrong edition gates optional units but still diagnoses core', () => {
  const v = { edition: 'other', agents: {}, graphs: 17 };
  exact(v, [D('core', 'SHAPE', '/edition'), G('core', 'ID', '/graphs'), ...['flow', 'configuration', 'compatibility', 'external'].map(u => G(u, 'CHECKS', ''))]);
});
test('closed choices never infer or merge a branch', () => {
  const v = example('agent-embedded'); v.agents.writer.interface.ref = 'other';
  exact(v, [D('core', 'SHAPE', '/agents/writer/interface'), G('core', 'REF', '/agents/writer/interface')]);
});
test('extra Ref member fails shape but does not hide readable target', () => {
  const v = example('agent-named'); v.agents.writer.interface.extra = true;
  exact(v, [D('core', 'SHAPE', '/agents/writer/interface/extra')]);
});
test('invalid catalog key blocks complete lookup without accepting numeric wrapper', () => {
  const v = example('agent-named'); v.principals = { 'bad/key': { description: 'x' } };
  includes(report(v), D('core', 'SHAPE', '/principals/bad~1key'), G('core', 'ID', '/principals/bad~1key'), G('core', 'REF', '/agents/writer/interface', 'reference'));
});
test('slot and uniqueness clauses keep independent observations', () => {
  const v = example('agent-embedded'); v.agents.writer.instructions.push(structuredClone(v.agents.writer.instructions[0]), { content: v.agents.writer.instructions[0].content });
  exact(v, [D('core', 'SHAPE', '/agents/writer/instructions/2'), D('core', 'SLOT-ID', '/agents/writer/instructions'), G('core', 'SLOT-ID', '/agents/writer/instructions')]);
});
test('graph path rejects cycles, missing successors and unreachable steps', () => {
  for (const edit of [s => { s[0].success = s[0].id; }, s => { s[0].failure = 'missing'; }, s => { s.push({ id: 'unused', kind: 'end', outcome: 'failure', reason: 'x' }); }]) {
    const v = example('two-agent-sequence'); edit(v.graphs.pipeline.steps);
    includes(report(v), D('flow', 'PATH', P), G('flow', 'DATA', `${P}/steps/1`, 'path'));
  }
});
test('duplicate step id blocks lookup without choosing a winner', () => {
  const v = example('two-agent-sequence'); v.graphs.pipeline.steps[0].id = 'review-call';
  includes(report(v), D('flow', 'STEP-ID', `${P}/steps`), G('flow', 'PATH', P));
});
test('bindings validate exact names, producer kind, ports and types', () => {
  const mutations = [b => { b.text = { input: 'missing' }; }, b => { b.text = { step: 'done', port: 'text' }; }, b => { b.text = { step: 'draft-call', port: 'missing' }; }, b => { delete b.text; }];
  for (const edit of mutations) { const v = example('two-agent-sequence'); edit(v.graphs.pipeline.steps[1].bindings); includes(report(v), D('flow', 'DATA', `${P}/steps/1`)); }
  const v = example('two-agent-sequence'); v.graphs.pipeline.inputs.text = 'json'; includes(report(v), D('flow', 'DATA', `${P}/steps/0`));
});
test('producer failure edge cannot supply success data', () => {
  const v = example('two-agent-sequence'); v.graphs.pipeline.steps[0].failure = 'review-call';
  includes(report(v), D('flow', 'DATA', `${P}/steps/1`));
});
test('unselected malformed operation does not suppress selected operation', () => {
  const v = example('two-agent-sequence'); v.interfaces.text.operations.other = { direction: 'outbound' };
  exact(v, [D('core', 'SHAPE', '/interfaces/text/operations/other')]);
});
test('governance triggered by effects needs actor and scope, never an inferred gate', () => {
  const v = example('two-agent-sequence'); v.interfaces.text.operations.rewrite.effects = 'external';
  exact(v, [D('flow', 'ACTOR', `${P}/steps/0`), D('flow', 'ACTOR', `${P}/steps/1`)]);
});
test('known governance trigger enforces actor despite unavailable other trigger', () => {
  const v = example('governed-call'); delete v.agents.writer.principal; v.agents.writer.tools = [{ ref: 'missing' }];
  includes(report(v), D('core', 'REF', '/agents/writer/tools/0'), D('flow', 'ACTOR', '/graphs/release/steps/2'));
});
test('approval entry cannot bypass earlier gate', () => {
  const v = example('governed-call'); v.graphs.release.entry = 'approve-2';
  includes(report(v), D('flow', 'PATH', '/graphs/release'), G('flow', 'APPROVAL', '/graphs/release/steps/0', 'path'));
});
test('gate context and inputs must be available before call', () => {
  const v = example('governed-call'); v.graphs.release.steps[2].scope.context = { step: 'send', port: 'text' };
  includes(report(v), D('flow', 'APPROVAL-DATA', '/graphs/release/steps/0'), D('flow', 'APPROVAL-DATA', '/graphs/release/steps/1'), D('flow', 'DATA', '/graphs/release/steps/2'));
});
test('null engine and missing engine remain different', () => {
  const v = example('two-configurations'); v.configurations.primary.agents[0].engine = null;
  exact(v, [D('compatibility', 'ENGINE', B, 'inconclusive')]);
  delete v.configurations.primary.agents[0].engine;
  exact(v, [D('configuration', 'SHAPE', B), G('compatibility', 'ENGINE', B)]);
});
test('unknown and incompatible requirements coexist without structural invalidity', () => {
  const v = example('two-configurations'), b = v.configurations.primary.agents[0]; b.requires.push(E); b.claims[0].status = 'unsupported';
  exact(v, [D('compatibility', 'ENGINE', B), D('compatibility', 'ENGINE', B, 'inconclusive')]);
  assert.equal(result(report(v), 'configuration').outcome, 'pass');
});
test('duplicate claim blocks only its capability; unknown evidence is not execution proof', () => {
  const v = example('two-configurations'), b = v.configurations.primary.agents[0]; b.claims.push(structuredClone(b.claims[0])); b.claims[1].status = 'unsupported';
  exact(v, [D('configuration', 'UNIQUE', `${B}/claims`), G('compatibility', 'ENGINE', B, 'reference'), D('compatibility', 'ENGINE', B)]);
});
test('incomplete claim identity index blocks even otherwise known claim', () => {
  const v = example('two-configurations'), b = v.configurations.primary.agents[0]; delete b.claims[1].capability; b.claims[0].status = 'unsupported';
  exact(v, [D('configuration', 'SHAPE', `${B}/claims/1`), G('configuration', 'UNIQUE', `${B}/claims`), G('compatibility', 'ENGINE', B)]);
});
test('malformed unused claim evidence does not block required unsupported capability', () => {
  const v = example('two-configurations'), b = v.configurations.primary.agents[0]; b.claims[0].status = 'unsupported'; b.claims[0].evidence = 17;
  exact(v, [D('configuration', 'SHAPE', `${B}/claims/0/evidence`), G('configuration', 'UNIQUE', `${B}/claims`), D('compatibility', 'ENGINE', B)]);
});
test('instruction body/target do not gate intrinsic format assessment', () => {
  const v = example('two-configurations'); delete v.instructions.draft.body; delete v.instructions.draft.target; v.configurations.primary.agents[0].claims[0].status = 'unsupported';
  exact(v, [D('core', 'SHAPE', '/instructions/draft'), D('compatibility', 'ENGINE', B)]);
});
test('all configurations structurally checked, only selected assessed', () => {
  const v = example('two-configurations'); delete v.selected; v.configurations.alternate.agents[0].claims[0].status = 'unsupported';
  exact(v, []); delete v.configurations.alternate.agents[0].engine;
  exact(v, [D('configuration', 'SHAPE', '/configurations/alternate/agents/0')]);
});
test('required extension is unsupported and duplicate identity independent', () => {
  const v = { ...minimal(), extensions: [{ edition: E, use: 'required', payload: null }, { edition: E, use: 'annotation', payload: {} }] };
  exact(v, [D('external', 'UNIQUE', '/extensions'), D('external', 'REQUIRED', '/extensions/0', 'unsupported'), G('external', 'REQUIRED', '/extensions/0', 'unsupported')]);
});
test('object order and Unicode annotation content do not affect observations', () => {
  const v = example('two-configurations'); v.annotations = { '\uE000': 'a', '\u{10000}': 'b' };
  const reversed = x => Array.isArray(x) ? x.map(reversed) : x && typeof x === 'object' ? Object.fromEntries(Object.entries(x).reverse().map(([k, v]) => [k, reversed(v)])) : x;
  assert.deepEqual(observations(report(v)), observations(report(reversed(v))));
});
test('CLI: one path, raw Report, negative report exit 0, host errors exit 2', () => {
  const dir = mkdtempSync(join(tmpdir(), 'agsdl-js-'));
  try {
    const cli = fileURLToPath(new URL('./cli.mjs', import.meta.url)), path = join(dir, 'artifact.json');
    writeFileSync(path, '{');
    let r = spawnSync(process.execPath, [cli, path], { encoding: 'utf8' });
    assert.equal(r.status, 0); assert.equal(r.stderr, ''); assert.equal(JSON.parse(r.stdout).results[0].outcome, 'fail');
    for (const args of [[], [path, path], [join(dir, 'absent')]]) { r = spawnSync(process.execPath, [cli, ...args], { encoding: 'utf8' }); assert.equal(r.status, 2); assert.equal(r.stdout, ''); assert.ok(r.stderr); }
  } finally { rmSync(dir, { recursive: true }); }
});
test('missing input/output port maps leave DATA gaps at existing consumers', () => {
  const v = example('two-agent-sequence'); delete v.interfaces.text.operations.rewrite.inputs;
  includes(report(v), D('core', 'SHAPE', '/interfaces/text/operations/rewrite'), G('flow', 'DATA', `${P}/steps/0`), G('flow', 'DATA', `${P}/steps/1`));
  const w = example('two-agent-sequence'); delete w.graphs.pipeline.outputs;
  includes(report(w), D('flow', 'SHAPE', P), G('flow', 'DATA', `${P}/steps/2`));
});
test('malformed graph and owner arrays collapse subjects without fabricated children', () => {
  const v = { ...minimal(), graphs: { broken: { steps: 17 } } };
  const r = report(v);
  for (const code of ['REF', 'STEP-ID', 'PATH', 'OPERATION', 'DATA', 'ACTOR', 'APPROVAL', 'APPROVAL-DATA', 'UNIQUE']) includes(r, G('flow', code, '/graphs/broken/steps'));
  assert.ok(!observations(r).some(x => x.includes('/steps/0')));
});
test('end discriminator missing checks common fields without fallback extras', () => {
  const v = example('two-agent-sequence'); delete v.graphs.pipeline.steps[2].outcome;
  const r = report(v);
  assert.deepEqual(result(r, 'flow').diagnostics, [{ code: 'SHAPE', location: `${P}/steps/2`, outcome: 'fail' }]);
  includes(r, G('flow', 'DATA', `${P}/steps/2`), G('flow', 'PATH', P));
});
test('scope resources duplicate fails separately from actor checks', () => {
  const v = example('governed-call'); v.graphs.release.steps[2].scope.resources.push(v.graphs.release.steps[2].scope.resources[0]);
  exact(v, [D('flow', 'UNIQUE', '/graphs/release/steps/2/scope/resources')]);
});
test('Tool null implementation and unknown effects contribute distinct scoped uncertainty', () => {
  const v = example('tool-incompatible'); v.configurations.primary.agents[0].tools[0].implementation = null;
  exact(v, [D('compatibility', 'TOOL', `${B}/tools/0`, 'inconclusive')]);
});
test('absent call terminates APPROVAL even with malformed approvers', () => {
  const v = example('governed-call'); v.graphs.release.steps[0].call = 'missing'; v.graphs.release.steps[0].approvers = null;
  exact(v, [D('flow', 'SHAPE', '/graphs/release/steps/0/approvers'), G('flow', 'REF', '/graphs/release/steps/0/approvers'), D('flow', 'APPROVAL', '/graphs/release/steps/0'), G('flow', 'APPROVAL-DATA', '/graphs/release/steps/0', 'reference'), D('flow', 'APPROVAL', '/graphs/release/steps/1')]);
});
test('unreadable resources locate UNIQUE gap at scope, SHAPE at value', () => {
  const v = example('governed-call'); v.graphs.release.steps[2].scope.resources = 17;
  exact(v, [D('flow', 'SHAPE', '/graphs/release/steps/2/scope/resources'), G('flow', 'UNIQUE', '/graphs/release/steps/2/scope'), G('flow', 'ACTOR', '/graphs/release/steps/2')]);
});
test('extra Edition member never hides readable instruction format incompatibility', () => {
  const v = example('two-configurations'); v.instructions.draft.format.extra = true; v.configurations.primary.agents[0].claims[0].status = 'unsupported';
  exact(v, [D('core', 'SHAPE', '/instructions/draft/format/extra'), D('compatibility', 'ENGINE', B)]);
});
test('all engine Edition identity projections ignore extras, shape and UNIQUE stay strict', () => {
  const cases = [
    ['engine', b => { b.engine.extra = true; }, `${B}/engine/extra`, false],
    ['requires', b => { b.requires = [{ ...b.claims[0].capability, extra: true }]; }, `${B}/requires/0/extra`, true],
    ['adapter', b => { b.applications[0].adapter.extra = true; }, `${B}/applications/0/adapter/extra`, false],
    ['settings', b => { b.settings.format.extra = true; }, `${B}/settings/format/extra`, false],
    ['claim', b => { b.claims[0].capability.extra = true; }, `${B}/claims/0/capability/extra`, true],
  ];
  for (const [name, mutate, p, uniqueness] of cases) {
    const v = example('two-configurations'), b = v.configurations.primary.agents[0]; b.claims[0].status = 'unsupported'; mutate(b);
    exact(v, [D('configuration', 'SHAPE', p), D('compatibility', 'ENGINE', B), ...(uniqueness ? [G('configuration', 'UNIQUE', `${B}/${name === 'requires' ? 'requires' : 'claims'}`)] : [])]);
  }
});
test('Tool implementation and requirement Edition projections retain incompatibility', () => {
  const v = example('tool-incompatible'), b = v.configurations.primary.agents[0].tools[0];
  b.implementation.extra = true;
  exact(v, [D('configuration', 'SHAPE', `${B}/tools/0/implementation/extra`), D('compatibility', 'TOOL', `${B}/tools/0`)]);
  const tool = v.tools[b.tool.ref]; tool.requires[0].extra = true;
  includes(report(v), D('compatibility', 'TOOL', `${B}/tools/0`), G('core', 'UNIQUE', `/tools/${b.tool.ref}/requires`));
});
test('external Edition extra fails shape without hiding required interpretation', () => {
  const v = { ...minimal(), extensions: [{ edition: { ...E, extra: true }, use: 'required', payload: null }] };
  exact(v, [D('external', 'SHAPE', '/extensions/0/edition/extra'), D('external', 'REQUIRED', '/extensions/0', 'unsupported'), G('external', 'REQUIRED', '/extensions/0', 'unsupported')]);
});
test('ambiguous or malformed call preserves independent duplicate approvers', () => {
  const v = {
    ...minimal(), principals: { p: { description: 'p' } },
    graphs: { g: { entry: 'a', inputs: {}, outputs: {}, steps: [
      { id: 'a', kind: 'approval', call: 'e', approvers: [{ ref: 'p' }, { ref: 'p' }], validForMs: 1, timeoutMs: 1, approved: 'e', denied: 'e', failure: 'e' },
      { id: 'e', kind: 'end', outcome: 'failure', reason: 'x' },
      { id: 'e', kind: 'end', outcome: 'failure', reason: 'x' },
    ] } },
  };
  const common = [D('flow', 'STEP-ID', '/graphs/g/steps'), G('flow', 'PATH', '/graphs/g'), D('flow', 'APPROVAL', '/graphs/g/steps/0')];
  exact(v, [...common, G('flow', 'APPROVAL', '/graphs/g/steps/0', 'reference'), G('flow', 'APPROVAL-DATA', '/graphs/g/steps/0', 'reference')]);
  v.graphs.g.steps[0].call = 17;
  exact(v, [...common, D('flow', 'SHAPE', '/graphs/g/steps/0/call'), G('flow', 'APPROVAL', '/graphs/g/steps/0'), G('flow', 'APPROVAL-DATA', '/graphs/g/steps/0')]);
});
