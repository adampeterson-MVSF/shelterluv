# Muttville App Monorepo

Polyglot monorepo for Muttville's dog adoption platform.

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    ShelterLuv API/Scraping                     │
└────────────────────────────┬──────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              services/etl_scraper_py/ (Python ETL)              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ config.py → config_loader.py → common/config.json       │  │
│  │ schema.py → common/schemas/dog.schema.json              │  │
│  │ dog_types.py (generated from schema)                    │  │
│  │                                                           │  │
│  │ extract.py → transform.py → load.py                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└────────────────────────────┬──────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Firestore (GCP)                              │
│  ┌──────────────────────┐  ┌──────────────────────┐           │
│  │  dogs collection     │  │  users collection    │           │
│  │  (validated schema)  │  │  (role-based auth)   │           │
│  └──────────────────────┘  └──────────────────────┘           │
└────────────────────────────┬──────────────────────────────────┘
                              │
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          services/webapp-react/ (React Frontend)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ src/types/Dog.types.ts (generated from schema)           │  │
│  │ src/statusMapping.js (re-exports common/statusMapping.js)│  │
│  │ src/repositories/dogRepository.js                         │  │
│  │ src/hooks/useDogs.js                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Data Flow**: ShelterLuv → ETL → Firestore → Webapp

**Configuration Flow**: `common/config.json` → `configArtifact.{js,py}` → Both JS and Python

**Schema Flow**: `common/schemas/dog.schema.json` → Generated artifacts → ETL + Webapp

**Exact file locations:**
- Schema: `common/schemas/dog.schema.json`
- Config: `common/config.json` → `services/etl_scraper_py/config.py` (via `config_loader.py`)
- Generated artifacts: `common/statusMapping.js`, `common/sizeConfig.js`, `services/webapp-react/src/types/Dog.types.ts`
- Generator: `generate_schema_artifacts.js` → `schemaArtifactsCore.js` → `schemaArtifactsCli.js`

**Breaking Changes Policy**: Breaking changes are allowed until first production user. No backward compatibility required. Internal APIs can change freely as long as tests and schema stay in sync.

## Architecture

**`common/`** - Shared configuration and generated artifacts
- `schemas/dog.schema.json` - Canonical JSON Schema
- `config.json` - Environment profiles, safe projects, roles
- `statusMapping.js`, `sizeConfig.js` - Generated from schema
- `firebaseConfig.js`, `devScriptSafety.js`, `userRoles.js` - Shared utilities

**`services/etl_scraper_py/`** - Python ETL pipeline
- Extracts from ShelterLuv API + scraping
- Normalizes, enriches, validates against schema
- Loads into Firestore `dogs` collection
- Entry point: `run_etl_local.py` (dev) or `main.py` (production)

**`services/webapp-react/`** - React frontend
- Firebase-authenticated Vite app
- Reads from Firestore `dogs` collection
- Uses generated TypeScript types from schema
- Entry point: `npm run dev` (dev) or `npm run build` (production)

## Configuration

**Single source**: `common/config.json` defines:
- `env_profiles`: Required/optional env vars per profile (`web`, `admin`, `etl`, `dev`)
- `python_env_profiles`: GCP project mappings (`dev`, `staging`, `e2e`, `demo`, `prod`)
- `safe_profiles`: Profiles allowed for dev operations
- `roles`: Valid user roles (`viewer`, `closer`, `staff`)

All scripts use `common/devScriptSafety.js` for safety checks. Never hardcode project IDs.

### Configuration Sharing Between JS and Python

**Single source**: `common/config.json` defines environment profiles and project mappings used by both JavaScript and Python code.

**JS consumption**:
- `common/configArtifact.js` - Generated artifact that provides normalized profile maps and safety rules
- Provides `{ envProfileName → { projectId, isSafe } }` and `{ projectId → { envProfileName, isSafe } }` mappings
- Used by `firebaseConfig.js`, `devScriptSafety.js`, and all Node scripts

**Python consumption**:
- `services/etl_scraper_py/config_loader.py` - Reads `common/config.json` via generated artifacts (not direct JSON parsing)
- Provides `get_env_profiles()`, `get_safe_profiles()`, `get_project_safety()` mappings
- Used by `config.py` for `EtlConfig` and `SafetyPolicy` construction

**Consistency guarantee**: Both languages use the same underlying data from `common/config.json`, ensuring environment profiles and safety rules are identical across the stack.

## Quick Start

### Schema Generation

```bash
npm run schema:gen    # Generate artifacts from schema
npm run schema:check  # Verify artifacts are in sync
```

**To change schema:**
1. Edit `common/schemas/dog.schema.json`
2. Run `npm run schema:gen`
3. Update ETL/webapp code to handle changes
4. Run `npm run schema:check` and tests

