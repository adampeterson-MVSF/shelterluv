#!/usr/bin/env node

/**
 * Test Firebase and Firestore configuration
 * Validates consistency between common/firebaseConfig and configData
 */

const { createAdminApp } = require('../common/firebaseAdmin');
const { getWebFirebaseConfigFromEnv } = require('../common/firebaseConfig');
const { getAdminProjectId } = require('../common/firebaseConfig');
const { getNormalizedProfileMap } = require('../common/configData');

function validateConfigConsistency() {
  console.log('\n🔍 Validating Firebase Config Consistency...');

  try {
    const profileMap = getNormalizedProfileMap();
    const adminProjectId = getAdminProjectId();

    console.log('✅ Config loaded successfully');
    console.log(`   Admin Project ID: ${adminProjectId}`);

    // Check that admin project ID exists in normalized profile map
    const adminProfile = Object.values(profileMap).find(profile => profile.gcp_project === adminProjectId);
    if (!adminProfile) {
      console.error(`❌ Admin project ID ${adminProjectId} not found in configData profile map`);
      return false;
    }

    console.log(`   Admin profile is safe: ${adminProfile.is_safe}`);
    console.log(`   Available profiles: ${Object.keys(profileMap).join(', ')}`);

    return true;
  } catch (error) {
    console.error(`❌ Failed to validate config consistency: ${error.message}`);
    return false;
  }
}

async function testAdminSDK() {
  console.log('\n🔧 Testing Firebase Admin SDK...');
  
  try {
    const projectId = getAdminProjectId();
    console.log(`   Using project ID: ${projectId}`);
    
    const adminApp = createAdminApp();
    console.log('✅ Admin SDK initialized');
    
    return { success: true, adminApp, projectId };
  } catch (error) {
    console.error(`❌ Failed to initialize Admin SDK: ${error.message}`);
    return { success: false, error: error.message };
  }
}

async function testFirestoreConnection(adminApp) {
  console.log('\n🗄️  Testing Firestore Connection...');
  
  try {
    const admin = require('firebase-admin');
    const db = admin.firestore(adminApp);
    
    // Test reading from dogs collection
    console.log('   Attempting to read from "dogs" collection...');
    const dogsRef = db.collection('dogs');
    const snapshot = await dogsRef.limit(1).get();
    
    console.log(`✅ Firestore connection successful`);
    console.log(`   Found ${snapshot.size} document(s) in test query`);
    
    if (snapshot.size > 0) {
      const doc = snapshot.docs[0];
      console.log(`   Sample document ID: ${doc.id}`);
      const data = doc.data();
      console.log(`   Sample document has ${Object.keys(data).length} fields`);
    }
    
    return true;
  } catch (error) {
    console.error(`❌ Firestore connection failed: ${error.message}`);
    console.error(`   Error code: ${error.code || 'unknown'}`);
    if (error.details) {
      console.error(`   Details: ${error.details}`);
    }
    return false;
  }
}

async function testFirestoreDatabases() {
  console.log('\n📊 Testing Firestore Database List...');
  
  try {
    const { execSync } = require('child_process');
    const projectId = getAdminProjectId();
    
    console.log(`   Querying databases for project: ${projectId}`);
    const result = execSync(
      `firebase firestore:databases:list --project=${projectId}`,
      { encoding: 'utf8', stdio: 'pipe' }
    );
    
    console.log('✅ Database list retrieved');
    console.log(result);
    
    return true;
  } catch (error) {
    console.error(`❌ Failed to list databases: ${error.message}`);
    if (error.stdout) console.log('   stdout:', error.stdout);
    if (error.stderr) console.log('   stderr:', error.stderr);
    return false;
  }
}

async function testFirestoreRules() {
  console.log('\n🔒 Checking Firestore Security Rules...');
  
  try {
    const fs = require('fs');
    const path = require('path');
    const rulesPath = path.join(__dirname, '..', 'firestore.rules');
    
    if (fs.existsSync(rulesPath)) {
      const rulesContent = fs.readFileSync(rulesPath, 'utf8');
      console.log('✅ Firestore rules file found');
      
      // Check if rules require authentication
      if (rulesContent.includes('isAuthenticated()')) {
        console.log('   ⚠️  Rules require authentication - users must be logged in');
      }
      
      if (rulesContent.includes('allow read')) {
        console.log('   ✅ Read rules configured');
      }
      
      return true;
    } else {
      console.warn('   ⚠️  firestore.rules file not found');
      return false;
    }
  } catch (error) {
    console.error(`❌ Failed to check rules: ${error.message}`);
    return false;
  }
}

async function main() {
  console.log('🧪 Firebase & Firestore Configuration Test');
  console.log('='.repeat(50));

  const results = {
    configConsistency: false,
    adminSDK: false,
    firestoreConnection: false,
    firestoreDatabases: false,
    firestoreRules: false
  };

  // Test 1: Config consistency
  results.configConsistency = validateConfigConsistency();

  // Test 2: Admin SDK
  const adminResult = await testAdminSDK();
  results.adminSDK = adminResult.success;

  // Test 3: Firestore connection (if admin SDK works)
  if (adminResult.success && adminResult.adminApp) {
    results.firestoreConnection = await testFirestoreConnection(adminResult.adminApp);
  }

  // Test 4: Firestore databases list
  results.firestoreDatabases = await testFirestoreDatabases();

  // Test 5: Firestore rules
  results.firestoreRules = await testFirestoreRules();

  // Summary
  console.log('\n' + '='.repeat(50));
  console.log('📊 Test Summary:');
  console.log(`   Config Consistency:   ${results.configConsistency ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Admin SDK:            ${results.adminSDK ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Firestore Connection: ${results.firestoreConnection ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Firestore Databases: ${results.firestoreDatabases ? '✅ PASS' : '❌ FAIL'}`);
  console.log(`   Firestore Rules:     ${results.firestoreRules ? '✅ PASS' : '❌ FAIL'}`);

  const allPassed = Object.values(results).every(r => r === true);
  console.log(`\n${allPassed ? '✅ All tests passed!' : '❌ Some tests failed'}`);

  process.exit(allPassed ? 0 : 1);
}

if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = { validateConfigConsistency, testAdminSDK, testFirestoreConnection };

