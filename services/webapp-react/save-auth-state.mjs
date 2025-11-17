/**
 * E2E utility; do not import from app code.
 * Script to save authentication state for E2E tests
 *
 * Usage:
 * 1. Make sure dev server is running: npm run dev
 * 2. Run this script: node save-auth-state.mjs
 * 3. Manually log in when the browser opens
 * 4. Auth state will be saved to playwright/.auth/muttville.json
 * 5. E2E tests will now use this authenticated state
 */

import { chromium } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const AUTH_STATE_PATH = path.join(process.cwd(), 'playwright', '.auth', 'muttville.json');
const BASE_URL = process.env.E2E_BASE_URL ?? 'http://localhost:5173';

async function saveAuthState() {
  console.log('Opening browser for authentication...');
  console.log('Please log in with a @muttville.org account.');
  console.log('Auth state will be saved automatically after login.\n');

  // Ensure directory exists
  const authDir = path.dirname(AUTH_STATE_PATH);
  if (!fs.existsSync(authDir)) {
    fs.mkdirSync(authDir, { recursive: true });
    console.log(`Created auth directory: ${authDir}`);
  }

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to the app
    await page.goto(BASE_URL);

    // Wait for user to log in (check for authenticated user elements)
    console.log('Waiting for authentication...');
    await page.waitForSelector('.user-info', { timeout: 300000 }); // 5 minutes timeout

    // Make sure we're back on the app origin (not Google OAuth redirect)
    const currentUrl = page.url();
    if (!currentUrl.includes('localhost:5173')) {
      console.log(`Redirecting back to app from ${currentUrl}...`);
      await page.goto(BASE_URL);
      await page.waitForSelector('.user-info', { timeout: 10000 });
    }

    // Wait for Firebase auth to fully initialize and persist to localStorage
    // Firebase stores auth tokens in localStorage, so we need to wait for that
    console.log('Waiting for Firebase auth to persist...');
    await page.waitForTimeout(5000); // Give Firebase more time to write to localStorage

    // Verify Firebase auth is actually persisted by checking localStorage
    const localStorageInfo = await page.evaluate(() => {
      const keys = [];
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i);
        keys.push(key);
      }
      const hasFirebaseAuth = keys.some(key => 
        key && (key.startsWith('firebase:authUser:') || key.startsWith('firebase:host:'))
      );
      return { hasFirebaseAuth, keys, count: localStorage.length };
    });

    console.log(`LocalStorage keys (${localStorageInfo.count}):`, localStorageInfo.keys.slice(0, 5).join(', '), '...');
    
    if (!localStorageInfo.hasFirebaseAuth) {
      console.warn('⚠️  Warning: Firebase auth token not found in localStorage.');
      console.warn('   Found keys:', localStorageInfo.keys.join(', '));
      console.warn('   Auth state will be saved anyway, but tests may fail.');
    } else {
      console.log('✅ Firebase auth token found in localStorage');
    }

    // Save auth state (matching path in auth.spec.js and playwright.config.js)
    // Make sure we're on the app origin when saving
    await context.storageState({ path: AUTH_STATE_PATH });
    console.log(`\n✅ Auth state saved to ${AUTH_STATE_PATH}`);
    console.log('E2E tests will now use this authenticated state.\n');

    // Keep browser open for a moment
    await page.waitForTimeout(2000);
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.log('Make sure you log in within 5 minutes.');
    process.exit(1);
  } finally {
    await browser.close();
  }
}

saveAuthState().catch(err => {
  console.error('Failed to save auth state:', err);
  process.exit(1);
});

