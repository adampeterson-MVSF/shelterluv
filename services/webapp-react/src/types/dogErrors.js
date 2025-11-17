/**
 * Structured error codes for dog repository operations.
 * Replaces string-based error handling with typed error objects.
 */

/**
 * Error codes for dog repository operations
 */
export const DOG_ERROR_CODES = {
  // Schema validation errors
  MISSING_REQUIRED_FIELD: 'MISSING_REQUIRED_FIELD',
  MISSING_ETL_CONTRACT_FIELDS: 'MISSING_ETL_CONTRACT_FIELDS',

  // Repository operation errors
  FIRESTORE_CONNECTION_ERROR: 'FIRESTORE_CONNECTION_ERROR',
  DOCUMENT_NOT_FOUND: 'DOCUMENT_NOT_FOUND'
};

/**
 * Structured error object for dog operations
 */
export class DogError extends Error {
  constructor(code, message, details) {
    super(message);
    this.name = 'DogError';
    this.code = code;
    this.details = details;
  }
}

/**
 * Creates a MISSING_REQUIRED_FIELD error
 */
export function createMissingRequiredFieldError(docId, fieldName) {
  return new DogError(
    DOG_ERROR_CODES.MISSING_REQUIRED_FIELD,
    `Dog document ${docId} missing required ${fieldName} field`,
    { docId, fieldName }
  );
}

/**
 * Creates a MISSING_ETL_CONTRACT_FIELDS error
 */
export function createMissingETLFieldsError(docId, missingFields) {
  return new DogError(
    DOG_ERROR_CODES.MISSING_ETL_CONTRACT_FIELDS,
    `Dog document ${docId} missing ETL-required fields: ${missingFields.join(', ')}. ETL schema contract violation - required fields must always be present.`,
    { docId, missingFields }
  );
}

/**
 * Creates a FIRESTORE_CONNECTION_ERROR
 */
export function createFirestoreError(originalError) {
  return new DogError(
    DOG_ERROR_CODES.FIRESTORE_CONNECTION_ERROR,
    `Firestore operation failed: ${originalError.message}`,
    { originalError: originalError.message }
  );
}

/**
 * Creates a DOCUMENT_NOT_FOUND error
 */
export function createDocumentNotFoundError(docId) {
  return new DogError(
    DOG_ERROR_CODES.DOCUMENT_NOT_FOUND,
    `Document not found: ${docId}`,
    { docId }
  );
}

/**
 * Type guard to check if an error is a DogError
 */
export function isDogError(error) {
  return error instanceof DogError;
}
