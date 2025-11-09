/**
 * E2E utility; do not import from app code.
 * Script to save authentication state for E2E tests
 *
 * Usage:
 * 1. Make sure dev server is running: npm run dev
 * 2. Run this script: node save-auth-state.js
 * 3. Manually log in when the browser opens
 * 4. Auth state will be saved to auth-state.json
 * 5. E2E tests will now use this authenticated state
 */

import { chromium } from '@playwright/test';

async function saveAuthState() {
  console.log('Opening browser for authentication...');
  console.log('Please log in with a @muttville.org account.');
  console.log('Auth state will be saved automatically after login.\n');

  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to the app
    await page.goto('http://localhost:5173');

    // Wait for user to log in (check for authenticated user elements)
    console.log('Waiting for authentication...');
    await page.waitForSelector('.user-info', { timeout: 300000 }); // 5 minutes timeout

    // Save auth state
    await context.storageState({ path: 'auth-state.json' });
    console.log('\n✅ Auth state saved to auth-state.json');
    console.log('E2E tests will now use this authenticated state.\n');

    // Keep browser open for a moment
    await page.waitForTimeout(2000);
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    console.log('Make sure you log in within 5 minutes.');
  } finally {
    await browser.close();
  }
}

saveAuthState().catch(console.error);

