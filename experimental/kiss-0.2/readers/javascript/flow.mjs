import { pointer } from '../../../../tooling/readers/javascript/json.mjs';
import * as S from './shape.mjs';
import { fieldLocation, mapReadable } from './reader.mjs';
const semantic = ['REF', 'STEP-ID', 'PATH', 'OPERATION', 'DATA', 'SCOPE', 'APPROVAL', 'APPROVAL-DATA', 'UNIQUE'];
const unknownStep = ['REF', 'OPERATION', 'DATA', 'SCOPE', 'APPROVAL', 'APPROVAL-DATA', 'UNIQUE'];
const kind = s => S.object(s) && ['invoke', 'approval', 'end'].includes(s.kind);
const successors = s => s.kind === 'invoke' ? ['success', 'failure'] : s.kind === 'approval' ? ['approved', 'denied', 'failure'] : [];

export function checkFlow(c) {
  const { root, d, gap, gaps, lookup, refField, choice, unique } = c;
  if (!S.has(root, 'graphs')) return;
  S.shape(root.graphs, S.map(S.graph), '/graphs', p => d('flow', 'SHAPE', p));
  if (!S.object(root.graphs)) { gaps('flow', semantic, '/graphs'); return; }
  for (const [name, g] of Object.entries(root.graphs)) {
    const gp = pointer('/graphs', name);
    if (!S.object(g) || !Array.isArray(g.steps)) { gaps('flow', semantic, S.object(g) ? fieldLocation(g, gp, 'steps') : gp); continue; }
    const sp = pointer(gp, 'steps'), steps = g.steps, catalog = new Map();
    let idsComplete = true;
    steps.forEach((s, i) => {
      if (!S.object(s) || !S.id(s.id)) { idsComplete = false; return; }
      const entries = catalog.get(s.id) ?? []; entries.push(i); catalog.set(s.id, entries);
    });
    if (!idsComplete) gap('flow', 'STEP-ID', sp);
    const duplicates = [...catalog.values()].some(xs => xs.length > 1);
    if (duplicates) d('flow', 'STEP-ID', sp);
    const stepLookup = id => {
      if (!S.id(id)) return { cause: 'shape' };
      if (!idsComplete) return { cause: 'reference' };
      const a = catalog.get(id) ?? [];
      if (a.length !== 1) return { cause: 'reference', missing: a.length === 0 };
      return { i: a[0], value: steps[a[0]] };
    };
    const projection = S.id(g.entry) && idsComplete && !duplicates && steps.every(s => kind(s) && (s.kind !== 'end' || ['success', 'failure', 'denied'].includes(s.outcome)) && successors(s).every(k => S.id(s[k])));
    const edges = [];
    if (projection) steps.forEach((s, i) => successors(s).forEach(label => edges.push({ from: i, to: stepLookup(s[label]).i, label })));
    function reachable(start, target, removed) {
      const seen = new Set(), pending = [start];
      while (pending.length) {
        const n = pending.pop(); if (n === undefined || seen.has(n)) continue;
        if (n === target) return true;
        seen.add(n);
        for (const e of edges) if (e.from === n && e !== removed) pending.push(e.to);
      }
      return target === undefined ? seen : false;
    }
    let pathOK = false;
    const entry = stepLookup(g.entry).i;
    if (!projection) gap('flow', 'PATH', gp);
    else {
      let bad = entry === undefined || edges.some(e => e.to === undefined);
      if (!bad) {
        const seen = reachable(entry), indegree = steps.map(() => 0);
        edges.forEach(e => indegree[e.to]++);
        const pending = indegree.flatMap((n, i) => n === 0 ? [i] : []);
        let visited = 0;
        while (pending.length) { const n = pending.pop(); visited++; for (const e of edges) if (e.from === n && --indegree[e.to] === 0) pending.push(e.to); }
        bad = seen.size !== steps.length || visited !== steps.length;
      }
      if (bad) d('flow', 'PATH', gp); else pathOK = true;
    }
    const operations = new Map();
    function selectedOperation(i) {
      if (operations.has(i)) return operations.get(i);
      const s = steps[i], p = pointer(sp, i);
      let result;
      if (!S.object(s) || s.kind !== 'invoke') result = { cause: 'reference' };
      else {
        const a = lookup(s.agent, 'agents');
        if (a.cause) result = { cause: a.cause };
        else if (!S.object(a.value)) result = { cause: 'shape' };
        else {
          const it = choice(a.value.interface, fieldLocation(a.value, a.p, 'interface'), 'interfaces');
          if (it.cause) result = { cause: it.cause };
          else if (!S.object(it.value) || !mapReadable(it.value.operations) || !S.id(s.operation)) result = { cause: 'shape' };
          else if (!S.has(it.value.operations, s.operation)) result = { cause: 'reference', invalid: true };
          else {
            const value = it.value.operations[s.operation];
            if (!S.object(value)) result = { cause: 'shape' };
            else result = { value, p: pointer(pointer(it.p, 'operations'), s.operation) };
          }
        }
      }
      operations.set(i, result);
      if (S.object(s) && s.kind === 'invoke') {
        if (result.invalid) d('flow', 'OPERATION', p);
        else if (result.cause) gap('flow', 'OPERATION', p, result.cause);
        else if (!['inbound', 'outbound', 'bidirectional'].includes(result.value.direction)) gap('flow', 'OPERATION', p);
        else if (result.value.direction === 'outbound') d('flow', 'OPERATION', p);
      }
      return result;
    }
    // Discover variant-specific subjects without inferring a malformed variant.
    steps.forEach((s, i) => {
      const p = pointer(sp, i);
      if (!kind(s)) { gaps('flow', unknownStep, p); return; }
      if (s.kind === 'invoke') {
        refField('flow', s, p, 'agent', 'agents'); selectedOperation(i);
        if (S.has(s, 'scope')) {
          const q = pointer(p, 'scope');
          const resources = S.object(s.scope) ? s.scope.resources : undefined;
          const resourceText = x => typeof x === 'string' && x.length > 0;
          if (!S.shape(resources, S.array(resourceText, 1))) gap('flow', 'UNIQUE', Array.isArray(resources) ? pointer(q, 'resources') : q);
          else unique('flow', resources, pointer(q, 'resources'), resourceText);
        }
      } else if (s.kind === 'end' && !['success', 'failure', 'denied'].includes(s.outcome)) gap('flow', 'DATA', p);
    });

    function data(callIndex, consumer, code, p, requireScope = false) {
      const s = steps[callIndex];
      const bad = cause => gap('flow', code, p, cause);
      let targets, targetUnavailable = false;
      if (s.kind === 'end') targets = g.outputs;
      else {
        const op = selectedOperation(callIndex);
        if (op.cause) { bad(op.cause); targetUnavailable = true; } else targets = op.value.inputs;
      }
      const targetKeysReady = mapReadable(targets);
      if (!targetUnavailable && !S.shape(targets, S.ports)) bad('shape');
      if (!S.shape(g.inputs, S.ports)) bad('shape');
      if (!pathOK) bad('path');
      if (!S.object(s.bindings)) bad('shape');
      else {
        if (!mapReadable(s.bindings)) bad('shape');
        if (targetKeysReady && mapReadable(s.bindings) && (Object.keys(s.bindings).length !== Object.keys(targets).length || Object.keys(s.bindings).some(k => !S.has(targets, k)))) d('flow', code, p);
        for (const [key, b] of Object.entries(s.bindings)) {
          if (!S.id(key)) continue;
          const target = S.has(targets, key) && portType(targets[key]) ? targets[key] : undefined;
          checkBinding(b, target);
        }
      }
      if (S.has(s, 'scope')) {
        if (!S.object(s.scope)) bad('shape');
        else checkBinding(s.scope.context, 'json');
      } else if (requireScope) bad('shape');
      function portType(value) { return ['string', 'boolean', 'json'].includes(value); }
      function sourcePort(ports, key) {
        if (!S.shape(ports, S.ports)) bad('shape');
        if (!S.object(ports)) return;
        if (S.has(ports, key)) return portType(ports[key]) ? ports[key] : undefined;
        if (mapReadable(ports)) d('flow', code, p);
      }
      function checkBinding(b, target) {
        if (!S.shape(b, S.binding)) { bad('shape'); return; }
        let actual;
        if (S.has(b, 'input')) {
          actual = sourcePort(g.inputs, b.input);
        } else {
          const producer = stepLookup(b.step);
          if (producer.cause) { if (producer.missing) d('flow', code, p); else bad(producer.cause); return; }
          if (!kind(producer.value)) { bad('reference'); return; }
          if (producer.value.kind !== 'invoke') { d('flow', code, p); return; }
          const op = selectedOperation(producer.i);
          if (op.cause) bad(op.cause === 'shape' ? 'shape' : 'reference');
          else actual = sourcePort(op.value.outputs, b.port);
          if (pathOK) {
            const edge = edges.find(e => e.from === producer.i && e.label === 'success');
            if (reachable(entry, consumer, edge)) d('flow', code, p);
          }
        }
        if (target !== undefined && actual !== undefined && target !== actual) d('flow', code, p);
      }
    }
    steps.forEach((s, i) => {
      if (!kind(s)) return;
      const p = pointer(sp, i);
      if (s.kind === 'invoke' || (s.kind === 'end' && s.outcome === 'success')) data(i, i, 'DATA', p);
      if (s.kind !== 'invoke') return;
      let governed = S.has(s, 'scope');
      const unavailable = new Set();
      const op = selectedOperation(i);
      if (op.cause) unavailable.add(op.cause);
      else if (!S.effects(op.value.effects)) unavailable.add('shape');
      else if (op.value.effects !== 'none') governed = true;
      const a = lookup(s.agent, 'agents');
      if (a.cause) unavailable.add(a.cause);
      else if (!S.object(a.value)) unavailable.add('shape');
      else if (S.has(a.value, 'tools')) {
        if (!Array.isArray(a.value.tools)) unavailable.add('shape');
        else for (const r of a.value.tools) {
          const t = lookup(r, 'tools');
          if (t.cause) unavailable.add(t.cause);
          else if (!S.object(t.value) || !S.effects(t.value.effects)) unavailable.add('shape');
          else if (t.value.effects !== 'none') governed = true;
        }
      }
      for (const gate of steps) {
        if (!kind(gate)) unavailable.add('shape');
        else if (gate.kind === 'approval') {
          if (!S.id(gate.call)) unavailable.add('shape');
          else if (S.id(s.id) && gate.call === s.id) governed = true;
          else if (!S.id(s.id)) unavailable.add('shape');
        }
      }
      if (governed) {
        if (!S.has(s, 'scope')) d('flow', 'SCOPE', p);
        else if (!S.shape(s.scope, S.scope)) gap('flow', 'SCOPE', p);
      } else unavailable.forEach(cause => gap('flow', 'SCOPE', p, cause));
    });

    const chains = new Map();
    steps.forEach((s, i) => {
      if (!kind(s) || s.kind !== 'approval') return;
      const p = pointer(sp, i), call = stepLookup(s.call);
      if (call.cause || !kind(call.value) || call.value.kind !== 'invoke') {
        if (call.missing || (!call.cause && kind(call.value) && call.value.kind !== 'invoke')) d('flow', 'APPROVAL', p);
        else gap('flow', 'APPROVAL', p, call.cause ?? 'reference');
        gap('flow', 'APPROVAL-DATA', p, call.cause === 'shape' ? 'shape' : 'reference');
        return;
      }
      data(call.i, i, 'APPROVAL-DATA', p, true);
      const group = chains.get(call.i) ?? []; group.push(i); chains.set(call.i, group);
      if (!S.shape(s, S.step)) gap('flow', 'APPROVAL', p);
      if (!pathOK) gap('flow', 'APPROVAL', p, 'path');
    });
    for (const [call, group] of chains) {
      if (!pathOK) continue;
      // A malformed chain member prevents structural chain assessment for its peers.
      if (group.some(i => !S.shape(steps[i], S.step))) { group.forEach(i => gap('flow', 'APPROVAL', pointer(sp, i))); continue; }
      let invalid = false;
      const next = new Map(group.map(i => [i, stepLookup(steps[i].approved).i]));
      for (const i of group) {
        const seen = new Set(); let at = i;
        while (at !== call && group.includes(at) && !seen.has(at)) { seen.add(at); at = next.get(at); }
        if (at !== call) invalid = true;
      }
      const firsts = group.filter(i => !group.some(j => next.get(j) === i));
      if (firsts.length !== 1) invalid = true;
      const first = firsts[0];
      for (const target of [...group, call]) {
        const incoming = edges.filter(e => e.to === target);
        if (target === first) {
          if (incoming.some(e => steps[e.from].kind === 'approval' && e.label === 'approved' && steps[e.from].call !== steps[call].id)) invalid = true;
        } else if (incoming.length !== 1 || incoming[0].label !== 'approved' || !group.includes(incoming[0].from)) invalid = true;
        if (target !== first && target === entry) invalid = true;
      }
      for (const i of group) {
        let later = next.get(i); const prohibited = new Set([call]);
        while (group.includes(later) && !prohibited.has(later)) { prohibited.add(later); later = next.get(later); }
        for (const label of ['denied', 'failure']) {
          const start = stepLookup(steps[i][label]).i;
          if ([...prohibited].some(t => reachable(start, t))) invalid = true;
        }
      }
      if (invalid) group.forEach(i => d('flow', 'APPROVAL', pointer(sp, i)));
    }
  }
}
