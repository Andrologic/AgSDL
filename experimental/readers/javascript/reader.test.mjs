import test from 'node:test';
import assert from 'node:assert/strict';
import { parse, stringify, uint, NumberToken } from './json.mjs';
import { run } from './reader.mjs';
import { hash } from './core.mjs';
import { transport } from './cli.mjs';
const K=(id,scope='s')=>({scope,id,version:'1'});
function doc(){return {contract:'proposal-0012-candidate-2',root:{key:K('root'),kind:'System'},definitions:[],relations:[],exports:[],dependencies:[],unresolved:[],extensions:[]};}
function add(d,id,kind,payload={}){d.definitions.push({key:K(id,d.root.key.scope),kind,owner:d.root.key,payload});return K(id,d.root.key.scope);}
const bytes=d=>Buffer.from(typeof d==='string'?d:JSON.stringify(d));
const execute=(operation,d,annexes={})=>run({operation,primary:bytes(d),annexes});
const last=x=>x.report.results.at(-1);
const finding=(x,rule,p,outcome='fail')=>x.report.results.some(r=>r.findings.some(f=>f.rule===rule&&f.location.pointer===p&&f.outcome===outcome));
function graphDoc(){const d=doc();const a=add(d,'a','Agent'),pr=add(d,'pr','Principal'),ins=add(d,'ins','Instructions'),act=add(d,'act','Action'),res=add(d,'res','Resource'),face=add(d,'face','Interface',{inputs:{x:'string'},outputs:{y:'string'},action:act}),flow=add(d,'flow','ControlFlow');
  d.relations=[{source:a,relation:'actsAs',target:pr,expectedKind:'Principal'},{source:a,relation:'exposes',target:face,expectedKind:'Interface'},{source:a,relation:'directedBy',target:ins,expectedKind:'Instructions'}];
  d.graphs=[{definition:flow,entry:'call',inputs:{x:'string',ctx:'json'},outputs:{y:'string'},steps:[{id:'call',kind:'invoke',agent:a,interface:face,action:act,resources:[res],principal:pr,context:{input:'ctx'},inputs:{x:'string'},outputs:{y:'string'},bindings:{x:{input:'x'}},success:'ok',failure:'bad'},{id:'ok',kind:'end',outcome:'success',bindings:{y:{step:'call',port:'y'}}},{id:'bad',kind:'end',outcome:'failure',reason:'failed'}]}];return d;
}
test('lossless numbers, exact mathematical uint and prototype keys',()=>{
  const source=Buffer.from('{"__proto__":{"huge":1e999999},"x":9007199254740993,"zero":-0}');const p=parse(source);assert.equal(p.error,undefined);assert.equal(Object.getPrototypeOf(p.tree),null);assert.equal(stringify(p.tree),source.toString());
  for(const s of ['0','-0','1.00','1e3','90071992547409910e-1'])assert.equal(uint(new NumberToken(s)),true,s);
  for(const s of ['1e-999999','1e999999','9007199254740991.1','9007199254740992','-1'])assert.equal(uint(new NumberToken(s)),false,s);
  assert.equal(uint(new NumberToken('0'),true),false);
  const out=transport({operation:'inspect',primary:source.toString('base64'),annexes:{}});assert.match(stringify(out),/"huge":1e999999/);
});
test('strict JSON bytes, duplicate decoded keys, escapes and spans',()=>{
  for(const src of ['\ufeff{}','{"a":1,"\\u0061":2}','[1,]','01','1.','true false','"\\udc00"','"\\ud800"','"a\n"'])assert.ok(parse(bytes(src)).error,src);
  assert.equal(parse(bytes('{"a":1,"\\u0061":2}')).error.byte,7);
  assert.equal(parse(Buffer.from([91,255,93])).error.byte,1);
  assert.equal(parse(bytes('[')).error.byte,1);
  const p=parse(bytes('{"é/~":"😀"}'));assert.equal(p.error,undefined);assert.deepEqual(p.spans.get('/é~1~0'),{start:8,end:14});
  assert.equal(parse(bytes('"\\ud83d\\ude00"')).tree,'😀');
});
test('inspect has syntax only; nonobjects are opaque; malformed dependency inventory',()=>{
  const a=execute('inspect','[123]');assert.equal(last(a).verdict,'pass');assert.equal(a.report.inventory.opaque[0].pointer,'');
  const d=doc();d.dependencies=[{id:'bad'},{id:'ok',rootKey:K('r','t'),status:'external',requiredFor:[],sha256:null}];
  const x=execute('inspect',d);assert.equal(last(x).findings.length,0);assert.ok(x.report.inventory.opaque.some(s=>s.pointer==='/dependencies'));assert.ok(!x.report.inventory.states.some(s=>s.state==='unknown'));
  const y=execute('validateD',d);assert.ok(y.report.inventory.states.some(s=>s.pointer==='/dependencies/1/sha256'));
});
test('exact exchange copies invalid UTF8 and invalid semantics, but enforces readable accounting',()=>{
  const raw=Buffer.from([255,0,42]);const x=run({operation:'exchange',primary:raw,annexes:{orphan:raw}});assert.equal(last(x).verdict,'pass');assert.deepEqual(x.artifacts.primary,raw);assert.equal(x.report.outputs.length,2);
  const d=doc();const y=execute('exchange',d,{orphan:raw});assert.equal(last(y).verdict,'fail');assert.equal(Object.keys(y.artifacts).length,0);
  d.dependencies=[{id:'x',rootKey:K('r','t'),status:'included',requiredFor:['exchange'],sha256:null}];const z=execute('exchange',d,{x:raw});assert.equal(last(z).verdict,'inconclusive');assert.equal(z.report.outputs.length,0);
  d.dependencies[0].sha256=hash(raw);assert.equal(last(execute('exchange',d,{x:raw})).verdict,'pass');
  d.dependencies[0].sha256='0'.repeat(64);assert.ok(finding(execute('exchange',d,{x:raw}),'E-PRESERVE','/dependencies/0'));
});
test('lossy exchange always refuses with prospective loss',()=>{const x=execute('lossyExchange','invalid');assert.equal(last(x).verdict,'fail');assert.equal(x.report.losses[0].information,'unspecified requested loss');assert.equal(x.report.outputs.length,0);assert.deepEqual(last(x).checks.map(c=>c.rule),['E-LOSS']);});
test('D reference, identity, owner, relation and cycle failures retain separate findings',()=>{
  const d=graphDoc();assert.equal(last(execute('validateD',d)).verdict,'pass');d.definitions.push(structuredClone(d.definitions[0]));d.definitions[1].owner=K('wrong');d.relations.push({source:K('root'),relation:'contains',target:K('root'),expectedKind:'System'}); // invalid Kind is a shape error
  let x=execute('validateD',d);assert.ok(finding(x,'D-IDENTITY','/definitions/7'));assert.ok(finding(x,'D-OWNER','/definitions/1'));assert.ok(finding(x,'P-SHAPE','/relations/3/expectedKind'));
  d.definitions.pop();d.relations[3]={source:K('a'),relation:'contains',target:K('a'),expectedKind:'Agent'};x=execute('validateD',d);assert.ok(finding(x,'D-CYCLE','/relations'));
});
test('Fragment deferral exempts only exposes and leaves deferred evidence',()=>{
  const d=graphDoc();delete d.graphs;d.root.kind='Fragment';d.exports=[K('a')];d.relations=d.relations.filter(r=>r.relation!=='exposes');d.unresolved=[{subject:K('a'),obligation:'agent-interface-minimum',rule:'fragment-interface-deferral',relation:'exposes',expectedKind:'Interface',missingMinimum:1,target:null,satisfyBy:'typed-exposes-relation',expiresBefore:'resolved-graph'}];
  const x=execute('validateD',d);assert.equal(last(x).verdict,'pass');assert.ok(finding(x,'D-DEFERRAL','/unresolved/0','deferred'));d.root.kind='System';d.exports=[];assert.ok(finding(execute('validateD',d),'D-DEFERRAL','/unresolved/0'));
});
test('extensions classify independently and custom Kind cannot hide behind annotations',()=>{
  const d=doc();d.extensions=[{identity:'vendor/ext',version:'1',operations:{validateD:{ignoreRule:'annotation-only'},validateG:'required'},payload:null}];
  assert.equal(last(execute('validateD',d)).verdict,'pass');assert.equal(last(execute('validateG',d)).verdict,'unsupported');
  add(d,'custom',{extension:{identity:'vendor/ext',version:'1'},name:'Odd'});assert.ok(finding(execute('validateD',d),'X-MODE','/extensions/0'));
});
test('G local pass, failed success dominance, malformed graph and opaque D',()=>{
  const d=graphDoc();assert.equal(last(execute('resolveG',d)).verdict,'pass');d.graphs[0].steps[0].failure='ok';d.graphs[0].steps.pop();assert.ok(finding(execute('validateG',d),'G-DATA','/graphs/0/steps/1'));
  d.graphs=17;assert.equal(last(execute('validateD',d)).verdict,'pass');const x=execute('validateG',d);assert.ok(finding(x,'P-SHAPE','/graphs'));assert.ok(last(x).checks.some(c=>c.rule==='G-DATA'&&c.state==='blocked'));
});
test('G approval gate validates pre-invocation data and alternate incoming edges',()=>{
  const d=graphDoc(),g=d.graphs[0];add(d,'gate','ApprovalRequirement',{approvers:[K('pr')],validForMs:10});g.entry='approve';g.steps.unshift({id:'approve',kind:'approval',requirement:K('gate'),timeoutMs:2,approved:'call',denied:'bad',failure:'bad'});
  assert.equal(last(execute('validateG',d)).verdict,'pass');g.steps[0].denied='call';assert.ok(finding(execute('validateG',d),'G-APPROVAL','/graphs/0/steps/0'));
  g.steps[0].denied='bad';g.steps[1].context={step:'call',port:'y'};assert.ok(finding(execute('validateG',d),'G-DATA','/graphs/0/steps/0'));
});
function external(){const p=graphDoc(),a=doc();a.root.key=K('root','ann');a.root.kind='PackageVersion';const face=add(a,'face','Interface',{inputs:{x:'string'},outputs:{y:'string'},action:K('act','ann')});const action=add(a,'act','Action');a.exports=[face,action];const ref=k=>({dependency:'dep',key:k});p.graphs[0].steps[0].interface=ref(face);p.graphs[0].steps[0].action=ref(action);p.relations[1].target=ref(face);const b=bytes(a);p.dependencies=[{id:'dep',rootKey:a.root.key,status:'included',requiredFor:[],sha256:hash(b)}];return {p,a,b};}
test('external G excludes lookup locally and resolves supplied exported targets',()=>{
  const {p,b}=external();const x=execute('validateG',p,{dep:b});assert.equal(last(x).verdict,'pass');assert.ok(last(x).checks.some(c=>c.rule==='G-TARGET'&&c.state==='excluded'));assert.ok(last(x).checks.some(c=>c.rule==='G-DATA'&&c.state==='excluded'));
  const y=execute('resolveG',p,{dep:b});assert.equal(last(y).verdict,'pass');assert.deepEqual(y.report.results.map(r=>r.input+':'+r.unit),['primary:D','annex/dep:D','annex/dep:G','primary:G']);
  assert.ok(!y.report.inventory.opaque.some(s=>s.input==='annex/dep'&&s.pointer==='/definitions/0/payload'));
  assert.equal(last(execute('resolveG',p)).verdict,'fail');
});
test('resolveG requires explicit dependencies even with absent graphs',()=>{
  const d=doc();d.dependencies=[{id:'needed',rootKey:K('r','t'),status:'external',requiredFor:['resolveG'],sha256:null}];const x=execute('resolveG',d);assert.equal(last(x).verdict,'fail');assert.ok(finding(x,'G-RESOLVE','/dependencies/0'));assert.ok(last(x).checks.some(c=>c.rule==='G-RESOLVE'&&c.state==='excluded'));
});
test('resolveG selected payloads report annex shape, integrity unknown and transitive refs',()=>{
  const {p,a}=external();a.definitions[0].payload.extra=1;let b=bytes(a);p.dependencies[0].sha256=hash(b);const x=execute('resolveG',p,{dep:b});assert.equal(last(x).verdict,'fail');assert.ok(x.report.results.some(r=>r.input==='annex/dep'&&r.unit==='G'&&r.findings.some(f=>f.rule==='P-SHAPE')));
  delete a.definitions[0].payload.extra;a.dependencies=[{id:'next',rootKey:K('r','next'),status:'external',requiredFor:[],sha256:null}];a.definitions[0].payload.action={dependency:'next',key:K('act','next')};b=bytes(a);p.dependencies[0].sha256=hash(b);assert.equal(last(execute('resolveG',p,{dep:b})).verdict,'unsupported');
});
test('R no defaults, unknown evidence and external hosting are inventoried without readiness',()=>{
  const d=doc();add(d,'a','Action');d.runtime={requirements:[{id:'need',capability:{identity:'vendor/cap',version:'1'},subject:K('a')} ]};let x=execute('validateR',d);assert.equal(last(x).verdict,'pass');assert.ok(x.report.inventory.states.some(s=>s.pointer==='/runtime/selection'&&s.state==='absent'));
  d.runtime.selection={engine:{identity:'custom/engine',version:'future'},interface:{identity:'custom/api',version:'1'},evidence:[{requirement:'need',claim:'satisfied',artifact:null}]};x=execute('validateR',d);assert.equal(last(x).verdict,'pass');assert.ok(x.report.inventory.states.some(s=>s.pointer==='/runtime/selection/evidence/0/artifact'&&s.state==='unknown'));assert.ok(last(x).checks.some(c=>c.rule==='X-READINESS'&&c.state==='excluded'));
  assert.ok(!execute('validateD',d).report.inventory.states.some(s=>s.pointer.startsWith('/runtime/selection')));
  d.runtime={};x=execute('validateR',d);assert.equal(last(x).verdict,'fail');assert.ok(!x.report.inventory.states.some(s=>s.pointer==='/runtime/selection'));
});
test('failed D cannot become a pass for absent G/R and syntax has fixed result phases',()=>{
  const d=doc();d.contract='wrong';for(const op of ['validateG','resolveG','validateR']){const x=execute(op,d);assert.equal(last(x).verdict,'fail');assert.ok(last(x).checks.some(c=>c.rule==='P-PREREQUISITE'&&c.state==='blocked'));}
  const x=execute('resolveG','[');assert.deepEqual(x.report.results.map(r=>[r.unit,r.phase]),[['D','unresolved-document'],['G','resolved-graph']]);
});
test('partial definition shape preserves identities and typed lookups',()=>{
  const d=graphDoc();d.definitions[0].owner=17;
  const x=execute('validateD',d);assert.ok(finding(x,'P-SHAPE','/definitions/0/owner'));assert.ok(!x.report.results[0].findings.some(f=>f.rule==='D-REFERENCE'));
  d.definitions.push({...structuredClone(d.definitions[0]),key:{...K('a'),version:'2'}});const y=execute('validateD',d);assert.ok(finding(y,'D-IDENTITY','/definitions/7'));assert.ok(y.report.results[0].checks.some(c=>c.rule==='D-REFERENCE'&&c.state==='blocked'));
});
test('malformed terminal remains present for independent path checks',()=>{
  const d=graphDoc();delete d.graphs[0].steps[2].reason;const x=execute('validateG',d);assert.ok(finding(x,'P-SHAPE','/graphs/0/steps/2'));assert.ok(!x.report.results.at(-1).findings.some(f=>f.rule==='G-PATH'));
});
test('host request rejects invalid loss permissions and preserves valid losses',()=>{
  const loss={input:'primary',location:{pointer:''},information:'metadata',reason:'requested',permission:null};
  const x=run({operation:'lossyExchange',primary:bytes('{}'),annexes:{},losses:[loss]});assert.deepEqual(x.report.losses,[loss]);
  assert.throws(()=>run({operation:'lossyExchange',primary:bytes('{}'),annexes:{},losses:[{...loss,permission:'allowed'}]}),/Loss/);
});

