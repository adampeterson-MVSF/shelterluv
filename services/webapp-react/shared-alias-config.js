/**
 * Shared alias configuration for Vite and Vitest.
 * Single source of truth for path aliases.
 */

import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const aliasConfig = {
  '@common': path.resolve(__dirname, '../../common'),
};

