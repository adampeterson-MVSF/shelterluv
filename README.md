# Muttville App Monorepo

A polyglot monorepo containing services for Muttville's dog adoption platform.

## Source of Truth

All services derive their data contracts and business logic from these canonical sources:

- **Dog Schema**: `common/schemas/dog.schema.json` - Complete JSON Schema for dog data structures
- **Status Semantics**: `common/statusMapping.js` - Status display logic and terminal status definitions
- **User Roles**: `common/userRoles.js` - Valid roles and role validation logic

All dog data in ETL + webapp must conform to `common/schemas/dog.schema.json`.

## Dog Data Runtime Contract

The ETL pipeline guarantees these fields are always present in Firestore `dogs` collection:

**Required Fields (always present):**
- `Internal-ID`, `ID`, `Name` - ShelterLuv identifiers
- `Status` - Current adoption status
- `AgeYears`, `AgeDisplay` - Age in canonical numeric/string format
- `IsInCustody`, `IsAvailableForAdoption`, `IsHospice`, `IsEventDog` - Boolean flags

**ETL-Computed Fields (always present):**
- `PersonalityNotes`, `IntakeNotes`, `MedicalNotes` - Categorized memo content (empty strings if no memos)
- `IsInCustody`, `IsAvailableForAdoption`, `IsHospice`, `IsEventDog` - Computed boolean flags

**ETL-Conditional Fields (present when applicable):**
- `FosterName`, `FosterPhone`, `FosterEmail` - Foster contact info (role-restricted, only when dog is in active foster care)

**Optional Fields (may be undefined):**
- `Photos`, `Description` - Public display content
- `CaseManager`, `AdoptionCategory`, `MedicalCategory`, `BehaviorCategory` - ShelterLuv profile data
- `Treatments` - Medical treatment history
- `ScrapeError` - Error message if scraping failed

## Contracts

**Dog Shape**: Defined in `common/schemas/dog.schema.json` (JSON Schema Draft 7). All dog data must conform to this schema with `"additionalProperties": false`.

**Status Enums**: `["AVAILABLE", "ADOPTED", "PENDING", "HOLD", "UNKNOWN"]` - Owned by schema, mapped to UI display in `common/statusMapping.js`.

**Size Enums**: `["Small", "Medium", "Large", "X-Large", "UNKNOWN"]` - Owned by schema, ordered for display in `common/sizeConfig.js`.

**User Roles**: `["viewer", "closer", "staff"]` - Owned by `common/userRoles.js`, enforced in AuthContext and repositories.

## Generated Files - DO NOT EDIT

These files are auto-generated from `common/schemas/dog.schema.json` via `npm run schema:gen`:

- `services/webapp-react/src/types/Dog.types.ts` - TypeScript type definitions
- `common/statusMapping.js` - Status display mappings and terminal status logic
- `common/sizeConfig.js` - Size category ordering and display logic

Edit the JSON schema and regenerate; never modify these files directly.

## Services

### `/services/webapp-react`
React frontend application with Google SSO authentication for dog browsing.

**Entrypoints:**
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm test` - Run unit tests
- `npm run test:e2e` - Run E2E tests

See [services/webapp-react/README.md](services/webapp-react/README.md) for setup, features, and development.

### `/services/etl-scraper-py`
Python ETL pipeline that extracts dog data from ShelterLuv API (including memos), processes with concurrent scraping, and loads into Firestore.

**Entrypoints:**
- `python run_etl_local.py` - Run ETL locally (development)
- `python clear_and_run_etl.py` - Clear existing data and run full ETL (development)
- `python main.py` - CLI interface for production deployments

See [services/etl-scraper-py/README.md](services/etl-scraper-py/README.md) for ETL pipeline details and development.

## Common

### `/common/schemas`
Language-neutral JSON Schema definitions for data validation across services. The single source of truth for all dog data structures.

### `/scratch`
Development artifacts not used by any service (e.g., `muttville_exploration.json`).

## Security

**Authentication**: Google SSO with @muttville.org domain restriction. Firestore read access requires authentication.

**Data Security**: ETL pipeline (admin SDK only) writes to Firestore. Client apps are read-only. All ShelterLuv credentials via GCP Secret Manager.

**Validation**: All dog data validated against `common/schemas/dog.schema.json` (JSON Schema Draft 7) with strict `"additionalProperties": false`.

**Repository Policy**: No secrets in source. Debug scripts must use `.env` or Secret Manager. Never run ETL debug scripts against prod.

**Debug scripts**: Python/Node debug scripts are manual/local-only tools, not CI. Do not commit real credentials into these scripts.

## Schema Contract

**Single source of truth**: ETL must produce docs matching `common/schemas/dog.schema.json`. Webapp's `normalizeDog` will **throw** on schema violations.

**Enforcement tools**: `check_firestore_data.js` + `common/firestoreChecks.js` are the tools to enforce this contract.

**ETL owns semantics**: ETL produces complete, schema-compliant data. Webapp trusts ETL and will **hard-fail** on schema violations.

## 🚀 Quick Start

Choose your development path in **[QUICK_START.md](QUICK_START.md)**:

- **Webapp Development Only**: Frontend work without ETL access
- **ETL Development Only**: Backend pipeline development
- **Full Stack Development**: Both frontend and backend

### Setup Overview

1. Clone this repository
2. Follow the appropriate path in **[QUICK_START.md](QUICK_START.md)**
3. Configure Google Cloud Project and Firebase
4. Deploy services (see **[DEPLOYMENT_COMMANDS.md](DEPLOYMENT_COMMANDS.md)**)

See [PERFORMANCE_README.md](PERFORMANCE_README.md) for performance testing and monitoring.

## Testing

- **ETL**: pytest in `services/etl-scraper-py/tests/`
- **Frontend**: Vitest (unit) + Playwright (E2E) in `services/webapp-react/`
- **Coverage**: Schema validation, auth flows, component rendering, ETL pipeline phases

### Testing & CI

**Unit Tests**: Pure functions, no I/O. Run in CI always.
- ETL: pytest unit tests (no network/Firestore)
- Webapp: Vitest unit tests

**Integration Tests**: Component interactions, mocked I/O. Run in CI always.
- ETL: pipeline integration tests with mocked APIs
- Webapp: component integration tests with mocked Firebase

**Live DB Tests**: Real Firestore/ShelterLuv APIs. Run manually/on-demand only.
- ETL: e2e tests marked with `@pytest.mark.live_db`
- Webapp: Playwright E2E tests with real Firebase project

Run `node generate_test_report.js` for unified test execution and reporting.

## Architecture in One Page

```
ETL (Python) → Firestore (dogs/users collections) → React Webapp
     ↓              ↓                              ↓