**Generator path**: `generate_schema_artifacts.js` → `schemaArtifactsCore.js` → `schemaArtifactsCli.js`. Never edit generated files.

### Run ETL Locally

```bash
cd services/etl_scraper_py
python3 run_etl_local.py
```

Uses env vars from `common/config.json` `etl` profile. See `services/etl_scraper_py/README.md`.

### Run Webapp Locally

```bash
cd services/webapp-react
npm run dev   # http://localhost:5173
```

Uses `VITE_`-prefixed env vars from `common/config.json` `web` profile. See `services/webapp-react/README.md`.

## Safety Model

**Conceptual Overview**: The system distinguishes between "safe" development/testing projects and "unsafe" production projects. All destructive operations (data writes, user management, schema changes) require explicit safety checks that verify the target project is in the approved "safe" list.

**Single source of truth**: `common/config.json` defines `safe_profiles` list. All safety checks use this file via `common/devScriptSafety.js` (Node) or `services/etl_scraper_py/config.py` (Python).

### Safety Layers

1. **Environment Variable Check**: `DEV_SCRIPTS_ENABLED=1` must be set for destructive operations
2. **Project ID Validation**: Project must be in `common/config.json` `safe_profiles` list
3. **Profile Matching**: Python `EnvProfile` enum must match `safe_profiles` (validated on import)

### Safe Profiles

Defined in `common/config.json`:
- `dev` - Development environment
- `staging` - Staging environment  
- `e2e` - End-to-end testing
- `demo` - Demo environment

**Blocked profiles**: Production projects (`muttville-prod`, `muttville-production`) are never in `safe_profiles` and will fail safety checks.

### Implementation Files

- **Node.js**: `common/devScriptSafety.js` - Exports `assertSafe()`, `isSafeProject()`, `assertDevScriptsEnabled()`
- **Python**: `services/etl_scraper_py/config.py` - `EnvProfile.get_safe_profiles()` validates against config.json
- **Config Loader**: `common/configArtifact.js` - Generated artifact from `common/config.json` with validation

**Usage**: All scripts that perform destructive operations (user seeding, data deletion, etc.) must call `assertSafe()` before execution. See `scripts/firebase_cli_tool.js` for examples.


## Testing

**Unified test runner**: `node generate_test_report.js` runs all tests and generates artifacts.

**Test types:**
- Unit tests: Pure functions, no I/O (run in CI always)
- Integration tests: Mocked I/O (run in CI always)
- E2E tests: Live DB/APIs (run manually/on-demand only)

