# Archived E2E Tests

These tests have been archived because they are no longer maintained or compatible with the current application architecture.

## Archived Tests

- `test_webapp_e2e.js` - Old comprehensive E2E test that required manual user interaction
- `test_webapp_manual.js` - Manual testing script with interactive browser session

## Why Archived

These tests were designed for an earlier version of the application and:

1. **Required manual intervention** - Tests would pause and wait for users to manually sign in
2. **Used outdated selectors** - UI components have changed significantly
3. **Not suitable for CI/CD** - Manual interaction prevents automated testing
4. **Redundant functionality** - Core functionality is now tested by `auth.spec.js`

## Current E2E Testing

The current E2E test suite (`auth.spec.js`) provides:

- **Automated authentication testing** with mocked Firebase auth
- **Role-based UI testing** for different user permission levels
- **Filter and search functionality** testing
- **Sorting behavior** verification
- **CI/CD compatible** - no manual intervention required

## Running Archived Tests

These tests are no longer maintained and may not work with the current application. They are kept for historical reference only.

If you need to run them for some reason:

```bash
# These will likely fail due to outdated selectors and auth flow changes
npx playwright test tests/e2e/archived/
```
