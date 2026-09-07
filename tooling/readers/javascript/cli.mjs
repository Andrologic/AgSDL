#!/usr/bin/env node
import { run, stringify } from './reader.mjs';

function decode(value, name) {
  if (typeof value !== 'string' || !/^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/.test(value)) {
    throw new TypeError(`${name} must be canonical base64`);
  }
  const bytes = Buffer.from(value, 'base64');
  if (bytes.toString('base64') !== value) throw new TypeError(`${name} must be canonical base64`);
  return bytes;
}

function transport(request) {
  if (!request || typeof request !== 'object' || Array.isArray(request)) {
    throw new TypeError('request must be an object');
  }
  if (!request.annexes || typeof request.annexes !== 'object' || Array.isArray(request.annexes)) {
    throw new TypeError('annexes must be an object');
  }
  const annexes = Object.create(null);
  for (const [id, value] of Object.entries(request.annexes)) annexes[id] = decode(value, `annex ${id}`);
  const outcome = run({ ...request, primary: decode(request.primary, 'primary'), annexes });
  const artifacts = Object.fromEntries(
    Object.entries(outcome.artifacts).map(([id, bytes]) => [id, Buffer.from(bytes).toString('base64')]),
  );
  return { report: outcome.report, artifacts };
}

process.stdin.setEncoding('utf8');
let input = '';
for await (const chunk of process.stdin) input += chunk;
try {
  process.stdout.write(`${stringify(transport(JSON.parse(input)))}\n`);
} catch (error) {
  process.stderr.write(`host request error: ${error.message}\n`);
  process.exitCode = 2;
}
