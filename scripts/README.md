# Scripts Directory

This directory contains consolidated CLI tools for Firebase operations and performance testing across the ShelterLuv project.

## Tools

### Firebase CLI Operations (`firebase_cli_tool.js`)

Unified tool for Firebase CLI operations and testing.

```bash
# Test Firebase CLI connectivity
node scripts/firebase_cli_tool.js connectivity

# Run data persistence tests (safe for dev/staging only)
node scripts/firebase_cli_tool.js persistence

# Dry run persistence tests (shows what would be done)
node scripts/firebase_cli_tool.js persistence --dry-run

# Verbose output
node scripts/firebase_cli_tool.js connectivity --verbose
```

**Commands:**
- `connectivity` - Test Firebase CLI connectivity and basic operations
- `persistence` - Run data persistence tests (user creation/verification)

**Safety:** Persistence tests automatically enforce dev/staging environment safety checks.

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

All tools include automatic safety checks:

- **Environment validation**: Prevents production environment operations
- **Project validation**: Only allows safe development/staging/demo projects
- **Dry-run support**: Test commands without making changes
- **Verbose logging**: Optional detailed output for debugging

## Legacy Scripts

Previous individual scripts have been consolidated:

- `firebase_cli_data_ops_test.js` → `firebase_cli_tool.js connectivity`
- `firebase_persistence_test.js` → `firebase_cli_tool.js persistence`
- `run_performance_tests.sh` → `run_performance_tests.js`

The old scripts have been removed to prevent confusion and ensure all tools use the unified safety and logging infrastructure.
