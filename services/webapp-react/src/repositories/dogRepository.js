/**
 * @typedef {import('../types/Dog.types').Dog} Dog
 */

import { collection, getDocs } from 'firebase/firestore';
import { db } from '../app';
import { normalizeDog } from '../types/dogNormalize';

/**
 * Fetches all dogs from Firestore.
 * Fails on malformed documents - trusts ETL to provide schema-compliant data.
 * @returns {Promise<{success: boolean, data: Dog[], error?: string}>} Result object with success/data or error
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
    console.error('Error fetching dogs from Firestore:', error);
    return { success: false, data: [], error: error.message };
  }
}

/**
 * Fetches a single dog by ID from Firestore
 * Fails on malformed documents - trusts ETL to provide schema-compliant data.
 * @param {string} id - Dog document ID
 * @returns {Promise<{success: boolean, data: Dog|null, error?: string}>} Result object with success/data or error
 */
export async function getDogById(id) {
  try {
    const { doc, getDoc } = await import('firebase/firestore');
    const dogDoc = await getDoc(doc(db, 'dogs', id));

    if (!dogDoc.exists()) {
      return { success: true, data: null };
    }

    // Trust ETL - fail on malformed documents
    const normalizedDog = normalizeDog(dogDoc);
    return { success: true, data: normalizedDog };

  } catch (error) {
    console.error('Error fetching dog from Firestore:', error);
    return { success: false, data: null, error: error.message };
  }
}

