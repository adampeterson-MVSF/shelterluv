# Webapp React

React frontend for Muttville dog adoption platform.

**Features**: Google SSO auth, advanced dog filtering/search, role-based foster contacts, responsive design.

## Quick Start

```bash
npm install
npm run dev  # → http://localhost:5173
```

## Environment Setup

Create `.env` file with Firebase config:

```bash
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=your_project_id
VITE_FIREBASE_STORAGE_BUCKET=your_project.firebasestorage.app
VITE_FIREBASE_MESSAGING_SENDER_ID=your_sender_id
VITE_FIREBASE_APP_ID=your_app_id
```

## Commands

```bash
# Development
npm run dev         # Start dev server
npm run build       # Production build
npm run preview     # Preview production build

# Testing
npm test            # Unit tests (Vitest)
npm run test:e2e    # E2E tests (Playwright)
npm run lint        # ESLint
npm run typecheck   # TypeScript check

# Schema
npm run generate:types  # Regenerate Dog.types.ts from schema
```

## Architecture

- **Data Flow**: Firestore → `dogRepository.getDogs()` → `normalizeDog()` → Components
- **Auth**: Google SSO → AuthContext (discriminated union) → RoleGuard components
- **Schema**: Mirrors `common/schemas/dog.schema.json` via generated types

See [main README](../../README.md) for detailed architecture.
