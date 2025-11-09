# Quick Start - Muttville App

## 🚀 Local Development

**Single path: Run ETL + webapp locally.**

### Prerequisites
- Node.js 18+
- Python 3.12+
- Google account with @muttville.org domain
- Firebase project access
- ShelterLuv API credentials (optional, for full ETL testing)

### Setup
```bash
git clone <repo-url> && cd shelterluv

# Install all dependencies
cd services/webapp-react && npm install
cd ../etl-scraper-py && pip install -r requirements.txt && pip install -r requirements-dev.txt

# Configure environment variables (.env)
# Copy from env.example and fill in your values
cp env.example .env

# Required Firebase vars for webapp (VITE_ prefix REQUIRED for Vite):
VITE_FIREBASE_API_KEY=your_api_key
VITE_FIREBASE_AUTH_DOMAIN=your_project.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=dev-muttville
VITE_FIREBASE_STORAGE_BUCKET=your_project.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=123456789
VITE_FIREBASE_APP_ID=1:123456789:web:abcdef123

# Admin scripts:
FIREBASE_PROJECT_ID=dev-muttville
DEV_SCRIPTS_ENABLED=0

# Optional ETL credentials (uses mock data if not provided):
SHELTERLUV_USER=your_username
SHELTERLUV_PASS=your_password

# Seed test users for authentication (requires admin credentials)
DEV_SCRIPTS_ENABLED=1 FIREBASE_PROJECT_ID=dev-muttville node seed_test_users.js

# Run ETL to populate data (optional, uses mock data if no ShelterLuv creds)
cd services/etl-scraper-py && python run_etl_local.py

# Start webapp in new terminal
cd services/webapp-react && npm run dev  # → http://localhost:5173
```

### Development Workflow
```bash
# Run all tests
npm run test:report

# Webapp development
cd services/webapp-react
npm run dev          # Start dev server
npm test             # Unit tests
npm run test:e2e     # E2E tests

# ETL development
cd services/etl-scraper-py
python run_etl_local.py    # Run ETL
python -m pytest tests/    # Unit tests
python perf/pipeline_performance_test.py  # Performance tests

# Schema management
npm run schema:gen   # Regenerate schema artifacts
npm run schema:check # Verify artifacts are current
```

## Troubleshooting

### Missing Environment Variables
If you see errors about missing environment variables:
- Check `common/firebaseEnvVars.js` for the complete list of required variables
- Ensure your `.env` file contains all required Firebase configuration
- For ETL testing, add ShelterLuv credentials to your `.env`

### Firebase Connection Issues
- Verify your Firebase project ID is in the allowlist (`common/firebaseSafetyConfig.js`)
- Check that your Google account has access to the Firebase project
- Ensure you're not accidentally targeting production projects

### ETL Fails with Authentication
- ShelterLuv credentials are optional for basic development
- If you need real data, contact the team for ShelterLuv API access
- The ETL will use mock data when credentials are missing

### Test Failures
- Run `npm run test:report` to see all test results
- Individual test suites: `npm test` (webapp), `python -m pytest tests/` (ETL)
- Check `artifacts/TESTS.txt` for detailed failure output

## Gotchas

### Node Scripts Environment Requirements
- **Node dev scripts** (`add_user.js`, `check_users.js`, `seed_test_users.js`) require:
  - `FIREBASE_PROJECT_ID` environment variable (not just Vite vars)
  - Admin service account credentials (via GCP Secret Manager or local key file)
  - `DEV_SCRIPTS_ENABLED=1` for any destructive operations

### ETL Environment Setup
- **ETL pipeline** requires `.env` file in project root with ShelterLuv credentials
- Optional `.env.local` for local overrides (ignored by git)
- Python dependencies: `pip install -r requirements.txt && pip install -r requirements-dev.txt`

### Firebase Project Configuration
- Vite env vars (`VITE_FIREBASE_*`) are for browser-only (webapp)
- Admin scripts use `FIREBASE_PROJECT_ID` directly (not Vite prefixed)
- Always verify project ID against `common/firebaseSafetyConfig.js` allowlist

## Environment Safety

> **⚠️ SAFETY FIRST**
>
> Set `DEV_SCRIPTS_ENABLED=1` before running destructive operations. Never target production projects. See `common/firebaseSafetyConfig.js` for allowed project lists.

See [README.md](../README.md) for architecture, data contracts, and security details.
