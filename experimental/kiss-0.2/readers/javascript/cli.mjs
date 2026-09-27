import { readFileSync } from 'node:fs';
import { validate } from './reader.mjs';
try {
  if (process.argv.length !== 3) throw new Error('Usage: node cli.mjs ARTIFACT');
  const report = validate(readFileSync(process.argv[2]));
  process.stdout.write(`${JSON.stringify(report)}\n`);
} catch (error) {
  process.stderr.write(`${error.message}\n`);
  process.exitCode = 2;
}
