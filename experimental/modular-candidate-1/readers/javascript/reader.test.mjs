import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {run} from './reader.mjs';
import {hash} from './core.mjs';

const fixture=name=>readFileSync(new URL(`../../fixtures/${name}`,import.meta.url));
const source=()=>JSON.parse(fixture('modular-system.json'));
const bytes=value=>Buffer.from(typeof value==='string'?value:JSON.stringify(value));
const execute=(operation,value,annexes={})=>run({operation,primary:Buffer.isBuffer(value)?value:bytes(value),annexes});
const result=(x,unit)=>x.report.results.find(r=>r.input==='primary'&&r.unit===unit);
const finding=(x,unit,rule,p,outcome='fail')=>result(x,unit).findings.some(f=>f.rule===rule&&f.location.pointer===p&&f.outcome===outcome);

test('all seven operations retain distinct modular boundaries',()=>{
  const raw=fixture('modular-system.json');
  assert.equal(result(execute('inspect',raw),'inspect').verdict,'pass');
  assert.equal(result(execute('validateD',raw),'D').verdict,'pass');
  assert.equal(result(execute('validateG',raw),'G').verdict,'pass');
  assert.equal(result(execute('resolveG',raw),'G').verdict,'pass');
  assert.equal(result(execute('validateR',raw),'R').verdict,'pass');
  const exchanged=execute('exchange',raw);assert.equal(result(exchanged,'exchange').verdict,'pass');assert.deepEqual(exchanged.artifacts.primary,raw);
  const lossy=execute('lossyExchange',raw);assert.equal(result(lossy,'exchange').verdict,'fail');assert.equal(Object.keys(lossy.artifacts).length,0);
  for(const x of[exchanged,lossy])assert.equal(x.report.contract,'proposal-0013-candidate-1');
});

test('edition markers remain separate without translating source bytes',()=>{
  const old=source();old.contract='proposal-0012-candidate-2';const x=execute('validateD',old);
  assert.equal(result(x,'D').verdict,'fail');assert.ok(finding(x,'D','P-SHAPE','/contract'));
  const invalid=execute('inspect',Buffer.from('['));assert.equal(result(invalid,'inspect').findings[0].location.byte,1);
});

test('resolveG accepts only direct annex bytes from the modular edition',()=>{
  const d=source(),face=d.definitions[4],actions=d.definitions.slice(5,7),ann={contract:'proposal-0013-candidate-1',root:{key:{scope:'mvp',id:'package',version:'1'},kind:'PackageVersion'},definitions:[structuredClone(face),...structuredClone(actions)],relations:[],exports:[face.key,...actions.map(x=>x.key)],dependencies:[],unresolved:[],extensions:[]};
  d.definitions.splice(4,3);for(const x of ann.definitions)x.owner=ann.root.key;const ref=k=>({dependency:'ui',key:k});d.graphs[0].steps[0].interface=ref(face.key);d.graphs[0].steps[0].action=ref(actions[0].key);d.graphs[0].steps[1].interface=ref(face.key);d.graphs[0].steps[1].action=ref(actions[1].key);for(const rel of d.relations.filter(x=>x.relation==='exposes'))rel.target=ref(face.key);
  let annex=bytes(ann);d.dependencies=[{id:'ui',rootKey:ann.root.key,status:'included',requiredFor:[],sha256:hash(annex)}];let x=execute('resolveG',d,{ui:annex});assert.equal(result(x,'G').verdict,'pass',JSON.stringify(x.report.results.map(r=>[r.input,r.unit,r.verdict,r.findings])));assert.ok(x.report.results.some(r=>r.input==='annex/ui'&&r.unit==='G'));
  ann.contract='proposal-0012-candidate-2';annex=bytes(ann);d.dependencies[0].sha256=hash(annex);x=execute('resolveG',d,{ui:annex});assert.equal(result(x,'G').verdict,'fail');
});

test('operation lookup is explicit, unique and inbound',()=>{
  const d=source(),face=d.definitions[4].payload,call=d.graphs[0].steps[0];
  call.operation='missing';let x=execute('validateG',d);assert.ok(finding(x,'G','G-TARGET','/graphs/0/steps/0'));
  call.operation='ask';face.operations.push(structuredClone(face.operations[0]));x=execute('validateG',d);assert.ok(result(x,'G').checks.some(c=>c.rule==='G-TARGET'&&c.state==='blocked'));
  face.operations.pop();face.operations[0].direction='outbound';x=execute('validateG',d);assert.ok(finding(x,'G','G-TARGET','/graphs/0/steps/0'));
});

