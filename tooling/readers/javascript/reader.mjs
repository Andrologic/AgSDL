import { run as inheritedRun, stringify } from '../../../experimental/modular-candidate-1/readers/javascript/reader.mjs';
import { contract, processor, validateD } from './core.mjs';
import { validateG } from './graph.mjs';

export { stringify };

export const run = request => inheritedRun(request, {
  contract,
  processor,
  validateD,
  validateG,
});
