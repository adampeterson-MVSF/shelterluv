/**
 * Centralized Firestore data validation and checking logic.
 * Extracted from check_firestore_data.js for reusability.
 */

const { getDogSchema } = require('./schemaArtifacts');

/**
 * Check the dogs collection for data integrity and schema compliance.
 * Pure function - no side effects, no logging.
 * @param {Object} db - Firestore database instance
 * @param {Object} options - Options for the check
 * @param {number} options.sampleLimit - Maximum number of documents to sample (default: 3)
 * @returns {Promise<Object>} Check results object
 */
async function checkDogsCollection(db, options = {}) {
  const { sampleLimit = 3 } = options;
  const results = {
    totalDocuments: 0,
    availableDogs: 0,
    sampleDocuments: [],
    schemaErrors: [],
    success: true
  };

  try {
    const dogsCollection = db.collection('dogs');
    const dogsSnapshot = await dogsCollection.get();

    results.totalDocuments = dogsSnapshot.size;

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
      }
    }

  } catch (error) {
    results.success = false;
    results.error = {
      message: error.message,
      code: error.code
    };
  }

  return results;
}

/**
 * Validate that documents comply with the required schema fields.
 * @param {Array} documents - Array of Firestore document snapshots
 * @returns {Array} Array of validation errors
 */
function validateSchemaCompliance(documents) {
  const schema = getDogSchema();
  const requiredFields = schema.required || [];
  const errors = [];

  documents.forEach((doc) => {
    const data = doc.data();

    // Check required fields
    requiredFields.forEach(field => {
      if (!data.hasOwnProperty(field) || data[field] === null || data[field] === undefined) {
        errors.push({
          documentId: doc.id,
          missingField: field
        });
      }
    });

    // Additional type validation for AgeYears (potential string vs number confusion)
    if (data.hasOwnProperty('AgeYears')) {
      const ageYears = data.AgeYears;
      if (typeof ageYears === 'string') {
        errors.push({
          documentId: doc.id,
          field: 'AgeYears',
          expectedType: 'number',
          actualType: 'string',
          value: ageYears
        });
      } else if (typeof ageYears !== 'number') {
        errors.push({
          documentId: doc.id,
          field: 'AgeYears',
          expectedType: 'number',
          actualType: typeof ageYears,
          value: ageYears
        });
      }
    }
  });

  return errors;
}

/**
 * Generate a structured summary of check results (counts + examples).
 * Pure function - returns structured data, not formatted strings.
 * @param {Object} results - Results from checkDogsCollection
 * @returns {Object} Summary object with counts and example errors
 */
function getCheckSummary(results) {
  const errorCount = results.schemaErrors.length;
  const exampleErrors = results.schemaErrors.slice(0, 5); // First 5 examples

  return {
    totalDocuments: results.totalDocuments,
    availableDogs: results.availableDogs,
    schemaErrorCount: errorCount,
    exampleErrors: exampleErrors,
    hasErrors: errorCount > 0,
    success: results.success
  };
}

/**
 * Generate a human-readable summary of check results.
 * @param {Object} results - Results from checkDogsCollection
 * @returns {string} Formatted summary
 */
function formatCheckSummary(results) {
  const summary = getCheckSummary(results);
  let output = `Dogs collection check results:\n`;
  output += `- Total documents: ${summary.totalDocuments}\n`;
  output += `- Available dogs: ${summary.availableDogs}\n`;

  if (summary.hasErrors) {
    output += `- Schema errors: ${summary.schemaErrorCount}\n`;
    summary.exampleErrors.forEach(error => {
      output += `  • Doc ${error.documentId} missing ${error.missingField}\n`;
    });
    if (summary.schemaErrorCount > summary.exampleErrors.length) {
      output += `  ... and ${summary.schemaErrorCount - summary.exampleErrors.length} more\n`;
    }
  } else {
    output += `- Schema compliance: ✅ All good\n`;
  }

  return output;
}

/**
 * Generate machine-readable JSON output of check results.
 * @param {Object} results - Results from checkDogsCollection
 * @returns {string} JSON string
 */
function formatCheckJson(results) {
  return JSON.stringify(results, null, 2);
}

module.exports = {
  checkDogsCollection,
  validateSchemaCompliance,
  getCheckSummary,
  formatCheckSummary,
  formatCheckJson
};