test('API enforces the closed request boundary',()=>{
  assert.throws(()=>run({operation:'inspect',primary:bytes('{}'),annexes:{},extra:1}),/request fields/);
  assert.throws(()=>run({operation:'inspect',primary:bytes('{}')}),/request fields/);
});
test('a non-invoke producer fails G-DATA rather than becoming unavailable',()=>{
  const d=graphDoc(),g=d.graphs[0];g.inputs.b='boolean';g.entry='cond';g.steps.unshift({id:'cond',kind:'condition',test:{input:'b'},true:'call',false:'bad',failure:'bad'});g.steps[1].context={step:'cond',port:'x'};assert.ok(finding(execute('validateG',d),'G-DATA','/graphs/0/steps/1'));
});
test('custom classification and source kinds use only their required fields',()=>{
  const d=doc();d.extensions=[{identity:'v/ext',version:'1',operations:{validateD:{ignoreRule:'annotation-only'}},payload:null}];add(d,'x',{extension:{identity:'v/ext',version:'1'},name:'x'});d.definitions[0].owner=null;assert.ok(finding(execute('validateD',d),'X-MODE','/extensions/0'));
  const g=graphDoc();g.definitions[0].kind=null;const x=execute('validateD',g);assert.ok(!x.report.results[0].findings.some(f=>f.rule==='D-RELATION'));assert.ok(last(x).checks.some(c=>c.rule==='D-RELATION'&&c.state==='blocked'));
});
test('malformed dependency hint preserves external reference declaration',()=>{
  const d=doc();d.dependencies=[{id:'x',rootKey:K('r','remote'),status:'external',requiredFor:[],sha256:null,location:null}];d.relations=[{source:K('root'),relation:'uses',target:{dependency:'x',key:K('resource','remote')},expectedKind:'Resource'}];const x=execute('validateD',d);assert.ok(finding(x,'P-SHAPE','/dependencies/0/location'));assert.ok(!last(x).findings.some(f=>f.rule==='D-REFERENCE'));
});
test('malformed engine does not hide an independently invalid evidence reference',()=>{
  const d=doc();d.runtime={requirements:[],selection:{engine:null,interface:{identity:'v/i',version:'1'},evidence:[{requirement:'missing',claim:'satisfied',artifact:null}]}};const x=execute('validateR',d);assert.ok(finding(x,'P-SHAPE','/runtime/selection/engine'));assert.ok(finding(x,'R-SELECTION','/runtime/selection/evidence/0'));
});

