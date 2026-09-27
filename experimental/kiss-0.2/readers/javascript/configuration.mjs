import { pointer } from '../../../../tooling/readers/javascript/json.mjs';
import * as S from './shape.mjs';
import { duplicate, editionKey, fieldLocation, mapReadable, readableRef } from './reader.mjs';

export function checkConfigurations(c) {
  const { root, d, gap, gaps, lookup, refCheck, refField, choice, unique, slotIds } = c;
  const selectedPresent = S.has(root, 'selected');
  let selected;
  if (selectedPresent) {
    S.shape(root.selected, S.id, '/selected', p => d('configuration', 'SHAPE', p));
    if (!S.id(root.selected)) {
      gap('configuration', 'SELECTION', '/selected'); gap('compatibility', 'CHECKS', '/selected');
    } else if (S.has(root, 'configurations') && !mapReadable(root.configurations)) {
      gap('configuration', 'SELECTION', '/selected'); gap('compatibility', 'CHECKS', '/selected');
    } else if (!S.has(root.configurations, root.selected)) {
      d('configuration', 'SELECTION', '/selected'); gap('compatibility', 'CHECKS', '/selected', 'reference');
    } else selected = root.selected;
  }
  if (!S.has(root, 'configurations')) return;
  S.shape(root.configurations, S.map(S.configuration), '/configurations', p => d('configuration', 'SHAPE', p));
  if (!S.object(root.configurations)) { gaps('configuration', ['REF', 'ASSIGN', 'CONTENT', 'TOOLS', 'UNIQUE'], '/configurations'); return; }

  function identityCounts(items, field) {
    const counts = new Map();
    if (Array.isArray(items)) for (const x of items) if (S.object(x) && readableRef(x[field])) counts.set(x[field].ref, (counts.get(x[field].ref) ?? 0) + 1);
    return counts;
  }
  const compareRefs = (wanted, got) => !duplicate(got) && wanted.size === new Set(got).size && got.every(x => wanted.has(x));
  function content(a, ap, b) {
    if (!S.object(a)) return { cause: 'shape' };
    const slots = slotIds(a, ap);
    if (slots.cause) return slots;
    if (!Array.isArray(b.applications) || b.applications.some(x => !S.object(x) || !S.id(x.slot))) return { cause: 'shape' };
    return { mismatch: JSON.stringify(slots.ids) !== JSON.stringify(b.applications.map(x => x.slot)) };
  }
  function tools(a, b) {
    if (!S.object(a)) return { cause: 'shape' };
    const needed = S.has(a, 'tools') ? a.tools : [];
    if (!Array.isArray(needed) || needed.some(x => !readableRef(x)) || !Array.isArray(b.tools) || b.tools.some(x => !S.object(x) || !readableRef(x.tool))) return { cause: 'shape' };
    return { mismatch: !compareRefs(new Set(needed.map(x => x.ref)), b.tools.map(x => x.tool.ref)) };
  }
  function coverage(code, result, p, isSelected) {
    if (result.cause) gap('configuration', code, p, result.cause);
    else if (result.mismatch) d('configuration', code, p);
    if (isSelected && (result.cause || result.mismatch)) gap('compatibility', code === 'CONTENT' ? 'ENGINE' : 'TOOL', p, result.cause ?? 'reference');
  }
  function assess(requirements, selection, claims, code, p) {
    if (selection !== null && !S.shape(selection, S.edition)) { gap('compatibility', code, p); return; }
    if (selection === null) { d('compatibility', code, p, 'inconclusive'); return; }
    const indexComplete = Array.isArray(claims) && claims.every(x => S.object(x) && S.shape(x.capability, S.edition));
    const required = new Map(requirements.map(e => [editionKey(e), e]));
    for (const key of required.keys()) {
      if (!indexComplete) { gap('compatibility', code, p); continue; }
      const matching = claims.filter(x => editionKey(x.capability) === key);
      if (matching.length > 1) { gap('compatibility', code, p, 'reference'); continue; }
      if (!matching.length) { d('compatibility', code, p, 'inconclusive'); continue; }
      const claim = matching[0];
      if (claim.status === 'unsupported') d('compatibility', code, p);
      else if (claim.status === 'unknown') d('compatibility', code, p, 'inconclusive');
      else if (claim.status !== 'supported' || !S.has(claim, 'evidence') || (claim.evidence !== null && !(typeof claim.evidence === 'string' && /^[a-f0-9]{64}$/.test(claim.evidence)))) gap('compatibility', code, p);
      else if (claim.evidence === null) d('compatibility', code, p, 'inconclusive');
    }
  }
  function requirementsArray(v, code, p) {
    const req = [];
    if (!Array.isArray(v)) gap('compatibility', code, p);
    else for (const x of v) { if (S.shape(x, S.edition)) req.push(x); else gap('compatibility', code, p); }
    return req;
  }
  function engine(b, p, ar) {
    const req = requirementsArray(b.requires, 'ENGINE', p);
    if (!Array.isArray(b.applications)) gap('compatibility', 'ENGINE', p);
    else for (const a of b.applications) {
      if (S.object(a) && S.shape(a.adapter, S.edition)) req.push(a.adapter);
      else gap('compatibility', 'ENGINE', p);
    }
    if (S.has(b, 'settings')) {
      if (S.object(b.settings) && S.shape(b.settings.format, S.edition)) req.push(b.settings.format);
      else gap('compatibility', 'ENGINE', p);
    }
    if (!S.object(ar.value) || !Array.isArray(ar.value.instructions)) gap('compatibility', 'ENGINE', p);
    else ar.value.instructions.forEach((s, i) => {
      const q = pointer(pointer(ar.p, 'instructions'), i);
      const r = choice(S.object(s) ? s.content : undefined, fieldLocation(s, q, 'content'), 'instructions');
      if (r.cause) gap('compatibility', 'ENGINE', p, r.cause);
      else if (!S.object(r.value) || !S.shape(r.value.format, S.edition)) gap('compatibility', 'ENGINE', p);
      else req.push(r.value.format);
    });
    assess(req, b.engine, b.claims, 'ENGINE', p);
  }
  function childTools(b, p, parentCause, isSelected) {
    const tp = fieldLocation(b, p, 'tools'), ts = S.object(b) ? b.tools : undefined;
    if (!Array.isArray(ts)) {
      gap('configuration', 'REF', tp); gap('configuration', 'UNIQUE', tp);
      if (isSelected) gap('compatibility', 'TOOL', tp, parentCause ?? 'shape');
      return;
    }
    const counts = identityCounts(ts, 'tool');
    ts.forEach((t, i) => {
      const q = pointer(tp, i);
      if (!S.object(t)) {
        gaps('configuration', ['REF', 'UNIQUE'], q);
        if (isSelected) gap('compatibility', 'TOOL', q, parentCause ?? 'shape');
        return;
      }
      const tr = refField('configuration', t, q, 'tool', 'tools');
      unique('configuration', t.claims, fieldLocation(t, q, 'claims'), S.claim, x => editionKey(x.capability));
      if (!isSelected) return;
      const cause = parentCause ?? (!readableRef(t.tool) ? 'shape' : counts.get(t.tool.ref) > 1 ? 'reference' : tr.cause);
      if (cause) { gap('compatibility', 'TOOL', q, cause); return; }
      if (!S.object(tr.value)) { gap('compatibility', 'TOOL', q); return; }
      const req = requirementsArray(tr.value.requires, 'TOOL', q);
      if (!S.effects(tr.value.effects)) gap('compatibility', 'TOOL', q);
      else if (tr.value.effects === 'unknown') d('compatibility', 'TOOL', q, 'inconclusive');
      assess(req, t.implementation, t.claims, 'TOOL', q);
    });
  }
  for (const [key, cfg] of Object.entries(root.configurations)) {
    const p = pointer('/configurations', key), isSelected = key === selected;
    if (!S.object(cfg)) {
      gaps('configuration', ['REF', 'ASSIGN', 'CONTENT', 'TOOLS', 'UNIQUE'], p);
      if (isSelected) gaps('compatibility', ['ENGINE', 'TOOL'], p);
      continue;
    }
    const gr = refField('configuration', cfg, p, 'graph', 'graphs');
    let desired;
    if (gr.cause) gap('configuration', 'ASSIGN', p, gr.cause);
    else if (!S.object(gr.value) || !Array.isArray(gr.value.steps) || gr.value.steps.some(s => !S.object(s) || !['invoke', 'approval', 'end'].includes(s.kind) || (s.kind === 'invoke' && !readableRef(s.agent)))) gap('configuration', 'ASSIGN', p);
    else desired = new Set(gr.value.steps.filter(s => s.kind === 'invoke').map(s => s.agent.ref));
    const bp = fieldLocation(cfg, p, 'agents');
    if (!Array.isArray(cfg.agents)) {
      gap('configuration', 'ASSIGN', p);
      gaps('configuration', ['REF', 'CONTENT', 'TOOLS', 'UNIQUE'], bp);
      if (isSelected) gaps('compatibility', ['ENGINE', 'TOOL'], bp);
      continue;
    }
    const counts = identityCounts(cfg.agents, 'agent');
    if (cfg.agents.some(b => !S.object(b) || !readableRef(b.agent))) gap('configuration', 'ASSIGN', p);
    else if (desired && !compareRefs(desired, cfg.agents.map(b => b.agent.ref))) d('configuration', 'ASSIGN', p);
    cfg.agents.forEach((b, i) => {
      const q = pointer(bp, i);
      if (!S.object(b)) {
        gaps('configuration', ['REF', 'CONTENT', 'TOOLS', 'UNIQUE'], q);
        if (isSelected) gaps('compatibility', ['ENGINE', 'TOOL'], q);
        return;
      }
      const ar = refField('configuration', b, q, 'agent', 'agents');
      unique('configuration', b.requires, fieldLocation(b, q, 'requires'), S.edition, editionKey);
      unique('configuration', b.claims, fieldLocation(b, q, 'claims'), S.claim, x => editionKey(x.capability));
      const cause = !readableRef(b.agent) ? 'shape' : counts.get(b.agent.ref) > 1 ? 'reference' : ar.cause;
      if (cause) {
        gaps('configuration', ['CONTENT', 'TOOLS'], q, cause);
        if (isSelected) gaps('compatibility', ['ENGINE', 'TOOL'], q, cause);
      } else {
        coverage('CONTENT', content(ar.value, ar.p, b), q, isSelected);
        coverage('TOOLS', tools(ar.value, b), q, isSelected);
        if (isSelected) engine(b, q, ar);
      }
      childTools(b, q, cause, isSelected);
    });
  }
}
