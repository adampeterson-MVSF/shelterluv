import { defineConfig, devices } from '@playwright/test';
import fs from 'fs';

// Check if auth state file exists
const authStatePath = './auth-state.json';
const hasAuthState = fs.existsSync(authStatePath);

/**
 * @see https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  testIgnore: '**/archived/**',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html'],
    ['list'],
    ['json', { outputFile: 'test-results.json' }]
  ],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    baseURL: 'http://localhost:5173',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',

    /* Use saved auth state if available */
    ...(hasAuthState && { storageState: authStatePath }),
  },

  /* Configure projects for major browsers */
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  /* Run your local dev server before starting the tests */
  webServer: process.env.SKIP_WEBSERVER ? undefined : {
    command: 'VITE_FIREBASE_API_KEY="AIzaSyBC6eEN0wmg8MxGM-hyZ_8OaSsJRRjNHE0" VITE_FIREBASE_AUTH_DOMAIN="muttville.firebaseapp.com" VITE_FIREBASE_PROJECT_ID="muttville" VITE_FIREBASE_STORAGE_BUCKET="muttville.firebasestorage.app" VITE_FIREBASE_MESSAGING_SENDER_ID="537540766155" VITE_FIREBASE_APP_ID="1:537540766155:web:31058157b8e4d87a5e2e4e" npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000, // Increase timeout to 2 minutes
  },
});
