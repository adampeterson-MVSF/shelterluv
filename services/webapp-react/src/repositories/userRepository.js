/**
 * @typedef {import('../types/Dog.types').Dog} Dog
 */

import { doc, getDoc } from 'firebase/firestore';
import { db } from '../app';
import { VALID_ROLE_VALUES } from '@common/userRoles';

/**
 * Fetches the user's application role from the /users collection.
 * Only returns valid roles; returns null for invalid or missing roles.
 * @param {string} uid - The Firebase Auth user ID.
 * @returns {Promise<{success: boolean, data: string|null, error?: string}>} Result object with success/data or error
 */
export async function getUserRole(uid) {
  if (!uid) return { success: true, data: null };

  try {
    const userDocRef = doc(db, 'users', uid);
    const userDocSnap = await getDoc(userDocRef);

    if (userDocSnap.exists()) {
      const userData = userDocSnap.data();
      const role = userData?.role;

      if (!role) return { success: true, data: null };

      if (!VALID_ROLE_VALUES.includes(role)) {
        console.warn('Unknown user role in Firestore:', role);
        return { success: true, data: null };
      }

      return { success: true, data: role };
    } else {
      // User is authenticated but has no profile in our DB
      console.warn(`User ${uid} has no matching user document.`);
      return { success: true, data: null };
    }
  } catch (error) {
    console.error('Error fetching user role:', error);
    return { success: false, data: null, error: 'Firestore connection failed' };
  }
}
