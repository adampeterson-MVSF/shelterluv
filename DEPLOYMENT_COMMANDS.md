# 🚀 Deployment Commands - Muttville App

**⚠️ PRODUCTION SAFETY**: Never deploy to production without verifying project IDs and safety checks. Production projects: `muttville-prod`, `muttville-production`.

---

## Pre-Deploy Checklist

**Complete these steps before any deployment:**

### 1. Run Full Test Suite
```bash
# Run all tests and generate report
node generate_test_report.js

# Should exit with code 0 (all tests pass)
```

### 2. Verify Schema Artifacts
```bash
# Regenerate and verify schema artifacts are current
npm run schema:gen && npm run schema:check

# Should exit with code 0 (no git diff)
```

### 3. Test ETL Pipeline (Dry Run)
```bash
cd services/etl-scraper-py

# Dry run with small dataset
python run_etl_local.py --limit 3 --dry-run

# Should complete without errors
```

### 4. Environment Verification
- [ ] `FIREBASE_PROJECT_ID` points to correct environment (safe: `dev-muttville`, `staging-muttville`, `muttville-demo`)
- [ ] `GCP_PROJECT_ID` matches Firebase project (never `muttville-prod` or `muttville-production`)
- [ ] `GOOGLE_CLOUD_PROJECT` set correctly for ETL
- [ ] All environment variables validated via `common/firebaseSafetyConfig.js`

### 5. Safety Checks (SAFE - read-only validation)
- [ ] Run safety validation: `node check_firestore_data.js` (should exit 0)
- [ ] Run user validation: `node check_users.js` (should exit 0)
- [ ] Verify no production projects in environment variables

### 6. Manual Smoke Tests
- [ ] Webapp builds successfully: `cd services/webapp-react && npm run build`
- [ ] ETL credentials valid: `cd services/etl-scraper-py && python check_credentials.py`
- [ ] Schema validation passes on sample data

---

## Golden Path Deployment

### 1. Deploy ETL Cloud Function (SAFE - read-only deployment)
```bash
cd services/etl-scraper-py

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
```

### 2. Deploy Webapp to Firebase Hosting (SAFE - static hosting deployment)
```bash
cd services/webapp-react

firebase use "$FIREBASE_PROJECT_ID"
npm run build
firebase deploy --only hosting --project="$FIREBASE_PROJECT_ID"
```

### 3. Trigger ETL Run (SAFE - normal data pipeline operation)
```bash
FUNCTION_URL=$(gcloud functions describe etl-scraper \
  --project="$GCP_PROJECT_ID" --format="value(httpsTrigger.url)")

curl -X POST "$FUNCTION_URL" \
  -H "Authorization: Bearer $(gcloud auth print-identity-token)"
```

---

## Advanced / Emergency Operations

### Rollback Webapp
```bash
firebase hosting:rollback --project="$FIREBASE_PROJECT_ID"
```

### 🚨 EMERGENCY ETL STOP (DESTRUCTIVE)
```bash
# ⚠️ IRREVERSIBLE: Deletes the ETL Cloud Function
# Only if ETL is corrupting production data and cannot be stopped otherwise
gcloud functions delete etl-scraper --project="$GCP_PROJECT_ID"
```

### 🚨 EMERGENCY DATA WIPE (DESTRUCTIVE)
```bash
# ⚠️ IRREVERSIBLE: Deletes ALL Firestore data in the project
# Only use if data is hopelessly corrupted and you have backups
firebase firestore:bulkdelete --all-collections --project="$GCP_PROJECT_ID" --yes
```

### Check ETL Logs
```bash
gcloud logging read \
  "resource.type=cloud_function AND resource.labels.function_name=etl-scraper" \
  --project="$GCP_PROJECT_ID" --limit=10
```
