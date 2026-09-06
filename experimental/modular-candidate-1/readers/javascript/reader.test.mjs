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
  ann.definitions[0].kind=17;annex=bytes(ann);d.dependencies[0].sha256=hash(annex);x=execute('resolveG',d,{ui:annex});assert.ok(result(x,'G').checks.some(c=>c.rule==='G-DATA'&&c.state==='blocked'));
  ann.definitions[0].kind='Interface';
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

test('malformed Tool collections return blocked reports instead of throwing',()=>{
  for(const field of['failures','requires']){
    const d=source();d.definitions[9].payload[field]={};const x=execute('validateR',d),r=result(x,'R');
    assert.ok(finding(x,'R','P-SHAPE',`/definitions/9/payload/${field}`));
    assert.ok(r.checks.some(c=>c.rule==='R-TOOL'&&c.state==='blocked'));
    assert.ok(x.report.inventory.states.some(s=>s.pointer==='/runtime/configurations/0/agents/0/tools/0'&&s.detail==='blocked'));
  }
});

test('external Agents exclude unknown closure and never become declared-supported',()=>{
  const d=source(),external={dependency:'dep',key:{scope:'remote',id:'agent',version:'1'}};
  d.dependencies.push({id:'dep',rootKey:{scope:'remote',id:'root',version:'1'},status:'external',requiredFor:[],sha256:null});d.graphs[0].steps[0].agent=external;
  for(const c of d.runtime.configurations){c.agents[0].agent=external;c.agents[0].tools=[];c.agents[0].applications=[];}
  const x=execute('validateR',d),r=result(x,'R'),ap='/runtime/configurations/0/agents/0';
  assert.ok(r.checks.some(c=>c.rule==='R-CONTENT'&&c.state==='excluded'&&c.locations.some(l=>l.pointer===ap)));
  assert.ok(r.checks.some(c=>c.rule==='R-TOOL'&&c.state==='excluded'&&c.locations.some(l=>l.pointer===ap)));
  assert.ok(x.report.inventory.states.some(s=>s.pointer===ap&&s.detail==='unknown'));
  assert.ok(!x.report.inventory.states.some(s=>s.pointer===ap&&s.detail==='declared-supported'));
});

test('malformed capability prerequisites block selected assessments',()=>{
  const d=source();d.definitions[12].payload.requires=null;const x=execute('validateR',d),r=result(x,'R');
  assert.ok(r.checks.some(c=>c.rule==='R-COMPATIBILITY'&&c.state==='blocked'));
  assert.ok(x.report.inventory.states.some(s=>s.pointer==='/runtime/configurations/0/agents/0'&&s.detail==='blocked'));
  assert.ok(!x.report.inventory.states.some(s=>s.pointer==='/runtime/configurations/0/agents/0'&&s.detail==='declared-supported'));
});

test('compatibility retains incompatible and unknown capability contributions',()=>{
  const d=source(),a=d.runtime.configurations[0].agents[0];a.claims[0].status='unsupported';a.claims.splice(1,1);const x=execute('validateR',d),p='/runtime/configurations/0/agents/0',findings=result(x,'R').findings.filter(f=>f.rule==='R-COMPATIBILITY'&&f.location.pointer===p);
  assert.deepEqual(new Set(findings.map(f=>f.outcome)),new Set(['fail','inconclusive']));
  assert.ok(x.report.inventory.states.some(s=>s.pointer===p&&s.detail==='incompatible'));
});

test('ambiguous bindings, choices and claims never choose a last record',()=>{
  let d=source(),a=d.runtime.configurations[0].agents[0];a.claims.unshift({...a.claims[0],status:'unsupported'});let x=execute('validateR',d),p='/runtime/configurations/0/agents/0';
  assert.ok(finding(x,'R','R-BINDING',p));assert.ok(x.report.inventory.states.some(s=>s.pointer===p&&s.detail==='blocked'));

  d=source();let tool=d.runtime.configurations[0].agents[0].tools[0];tool.choices.push(structuredClone(tool.choices[0]));x=execute('validateR',d);p='/runtime/configurations/0/agents/0/tools/0';
  assert.ok(result(x,'R').checks.some(c=>c.rule==='R-COMPATIBILITY'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===p)));assert.ok(x.report.inventory.states.some(s=>s.pointer===p&&s.detail==='blocked'));

  d=source();let config=d.runtime.configurations[0];config.agents[0].tools[0].selected='missing';config.agents.push(structuredClone(config.agents[0]));config.agents.at(-1).tools[0].selected='search-a';x=execute('validateR',d);
  assert.ok(result(x,'R').findings.some(f=>f.rule==='R-TOOL'&&f.details.includes('Selected Implementation missing')));
  assert.ok(x.report.inventory.states.some(s=>s.pointer==='/runtime/configurations/0/agents/0'&&s.detail==='blocked'));

  d=source();a=d.runtime.configurations[0].agents[0];a.tools.push(structuredClone(a.tools[0]));x=execute('validateR',d);
  assert.ok(result(x,'R').findings.some(f=>f.rule==='R-TOOL'&&f.details.includes('Duplicate ToolBinding')));
  assert.ok(x.report.inventory.states.filter(s=>s.pointer.startsWith('/runtime/configurations/0/agents/0/tools/')&&s.detail==='blocked').length>=2);
});

