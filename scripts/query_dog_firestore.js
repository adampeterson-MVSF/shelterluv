#!/usr/bin/env node

/**
 * Query a specific dog document from Firestore using Admin SDK
 * Usage: node scripts/query_dog_firestore.js <dog-id>
 */

const { getAdminApp } = require('../common/adminInit');
const { assertSafeForDestructiveOps } = require('../common/devScriptSafety');
const { getAdminProjectId } = require('../common/firebaseConfig');

async function queryDog(id) {
  try {
    console.log(`\n🔍 Querying dog document: ${id}\n`);

    // Safety check - ensure we're on a safe project
    const projectId = getAdminProjectId();
    assertSafeForDestructiveOps(projectId);

    // Use shared admin app initialization
    const adminApp = getAdminApp();
    const db = adminApp.firestore();

    console.log(`✅ Connected to Firestore project: ${projectId}\n`);
    
    // Get the document
    const docRef = db.collection('dogs').doc(id);
    const docSnap = await docRef.get();
    
    if (!docSnap.exists) {
      console.log('❌ Document does not exist');
      return;
    }
    
    console.log('✅ Document exists\n');
    
    const data = docSnap.data();
    
    // Show document structure
    console.log('📄 Document Structure:');
    console.log('='.repeat(60));
    console.log(`Document ID: ${docSnap.id}`);
    console.log(`Fields: ${Object.keys(data).length}`);
    console.log('\nField List:');
    Object.keys(data).sort().forEach(key => {
      const value = data[key];
      const type = Array.isArray(value) ? 'array' : typeof value;
      const preview = Array.isArray(value) 
        ? `[${value.length} items]`
        : typeof value === 'string' && value.length > 50
        ? `${value.substring(0, 50)}...`
        : value;
      console.log(`  ${key}: ${type} = ${JSON.stringify(preview)}`);
    });
    
    // Check required fields
    console.log('\n🔍 Required Fields Check:');
    console.log('='.repeat(60));
    const requiredFields = [
      'Internal-ID',
      'ID',
      'Name',
      'Status',
      'AgeYears',
      'AgeDisplay',
      'IsInCustody',
      'IsAvailableForAdoption',
      'IsHospice',
      'IsEventDog',
      'PersonalityNotes',
      'IntakeNotes',
      'MedicalNotes'
    ];
    
    const missing = requiredFields.filter(field => data[field] === undefined);
    const present = requiredFields.filter(field => data[field] !== undefined);
    
    console.log(`✅ Present (${present.length}/${requiredFields.length}):`);
    present.forEach(field => {
      const value = data[field];
      const preview = typeof value === 'string' && value.length > 30
        ? `${value.substring(0, 30)}...`
        : value;
      console.log(`   ${field}: ${JSON.stringify(preview)}`);
    });
    
    if (missing.length > 0) {
      console.log(`\n❌ Missing (${missing.length}):`);
      missing.forEach(field => console.log(`   ${field}`));
    }
    
    // Show sample data
    console.log('\n📋 Sample Data:');
    console.log('='.repeat(60));
    console.log(`Name: ${data.Name || 'N/A'}`);
    console.log(`Status: ${data.Status || 'N/A'}`);
    console.log(`AgeDisplay: ${data.AgeDisplay || 'N/A'}`);
    console.log(`Breed: ${data.Breed || 'N/A'}`);
    console.log(`Size: ${data.Size || 'N/A'}`);
    console.log(`Location: ${data.Location || 'N/A'}`);
    console.log(`CaseManager: ${data.CaseManager || 'N/A'}`);
    
    // Check ETL contract fields
    console.log('\n🔍 ETL Contract Fields:');
    console.log('='.repeat(60));
    const etlFields = [
      'AgeYears',
      'AgeDisplay',
      'IsInCustody',
      'IsAvailableForAdoption',
      'IsHospice',
      'IsEventDog'
    ];
    
    etlFields.forEach(field => {
      const value = data[field];
      const status = value !== undefined ? '✅' : '❌';
      console.log(`${status} ${field}: ${JSON.stringify(value)}`);
    });
    
    console.log('\n' + '='.repeat(60));
    console.log('✅ Document query complete');
    
  } catch (error) {
    console.error('❌ Error querying document:', error.message);
    console.error(error);
    process.exit(1);
  }
}

// Get dog ID from command line
const dogId = process.argv[2];

if (!dogId) {
  console.error('Usage: node scripts/query_dog_firestore.js <dog-id>');
  console.error('Example: node scripts/query_dog_firestore.js 212143233');
  process.exit(1);
}

queryDog(dogId).then(() => {
  process.exit(0);
}).catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});

