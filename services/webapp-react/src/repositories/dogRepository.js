/**
 * @typedef {import('../types/Dog.types').Dog} Dog
 */

import { collection, getDocs, query, orderBy, limit, startAfter } from 'firebase/firestore';
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
 * @property {'not_found'|'permission'|'network'|'validation'|'unknown'|'cancelled'} kind - Error kind for UI handling
 * @property {string} message - Human-readable error message
 */

/**
 * Fetches dogs from Firestore with pagination support.
 * Fails on malformed documents - trusts ETL to provide schema-compliant data.
 * @param {number} [limitCount=20] - Maximum number of dogs to fetch
 * @param {Object} [startAfterDoc=null] - Document to start after for pagination
 * @param {AbortSignal} [signal] - Optional abort signal
 * @returns {Promise<DogResult>} Result object with success/data or error
 */
export async function getDogs(limitCount = 20, startAfterDoc = null, signal) {
  try {
    const dogsCollection = collection(db, 'dogs');
    let dogsQuery = query(dogsCollection, orderBy('name'), limit(limitCount));

    if (startAfterDoc) {
      dogsQuery = query(dogsCollection, orderBy('name'), limit(limitCount), startAfter(startAfterDoc));
    }

    const dogsSnapshot = await getDocs(dogsQuery);
    const dogsList = [];

    for (const doc of dogsSnapshot.docs) {
      // Check if request was aborted before expensive normalization
      if (signal?.aborted) {
        return { success: false, data: null, error: { kind: 'cancelled', message: 'Request was cancelled' } };
      }

      try {
        // Trust ETL - fail on malformed documents
        const normalizedDog = normalizeDog(doc);
        dogsList.push(normalizedDog);
      } catch (error) {
        console.error('[DogRepository] Failed to normalize dog:', doc.id, error);
        // Continue with other dogs instead of failing the whole query
        // This allows partial success when some documents are malformed
      }
    }

    return { success: true, data: dogsList, lastDoc: dogsSnapshot.docs[dogsSnapshot.docs.length - 1] || null };
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
 * @param {AbortSignal} [signal] - Optional abort signal
 * @returns {Promise<DogResult>} Result object with success/data or error
 */
export async function getDogById(id, signal) {
  try {
    const { doc, getDoc } = await import('firebase/firestore');
    const dogDocRef = doc(db, 'dogs', id);
    const dogDoc = await getDoc(dogDocRef);

    // Check if request was aborted before processing
    if (signal?.aborted) {
      return { success: false, data: null, error: { kind: 'cancelled', message: 'Request was cancelled' } };
    }

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