test('an unreadable graph index blocks lookup and assessment',()=>{
  const d=source();d.graphs=[{}];const x=execute('validateR',d),r=result(x,'R');
  assert.ok(r.checks.some(c=>c.rule==='R-SELECTION'&&c.state==='blocked'));
  assert.ok(!r.findings.some(f=>f.rule==='R-SELECTION'&&f.details.includes('does not exist')));
  assert.ok(r.checks.some(c=>c.rule==='R-COMPATIBILITY'&&c.state==='blocked'));
});

test('G rejects duplicate graph definitions and approvers',()=>{
  let d=source();d.graphs.push(structuredClone(d.graphs[0]));let x=execute('validateG',d);assert.ok(result(x,'G').findings.some(f=>f.rule==='G-TARGET'&&f.details.includes('Duplicate Graph definition')));
  d=JSON.parse(fixture('approval-two-gates.json'));d.definitions[13].payload.approvers.push(structuredClone(d.definitions[13].payload.approvers[0]));x=execute('validateG',d);assert.ok(result(x,'G').findings.some(f=>f.rule==='G-TARGET'&&f.details.includes('Duplicate approver Ref')));
});

test('Tool evidence states use only exact Implementation claim pointers',()=>{
  const d=source();d.runtime.configurations[0].agents[0].tools[0].choices[0].claims[0].evidence=null;const states=execute('validateR',d).report.inventory.states;
  assert.ok(states.some(s=>s.pointer==='/runtime/configurations/0/agents/0/tools/0/choices/0/claims/0/evidence'));
  assert.ok(!states.some(s=>s.pointer==='/runtime/configurations/0/agents/0/tools/0/claims/0/evidence'));
});

test('missing transitive Applications fail at the AgentBinding',()=>{
  const d=source();d.runtime.configurations[0].agents[0].applications.shift();const x=execute('validateR',d),ap='/runtime/configurations/0/agents/0';
  assert.ok(finding(x,'R','R-CONTENT',ap));
  assert.ok(!result(x,'R').findings.some(f=>f.rule==='R-CONTENT'&&f.location.pointer===`${ap}/applications/0`&&f.details.includes('earlier')));
});

test('selected Operation target defects point to the Operation record',()=>{
  const d=source();d.definitions[4].payload.operations[0].action.id='missing';const x=execute('validateG',d);
  assert.ok(finding(x,'G','G-TARGET','/definitions/4/payload/operations/0'));
});

test('an unreadable Skill closure cannot prove that Applications are extra',()=>{
  const d=source();d.definitions[12].payload.dependencies=null;const x=execute('validateR',d),r=result(x,'R');
  assert.ok(r.checks.some(c=>c.rule==='R-CONTENT'&&c.state==='blocked'));
  assert.ok(!r.findings.some(f=>f.rule==='R-CONTENT'&&f.details.includes('not reachable')));
});

test('an unreadable Tool effect blocks its selected assessment',()=>{
  const d=source();d.definitions[9].payload.effects=17;const x=execute('validateR',d),p='/runtime/configurations/0/agents/0/tools/0';
  assert.ok(finding(x,'R','P-SHAPE','/definitions/9/payload/effects'));
  assert.ok(result(x,'R').checks.some(c=>c.rule==='R-COMPATIBILITY'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===p)));
  assert.ok(x.report.inventory.states.some(s=>s.pointer===p&&s.detail==='blocked'));
});

test('partial G prerequisites block dependent checks without invented failures',()=>{
  let d=source();d.relations[1].target=null;let x=execute('validateG',d),r=result(x,'G'),step='/graphs/0/steps/0';
  assert.ok(r.checks.some(c=>c.rule==='G-TARGET'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));
  assert.ok(!r.findings.some(f=>f.rule==='G-TARGET'&&f.details.includes('does not expose')));

  d=source();d.graphs[0].steps[0].resources=null;x=execute('validateG',d);r=result(x,'G');
  assert.ok(r.checks.some(c=>c.rule==='G-TARGET'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));

  d=source();d.graphs[0].steps[0].interface.id='missing';x=execute('validateG',d);r=result(x,'G');
  assert.ok(r.checks.some(c=>c.rule==='G-DATA'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));

  d=source();d.graphs[0].steps[1].context={step:'call-a',port:'anything'};d.graphs[0].steps[0].kind=17;x=execute('validateG',d);r=result(x,'G');
  assert.ok(r.checks.some(c=>c.rule==='G-DATA'&&c.state==='blocked'&&c.locations.some(l=>l.pointer==='/graphs/0/steps/1')));
  assert.ok(!r.findings.some(f=>f.rule==='G-DATA'&&f.location.pointer==='/graphs/0/steps/1'&&f.details.includes('wrong type')));
});

