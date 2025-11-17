# E2E Test Setup Guide

## Quick Start

To run E2E tests with authenticated user flows:

```bash
# 1. Start the dev server (in one terminal)
npm run dev

# 2. Save auth state (in another terminal)
npm run test:e2e:save-auth

# 3. When browser opens, log in with a @muttville.org account
#    The script will automatically save auth state when it detects you're logged in

# 4. Run E2E tests
npm run test:e2e
```

## Helper Script

Use the combined script to save auth state and run tests:

```bash
npm run test:e2e:with-auth
```

**Note**: This requires the dev server to be running first.

## Auth State File

- **Location**: `playwright/.auth/muttville.json`
- **Created by**: `save-auth-state.mjs`
- **Used by**: Authenticated user tests in `tests/e2e/auth.spec.js`

## Troubleshooting

### "Auth state file not found" / Tests skipped

If authenticated tests are being skipped, it means the auth state file is missing. Run `npm run test:e2e:save-auth` first to create the auth state file. Tests will be **skipped** (not failed) when auth state is missing, so you can run the full test suite without authentication and only the authenticated tests will be skipped.

### Tests pass but show "No auth state found"

If you see this message, check that:
1. The auth state file exists at `playwright/.auth/muttville.json`
2. The file is readable
3. The path matches what's configured in `auth.spec.js`

**Note**: Tests will skip (not fail) when auth state is missing, allowing you to run unauthenticated tests without requiring auth setup.

### Browser doesn't open

Make sure:
- Dev server is running (`npm run dev`)
- Port 5173 is accessible
- No firewall is blocking the connection