See [Testing & CI](#testing--ci) section below.

## Data Contracts

**Dog Schema**: `common/schemas/dog.schema.json` (JSON Schema Draft 7). All dog data must conform with `"additionalProperties": false`.

**Required fields** (ETL guarantees): `Internal-ID`, `ID`, `Name`, `Status`, `AgeYears`, `AgeDisplay`, `IsInCustody`, `IsAvailableForAdoption`, `IsHospice`, `IsEventDog`, `PersonalityNotes`, `IntakeNotes`, `MedicalNotes`.

**Status enums**: `["AVAILABLE", "ADOPTED", "PENDING", "HOLD", "UNKNOWN"]` - from schema, mapped in `common/statusMapping.js`.

**Size enums**: `["Small", "Medium", "Large", "X-Large", "UNKNOWN"]` - from schema, ordered in `common/sizeConfig.js`.

**User roles**: `["viewer", "closer", "staff"]` - from `common/userRoles.js`.

## Deployment

**Pre-deploy checks** (required):
1. `npm run schema:gen && npm run schema:check` - Schema artifacts in sync
2. `node generate_test_report.js` - All tests pass
3. `node scripts/firebase_cli_tool.js check-data` - Firestore data integrity
4. `node scripts/firebase_cli_tool.js check-users` - User data integrity

**⚠️ PRODUCTION SAFETY**: Production projects (`muttville-prod`, `muttville-production`) require explicit safety checks. Never deploy without completing pre-deploy checks.

### Pre-Deploy Checks (Required)

**FAIL FAST**: If any check fails, STOP and fix before deploying.

#### Schema & Tests (FAIL = STOP)
```bash
# Generate fresh schema artifacts and verify no drift
npm run schema:gen && npm run schema:check
# If fails: Commit schema changes or fix drift

# Run full test suite and generate report
node generate_test_report.js
# If fails: Fix tests before deploying
```

#### Environment Safety (FAIL = STOP)
```bash
# Validate Firestore data integrity
node scripts/firebase_cli_tool.js check-data

# Validate user data integrity
node scripts/firebase_cli_tool.js check-users

# Verify environment variables are safe
# FIREBASE_PROJECT_ID should be: dev-muttville, staging-muttville, muttville-demo
# NEVER: muttville-prod, muttville-production
```

#### Build Verification (FAIL = STOP)
```bash
# Webapp builds successfully
cd services/webapp-react && npm run build

# ETL deploys successfully (dry run)
cd services/etl_scraper_py && python run_etl_local.py --limit 3 --dry-run
```

### Deploy to Staging

**Environment**: `staging-muttville`

```bash
# Set staging environment
export FIREBASE_PROJECT_ID=staging-muttville
export GCP_PROJECT_ID=staging-muttville

# Deploy ETL Cloud Function
cd services/etl_scraper_py
gcloud functions deploy etl-scraper \
  --project="$GCP_PROJECT_ID" \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated=false \
  --entry-point main \
  --source=. \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GCP_PROJECT_ID" \
  --memory=512MB \
  --timeout=540s

# Deploy Webapp
cd ../webapp-react
firebase use "$FIREBASE_PROJECT_ID"
npm run build
firebase deploy --only hosting --project="$FIREBASE_PROJECT_ID"

# Trigger ETL to populate data
FUNCTION_URL=$(gcloud functions describe etl-scraper \
  --project="$GCP_PROJECT_ID" --format="value(httpsTrigger.url)")
curl -X POST "$FUNCTION_URL" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

### Deploy to Production

**Environment**: `muttville-prod`

```bash
# Set production environment
export FIREBASE_PROJECT_ID=muttville-prod
export GCP_PROJECT_ID=muttville-prod

# Deploy ETL Cloud Function
cd services/etl_scraper_py
gcloud functions deploy etl-scraper \
  --project="$GCP_PROJECT_ID" \
  --runtime python312 \
  --trigger-http \
  --allow-unauthenticated=false \
  --entry-point main \
  --source=. \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$GCP_PROJECT_ID" \
  --memory=512MB \
  --timeout=540s

# Deploy Webapp
cd ../webapp-react
firebase use "$FIREBASE_PROJECT_ID"
npm run build
firebase deploy --only hosting --project="$FIREBASE_PROJECT_ID"

# Trigger ETL to populate data
FUNCTION_URL=$(gcloud functions describe etl-scraper \
  --project="$GCP_PROJECT_ID" --format="value(httpsTrigger.url)")
curl -X POST "$FUNCTION_URL" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

### Emergency Operations (Use Only When Required)

#### Rollback Webapp
```bash
firebase hosting:rollback --project="$FIREBASE_PROJECT_ID"
```

#### Check ETL Logs
```bash
gcloud logging read \
  "resource.type=cloud_function AND resource.labels.function_name=etl-scraper" \
  --project="$GCP_PROJECT_ID" --limit=10
```

#### 🚨 EMERGENCY: Stop ETL Function
```bash
# Only if ETL is malfunctioning and cannot be stopped otherwise
gcloud functions delete etl-scraper --project="$GCP_PROJECT_ID"
```

#### 🚨 EMERGENCY: Wipe All Data
```bash
# Only if data is hopelessly corrupted and you have backups
firebase firestore:bulkdelete --all-collections --project="$GCP_PROJECT_ID" --yes
```

### Testing & CI

**Unit Tests**: Pure functions, no I/O. Run in CI always.
- ETL: pytest unit tests (no network/Firestore)
- Webapp: Vitest unit tests

**Integration Tests**: Component interactions, mocked I/O. Run in CI always.
- ETL: pipeline integration tests with mocked APIs
- Webapp: component integration tests with mocked Firebase

**Live DB Tests**: Real Firestore/ShelterLuv APIs. Run manually/on-demand only.
- ETL: e2e tests marked with `@pytest.mark.live_db`
- Webapp: Playwright E2E tests with real Firebase project (authenticated tests skip gracefully when auth state missing)

**Test Infrastructure**:
- ETL tests use shared fixtures from `tests/conftest.py` (including `parser` fixture for memo parsing)
- ETL mocks patch functions at point of use (e.g., `main.pipeline.run_etl_process`)
- E2E tests filter harmless 404s (favicon, manifest) and skip authenticated tests when auth state unavailable

Run `node generate_test_report.js` for unified test execution and reporting.

## Performance Testing

See [PERFORMANCE_README.md](PERFORMANCE_README.md) for performance testing entry points:
- ETL: `services/etl_scraper_py/perf/pipeline_performance_test.py`
- Webapp: `services/webapp-react/perf/performance_test.js`
- Orchestrator: `scripts/run_performance_tests.js`

All perf tests use `common/devScriptSafety.js` for safety checks. No second config system.
