import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';
import { aliasConfig } from './shared-alias-config.js';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: aliasConfig
  },
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: './src/test/setup.jsx',
    exclude: ['tests/e2e/**', 'node_modules/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.config.js',
        '**/*.types.ts',
        'check_firestore_data.js',
        'performance_test.js',
        'test_webapp_*.js'
      ]
    }
  }
});