test('an unrelated malformed operation does not hide a readable selected operation',()=>{
  const d=source();d.graphs[0].steps[1].operation='ask';d.graphs[0].steps[1].action=d.graphs[0].steps[0].action;d.definitions[4].payload.operations[1].extra=true;
  const x=execute('validateG',d);assert.ok(finding(x,'G','P-SHAPE','/definitions/4/payload/operations/1/extra'));
  assert.ok(result(x,'G').checks.some(c=>c.rule==='G-TARGET'&&c.state==='completed'));
  assert.ok(!result(x,'G').checks.some(c=>c.rule==='G-TARGET'&&c.state==='blocked'));
});

test('runtime selection and coverage never infer a fallback',()=>{
  const d=source();delete d.runtime.selected;let x=execute('validateR',d);assert.equal(result(x,'R').verdict,'pass');assert.ok(result(x,'R').checks.some(c=>c.rule==='R-COMPATIBILITY'&&c.state==='excluded'));
  d.runtime.selected='missing';x=execute('validateR',d);assert.ok(finding(x,'R','R-SELECTION','/runtime'));assert.ok(result(x,'R').checks.some(c=>c.rule==='R-COMPATIBILITY'&&c.state==='blocked'));
  d.runtime.selected='portable';d.runtime.configurations[0].agents.pop();x=execute('validateR',d);assert.ok(finding(x,'R','R-BINDING','/runtime/configurations/0'));
});

test('content closure rejects additions, late prerequisites and multi-node cycles',()=>{
  const d=source(),binding=d.runtime.configurations[0].agents[0],unused=structuredClone(d.definitions[11]);unused.key={scope:'mvp',id:'unused-instructions',version:'1'};unused.owner=d.root.key;d.definitions.push(unused);binding.applications.push({content:unused.key,adapter:{identity:'example/plain-adapter',version:'1'},parameters:{}});let x=execute('validateR',d);assert.ok(result(x,'R').findings.some(f=>f.rule==='R-CONTENT'&&f.details.includes('not reachable')));
  const cycle=source(),skill=cycle.definitions[12],other=structuredClone(skill);other.key={scope:'mvp',id:'other-skill',version:'1'};other.payload.dependencies=[skill.key];skill.payload.dependencies=[other.key];cycle.definitions.push(other);for(const c of cycle.runtime.configurations)for(const a of c.agents)a.applications.unshift({content:other.key,adapter:{identity:'example/plain-adapter',version:'1'},parameters:{}});x=execute('validateR',cycle);assert.ok(result(x,'R').findings.filter(f=>f.rule==='R-CONTENT'&&f.details.includes('cycle')).length>=2);
});

test('Skill closure and duplicate capability declarations are independent',()=>{
  const d=source();d.definitions[12].payload.extra=true;d.runtime.configurations[0].agents[0].requires.push(structuredClone(d.runtime.configurations[0].agents[0].requires[0]));const x=execute('validateR',d);
  assert.ok(finding(x,'R','P-SHAPE','/definitions/12/payload/extra'));
  assert.ok(result(x,'R').findings.some(f=>f.rule==='R-BINDING'&&f.details.includes('Duplicate Edition')));
});

test('partial Skill shape preserves an independent incompatible claim',()=>{
  const d=JSON.parse(fixture('partial-content-prerequisite.json'));const x=execute('validateR',d),r=result(x,'R');
  assert.ok(finding(x,'R','P-SHAPE','/definitions/12/payload/dependencies'));assert.ok(finding(x,'R','R-COMPATIBILITY','/runtime/configurations/0/agents/0'));
  assert.ok(r.checks.some(c=>c.rule==='R-CONTENT'&&c.state==='blocked'));assert.ok(r.checks.some(c=>c.rule==='R-COMPATIBILITY'&&c.state==='completed'));
});

test('approval chains reject bypasses and validate call data at every gate',()=>{
  const good=JSON.parse(fixture('approval-two-gates.json'));assert.equal(result(execute('validateG',good),'G').verdict,'pass');
  const bypass=JSON.parse(fixture('approval-refusal-bypass.json'));assert.ok(finding(execute('validateG',bypass),'G','G-APPROVAL','/graphs/0/steps/1'));
  const unavailable=JSON.parse(fixture('approval-input-unavailable.json')),x=execute('validateG',unavailable);assert.ok(finding(x,'G','G-DATA','/graphs/0/steps/0'));assert.ok(finding(x,'G','G-DATA','/graphs/0/steps/1'));
});

test('host request validation rejects malformed prospective loss records',()=>{
  assert.throws(()=>run({operation:'lossyExchange',primary:bytes(source()),annexes:{},losses:[{input:'primary',location:{byte:-1},information:'x',reason:'x',permission:null}]}),/Invalid prospective Loss/);
});
