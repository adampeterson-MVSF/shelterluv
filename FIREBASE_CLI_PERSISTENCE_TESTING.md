# Firebase CLI Persistence Testing

**⚠️ MANUAL TOOLS ONLY - NOT CI-SAFE**: These scripts perform destructive operations and are for manual testing/debugging only. Never run in automated environments.

**⚠️ SAFETY FIRST**: Never run destructive operations without proper safety checks.

## Single Recommended Workflow

Use **one script** for testing Firebase CLI persistence and connectivity:

### Primary Test: `scripts/firebase_persistence_test.js` (MANUAL ONLY)
Full persistence testing with user creation, verification, and cleanup.

```bash
DEV_SCRIPTS_ENABLED=1 FIREBASE_PROJECT_ID=dev-muttville node scripts/firebase_persistence_test.js
```

**What it tests:**
- User creation via `add_user.js`
- User verification via `check_users.js`
- Firebase CLI connectivity
- Data persistence integrity

**When to use:** Manual debugging and testing only - NEVER in CI.

### Alternative: `scripts/firebase_cli_data_ops_test.js` (MANUAL ONLY)
Basic CLI connectivity and structure verification (no user operations).

```bash
FIREBASE_PROJECT_ID=dev-muttville node scripts/firebase_cli_data_ops_test.js
```

**What it tests:**
- Firebase project access
- Firestore database connectivity
- Index verification

**When to use:** Manual connectivity checks only - NEVER in CI.

### Demo Script: `scripts/firebase_cli_persistence_demo.sh`
Commented shell script for manual debugging - NOT for automated use.

## Manual CLI Commands

Read-only operations (no safety flags needed):
```bash
firebase firestore:databases:list --project dev-muttville
firebase firestore:indexes --project dev-muttville
```

Destructive operations (require safety checks):
```bash
# NEVER run against production projects
# Use dev scripts instead: node add_user.js, node check_users.js
firebase firestore:delete /dogs/doc_id --project dev-muttville
```

**Safety enforcement:** All destructive operations should use the shared safety modules:
- `common/devScriptSafety.js` - Guards for destructive operations
- `common/firebaseSafetyConfig.js` - Project validation
- `common/adminInit.js` - Safe Firebase Admin initialization
