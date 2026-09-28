import { createHash } from 'node:crypto';
import { parse, pointer } from '../../../../tooling/readers/javascript/json.mjs';
import * as S from './shape.mjs';
import { checkFlow } from './flow.mjs';
import { checkConfigurations } from './configuration.mjs';
export const EDITION = 'agsdl-exp-0017-c1';
export const PROCESSOR = Object.freeze({ identity: 'agsdl-experimental/javascript-kiss-reader', version: '0017-c1' });
export const editionKey = v => JSON.stringify([v.identity, v.version]);
// Semantic identity projection: extra fields still fail SHAPE at their source.
export const readableEdition = v => S.object(v) && typeof v.identity === 'string' && v.identity.length > 0 && typeof v.version === 'string' && v.version.length > 0;
export const readableRef = v => S.object(v) && S.id(v.ref);
export const fieldLocation = (v, p, k) => S.has(v, k) ? pointer(p, k) : p;
export const duplicate = xs => new Set(xs).size !== xs.length;
export const mapReadable = v => S.object(v) && Object.keys(v).every(S.id);

export function validate(bytes) {
  if (!(bytes instanceof Uint8Array)) throw new TypeError('validate expects a Buffer or Uint8Array');
  const source = Buffer.from(bytes);
  const units = ['syntax', 'core', 'flow', 'configuration', 'compatibility', 'external'];
  const subjects = ['', '', '/graphs', '/configurations', '/selected', '/extensions'];
  const results = Object.fromEntries(units.map((unit, i) => [unit, { unit, phase: 'local', subject: subjects[i], presence: unit === 'syntax' ? 'present' : 'undetermined', outcome: 'pass', diagnostics: [], incomplete: [] }]));
  const d = (u, code, location, outcome = 'fail') => {
    const a = results[u].diagnostics;
    if (!a.some(x => x.code === code && x.location === location && x.outcome === outcome)) a.push({ code, location, outcome });
  };
  const gap = (u, code, location, cause = 'shape') => {
    const a = results[u].incomplete;
    let g = a.find(x => x.code === code && x.location === location);
    if (!g) { g = { code, location, causes: [] }; a.push(g); }
    if (!g.causes.includes(cause)) g.causes.push(cause);
  };
  const gaps = (u, codes, p, cause = 'shape') => codes.forEach(c => gap(u, c, p, cause));
  const finish = () => {
    for (const r of Object.values(results)) {
      const outcomes = r.diagnostics.map(x => x.outcome).concat(r.incomplete.map(g => g.causes.includes('unsupported') ? 'unsupported' : 'inconclusive'));
      r.outcome = ['fail', 'unsupported', 'inconclusive'].find(o => outcomes.includes(o)) ?? (r.presence === 'absent' ? 'not-applicable' : 'pass');
    }
    return { edition: EDITION, processor: { ...PROCESSOR }, operation: 'validate', input: { id: 'primary', sha256: createHash('sha256').update(source).digest('hex') }, results: Object.values(results) };
  };
  const parsed = parse(source);
  if (parsed.error) { d('syntax', 'SYNTAX', ''); units.slice(1).forEach(u => gap(u, 'CHECKS', '')); return finish(); }
  const root = parsed.tree;
  if (!S.object(root)) { d('core', 'SHAPE', ''); units.slice(1).forEach(u => gap(u, 'CHECKS', '')); return finish(); }
  results.core.presence = 'present';
  for (const [u, present] of [['flow', S.has(root, 'graphs')], ['configuration', S.has(root, 'configurations') || S.has(root, 'selected')], ['compatibility', S.has(root, 'selected')], ['external', S.has(root, 'extensions')]]) results[u].presence = present ? 'present' : 'absent';
  S.shape(root, S.documentCore, '', p => d('core', 'SHAPE', p));

  const index = new Map();
  let complete = true;
  for (const name of Object.keys(S.catalogs)) {
    if (!S.has(root, name) && name !== 'agents') continue;
    const cat = root[name], p = fieldLocation(root, '', name);
    if (!S.object(cat)) { complete = false; gap('core', 'ID', p); continue; }
    for (const [key, value] of Object.entries(cat)) {
      const q = pointer(p, key);
      if (!S.id(key)) { complete = false; gap('core', 'ID', q); continue; }
      const entries = index.get(key) ?? [];
      entries.push({ value, p: q, kind: name }); index.set(key, entries);
    }
  }
  for (const entries of index.values()) if (entries.length > 1) entries.forEach(x => d('core', 'ID', x.p));
  const lookup = (v, kind) => {
    if (!readableRef(v)) return { cause: 'shape' };
    if (!complete) return { cause: 'reference' };
    const entries = index.get(v.ref) ?? [];
    if (entries.length > 1) return { cause: 'reference' };
    if (!entries.length || entries[0].kind !== kind) return { cause: 'reference', missing: true };
    return entries[0];
  };
  const refCheck = (u, v, p, kind) => {
    const r = lookup(v, kind);
    if (r.missing) d(u, 'REF', p);
    else if (r.cause) gap(u, 'REF', p, r.cause);
    return r;
  };
  const refField = (u, v, p, k, kind) => refCheck(u, S.object(v) ? v[k] : undefined, fieldLocation(v, p, k), kind);
  const choice = (v, p, kind) => {
    if (!S.object(v) || S.has(v, 'ref') === S.has(v, 'value')) return { cause: 'shape' };
    return S.has(v, 'ref') ? lookup(v, kind) : { value: v.value, p: pointer(p, 'value'), kind };
  };
  const choiceCheck = (v, p, kind) => {
    if (!S.object(v) || S.has(v, 'ref') === S.has(v, 'value')) gap('core', 'REF', p);
    else if (S.has(v, 'ref')) refCheck('core', v, p, kind);
  };
  const unique = (u, v, p, type, key = x => x, code = 'UNIQUE') => {
    if (!S.shape(v, S.array(type))) { gap(u, code, p); return; }
    if (duplicate(v.map(key))) d(u, code, p);
  };
  const slotIds = (a, p, report = false) => {
    const q = fieldLocation(a, p, 'instructions'), slots = S.object(a) ? a.instructions : undefined;
    if (!Array.isArray(slots)) { if (report) gap('core', 'SLOT-ID', q); return { causes: ['shape'] }; }
    const ids = slots.filter(x => S.object(x) && S.id(x.id)).map(x => x.id);
    const dup = duplicate(ids), bad = ids.length !== slots.length;
    if (report) { if (bad) gap('core', 'SLOT-ID', q); if (dup) d('core', 'SLOT-ID', q); }
    return { ids, causes: [...(bad ? ['shape'] : []), ...(dup ? ['reference'] : [])] };
  };
  const coreAgent = (a, p) => {
    if (!S.object(a)) { gaps('core', ['REF', 'SLOT-ID', 'UNIQUE'], p); return; }
    slotIds(a, p, true);
    if (!Array.isArray(a.instructions)) gap('core', 'REF', fieldLocation(a, p, 'instructions'));
    else a.instructions.forEach((s, i) => {
      const q = pointer(pointer(p, 'instructions'), i);
      choiceCheck(S.object(s) ? s.content : undefined, fieldLocation(s, q, 'content'), 'instructions');
    });
    choiceCheck(a.interface, fieldLocation(a, p, 'interface'), 'interfaces');
    if (S.has(a, 'tools')) {
      const q = pointer(p, 'tools'); unique('core', a.tools, q, S.ref, x => x.ref);
      if (!Array.isArray(a.tools)) gap('core', 'REF', q);
      else a.tools.forEach((r, i) => refCheck('core', r, pointer(q, i), 'tools'));
    }
  };
  if (!S.object(root.agents)) gaps('core', ['REF', 'SLOT-ID', 'UNIQUE'], fieldLocation(root, '', 'agents'));
  else Object.entries(root.agents).forEach(([k, a]) => coreAgent(a, pointer('/agents', k)));
  if (S.has(root, 'tools')) {
    if (!S.object(root.tools)) gap('core', 'UNIQUE', '/tools');
    else for (const [k, t] of Object.entries(root.tools)) {
      const p = pointer('/tools', k);
      if (!S.object(t)) gap('core', 'UNIQUE', p);
      else { unique('core', t.requires, fieldLocation(t, p, 'requires'), S.edition, editionKey); unique('core', t.failures, fieldLocation(t, p, 'failures'), x => typeof x === 'string' && x.length > 0); }
    }
  }
  if (root.edition !== EDITION) { units.slice(2).forEach(u => gap(u, 'CHECKS', '')); return finish(); }
  const ctx = { root, d, gap, gaps, lookup, refCheck, refField, choice, unique, slotIds };
  checkFlow(ctx);
  checkConfigurations(ctx);
  if (S.has(root, 'extensions')) {
    S.shape(root.extensions, S.array(S.extension), '/extensions', p => d('external', 'SHAPE', p));
    if (!Array.isArray(root.extensions)) gaps('external', ['UNIQUE', 'REQUIRED'], '/extensions');
    else {
      const ids = [];
      root.extensions.forEach((e, i) => {
        const p = pointer('/extensions', i), goodEdition = S.object(e) && readableEdition(e.edition);
        if (goodEdition) ids.push(editionKey(e.edition)); else gap('external', 'UNIQUE', '/extensions');
        if (!goodEdition || !['annotation', 'required'].includes(e.use)) gap('external', 'REQUIRED', p);
        else if (e.use === 'required') { d('external', 'REQUIRED', p, 'unsupported'); gap('external', 'REQUIRED', p, 'unsupported'); }
      });
      if (duplicate(ids)) d('external', 'UNIQUE', '/extensions');
    }
  }
  return finish();
}
