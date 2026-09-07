#!/usr/bin/env node
import { run, stringify } from './reader.mjs';
import { pathToFileURL } from 'node:url';
export function transport(request) {
  if(!request||Array.isArray(request)||typeof request!=='object')throw new TypeError('Request must be an object');
  const keys=Object.keys(request);if(keys.some(k=>!['operation','primary','annexes','losses'].includes(k))||!['operation','primary','annexes'].every(k=>Object.hasOwn(request,k)))throw new TypeError('Invalid request fields');
  const decode=s=>{if(typeof s!=='string'||! /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(s))throw new TypeError('Expected canonical base64');const b=Buffer.from(s,'base64');if(b.toString('base64')!==s)throw new TypeError('Expected canonical base64');return b;};
  if(!request.annexes||Array.isArray(request.annexes)||typeof request.annexes!=='object'||Object.keys(request.annexes).some(k=>!k))throw new TypeError('Invalid annex map');
  const annexes=Object.create(null);for(const [k,v]of Object.entries(request.annexes))annexes[k]=decode(v);
  const result=run({...request,primary:decode(request.primary),annexes});
  return {report:result.report,artifacts:Object.fromEntries(Object.entries(result.artifacts).map(([id,b])=>[id,b.toString('base64')]))};
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  try{const chunks=[];for await(const b of process.stdin)chunks.push(b);const request=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(Buffer.concat(chunks)));process.stdout.write(stringify(transport(request))+'\n');}
  catch(e){process.stderr.write(`Invalid host request: ${e.message}\n`);process.exitCode=2;}
}
