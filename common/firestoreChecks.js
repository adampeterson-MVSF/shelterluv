/**
 * Centralized Firestore data validation and checking logic.
 * Extracted from check_firestore_data.js for reusability.
 */

const { getRequiredFieldsFromSchema } = require('./schemaArtifacts');

/**
 * Check the dogs collection for data integrity and schema compliance.
 * Thin wrapper over schemaArtifacts + firestore access.
 * @param {Object} db - Firestore database instance
 * @param {Object} options - Options for the check
 * @param {number} options.sampleLimit - Maximum number of documents to sample (default: 3)
 * @param {boolean} options.json - Output machine-parseable JSON instead of formatted text
 * @returns {Object|string} Check results object or JSON string if json=true
 */
async function checkDogsCollection(db, options = {}) {
  const { sampleLimit = 3, json = false } = options;
  const results = {
    totalDocuments: 0,
    availableDogs: 0,
    sampleDocuments: [],
    schemaErrors: [],
    success: true
  };

  try {
    console.log('🔍 Checking dogs collection in Firestore...');
    const dogsCollection = db.collection('dogs');
    const dogsSnapshot = await dogsCollection.get();

    results.totalDocuments = dogsSnapshot.size;
    console.log(`📊 Found ${results.totalDocuments} documents in dogs collection`);

    if (results.totalDocuments > 0) {
      // Sample documents
      const sampleSize = Math.min(sampleLimit, results.totalDocuments);
      const docsArray = dogsSnapshot.docs.slice(0, sampleSize);

      results.sampleDocuments = docsArray.map(doc => ({
        id: doc.id,
        data: doc.data()
      }));

      // Count available dogs
      const availableDogsQuery = dogsCollection.where('Status', '==', 'AVAILABLE');
      const availableSnapshot = await availableDogsQuery.get();
      results.availableDogs = availableSnapshot.size;

      // Schema validation
      const schemaErrors = validateSchemaCompliance(dogsSnapshot.docs);
      results.schemaErrors = schemaErrors;

      if (schemaErrors.length > 0) {
        results.success = false;
        console.error('\n❌ ERROR: Found documents missing ETL-required fields!');
        console.error('This indicates ETL schema contract violations.');
      } else {
        console.log('✅ All documents have required ETL fields.');
      }
    } else {
      console.log('📭 No dogs found in collection');
    }

  } catch (error) {
    results.success = false;
    console.error('❌ Error checking Firestore:', error.message);
    if (error.code) {
      console.error('Error code:', error.code);
    }
  }

  return json ? JSON.stringify(results, null, 2) : results;
}

/**
 * Validate that documents comply with the required schema fields.
 * @param {Array} documents - Array of Firestore document snapshots
 * @returns {Array} Array of validation errors
 */
function validateSchemaCompliance(documents) {
  const requiredFields = getRequiredFieldsFromSchema();
  const errors = [];

  documents.forEach((doc) => {
    const data = doc.data();
    requiredFields.forEach(field => {
      if (!data.hasOwnProperty(field) || data[field] === null || data[field] === undefined) {
        errors.push({
          documentId: doc.id,
          missingField: field
        });
      }
    });
  });

  return errors;
}

/**
 * Generate a human-readable summary of check results.
 * @param {Object} results - Results from checkDogsCollection
 * @returns {string} Formatted summary
 */
function formatCheckSummary(results) {
  let summary = `Dogs collection check results:\n`;
  summary += `- Total documents: ${results.totalDocuments}\n`;
  summary += `- Available dogs: ${results.availableDogs}\n`;

  if (results.schemaErrors.length > 0) {
    summary += `- Schema errors: ${results.schemaErrors.length}\n`;
    results.schemaErrors.forEach(error => {
      summary += `  • Doc ${error.documentId} missing ${error.missingField}\n`;
    });
  } else {
    summary += `- Schema compliance: ✅ All good\n`;
  }

  return summary;
}

module.exports = {
  checkDogsCollection,
  validateSchemaCompliance,
  formatCheckSummary
};