ShelterLuv API  Dog Schema Contract          Authenticated UI
(normalize +    (required/optional fields,   (trusts ETL and will
 enrich + scrape) status/size enums)          **hard-fail** on schema violations)
```

**ETL owns semantics; webapp trusts ETL and will **hard-fail** on schema violations.**

**Schema is SSoT - All status/size semantics flow from `common/schemas/dog.schema.json`.**

### Data Flow Contract

- **ETL Pipeline**: Python extract/transform/load pipeline with concurrent ShelterLuv scraping. Owns all dog data semantics and guarantees Firestore contract compliance.
- **Data Store**: Firebase Firestore (dogs collection + users collection) - single source of truth for runtime data
- **Frontend**: React app with Firebase Auth (Google SSO) consuming Firestore data (read-only). Trusts ETL to provide complete, schema-compliant data without defensive defaults.
- **Data Definition**: JSON Schema in `/common/schemas` (single source of truth for all services)
- **Schema Artifacts**: Auto-generated TypeScript types and UI mappings from schema via `npm run schema:gen`
- **Validation**: Runtime schema validation in ETL and React components with `"additionalProperties": false`
- **Hosting**: Firebase Hosting serves built React app

### Environment Variables

**Webapp/Browser (Vite):**
- `VITE_FIREBASE_API_KEY`, `VITE_FIREBASE_AUTH_DOMAIN`, `VITE_FIREBASE_PROJECT_ID`, `VITE_FIREBASE_STORAGE_BUCKET`, `VITE_FIREBASE_MESSAGING_SENDER_ID`, `VITE_FIREBASE_APP_ID`
- **Note:** Vite requires `VITE_` prefix for variables accessible in browser code

**Admin/Node scripts:**
- `FIREBASE_PROJECT_ID` - Core project identifier for admin operations
- `DEV_SCRIPTS_ENABLED=1` - Required for destructive dev operations

**ETL Pipeline (Python):**
- `SHELTERLUV_USER`, `SHELTERLUV_PASS`, `SHELTERLUV_API_KEY` - ShelterLuv API credentials
- `GCP_PROJECT` - Google Cloud project ID
- `DOGS_COLLECTION` - Firestore collection name
- `E2E_LIVE_DB` - Use live database for E2E tests
- `DISABLE_SECRET_MANAGER` - Skip GCP Secret Manager for local development

### Firestore Contract - Hard Requirements

ETL guarantees these fields are always present and schema-compliant in Firestore `dogs` docs:

**Required Fields (always present, no defensive defaults):**
- `Internal-ID`, `ID`, `Name` - ShelterLuv identifiers
- `Status` - Current adoption status
- `AgeYears`, `AgeDisplay` - Age in canonical numeric/string format
- `IsInCustody`, `IsAvailableForAdoption`, `IsHospice`, `IsEventDog` - Boolean flags
- `PersonalityNotes`, `IntakeNotes`, `MedicalNotes` - Categorized memo content

**ETL-Conditional Fields (may be undefined, no defensive defaults):**
- `FosterName`, `FosterPhone`, `FosterEmail` - Foster contact info (role-restricted, only when dog is in active foster care)

**Optional Fields (may be undefined, no defensive defaults):**
- `Photos`, `Description` - Public display content
- `CaseManager`, `AdoptionCategory`, `MedicalCategory`, `BehaviorCategory` - ShelterLuv profile data
- `Treatments` - Medical treatment history
- `ScrapeError` - Error message if scraping failed

### How Dog Data Flows

ShelterLuv API (animals, events, people, memos) → ETL Extract → Transform (normalize + enrich + scrape) → Load to Firestore → React Components (authenticated access)

**Status**: ✅ **Production-ready** - ETL pipeline successfully tested with real ShelterLuv data.