test('malformed producer and external target kinds block dependent type checks',()=>{
  const d=graphDoc();d.graphs[0].steps[0].kind=null;const x=execute('validateG',d);assert.ok(!last(x).findings.some(f=>f.rule==='G-DATA'));assert.ok(last(x).checks.some(c=>c.rule==='G-DATA'&&c.state==='blocked'));
  const {p,a}=external();a.definitions[1].kind=null;const b=bytes(a);p.dependencies[0].sha256=hash(b);const y=execute('resolveG',p,{dep:b});assert.equal(last(y).verdict,'fail');assert.ok(!last(y).findings.some(f=>f.rule==='G-RESOLVE'));assert.ok(last(y).checks.some(c=>c.rule==='G-RESOLVE'&&c.state==='blocked'));
});
test('an extra relation field does not hide independently missing targets',()=>{
  const d=doc();d.relations=[{source:K('missing'),relation:'uses',target:K('also-missing'),expectedKind:'Resource',extra:true}];const x=execute('validateD',d);assert.ok(finding(x,'P-SHAPE','/relations/0/extra'));assert.ok(finding(x,'D-REFERENCE','/relations/0'));
});
test('runtime parent shape does not suppress observable requirement and selection checks',()=>{
  const d=doc();d.runtime={requirements:[{id:'need',capability:{identity:'v/c',version:'1'},subject:K('missing')}],extra:true};const x=execute('validateR',d);assert.ok(finding(x,'R-REQUIREMENT','/runtime/requirements/0'));assert.ok(!x.report.inventory.states.some(s=>s.pointer==='/runtime/selection'));
  d.runtime={selection:{engine:{identity:'v/e',version:'1'},interface:{identity:'v/i',version:'1'},hosting:K('missing'),evidence:[]}};const y=execute('validateR',d);assert.ok(finding(y,'R-SELECTION','/runtime/selection'));assert.ok(!y.report.inventory.states.some(s=>s.pointer==='/runtime/selection'));
});
test('extra fields on an Agent relation do not invent a missing Interface',()=>{
  const d=graphDoc();d.relations[1].extra=true;const x=execute('validateG',d);assert.ok(finding(x,'P-SHAPE','/relations/1/extra'));assert.ok(!last(x).findings.some(f=>f.rule==='G-TARGET'));assert.ok(!x.report.results[0].findings.some(f=>f.rule==='D-AGENT'));
});

