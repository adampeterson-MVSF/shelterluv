# Scripts Directory

This directory contains consolidated CLI tools for Firebase operations and performance testing across the ShelterLuv project.

## Tools

### Firebase CLI Operations (`firebase_cli_tool.js`)

Unified tool for Firebase CLI operations, user management, and data validation.

```bash
# Test Firebase CLI connectivity
node scripts/firebase_cli_tool.js connectivity

# User management
node scripts/firebase_cli_tool.js add-user user@muttville.org uid123 staff
node scripts/firebase_cli_tool.js check-users
node scripts/firebase_cli_tool.js seed-users --dry-run

# Data validation
node scripts/firebase_cli_tool.js check-data --limit 10
node scripts/firebase_cli_tool.js check-data --json

# Run data persistence tests (safe for dev/staging only)
node scripts/firebase_cli_tool.js persistence

# Dry run operations
node scripts/firebase_cli_tool.js add-user user@muttville.org uid123 staff --dry-run
node scripts/firebase_cli_tool.js seed-users --reset --dry-run
```

**Commands:**

**Non-destructive (safe):**
- `connectivity` - Test Firebase CLI connectivity and basic operations (read-only)
- `check-users` - Validate user documents in Firestore users collection (read-only)
- `check-data` - Validate dog documents in Firestore dogs collection (read-only)

**Destructive (requires safety checks):**
- `add-user` - Add or update a user in Firestore
  - ⚠️ **Requires**: `DEV_SCRIPTS_ENABLED=1` and project in `safe_profiles`
  - Use `--dry-run` to preview changes
- `seed-users` - Seed test users with different permission levels
  - ⚠️ **Requires**: `DEV_SCRIPTS_ENABLED=1` and project in `safe_profiles`
  - Use `--dry-run` to preview changes
  - Use `--reset` to delete and re-seed (dangerous!)
- `persistence` - Run data persistence tests (user creation/verification)
  - ⚠️ **Requires**: `DEV_SCRIPTS_ENABLED=1` and project in `safe_profiles`

**Safety:** All destructive commands automatically enforce dev/staging environment safety checks via `common/devScriptSafety.js`. Production projects are blocked.

### Performance Testing (`run_performance_tests.js`)

Unified performance testing across all services.

```bash
# Run all performance tests
node scripts/run_performance_tests.js

# Run specific service tests
node scripts/run_performance_tests.js etl
node scripts/run_performance_tests.js webapp

# Continue testing even if one service fails
node scripts/run_performance_tests.js --continue-on-error

# Verbose output
node scripts/run_performance_tests.js --verbose
```

**Services:**
- `etl` - ETL pipeline performance (10 dogs by default)
- `webapp` - Webapp performance and responsiveness

**Safety:** Automatically prevents running against production environments.

### Shared Library (`lib/firebaseTools.js`)

Common utilities used by CLI tools:

- `runCommand()` - Execute shell commands with error handling
- `runFirebaseCommand()` - Execute Firebase CLI commands with safety checks
- `runPersistenceScenario()` - Run test scenarios with logging
- `parseBasicArgs()` - Parse common CLI arguments
- `formatScenarioSummary()` - Format test result summaries

## Development

### Adding New Commands

To add a new command to `firebase_cli_tool.js`:

1. Add the command definition to the `COMMANDS` object
2. Implement the handler function
3. Update the help text

### Adding New Services

To add a new service to performance testing:

1. Add the service configuration to the `SERVICES` object in `run_performance_tests.js`
2. Ensure the service has appropriate performance test scripts

## Safety

All tools include automatic safety checks using unified configuration from `common/config.json`:

- **Environment validation**: Prevents production environment operations
- **Project validation**: Only allows safe projects listed in `config.json` `safe_profiles`
- **Unified config**: All project IDs and safe profiles read from `common/config.json` (never hardcoded)
- **Dry-run support**: Test commands without making changes
- **Verbose logging**: Optional detailed output for debugging

**Configuration Source**: `common/config.json` is the single source of truth for:
- Environment profiles (`env_profiles`)
- Python environment profiles (`python_env_profiles`) 
- Safe profiles list (`safe_profiles`)
- User roles (`roles`)

## Legacy Scripts

Previous individual scripts have been consolidated:

- `firebase_cli_data_ops_test.js` → `firebase_cli_tool.js connectivity`
- `firebase_persistence_test.js` → `firebase_cli_tool.js persistence`
- `run_performance_tests.sh` → `run_performance_tests.js`
- `add_user.js` → `firebase_cli_tool.js add-user`
- `check_users.js` → `firebase_cli_tool.js check-users`
- `check_firestore_data.js` → `firebase_cli_tool.js check-data`
- `seed_test_users.js` → `firebase_cli_tool.js seed-users`

The old scripts have been removed to prevent confusion and ensure all tools use the unified safety and logging infrastructure.

## Test Artifacts

### Regenerating `artifacts/TESTS.txt`

The `artifacts/TESTS.txt` file contains a human-readable summary of test results and is automatically generated when running tests:

```bash
# Run all tests and generate artifacts
npm test

# Or run tests with the test runner directly
node -e "require('./common/testRunner').runAllTests().then(results => { require('./common/testRunner').writeTestArtifacts(results); })"
```

The file includes:
- Test commands executed for each service (webapp, ETL, E2E)
- Exit codes and stderr output for debugging failures
- Summary of overall test status

**Note**: `artifacts/TESTS.txt` is generated content - do not edit manually. It serves as a record of test execution for CI/CD and debugging.
