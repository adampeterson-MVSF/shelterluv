# React App Tests

This directory contains unit and E2E tests for the React frontend application.

## Credential Setup

The React app tests use mocked Firebase services by default, but some tests may require Firebase configuration:

### Firebase Configuration (Optional for most tests)
Create `.env.local` in `services/webapp-react/`:

```bash
# Firebase Configuration (get from Firebase Console)
VITE_FIREBASE_API_KEY=your_api_key_here
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

**Note**: Most unit tests mock Firebase, so these credentials are only needed for E2E tests or if you want to run tests against a real Firebase project.

## Test Categories

### Unit Tests
Located in component-specific test files alongside source code:
- **Component tests**: `*.test.jsx` files test React component rendering and interactions
- **Hook tests**: `useDogs.test.js` tests custom React hooks
- **Context tests**: `AuthContext.test.jsx` tests authentication state management
- **Repository tests**: `dogRepository.test.js`, `userRepository.test.js` test data access logic

### End-to-End Tests
Located in `tests/e2e/`:
- **Authentication tests**: `auth.spec.js` tests Google SSO login flow
- **Archived tests**: Legacy E2E tests in `archived/` directory

## Running Tests

### All Tests
```bash
cd services/webapp-react
npm test
```

### Watch Mode (during development)
```bash
npm run test:watch
```

### With Coverage
```bash
npm run test:coverage
```

### Specific Test File
```bash
npm test DogCard.test.jsx
```

### E2E Tests (Playwright)
```bash
# Install Playwright browsers (first time only)
npx playwright install

# Run E2E tests
npx playwright test

# Run with UI
npx playwright test --ui
```

## Test Architecture

### Mock Strategy
- **Firebase Auth**: Mocked sign-in/sign-out flows
- **Firestore**: Mocked database operations
- **React Router**: Mocked navigation hooks
- **Environment variables**: Loaded from `.env.local` via dotenv in test setup

### Test Setup
- **Global setup**: `src/test/setup.jsx` configures Vitest environment
- **Test helpers**: Centralized rendering utilities for providers
- **Mock data**: Predefined dog records and user states

### Test Utilities
```javascript
// Render component with all required providers
global.renderWithProviders(<MyComponent />, options)

// Render with just routing
global.renderWithRouter(<MyComponent />, options)

// Render with auth context only
global.renderWithAuth(<MyComponent />, options)
```

## Common Test Patterns

### Component Testing
```javascript
import { renderWithProviders } from '../test/setup';

test('renders dog card correctly', () => {
  const dog = { name: 'Buddy', age: '3 years' };
  const { getByText } = renderWithProviders(<DogCard dog={dog} />);

  expect(getByText('Buddy')).toBeInTheDocument();
});
```

### Hook Testing
```javascript
import { renderHook, waitFor } from '@testing-library/react';
import { renderWithProviders } from '../test/setup';

test('fetches dogs successfully', async () => {
  const { result } = renderHook(() => useDogs(), {
    wrapper: ({ children }) => renderWithProviders(children)
  });

  await waitFor(() => {
    expect(result.current.dogs).toHaveLength(5);
  });
});
```

## Debugging Test Failures

### Firebase Connection Issues
```
Error: Firestore connection failed: Cannot read properties of undefined (reading 'exists')
```
**Solution**: Check that Firebase mocks are properly configured in the test setup.

### Missing Environment Variables
```
ReferenceError: VITE_FIREBASE_API_KEY is not defined
```
**Solution**: Ensure `.env.local` exists with Firebase config, or run tests that don't require real Firebase.

### Auth Context Errors
```
Error: useAuth must be used within an AuthProvider
```
**Solution**: Use `renderWithProviders` or `renderWithAuth` helper instead of basic `render`.

## Contributing

When adding new tests:
1. Place test files next to the code they test (e.g., `Component.test.jsx`)
2. Use descriptive test names and organize with `describe` blocks
3. Mock external dependencies (Firebase, APIs, navigation)
4. Include credential setup comments if tests require real Firebase
5. Use the centralized test helpers for consistent provider setup