test('unreadable definitions block lookup without inventing missing targets',()=>{
  const d=graphDoc();d.definitions=null;const x=execute('validateD',d);
  assert.ok(!last(x).findings.some(f=>f.rule==='D-REFERENCE'));
  const blocked=last(x).checks.find(c=>c.rule==='D-REFERENCE'&&c.state==='blocked');
  for(let i=0;i<3;i++)assert.ok(blocked.locations.some(l=>l.pointer===`/relations/${i}`));
});
test('absent graphs retain completed dependency checks in resolveG',()=>{
  const x=execute('resolveG',doc());
  assert.deepEqual(last(x).checks.filter(c=>c.rule==='G-RESOLVE'),[
    {rule:'G-RESOLVE',state:'completed',locations:[]},
    {rule:'G-RESOLVE',state:'excluded',locations:[{pointer:'/graphs'}]}
  ]);
});
test('malformed selection does not advertise runtime child states',()=>{
  const d=doc();d.runtime={requirements:[],selection:{engine:{identity:'engine',version:'1'},provider:'bad provider',evidence:[]}};
  const x=execute('validateR',d);assert.ok(finding(x,'P-SHAPE','/runtime/selection/provider'));
  assert.ok(!x.report.inventory.states.some(s=>s.pointer.startsWith('/runtime/')));
});
test('selected key collision preserves independent annex payload checks',()=>{
  const {p,a}=external();p.definitions.push({...a.definitions[0],owner:p.root.key});
  a.definitions[0].payload.extra=null;const b=bytes(a);p.dependencies[0].sha256=hash(b);
  const x=execute('resolveG',p,{dep:b});
  assert.ok(finding(x,'G-RESOLVE','/graphs/0/steps/0'));
  assert.ok(x.report.results.some(r=>r.input==='annex/dep'&&r.unit==='G'&&r.findings.some(f=>f.rule==='P-SHAPE'&&f.location.pointer==='/definitions/0/payload/extra')));
  assert.ok(!last(x).findings.some(f=>f.details==='Agent does not expose invocation Interface'));
  assert.ok(!last(x).checks.some(c=>c.rule==='G-DATA'&&c.state==='blocked'));
});
