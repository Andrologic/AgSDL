import * as S from './shape.mjs';
import { pointer, stringify } from './json.mjs';
import { contract, context, hash, Result, validateD, rows, key, edition, equal, ext, declaration, modes, lookup } from './core.mjs';
import { validateG } from './graph.mjs';
export { stringify } from './json.mjs';
export function run(request) {
  if(!S.object(request)||!['operation','primary','annexes'].every(k=>Object.hasOwn(request,k))||Object.keys(request).some(k=>!['operation','primary','annexes','losses'].includes(k)))throw new TypeError('Invalid request fields');
  const {operation,primary,annexes={},losses}=request;
  if(!(primary instanceof Uint8Array)||!S.object(annexes)||Object.entries(annexes).some(([k,v])=>!k||!(v instanceof Uint8Array)))throw new TypeError('Expected primary bytes and an annex byte map');
  if(losses!==undefined&&(!Array.isArray(losses)||losses.some(loss=>{
    if(!S.object(loss)||!equal(Object.keys(loss).sort(),['input','location','information','reason','permission'].sort()))return true;
    if(['input','information','reason'].some(k=>typeof loss[k]!=='string'||!loss[k])||loss.permission!==null)return true;
    const loc=loss.location;return !S.object(loc)||Object.keys(loc).length!==1||!(Object.hasOwn(loc,'pointer')?typeof loc.pointer==='string':Object.hasOwn(loc,'byte')&&Number.isSafeInteger(loc.byte)&&loc.byte>=0);
  })))throw new TypeError('Invalid prospective Loss record');
  if(!['inspect','validateD','validateG','resolveG','validateR','exchange','lossyExchange'].includes(operation))throw new TypeError('Unknown operation');
  if(losses!==undefined&&operation!=='lossyExchange')throw new TypeError('losses is only allowed for lossyExchange');
  const ctx=context('primary',primary,annexes), contexts=[ctx], inventory={tree:ctx.tree,states:[],opaque:[]};
  const report={contract,processor:{identity:'agsdl-experiment/javascript-reader',version:'0.1.0-candidate-2'},operation,inputs:[{id:'primary',sha256:hash(primary)},...Object.keys(annexes).sort().map(id=>({id:`annex/${id}`,sha256:hash(annexes[id])}))],results:[],inventory,losses:[],outputs:[]};
  const artifacts=Object.create(null); let selected=new Set();
  if(operation==='inspect') {const r=new Result('primary','inspect',null,['P-SYNTAX']);if(ctx.error)r.find('P-SYNTAX',ctx.error.byte,'Invalid UTF-8 JSON','fail',true);report.results.push(r.finish());}
  else if(operation==='exchange'||operation==='lossyExchange') {
    const r=new Result('primary','exchange',null,[operation==='exchange'?'E-PRESERVE':'E-LOSS']);
    if(operation==='lossyExchange'){
      r.find('E-LOSS','','Lossy exchange is refused');report.losses=losses?.length?losses:[{input:'primary',location:{pointer:''},information:'unspecified requested loss',reason:'This edition permits no lossy exchange',permission:null}];
    }else{
      if(S.valid(S.List(S.Dependency),ctx.tree?.dependencies)) {
        const ids=new Set(), roots=new Set();
        for(const [i,d]of ctx.tree.dependencies.entries()) {
          const supplied=Object.hasOwn(annexes,d.id), p=`/dependencies/${i}`;
          if(ids.has(d.id)||roots.has(key(d.rootKey))||new Set(d.requiredFor).size!==d.requiredFor.length||(d.status==='included')!==supplied)r.find('E-PRESERVE','','Dependency accounting refuses exchange');
          if(d.sha256!==null&&supplied&&hash(annexes[d.id])!==d.sha256)r.find('E-PRESERVE',p,'Hash mismatch');
          if(d.requiredFor.includes('exchange')) {if(!supplied||d.status!=='included')r.find('E-PRESERVE','','Required bytes missing');if(d.sha256===null)r.find('E-PRESERVE','','Required integrity unknown','inconclusive');}
          ids.add(d.id);roots.add(key(d.rootKey));
        }
        for(const id of Object.keys(annexes))if(!ids.has(id))r.find('E-PRESERVE','','Undeclared annex');
      }
      if(r.finish().verdict==='pass'){artifacts.primary=Buffer.from(primary);for(const id of Object.keys(annexes))artifacts[`annex/${id}`]=Buffer.from(annexes[id]);report.outputs=report.inputs.map(x=>({...x}));}
    }
    report.results.push(r.finish());
  }else{
    report.results.push(validateD(ctx));
    if(operation==='validateR')report.results.push(validateR(ctx,inventory));
    if(operation==='validateG'||operation==='resolveG') {
      const g=validateG(ctx,operation,inventory);contexts.push(...g.contexts);report.results.push(...g.results);selected=g.selected;
    }
  }
  for(const c of contexts) collect(c,operation,inventory,selected,c!==ctx);
  // A maximal slice contains every uninterpreted child; discard nested slices.
  inventory.opaque=inventory.opaque.filter((s,i,a)=>!a.some((t,j)=>j!==i&&t.input===s.input&&t.start<=s.start&&t.end>=s.end&&(t.start<s.start||t.end>s.end)));
  inventory.opaque=[...new Map(inventory.opaque.map(s=>[`${s.input}:${s.pointer}`,s])).values()];
  inventory.states=[...new Map(inventory.states.map(s=>[JSON.stringify(s),s])).values()];
  return {report,artifacts};
}
export function state(inv,ctx,p,s,detail=s){inv.states.push({input:ctx.id,pointer:p,state:s,detail});}
function collect(ctx,operation,inv,selected,annex=false) {
  const d=ctx.tree, exchange=['inspect','exchange','lossyExchange'].includes(operation);
  const slice=p=>{const span=ctx.spans.get(p);if(span)inv.opaque.push({input:ctx.id,pointer:p,...span});};
  if(exchange)state(inv,ctx,'/dependencies',ctx.error||!S.object(d)?'unchecked':!S.has(d,'dependencies')?'absent':S.valid(S.List(S.Dependency),d.dependencies)?'declared':'unchecked');
  if(ctx.error)return;
  if(!S.object(d)){slice('');return;}
  for(const k of ['graphs','runtime']){
    const interpreted=!annex&&((k==='graphs'&&['validateG','resolveG'].includes(operation))||(k==='runtime'&&operation==='validateR'));
    state(inv,ctx,`/${k}`,!S.has(d,k)?'absent':interpreted?'declared':'unchecked');if(S.has(d,k)&&!interpreted)slice(`/${k}`);
  }
  if(!exchange||S.valid(S.List(S.Dependency),d.dependencies))for(const x of rows(ctx,'dependencies',S.Dependency))if(x.ok&&x.v.sha256===null)state(inv,ctx,`${x.p}/sha256`,'unknown');
  if(exchange&&S.has(d,'dependencies')&&!S.valid(S.List(S.Dependency),d.dependencies))slice('/dependencies');
  for(const x of rows(ctx,'relations',S.Relation))if(x.ok&&ext(x.v.target))state(inv,ctx,`${x.p}/target`,'unchecked');
  for(const k of ['annotations','evidence'])if(S.has(d,k))slice(`/${k}`);
  if(S.object(d.root))for(const k of ['payload','annotations'])if(S.has(d.root,k))slice(`/root/${k}`);
  for(const [i,v]of (Array.isArray(d.definitions)?d.definitions:[]).entries())if(S.object(v))for(const k of ['payload','annotations','provenance'])if(S.has(v,k)&&!(k==='payload'&&selected.has(`${ctx.id}:/definitions/${i}/payload`)))slice(`/definitions/${i}/${k}`);
  for(const [i,v]of (Array.isArray(d.extensions)?d.extensions:[]).entries())if(S.has(v,'payload'))slice(`/extensions/${i}/payload`);
}
function validateR(ctx,inv) {
  const r=new Result(ctx.id,'R','unresolved-document',['P-SHAPE','X-MODE','R-REQUIREMENT','R-SELECTION']);r.boundary(true);r.prerequisites=[ctx.d];if(ctx.d.verdict!=='pass')r.mark('P-PREREQUISITE','blocked','');
  modes(ctx,r,'validateR');
  if(ctx.error||!S.object(ctx.tree)){for(const rule of ['P-SHAPE','R-REQUIREMENT','R-SELECTION'])r.mark(rule,'blocked','');return r.finish();}
  if(!S.has(ctx.tree,'runtime')){for(const rule of ['P-SHAPE','R-REQUIREMENT','R-SELECTION'])r.mark(rule,'excluded','/runtime');return r.finish();}
  const rt=ctx.tree.runtime;r.shape(S.Runtime,rt,'/runtime');
  if(!S.shell(S.Runtime,rt)||!Array.isArray(rt.requirements)){r.mark('R-REQUIREMENT','blocked','/runtime');r.mark('R-SELECTION','blocked','/runtime');return r.finish();}
  const ids=new Set(),pairs=new Set();
  for(const [i,v]of rt.requirements.entries()){
    const p=`/runtime/requirements/${i}`,idOK=typeof v?.id==='string'&&v.id.length,subjectOK=S.valid(S.Key,v?.subject),capOK=S.valid(S.Edition,v?.capability);
    if(idOK){r.mark('R-REQUIREMENT');if(ids.has(v.id))r.find('R-REQUIREMENT',p,'Duplicate requirement id');ids.add(v.id);}
    if(subjectOK){r.mark('R-REQUIREMENT');const found=ctx.defs.get(key(v.subject));if(found?.length>1)r.mark('R-REQUIREMENT','blocked',p);else if(!found||found[0].root)r.find('R-REQUIREMENT',p,'Requirement subject is not a local definition');}
    if(capOK&&subjectOK){r.mark('R-REQUIREMENT');const sig=edition(v.capability)+key(v.subject);if(pairs.has(sig))r.find('R-REQUIREMENT',p,'Duplicate capability/subject pair');pairs.add(sig);}
    if(!idOK||!subjectOK||!capOK)r.mark('R-REQUIREMENT','blocked',p);
  }
  state(inv,ctx,'/runtime/selection',S.has(rt,'selection')?'declared':'absent');
  if(!S.has(rt,'selection')){r.mark('R-SELECTION','excluded','/runtime/selection');return r.finish();}
  const sel=rt.selection;
  if(!S.object(sel)){r.mark('R-SELECTION','blocked','/runtime/selection');return r.finish();}
  const selectionOK=S.valid(S.Selection,sel);
  if(selectionOK){
    state(inv,ctx,'/runtime/selection/engine','unchecked');
    for(const k of ['model','provider','hosting'])state(inv,ctx,`/runtime/selection/${k}`,S.has(sel,k)?'declared':'absent');
  }
  if(S.has(sel,'hosting')){
    if(S.valid(S.Ref,sel.hosting)){r.mark('R-SELECTION');declaration(ctx,sel.hosting,'Environment',r,'R-SELECTION','/runtime/selection');if(selectionOK&&ext(sel.hosting))state(inv,ctx,'/runtime/selection/hosting','unchecked');}
    else r.mark('R-SELECTION','blocked','/runtime/selection');
  }
  const claims=new Set();
  if(!Array.isArray(sel.evidence))r.mark('R-SELECTION','blocked','/runtime/selection');
  else for(const [i,v]of sel.evidence.entries()){
    const p=`/runtime/selection/evidence/${i}`;
    if(typeof v?.requirement!=='string'||!v.requirement){r.mark('R-SELECTION','blocked',p);continue;}
    r.mark('R-SELECTION');
    if(!ids.has(v.requirement)||claims.has(v.requirement))r.find('R-SELECTION',p,'Evidence names unknown or repeated requirement');claims.add(v.requirement);
    if(selectionOK){state(inv,ctx,p,'unchecked');if(v.artifact===null)state(inv,ctx,`${p}/artifact`,'unknown');}
  }
  if(selectionOK)for(const id of ids)if(!claims.has(id))state(inv,ctx,'/runtime/selection/evidence','absent',id);
  return r.finish();
}