test('an ambiguous approval call blocks lookup',()=>{
  const d=JSON.parse(fixture('approval-two-gates.json')),invoke=d.graphs[0].steps.find(s=>s.kind==='invoke');d.graphs[0].steps.push(structuredClone(invoke));const x=execute('validateG',d),r=result(x,'G');
  assert.ok(r.checks.some(c=>c.rule==='G-APPROVAL'&&c.state==='blocked'));
  assert.ok(!r.findings.some(f=>f.rule==='G-APPROVAL'&&f.details.includes('call is not')));
});

test('Graph definition uniqueness survives an unreadable steps collection',()=>{
  const d=source();d.graphs.push(structuredClone(d.graphs[0]));d.graphs[0].steps=null;const x=execute('validateG',d);
  assert.ok(finding(x,'G','G-TARGET','/graphs/1'));
});

test('selected Operation lookup blocks unreadable ids and semantics',()=>{
  let d=source();delete d.definitions[4].payload.operations[0].id;let x=execute('validateG',d),r=result(x,'G'),step='/graphs/0/steps/0';
  assert.ok(r.checks.some(c=>c.rule==='G-TARGET'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));
  assert.ok(!r.findings.some(f=>f.rule==='G-TARGET'&&f.details.includes('does not exist')));
  d=source();d.definitions[4].payload.operations[0].direction=17;x=execute('validateG',d);r=result(x,'G');
  assert.ok(r.checks.some(c=>c.rule==='G-TARGET'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));
});

test('Application content keeps its local kind check',()=>{
  const d=source(),application=d.runtime.configurations[0].agents[0].applications[0];application.content=d.definitions[5].key;const x=execute('validateR',d);
  assert.ok(result(x,'R').findings.some(f=>f.rule==='R-CONTENT'&&f.location.pointer==='/runtime/configurations/0/agents/0/applications/0'&&f.details.includes('wrong kind')));
});

test('partial Agent relations preserve readable capability requirements',()=>{
  const d=source(),binding=d.runtime.configurations[0].agents[0],ap='/runtime/configurations/0/agents/0';d.relations[1].target=null;binding.claims[2].status='unsupported';const x=execute('validateR',d),r=result(x,'R');
  assert.ok(finding(x,'R','R-COMPATIBILITY',ap));
  assert.ok(r.checks.some(c=>c.rule==='R-CONTENT'&&c.state==='completed'));
  assert.ok(x.report.inventory.states.some(s=>s.pointer===ap&&s.detail==='incompatible'));
});

test('unreadable binding collections and identities do not prove omissions',()=>{
  for(const field of['applications','tools']){
    const d=source(),ap='/runtime/configurations/0/agents/0';d.runtime.configurations[0].agents[0][field]=null;const x=execute('validateR',d),r=result(x,'R');
    assert.ok(r.checks.some(c=>c.rule===(field==='applications'?'R-CONTENT':'R-TOOL')&&c.state==='blocked'));
    assert.ok(!r.findings.some(f=>f.location.pointer===ap&&f.details.includes(field==='applications'?'Required Application missing':'coverage differs')));
  }
  const d=source(),ap='/runtime/configurations/0/agents/0';d.runtime.configurations[0].agents[0].applications[0].content=null;d.runtime.configurations[0].agents[0].tools[0].tool=null;const r=result(execute('validateR',d),'R');
  assert.ok(!r.findings.some(f=>f.location.pointer===ap&&['Required Application missing','ToolBinding coverage differs from required Tools'].includes(f.details)));
});

test('unreadable and ambiguous Operation selectors block dependent data checks',()=>{
  let d=source(),step='/graphs/0/steps/0';d.graphs[0].steps[0].operation=null;let x=execute('validateG',d),r=result(x,'G');
  assert.ok(r.checks.some(c=>c.rule==='G-TARGET'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));
  assert.ok(r.checks.some(c=>c.rule==='G-DATA'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));
  assert.ok(!r.findings.some(f=>f.rule==='G-TARGET'&&f.details.includes('does not exist')));
  d=source();d.definitions[4].payload.operations.push(structuredClone(d.definitions[4].payload.operations[0]));x=execute('validateG',d);r=result(x,'G');
  assert.ok(r.checks.some(c=>c.rule==='G-DATA'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));
});

