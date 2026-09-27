// Candidate grammar only. Lexical primitives come from the existing byte parser.
import { NumberToken, pointer, uint } from '../../../../tooling/readers/javascript/json.mjs';
export const object = v => v !== null && typeof v === 'object' && !Array.isArray(v) && !(v instanceof NumberToken);
export const has = (v, k) => object(v) && Object.hasOwn(v, k);
export const id = v => typeof v === 'string' && /^[A-Za-z][A-Za-z0-9_-]*$/.test(v);
const text = v => typeof v === 'string' && v.length > 0;
const one = (...values) => v => values.includes(v);
const array = (item, min = 0) => ({ array: item, min });
const map = (item, min = 0) => ({ map: item, min });
const record = fields => ({ fields });
const optional = type => ({ optional: type });
export const edition = record({ identity: text, version: text });
export const ref = record({ ref: id });
const json = () => true;
const hash = v => typeof v === 'string' && /^[a-f0-9]{64}$/.test(v);
const nullable = type => ({ nullable: type });
export const effects = one('none', 'external', 'unknown');
export const ports = map(one('string', 'boolean', 'json'));
export const binding = { branch: 'binding' };
export const instructions = record({ target: one('Agent'), at: one('before-invoke'), format: edition, body: text });
export const operation = record({ direction: one('inbound', 'outbound', 'bidirectional'), mode: one('request-response'), inputs: ports, outputs: ports, effects });
export const iface = record({ operations: map(operation, 1) });
export const instructionChoice = { choice: instructions };
export const interfaceChoice = { choice: iface };
export const slot = record({ id, content: instructionChoice });
export const agent = record({ instructions: array(slot, 1), interface: interfaceChoice, principal: optional(ref), tools: optional(array(ref)) });
export const tool = record({ inputs: ports, outputs: ports, effects, failures: array(text), requires: array(edition) });
export const claim = record({ capability: edition, status: one('supported', 'unsupported', 'unknown'), evidence: nullable(hash) });
export const scope = record({ action: text, resources: array(text, 1), context: binding });
const invoke = record({ id, kind: one('invoke'), agent: ref, operation: id, bindings: map(binding), success: id, failure: id, scope: optional(scope) });
const approval = record({ id, kind: one('approval'), call: id, approvers: array(ref, 1), validForMs: v => uint(v, true), timeoutMs: v => uint(v, true), approved: id, denied: id, failure: id });
const endSuccess = record({ id, kind: one('end'), outcome: one('success'), bindings: map(binding) });
const endOther = record({ id, kind: one('end'), outcome: one('failure', 'denied'), reason: text });
export const step = { branch: 'step' };
export const graph = record({ entry: id, inputs: ports, outputs: ports, steps: array(step, 1) });
export const application = record({ slot: id, adapter: edition, parameters: json });
export const toolBinding = record({ tool: ref, implementation: nullable(edition), parameters: json, claims: array(claim) });
export const agentBinding = record({ agent: ref, engine: nullable(edition), parameters: json, requires: array(edition), claims: array(claim), applications: array(application), tools: array(toolBinding), settings: optional(record({ format: edition, value: json })) });
export const configuration = record({ graph: ref, agents: array(agentBinding) });
export const extension = record({ edition, use: one('required', 'annotation'), payload: json });
export const catalogs = { principals: record({ description: text }), instructions, interfaces: iface, agents: agent, tools: tool, graphs: graph };
export const documentCore = record({ edition: one('agsdl-exp-0016-c1'), agents: map(agent), principals: optional(map(catalogs.principals)), instructions: optional(map(instructions)), interfaces: optional(map(iface)), tools: optional(map(tool)), graphs: optional(json), configurations: optional(json), selected: optional(json), extensions: optional(json), annotations: optional(json) });
export { array, map, nullable };

// Returns complete shape validity; callers can separately project readable fields.
export function shape(v, type, p = '', emit = () => {}) {
  let ok = true;
  const bad = q => { ok = false; emit(q); };
  const child = (x, t, q) => { if (!shape(x, t, q, emit)) ok = false; };
  if (typeof type === 'function') { if (!type(v)) bad(p); }
  else if (type.nullable) { if (v !== null) child(v, type.nullable, p); }
  else if (type.array) {
    if (!Array.isArray(v)) bad(p);
    else { if (v.length < type.min) bad(p); v.forEach((x, i) => child(x, type.array, pointer(p, i))); }
  } else if (type.map) {
    if (!object(v)) bad(p);
    else { if (Object.keys(v).length < type.min) bad(p); for (const [k, x] of Object.entries(v)) { if (!id(k)) bad(pointer(p, k)); child(x, type.map, pointer(p, k)); } }
  } else if (type.choice) {
    if (!object(v) || has(v, 'ref') === has(v, 'value')) bad(p);
    else child(v, has(v, 'ref') ? ref : record({ value: type.choice }), p);
  } else if (type.branch === 'binding') {
    if (!object(v) || has(v, 'input') === has(v, 'step')) bad(p);
    else child(v, has(v, 'input') ? record({ input: id }) : record({ step: id, port: id }), p);
  } else if (type.branch === 'step') {
    if (!object(v)) bad(p);
    else if (!['invoke', 'approval', 'end'].includes(v.kind)) { bad(p); if (!id(v.id)) bad(has(v, 'id') ? pointer(p, 'id') : p); }
    else if (v.kind === 'end' && !['success', 'failure', 'denied'].includes(v.outcome)) { bad(p); if (!id(v.id)) bad(has(v, 'id') ? pointer(p, 'id') : p); }
    else child(v, v.kind === 'invoke' ? invoke : v.kind === 'approval' ? approval : v.outcome === 'success' ? endSuccess : endOther, p);
  } else {
    if (!object(v)) bad(p);
    else {
      for (const k of Object.keys(v)) if (!Object.hasOwn(type.fields, k)) bad(pointer(p, k));
      for (const [k, t] of Object.entries(type.fields)) {
        if (!has(v, k)) { if (!t.optional) bad(p); }
        else child(v[k], t.optional ?? t, pointer(p, k));
      }
    }
  }
  return ok;
}
