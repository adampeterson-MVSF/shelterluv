import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { execSync } from 'child_process'
import { aliasConfig } from './shared-alias-config.js'

// Type check plugin - only runs when explicitly requested
const typeCheckPlugin = {
  name: 'type-check',
  buildStart() {
    // Only run type check if TYPE_CHECK=true (not just in production)
    if (process.env.TYPE_CHECK === 'true') {
      console.log('Running TypeScript type check...');
      try {
        execSync('npm run typecheck', { stdio: 'inherit' });
        console.log('✅ Type check passed');
      } catch (error) {
        console.error('❌ Type check failed');
        throw error;
      }
    }
  }
};

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    typeCheckPlugin
  ],
  resolve: {
    alias: aliasConfig,
  },
  // Look for .env files in the monorepo root (parent of webapp directory)
  envDir: path.resolve(__dirname, '..', '..'),
})