test('approval gates block unreadable call data prerequisites',()=>{
  for(const field of['inputs','bindings']){
    const d=JSON.parse(fixture('approval-two-gates.json')),call=d.graphs[0].steps.find(s=>s.kind==='invoke');call[field]=null;const r=result(execute('validateG',d),'G');
    for(const step of['/graphs/0/steps/0','/graphs/0/steps/1'])assert.ok(r.checks.some(c=>c.rule==='G-DATA'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));
    if(field==='inputs')for(const step of['/graphs/0/steps/0','/graphs/0/steps/1'])assert.ok(!r.findings.some(f=>f.rule==='G-DATA'&&f.location.pointer===step&&f.details.includes('wrong type')));
  }
});

test('partial runtime indexes do not invent missing selected records',()=>{
  let d=source();d.runtime.configurations=null;let x=execute('validateR',d),r=result(x,'R');
  assert.ok(r.checks.some(c=>c.rule==='R-SELECTION'&&c.state==='blocked'));
  assert.ok(!r.findings.some(f=>f.rule==='R-SELECTION'&&f.details.includes('does not exist')));
  d=source();d.runtime.configurations[0].agents=null;x=execute('validateR',d);r=result(x,'R');
  assert.ok(r.checks.some(c=>c.rule==='R-BINDING'&&c.state==='blocked'));
  assert.ok(!r.findings.some(f=>f.rule==='R-BINDING'&&f.details.includes('coverage differs')));
  d=source();const tool=d.runtime.configurations[0].agents[0].tools[0];tool.choices=null;tool.selected='missing';x=execute('validateR',d);r=result(x,'R');
  assert.ok(r.checks.some(c=>c.rule==='R-TOOL'&&c.state==='blocked'));
  assert.ok(!r.findings.some(f=>f.rule==='R-TOOL'&&f.details.includes('Selected Implementation missing')));
});

test('null relations block closure without crashing readable checks',()=>{
  const d=source();d.relations.push(null);const r=result(execute('validateR',d),'R');
  assert.ok(r.checks.some(c=>c.rule==='R-CONTENT'&&c.state==='blocked'));
  assert.ok(r.checks.some(c=>c.rule==='R-TOOL'&&c.state==='blocked'));
});

test('a malformed uses relation does not hide a readable Principal mismatch',()=>{
  const d=source(),step='/graphs/0/steps/0';d.graphs[0].steps[0].principal=d.definitions[3].key;d.relations.push({source:d.definitions[0].key,relation:'uses',expectedKind:'Tool',target:null});const x=execute('validateG',d),r=result(x,'G');
  assert.ok(r.checks.some(c=>c.rule==='G-TARGET'&&c.state==='blocked'&&c.locations.some(l=>l.pointer===step)));
  assert.ok(r.findings.some(f=>f.rule==='G-TARGET'&&f.location.pointer===step&&f.details.includes('principal differs')));
});

test('a later unreadable Application does not hide a known order violation',()=>{
  const d=source(),binding=d.runtime.configurations[0].agents[0];binding.applications.reverse();binding.applications.push(null);const r=result(execute('validateR',d),'R');
  assert.ok(r.findings.some(f=>f.rule==='R-CONTENT'&&f.location.pointer==='/runtime/configurations/0/agents/0/applications/0'&&f.details.includes('appear earlier')));
});

test('partial relations outside R closure do not affect reachable content',()=>{
  for(const [relation,expectedKind] of [['actsAs','Principal'],['exposes','Interface'],['contains','Instructions']]){
    const d=source(),binding=d.runtime.configurations[0].agents[0],content=structuredClone(d.definitions.find(x=>x.kind==='Instructions'));content.key.id+='-extra';d.definitions.push(content);binding.applications.push({...structuredClone(binding.applications[0]),content:content.key});d.relations.push({source:binding.agent,relation,expectedKind,target:null});const r=result(execute('validateR',d),'R');
    assert.ok(r.findings.some(f=>f.rule==='R-CONTENT'&&f.location.pointer==='/runtime/configurations/0/agents/0/applications/2'&&f.details.includes('not reachable')));
  }
});

test('a partial contains relation does not hide missing Interface exposure',()=>{
  const d=source(),step='/graphs/0/steps/0',agent=d.graphs[0].steps[0].agent;d.relations=d.relations.filter(relation=>!(relation.relation==='exposes'&&JSON.stringify(relation.source)===JSON.stringify(agent)));d.relations.push({source:agent,relation:'contains',expectedKind:'Resource',target:null});const r=result(execute('validateG',d),'G');
  assert.ok(r.findings.some(f=>f.rule==='G-TARGET'&&f.location.pointer===step&&f.details.includes('does not expose')));
});
