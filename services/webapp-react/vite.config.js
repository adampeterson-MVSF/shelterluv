import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import { execSync } from 'child_process'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    react(),
    // Type checking plugin - runs tsc --noEmit on build
    {
      name: 'type-check',
      buildStart() {
        if (process.env.NODE_ENV === 'production') {
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
    }
  ],
  resolve: {
    alias: {
      '@common': path.resolve(__dirname, '../../common'),
    },
  },
})
