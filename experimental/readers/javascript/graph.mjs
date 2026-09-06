import * as S from './shape.mjs';
import { pointer } from './json.mjs';
import { Result, context, validateD, rows, key, equal, ext, declaration, modes, lookup, cyclic, canonical, hash } from './core.mjs';
const RULES=['P-SHAPE','X-MODE','G-TARGET','G-PATH','G-DATA','G-APPROVAL'];
export function validateG(primary,operation,inventory) {
  const resolve=operation==='resolveG', phase=resolve?'resolved-graph':'unresolved-document';
  const r=new Result(primary.id,'G',phase,[...RULES,...(resolve?['G-RESOLVE']:[])]);r.boundary();r.prerequisites=[primary.d];if(primary.d.verdict!=='pass')r.mark('P-PREREQUISITE','blocked','');
  const selections=[],contexts=[],annexResults=new Map(),byId=new Map(),selected=new Set(),required=new Set();
  const state=(ctx,p)=>inventory.states.push({input:ctx.id,pointer:p,state:'unchecked',detail:'External target content unchecked'});
  function refs(step){if(!S.object(step))return [];if(step.kind==='invoke')return ['agent','interface','action','principal'].map(k=>[k,step[k]]).concat((Array.isArray(step.resources)?step.resources:[]).map((x,i)=>[`resources/${i}`,x]));if(step.kind==='approval')return [['requirement',step.requirement]];return [];}
  if(resolve){
    if(Array.isArray(primary.tree?.dependencies)&&primary.tree.dependencies.every(d=>S.valid(S.Dependency.fields.requiredFor,d?.requiredFor)))r.mark('G-RESOLVE');
    else r.mark('G-RESOLVE','blocked',S.has(primary.tree,'dependencies')?'/dependencies':'');
    for(const x of rows(primary,'dependencies',S.Dependency))if(Array.isArray(x.v?.requiredFor)&&x.v.requiredFor.includes('resolveG')&&typeof x.v.id==='string')required.add(x.v.id);
    if(Array.isArray(primary.tree?.graphs))for(const g of primary.tree.graphs)if(Array.isArray(g?.steps))for(const s of g.steps)for(const [,ref]of refs(s))if(S.valid(S.Ref,ref)&&ext(ref))required.add(ref.dependency);
    for(const id of [...required].sort())loadAnnex(id);
  }
  function loadAnnex(id){
    if(byId.has(id))return byId.get(id);
    const dep=primary.deps.get(id);
    if(dep?.length!==1)return null;
    const {v:d,p}=dep[0];r.mark('G-RESOLVE');
    if(!S.valid(S.Dependency.fields.status,d.status)||!S.valid(S.Key,d.rootKey)){r.mark('G-RESOLVE','blocked',p);return null;}
    if(d.status!=='included'||!Object.hasOwn(primary.annexes,id)){r.find('G-RESOLVE',p,'Required annex bytes missing');return null;}
    if(!S.valid(S.Dependency.fields.sha256,d.sha256))r.mark('G-RESOLVE','blocked',p);
    else if(d.sha256===null)r.find('G-RESOLVE',p,'Required annex integrity unknown','inconclusive');
    else if(hash(primary.annexes[id])!==d.sha256)r.find('G-RESOLVE',p,'Required annex hash mismatch');
    const ctx=context(`annex/${id}`,primary.annexes[id]);validateD(ctx);contexts.push(ctx);byId.set(id,ctx);r.prerequisites.push(ctx.d);
    if(ctx.error||!S.valid(S.Root,ctx.tree?.root)||ctx.tree.contract!=='proposal-0012-candidate-2'||!equal(ctx.tree.root.key,d.rootKey))r.find('G-RESOLVE',p,'Invalid annex content or root key');
    if(ctx.d.verdict!=='pass')r.mark('P-PREREQUISITE','blocked','');
    return ctx;
  }

  modes(primary,r,'validateG');
  function annexResult(ctx){if(ctx===primary)return r;if(!annexResults.has(ctx.id)){const a=new Result(ctx.id,'G',phase,['P-SHAPE','G-TARGET']);a.boundary();a.prerequisites=[ctx.d];annexResults.set(ctx.id,a);}return annexResults.get(ctx.id);}
  const selectedCache=new Map();
  function target(ctx,ref,kind,consumer,p,rule='G-TARGET') {
    const owner=annexResult(ctx);
    const subject=p.includes('/payload/')?p.split('/payload/')[0]+'/payload':ctx===primary?consumer:p.replace(/\/target$/, '');
    if(!S.valid(S.Ref,ref)){owner.mark(rule,'blocked',consumer);return null;}
    owner.mark(rule);
    if(!declaration(ctx,ref,kind,owner,rule,subject))return null;
    let dst=ctx,k=ref;
    if(ext(ref)) {
      if(!resolve){state(ctx,p);r.mark(rule,'excluded',consumer);return {external:true};}
      if(ctx!==primary){state(ctx,p);r.find('G-RESOLVE',consumer,'Selected transitive external reference','unsupported');owner.mark(rule,'excluded',p);return {external:true};}
      r.mark('G-RESOLVE');dst=loadAnnex(ref.dependency);k=ref.key;
      if(!dst){r.mark('G-RESOLVE','blocked',consumer);r.mark('G-TARGET','blocked',consumer);return null;}
      if(dst.error||!S.valid(S.Root,dst.tree?.root)){r.mark('G-TARGET','blocked',consumer);return null;}
      const exported=Array.isArray(dst.tree.exports)&&dst.tree.exports.some(x=>S.valid(S.Key,x)&&equal(x,k));
      const found=lookup(dst,k);
      if(dst.defs.get(key(k))?.length>1){r.mark('G-RESOLVE','blocked',consumer);return null;}
      if(!Array.isArray(dst.tree.exports)){r.mark('G-RESOLVE','blocked',consumer);return null;}
      if(!exported||!found||found.root){r.find('G-RESOLVE',consumer,'External target missing or unexported');return null;}
      if(!S.valid(S.Kind,found.v.kind)){r.mark('G-RESOLVE','blocked',consumer);r.mark('G-TARGET','blocked',consumer);return null;}
      if(found.v.kind!==kind){r.find('G-RESOLVE',consumer,'External target has wrong kind');return null;}
    }
    const found=lookup(dst,k);if(!found)return null;
    const colliding=resolve&&[primary,...contexts].filter(c=>c.defs.has(key(k))).length>1;
    if(colliding){r.find('G-RESOLVE',consumer,'Selected key occurs in multiple document boundaries');r.mark('G-TARGET','blocked',consumer);}
    if(resolve)selections.push({k,consumer});
    return {...found,ctx:dst,colliding};
  }
  function payload(found,type,consumer){
    if(!found||found.external)return null;
    const p=`${found.p}/payload`, token=`${found.ctx.id}:${p}`;selected.add(token);
    if(!selectedCache.has(token)){const ar=annexResult(found.ctx);selectedCache.set(token,ar.shape(type,found.v.payload,p));}
    if(!S.object(found.v.payload)){r.mark('G-TARGET','blocked',consumer);if(type===S.Interface)r.mark('G-DATA','blocked',consumer);return null;}
    return found.v.payload;
  }
  function same(a,b){if(a?.colliding||b?.colliding)return undefined;return a&&b&&!a.external&&!b.external&&equal(a.v.key,b.v.key);}
  function matchRefs(ownerCtx,a,b,kind,consumer,p){const ta=target(ownerCtx,a,kind,consumer,p);if(!ta||!b)return null;if(ta.external||b.external)return undefined;return same(ta,b);}
  function invokeTargets(s,p){
    const agent=target(primary,s.agent,'Agent',p,`${p}/agent`), face=target(primary,s.interface,'Interface',p,`${p}/interface`),action=target(primary,s.action,'Action',p,`${p}/action`),principal=target(primary,s.principal,'Principal',p,`${p}/principal`);
    const resources=new Set();for(const [i,v]of (Array.isArray(s.resources)?s.resources:[]).entries()){if(!S.valid(S.Ref,v)){r.mark('G-TARGET','blocked',p);continue;}target(primary,v,'Resource',p,`${p}/resources/${i}`);const sig=canonical(v);if(resources.has(sig))r.find('G-TARGET',p,'Duplicate Resource Ref');resources.add(sig);}
    if(!face)r.mark('G-DATA','blocked',p);
    if(!face||!agent||!action||!principal)r.mark('G-TARGET','blocked',p);
    if(!Array.isArray(s.resources))r.mark('G-TARGET','blocked',p);
    const ip=payload(face,S.Interface,p);
    if(face?.external)r.mark('G-DATA','excluded',p);
    if(ip){const ar=annexResult(face.ctx);const a=target(face.ctx,ip.action,'Action',p,`${face.p}/payload/action`);if(a&&!a.external&&action&&!action.external&&same(a,action)===false)r.find('G-TARGET',p,'Interface action differs from invocation');
      for(const field of ['inputs','outputs'])if(S.valid(S.Ports,ip[field])&&S.valid(S.Ports,s[field])){r.mark('G-DATA');if(!equal(ip[field],s[field]))r.find('G-DATA',p,'Interface port maps differ from invocation');}else r.mark('G-DATA','blocked',p);ar.mark('G-TARGET');}
    if(agent&&!agent.external){
      const usable=x=>S.valid(S.Relation,{source:x.v?.source,relation:x.v?.relation,target:x.v?.target,expectedKind:x.v?.expectedKind});
      const rs=rows(agent.ctx,'relations',S.Relation).filter(x=>usable(x)&&equal(x.v.source,agent.v.key));
      if(!Array.isArray(agent.ctx.tree.relations)||rows(agent.ctx,'relations',S.Relation).some(x=>(!S.valid(S.Key,x.v?.source)||equal(x.v.source,agent.v.key))&&!usable(x))){r.mark('G-TARGET','blocked',p);return;}
      const exposes=rs.filter(x=>x.v.relation==='exposes');let matched=false,unknown=false;
      for(const x of exposes){const m=matchRefs(agent.ctx,x.v.target,face,'Interface',p,`${x.p}/target`);if(m===true)matched=true;if(m===undefined)unknown=true;}
      if(!matched&&!unknown&&face&&!face.external)r.find('G-TARGET',p,'Agent does not expose invocation Interface');
      const acts=rs.filter(x=>x.v.relation==='actsAs');if(acts.length!==1)r.find('G-TARGET',p,'Agent principal relation is not unique');else{const m=matchRefs(agent.ctx,acts[0].v.target,principal,'Principal',p,`${acts[0].p}/target`);if(m===false)r.find('G-TARGET',p,'Invocation principal differs from Agent');}
    }
  }
  if(primary.error||!S.object(primary.tree)){for(const rule of RULES.filter(x=>x!=='X-MODE'))r.mark(rule,'blocked','');if(resolve)r.mark('G-RESOLVE','blocked','');return finish();}
  if(!S.has(primary.tree,'graphs')){for(const rule of RULES.filter(x=>x!=='X-MODE'))r.mark(rule,'excluded','/graphs');if(resolve)r.mark('G-RESOLVE','excluded','/graphs');return finish();}
  const graphs=primary.tree.graphs;r.shape(S.List(S.Graph),graphs,'/graphs');
  if(!Array.isArray(graphs)){for(const rule of ['G-TARGET','G-PATH','G-DATA','G-APPROVAL',...(resolve?['G-RESOLVE']:[])])r.mark(rule,'blocked','/graphs');return finish();}
  const graphDefs=new Set();
  for(const [gi,g]of graphs.entries()){
    const gp=`/graphs/${gi}`;
    if(!S.object(g)){for(const rule of ['G-TARGET','G-PATH','G-DATA','G-APPROVAL'])r.mark(rule,'blocked',gp);continue;}
    if(S.valid(S.Key,g.definition)){r.mark('G-TARGET');declaration(primary,g.definition,'ControlFlow',r,'G-TARGET',gp);if(graphDefs.has(key(g.definition)))r.find('G-TARGET',gp,'Repeated graph ControlFlow');graphDefs.add(key(g.definition));}else r.mark('G-TARGET','blocked',gp);
    if(!Array.isArray(g.steps)){for(const rule of ['G-TARGET','G-PATH','G-DATA','G-APPROVAL'])r.mark(rule,'blocked',gp);continue;}
    const steps=g.steps.map((v,i)=>({v,p:`${gp}/steps/${i}`,ok:S.valid(S.Step,v)}));
    const stepMap=new Map(), edges=[];let pathBad=false,pathBlocked=false;
    const idCounts=new Map();
    for(const x of steps){
      const id=x.v?.id;
      if(typeof id==='string'&&id.length){idCounts.set(id,(idCounts.get(id)||0)+1);if(stepMap.has(id))pathBad=true;stepMap.set(id,x);}
      else pathBlocked=true;
      const s=x.v;
      const labels=s?.kind==='invoke'?['success','failure']:s?.kind==='condition'?['true','false','failure']:s?.kind==='approval'?['approved','denied','failure']:s?.kind==='end'?[]:null;
      if(!labels){pathBlocked=true;continue;}
      for(const label of labels)if(typeof s[label]==='string'&&s[label].length&&typeof id==='string')edges.push({from:id,to:s[label],label});else pathBlocked=true;
    }
    const reachable=(from,skip)=>{const seen=new Set(),stack=[from];while(stack.length){const a=stack.pop();if(seen.has(a))continue;seen.add(a);for(const e of edges)if(e.from===a&&(!skip||!skip(e)))stack.push(e.to);}return seen;};
    if(typeof g.entry!=='string'){pathBlocked=true;}else if(!stepMap.has(g.entry))pathBad=true;
    if(edges.some(e=>!stepMap.has(e.to))||cyclic(edges.map(e=>[e.from,e.to])))pathBad=true;
    if(!pathBlocked&&typeof g.entry==='string'&&steps.filter(x=>typeof x.v?.id==='string').some(x=>!reachable(g.entry).has(x.v.id)))pathBad=true;
    if(!steps.length)pathBlocked=true;
    if(pathBad)r.find('G-PATH',gp,'Invalid step identity, entry, edge, cycle, reachability or terminal path');
    if(pathBlocked)r.mark('G-PATH','blocked',gp);else r.mark('G-PATH');
    const pathOK=!pathBad&&!pathBlocked;
    function binding(b,type,consumer,consumerId){
      if(!S.valid(S.Binding,b)){r.mark('G-DATA','blocked',consumer);return;}
      r.mark('G-DATA');
      if(S.has(b,'input')){if(!S.valid(S.Ports,g.inputs))r.mark('G-DATA','blocked',consumer);else if(!Object.hasOwn(g.inputs,b.input)||g.inputs[b.input]!==type)r.find('G-DATA',consumer,'Graph input binding missing or wrong type');}
      else {const producer=stepMap.get(b.step);if(idCounts.get(b.step)>1){r.mark('G-DATA','blocked',consumer);return;}if(producer&&!['invoke','condition','approval','end'].includes(producer.v?.kind)){r.mark('G-DATA','blocked',consumer);return;}if(producer?.v.kind==='invoke'&&!S.valid(S.Ports,producer.v.outputs)){r.mark('G-DATA','blocked',consumer);return;}if(!producer||producer.v.kind!=='invoke'||!Object.hasOwn(producer.v.outputs,b.port)||producer.v.outputs[b.port]!==type)r.find('G-DATA',consumer,'Step output binding missing or wrong type');
        if(!pathOK)r.mark('G-DATA','blocked',consumer);else if(reachable(g.entry,e=>e.from===b.step&&e.label==='success').has(consumerId))r.find('G-DATA',consumer,'Producer success edge does not dominate consumer');}
    }
    function bindings(s,consumer,consumerId){if(S.valid(S.Ports,s.inputs)&&S.object(s.bindings)){r.mark('G-DATA');if(!equal(Object.keys(s.inputs).sort(),Object.keys(s.bindings).sort()))r.find('G-DATA',consumer,'Invocation binding names differ from inputs');for(const [name,b]of Object.entries(s.bindings))if(Object.hasOwn(s.inputs,name))binding(b,s.inputs[name],consumer,consumerId);}else r.mark('G-DATA','blocked',consumer);binding(s.context,'json',consumer,consumerId);}
    for(const x of steps){if(!S.object(x.v)||!['invoke','condition','approval','end'].includes(x.v.kind)){for(const rule of ['G-TARGET','G-DATA','G-APPROVAL'])r.mark(rule,'blocked',x.p);continue;}const s=x.v,p=x.p;
      if(s.kind==='invoke'){invokeTargets(s,p);bindings(s,p,s.id);}
      if(s.kind==='condition')binding(s.test,'boolean',p,s.id);
      if(s.kind==='end'&&s.outcome==='success'){if(!S.valid(S.Ports,g.outputs)||!S.object(s.bindings))r.mark('G-DATA','blocked',p);else{r.mark('G-DATA');if(!equal(Object.keys(g.outputs).sort(),Object.keys(s.bindings).sort()))r.find('G-DATA',p,'Terminal binding names differ from graph outputs');for(const [name,b]of Object.entries(s.bindings))if(Object.hasOwn(g.outputs,name))binding(b,g.outputs[name],p,s.id);}}
      if(s.kind==='approval'){
        const requirement=target(primary,s.requirement,'ApprovalRequirement',p,`${p}/requirement`),ap=payload(requirement,S.ApprovalRequirement,p);
        if(ap&&Array.isArray(ap.approvers)){const seen=new Set();for(const [i,ref]of ap.approvers.entries()){if(!S.valid(S.Ref,ref)){annexResult(requirement.ctx).mark('G-TARGET','blocked',`${requirement.p}/payload`);continue;}const loc=`${requirement.p}/payload`;target(requirement.ctx,ref,'Principal',p,`${loc}/approvers/${i}`);if(seen.has(canonical(ref)))annexResult(requirement.ctx).find('G-TARGET',loc,'Duplicate approver Ref');seen.add(canonical(ref));}}
        const approved=idCounts.get(s.approved)>1?null:stepMap.get(s.approved);
        if(idCounts.get(s.approved)>1){r.mark('G-APPROVAL','blocked',p);r.mark('G-DATA','blocked',p);continue;}
        if(!approved||approved.v.kind!=='invoke')r.find('G-APPROVAL',p,'Approved successor is not an invocation');
        if(!pathOK){r.mark('G-APPROVAL','blocked',p);r.mark('G-DATA','blocked',p);}else{
          r.mark('G-APPROVAL');const incoming=edges.filter(e=>e.to===s.approved);if(incoming.length!==1||incoming[0].from!==s.id||incoming[0].label!=='approved'||reachable(s.denied).has(s.approved)||reachable(s.failure).has(s.approved))r.find('G-APPROVAL',p,'Protected invocation has an alternate incoming or refusal path');
          if(approved?.v.kind==='invoke')bindings(approved.v,p,s.id);
        }
      }
    }
  }
  return finish();
  function finish(){for(const {k,consumer}of selections)if([primary,...contexts].filter(c=>c.defs.has(key(k))).length>1)r.find('G-RESOLVE',consumer,'Selected key occurs in multiple document boundaries');const ars=[...annexResults.values()].sort((a,b)=>a.input.localeCompare(b.input)).map(a=>a.finish());r.prerequisites.push(...ars);return {contexts,selected,results:[...contexts.sort((a,b)=>a.id<b.id?-1:a.id>b.id?1:0).map(c=>c.d),...ars,r.finish()]};}
}
