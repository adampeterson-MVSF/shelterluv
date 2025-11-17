/**
 * @typedef {import('../types/Dog.types').Dog} Dog
 */

import { collection, getDocs } from 'firebase/firestore';
import { db } from '../app';
import { normalizeDog } from '../types/dogNormalize';
import { isDogError, createFirestoreError, DOG_ERROR_CODES } from '../types/dogErrors';

/**
 * Maps DogError codes to normalized error kinds for UI consumption.
 * @param {import('../types/dogErrors').DogError} dogError - The raw DogError
 * @returns {DogError} Normalized error with kind and message
 */
function mapDogErrorToUnion(dogError) {
  switch (dogError.code) {
    case DOG_ERROR_CODES.DOCUMENT_NOT_FOUND:
      return { kind: 'not_found', message: dogError.message };
    case DOG_ERROR_CODES.FIRESTORE_CONNECTION_ERROR:
      return { kind: 'network', message: dogError.message };
    case DOG_ERROR_CODES.MISSING_REQUIRED_FIELD:
    case DOG_ERROR_CODES.MISSING_ETL_CONTRACT_FIELDS:
      return { kind: 'validation', message: dogError.message };
    default:
      return { kind: 'unknown', message: dogError.message };
  }
}

/**
 * @typedef {Object} DogResult
 * @property {boolean} success - Whether the operation succeeded
 * @property {Dog[]|null} data - Dog data if success, null if error
 * @property {DogError|null} error - Structured error if operation failed
 */

/**
 * @typedef {Object} DogError
 * @property {'not_found'|'permission'|'network'|'validation'|'unknown'} kind - Error kind for UI handling
 * @property {string} message - Human-readable error message
 */

/**
 * Fetches all dogs from Firestore.
 * Fails on malformed documents - trusts ETL to provide schema-compliant data.
 * @returns {Promise<DogResult>} Result object with success/data or error
 */
export async function getDogs() {
  try {
    const dogsCollection = collection(db, 'dogs');
    const dogsSnapshot = await getDocs(dogsCollection);
    const dogsList = [];

    for (const doc of dogsSnapshot.docs) {
      // Trust ETL - fail on malformed documents
      const normalizedDog = normalizeDog(doc);
      dogsList.push(normalizedDog);
    }

    return { success: true, data: dogsList };
  } catch (error) {
    // Map error to normalized union type
    const dogError = isDogError(error) ? error : createFirestoreError(error);
    return { success: false, data: null, error: mapDogErrorToUnion(dogError) };
  }
}

/**
 * Fetches a single dog by ID from Firestore
 * Fails on malformed documents - trusts ETL to provide schema-compliant data.
 * @param {string} id - Dog document ID
 * @returns {Promise<DogResult>} Result object with success/data or error
 */
export async function getDogById(id) {
  try {
    const { doc, getDoc } = await import('firebase/firestore');
    const dogDocRef = doc(db, 'dogs', id);
    const dogDoc = await getDoc(dogDocRef);

    if (!dogDoc.exists()) {
      return { success: true, data: null };
    }

    // Trust ETL - fail on malformed documents
    const normalizedDog = normalizeDog(dogDoc);
    return { success: true, data: normalizedDog };

  } catch (error) {
    // Map error to normalized union type
    const dogError = isDogError(error) ? error : createFirestoreError(error);
    return { success: false, data: null, error: mapDogErrorToUnion(dogError) };
  }
}

