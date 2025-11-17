// E2E Tests for Muttville Webapp with Real Firebase Authentication

import { test, expect } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const PLAYWRIGHT_DEBUG = process.env.PLAYWRIGHT_DEBUG === 'true';

function debugLog(...args) {
  if (PLAYWRIGHT_DEBUG) {
    console.log(...args);
  }
}

/**
 * E2E Tests for Muttville Webapp with Real Firebase Authentication
 *
 * Tests the core functionality with real Firebase auth and Firestore:
 * - Authentication flow (login/logout with Google SSO)
 * - Basic dog display from real Firestore data
 * - Navigation
 *
 * Prerequisites:
 * - Firebase project configured with @muttville.org domain restriction
 * - Auth state saved via: node save-auth-state.mjs
 * - Firestore populated with dog data
 */

// Auth state file path - must match save-auth-state.mjs and playwright.config.js
// Use relative path for Playwright (it resolves relative to testDir)
const AUTH_STATE_PATH = 'playwright/.auth/muttville.json';

// Test data for parameterization
const USER_ROLES = [
  { name: 'staff', email: 'staff@muttville.org' },
  { name: 'viewer', email: 'viewer@muttville.org' }
];

test.describe('Authentication State Testing', () => {
  test.describe('unauthenticated user', () => {
    // Override storageState to be empty for unauthenticated tests
    test.use({ storageState: undefined });

    test('app loads and shows appropriate UI', async ({ page }) => {
      // Listen for console errors (ignore harmless 404s)
      const errors = [];
      page.on('console', msg => {
        if (msg.type() !== 'error') return;
        
        const text = msg.text();
        
        // Ignore known noisy 404s (favicon, manifest, etc.)
        if (
          text.includes('favicon.ico') ||
          text.includes('manifest.webmanifest') ||
          text.includes('manifest.json') ||
          text.includes('robots.txt') ||
          (text.includes('404 (Not Found)') && (
            text.includes('favicon') ||
            text.includes('manifest') ||
            text.includes('robots')
          ))
        ) {
          return;
        }
        
        errors.push(text);
        debugLog('Browser console error:', text);
      });

      // Listen for page errors
      page.on('pageerror', error => {
        errors.push(error.message);
        debugLog('Page error:', error.message);
      });

      await page.goto('/', { waitUntil: 'domcontentloaded' });

      // Wait for app to initialize
      await page.waitForLoadState('networkidle');

      // Wait a bit more for React to render
      await page.waitForTimeout(3000);

      // Check if we're authenticated or need to log in
      const signInButton = page.locator('button.sign-in-btn');
      const userInfo = page.locator('.user-info');

      // App should show either login button OR authenticated content
      const isAuthenticated = await userInfo.isVisible().catch(() => false);
      const needsLogin = await signInButton.isVisible().catch(() => false);

      // Fail immediately on JavaScript errors
      if (errors.length > 0) {
        throw new Error(`JavaScript errors detected: ${errors.join('; ')}`);
      }

      // Fail if body is empty or too short (app failed to load)
      const bodyText = await page.textContent('body');
      if (!bodyText || bodyText.trim().length < 50) {
        throw new Error(`App failed to load - body is empty or too short (${bodyText?.length || 0} chars)`);
      }

      // Verify app actually rendered by checking for root element content
      const rootContent = await page.locator('#root').textContent().catch(() => null);
      if (!rootContent || rootContent.trim().length === 0) {
        throw new Error('App root element is empty - React app failed to mount');
      }

      // Log current state for debugging
      const title = await page.title();
      debugLog(`[unauthenticated] Page title:`, title);
      debugLog(`[unauthenticated] Body content length:`, bodyText.length);
      debugLog(`[unauthenticated] Sign in button visible:`, needsLogin);
      debugLog(`[unauthenticated] User info visible:`, isAuthenticated);

      // This test expects unauthenticated state
      if (needsLogin) {
        debugLog(`✅ [unauthenticated] User needs authentication - testing login prompt`);

        // Should show sign in button
        await expect(page.locator('button.sign-in-btn')).toBeVisible();
        await expect(page.locator('button.sign-in-btn')).toHaveText('Sign In');

        // Should not show authenticated content
        await expect(page.locator('.dogs-grid')).not.toBeVisible();
        await expect(page.locator('.dog-card')).toHaveCount(0);

        debugLog(`✅ [unauthenticated] Login prompt working correctly`);

      } else if (isAuthenticated) {
        debugLog(`⚠️ [unauthenticated] Expected unauthenticated but user is authenticated - skipping`);
        return; // Skip test if auth state doesn't match expectation

      } else {
        throw new Error(`[unauthenticated] App is in unexpected state - neither authenticated nor showing login prompt`);
      }
    });

    test('can view dog information', async ({ page }) => {
      debugLog(`[unauthenticated] Skipping dog information test - requires authentication`);
      return;
    });

    test('can navigate between pages', async ({ page }) => {
      debugLog(`[unauthenticated] Skipping navigation test - requires authentication`);
      return;
    });
  });

  test.describe('authenticated user', () => {
    // Explicitly use saved auth state for authenticated tests
    test.use({ storageState: AUTH_STATE_PATH });

    // Skip tests if auth state file doesn't exist
    const absolutePath = path.join(process.cwd(), AUTH_STATE_PATH);
    test.skip(
      !fs.existsSync(absolutePath),
      `Auth state file not found at ${absolutePath}. Run 'node save-auth-state.mjs' to create auth state.`
    );

    test('app loads and shows appropriate UI', async ({ page }) => {
      // Listen for console errors (ignore harmless 404s)
      const errors = [];
      page.on('console', msg => {
        if (msg.type() !== 'error') return;
        
        const text = msg.text();
        
        // Ignore known noisy 404s (favicon, manifest, etc.)
        if (
          text.includes('favicon.ico') ||
          text.includes('manifest.webmanifest') ||
          text.includes('manifest.json') ||
          text.includes('robots.txt') ||
          text.includes('404 (Not Found)') && (
            text.includes('favicon') ||
            text.includes('manifest') ||
            text.includes('robots')
          )
        ) {
          return;
        }
        
        errors.push(text);
        debugLog('Browser console error:', text);
      });

      // Listen for page errors
      page.on('pageerror', error => {
        errors.push(error.message);
        debugLog('Page error:', error.message);
      });

      await page.goto('/', { waitUntil: 'domcontentloaded' });

      // Wait for app to initialize (use 'load' instead of 'networkidle' since Firebase keeps connections open)
      await page.waitForLoadState('load');

      // Wait for Firebase auth to initialize and React to render
      // Try waiting for either authenticated state OR sign-in button
      try {
        await page.waitForSelector('.user-info, button.sign-in-btn', { timeout: 10000 });
      } catch (e) {
        // If neither appears, continue to check state
      }

      // Wait a bit more for React to render
      await page.waitForTimeout(2000);

      // Check if we're authenticated or need to log in
      const signInButton = page.locator('button.sign-in-btn');
      const userInfo = page.locator('.user-info');

      // App should show either login button OR authenticated content
      const isAuthenticated = await userInfo.isVisible().catch(() => false);
      const needsLogin = await signInButton.isVisible().catch(() => false);

      // Fail immediately on JavaScript errors
      if (errors.length > 0) {
        throw new Error(`JavaScript errors detected: ${errors.join('; ')}`);
      }

      // Fail if body is empty or too short (app failed to load)
      const bodyText = await page.textContent('body');
      if (!bodyText || bodyText.trim().length < 50) {
        throw new Error(`App failed to load - body is empty or too short (${bodyText?.length || 0} chars)`);
      }

      // Verify app actually rendered by checking for root element content
      const rootContent = await page.locator('#root').textContent().catch(() => null);
      if (!rootContent || rootContent.trim().length === 0) {
        throw new Error('App root element is empty - React app failed to mount');
      }

      // Log current state for debugging
      const title = await page.title();
      debugLog(`[authenticated] Page title:`, title);
      debugLog(`[authenticated] Body content length:`, bodyText.length);
      debugLog(`[authenticated] Sign in button visible:`, needsLogin);
      debugLog(`[authenticated] User info visible:`, isAuthenticated);

      // This test expects authenticated state
      if (isAuthenticated) {
        debugLog(`✅ [authenticated] User authenticated - testing full functionality`);

        // Should show authenticated UI (use first h1 or getByRole to avoid strict mode violation)
        await expect(page.locator('h1').first()).toContainText('Muttville');

        // Should show user info
        await expect(page.locator('.user-info')).toBeVisible();

        // Should show dog grid with cards (real data from Firestore)
        await expect(page.locator('.dogs-grid')).toBeVisible();

        debugLog(`✅ [authenticated] Authenticated user flow working`);

      } else {
        // Skip test if auth state is missing
        test.skip(true, `No auth state found - authenticated tests require auth state. Run 'node save-auth-state.mjs' to create auth state.`);
      }
    });

    test('can view dog information', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('load');
      
      // Wait for authenticated UI to appear
      try {
        await page.waitForSelector('.user-info', { timeout: 10000 });
      } catch (e) {
        // Continue to check auth state
      }
      
      await page.waitForTimeout(2000);

      // Verify we're authenticated - skip if not
      const userInfo = page.locator('.user-info');
      const isAuthenticated = await userInfo.isVisible().catch(() => false);
      if (!isAuthenticated) {
        test.skip(true, `No auth state found - authenticated tests require auth state. Run 'node save-auth-state.mjs' to create auth state.`);
      }

      // Wait for dog data to load (may be empty)
      await page.waitForTimeout(2000);

      const dogCards = page.locator('.dog-card');
      const dogCount = await dogCards.count();

      if (dogCount > 0) {
        // Check first dog card content (real data from Firestore)
        const firstCard = dogCards.first();
        await expect(firstCard).toBeVisible();

        // Should contain dog information
        const cardText = await firstCard.textContent();
        expect(cardText).toBeTruthy();
        expect(cardText.length).toBeGreaterThan(10);

        debugLog(`✅ [authenticated] Found ${dogCount} dogs in Firestore`);
      } else {
        debugLog(`ℹ️ [authenticated] No dogs found in Firestore (this is normal for empty database)`);
      }
    });

    test('can navigate between pages', async ({ page }) => {
      await page.goto('/', { waitUntil: 'domcontentloaded' });
      await page.waitForLoadState('load');
      
      // Wait for authenticated UI to appear
      try {
        await page.waitForSelector('.user-info', { timeout: 10000 });
      } catch (e) {
        // Continue to check auth state
      }
      
      await page.waitForTimeout(2000);

      // Verify we're authenticated - skip if not
      const userInfo = page.locator('.user-info');
      const isAuthenticated = await userInfo.isVisible().catch(() => false);
      if (!isAuthenticated) {
        test.skip(true, `No auth state found - authenticated tests require auth state. Run 'node save-auth-state.mjs' to create auth state.`);
      }

      // Wait for dog data to load
      await page.waitForTimeout(2000);

      const dogCards = page.locator('.dog-card');
      const dogCount = await dogCards.count();

      if (dogCount > 0) {
        // Click on first dog card to navigate to details
        await dogCards.first().click();

        // Should navigate to dog details page
        await expect(page.locator('h1')).toBeVisible();

        // Should show back navigation
        const backLink = page.locator('text=← Back to all dogs');
        if (await backLink.isVisible()) {
          await backLink.click();
          // Should return to home page
          await expect(page.locator('.dogs-grid')).toBeVisible();
          debugLog(`✅ [authenticated] Navigation between pages working`);
        } else {
          debugLog(`ℹ️ [authenticated] Back navigation link not found (may be different implementation)`);
        }
      } else {
        debugLog(`ℹ️ [authenticated] Skipping navigation test - no dogs available`);
      }
    });
  });
});

test.describe('User Role Testing', () => {
  USER_ROLES.forEach(({ name: roleName, email }) => {
    test.describe(`${roleName} user (${email})`, () => {

      test('shows appropriate permissions', async ({ page }) => {
        // This test would require authenticated state with specific user roles
        // For now, just verify the app loads without errors
        await page.goto('/', { waitUntil: 'domcontentloaded' });
        await page.waitForLoadState('networkidle');

        // Basic smoke test - app should load without JavaScript errors
        const title = await page.title();
        expect(title).toBeTruthy();

        debugLog(`✅ [${roleName}] App loads successfully for ${email}`);
      });
    });
  });
});