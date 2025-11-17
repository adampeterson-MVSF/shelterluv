# Common Data Schemas

This directory contains JSON Schema definitions that serve as the single source of truth for data structures across all services in the monorepo.

## One Schema → Many Artifacts

**The `dog.schema.json` file is the ONLY place where dog data structure is defined.** All other representations are automatically generated from this single source of truth.

**🚫 NEVER EDIT GENERATED FILES BY HAND** - They will be overwritten by `npm run schema:gen`.

### Generated Artifacts (Auto-generated from `dog.schema.json`)
- `common/statusMapping.js` - Status display constants and terminal status helpers
- `common/sizeConfig.js` - Size ordering and normalization functions
- `services/webapp-react/src/types/Dog.types.ts` - TypeScript interfaces for frontend

### CI Enforcement
```bash
# This command runs in CI and fails if anyone manually edited generated files
npm run schema:check
```

## Schema Lifecycle

When making changes to data structures, follow this workflow:

1. **Edit Schema**: Modify `dog.schema.json` to add/remove/change fields
2. **Regenerate Artifacts**: Run `npm run schema:gen` from repository root to update all derived files
3. **Update Code**: Modify ETL and frontend code to handle new/changed fields
4. **Test**: Run full test suites to ensure compatibility
5. **Deploy**: Coordinate deployment of schema changes across all services

**Automation**:
```bash
# Regenerate all schema-derived files
npm run schema:gen

# CI check - fails if generated files have been manually modified
npm run schema:check
```

## Usage

### Python ETL Service
```python
import json
import os
from jsonschema import Draft7Validator

# Load schema once at module import
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'common', 'schemas', 'dog.schema.json')
with open(SCHEMA_PATH) as f:
    DOG_SCHEMA = json.load(f)

DOG_VALIDATOR = Draft7Validator(DOG_SCHEMA)

# Validate dog record before writing to database
errors = sorted(DOG_VALIDATOR.iter_errors(dog_dict), key=lambda e: e.path)
if errors:
    raise EtlError(f"Schema validation failed: {errors[0].message}")
```

### JavaScript/TypeScript Services
Frontend services mirror the schema through `src/types/Dog.types.ts` and `normalizeDog()` function in `dogNormalize.js` for consistent data access. **No runtime validation yet; schema drives TypeScript/docs only.**

**Type Generation**:
```bash
# Regenerate Dog.types.ts from schema (requires json-schema-to-typescript)
cd services/webapp-react
npm run generate:types

# Or run directly:
npx json-schema-to-typescript ../../common/schemas/dog.schema.json src/types/Dog.types.ts
```

## Invariants

**Statuses are enumerated here; all code must treat this file as authoritative.**

- Status values in `dog.schema.json` are the single source of truth
- All status interpretation (display, terminal status, etc.) derives from this schema
- If you change status enums, run `npm run schema:gen` and fix any breakage

**Schema changes require regeneration of all artifacts:**

```bash
# After modifying dog.schema.json
npm run schema:gen
```

This updates `statusMapping.js`, `sizeConfig.js`, and TypeScript types.

## Schemas

### `dog.schema.json` (v1.2.0)

Complete schema for dog data including ShelterLuv API fields, scraped data, derived flags, and enriched foster information.

**Schema Version History**:
- **v1.2.0** (Current): Strengthened required fields and formalized structured notes
  - **BREAKING**: Made ETL-computed fields required: `AgeYears`, `AgeDisplay`, `IsInCustody`, `IsAvailableForAdoption`, `IsHospice`, `IsEventDog`
  - Added structured notes fields: `PersonalityNotes`, `IntakeNotes`, `MedicalNotes` (parsed from `MemosRawHTML`)
  - Marked `Age` field as deprecated (use `AgeYears`/`AgeDisplay`)
- **v1.1.0**: Added foster enrichment fields, derived flags, and structured notes
  - New fields: `Stage`, `Weight`, `FosterName`, `FosterPhone`, `FosterEmail`, `IsHospice`, `IsEventDog`
- **v1.0.0**: Initial schema with core ShelterLuv API and scraped fields

**Field Sources**:
- `[API]`: Direct from ShelterLuv API (`get_animals()`)
- `[SCRAPE]`: Web scraped from ShelterLuv website
- `[DERIVED]`: Computed by ETL pipeline from other data sources

**Key Features**:
- **Foster Enrichment**: `FosterName`, `FosterPhone`, `FosterEmail` populated by joining animal events (Foster/FosterReturn) with people records
- **Derived Flags**: `IsHospice` and `IsEventDog` computed from event history and notes
- **Structured Notes**: `PersonalityNotes`, `IntakeNotes`, `MedicalNotes` parsed from raw memos using keyword-based categorization
- **Strict Validation**: `"additionalProperties": false` catches accidental field additions

## Validation Rules

**Python ETL Service**: Validates all dog records against `dog.schema.json` using `jsonschema` library before writing to Firestore.

**Frontend Services**: Do not currently validate against schema. Firestore provides basic type safety.

Schemas are versioned. Breaking changes require coordinated updates to ETL validation and frontend components.

## How to Debug Schema Drift Test Failures

When schema synchronization tests fail, follow these steps:

### 1. Identify the Drift

**Error message will indicate:**
- Missing status in `STATUS_MAPPING`
- Missing size in `SIZE_ORDER`
- Checksum mismatch between schema and artifacts

### 2. Check What Changed

```bash
# View schema changes
git diff common/schemas/dog.schema.json

# Check current schema checksum
node -e "const core = require('./schemaArtifactsCore'); const fs = require('fs'); const schema = fs.readFileSync('common/schemas/dog.schema.json', 'utf8'); console.log('Checksum:', core.generateSchemaChecksum(schema));"
```

### 3. Regenerate Artifacts

```bash
# Regenerate all artifacts from schema
npm run schema:gen

# Verify artifacts are in sync
npm run schema:check
```

### 4. Common Issues

**Status enum changed but STATUS_MAPPING not updated:**
- Run `npm run schema:gen` to regenerate `common/statusMapping.js`
- Commit the generated file

**Size enum changed but SIZE_ORDER not updated:**
- Run `npm run schema:gen` to regenerate `common/sizeConfig.js`
- Verify size order matches schema enum order

**Checksum mismatch:**
- Someone manually edited a generated file
- Run `npm run schema:gen` to regenerate
- Never edit `statusMapping.js`, `sizeConfig.js`, or `Dog.types.ts` manually

### 5. Verify Fix

```bash
# Run schema sync tests
npm run schema:check

# Run full test suite
node generate_test_report.js
```
