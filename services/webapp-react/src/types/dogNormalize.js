/**
 * @typedef {import('./Dog.types').Dog} Dog
 */

import { createMissingRequiredFieldError, createMissingETLFieldsError } from './dogErrors';
import { getStatusDisplay } from '../statusMapping.js';

/**
 * Normalization functions for Dog objects
 *
 * ETL is the single source of truth for all semantic flags.
 * This function only normalizes shape and adds computed display fields.
 */

function validateRequiredFields(doc, data) {
  if (!data.internalId) {
    throw createMissingRequiredFieldError(doc.id, 'internalId');
  }
}

function validateETLContract(doc, data) {
  // New nested schema has different required fields
  const requiredFields = ['internalId', 'publicId', 'name', 'status', 'physical'];
  const missingFields = requiredFields.filter(field => data[field] === undefined);
  if (missingFields.length > 0) {
    throw createMissingETLFieldsError(doc.id, missingFields);
  }
}

function buildNormalizedDogObject(doc, data) {
  // Pass through all nested fields from ETL - no transformation needed
  const dog = {
    id: doc.id,
    // Identity
    internalId: data.internalId,
    publicId: data.publicId,
    name: data.name,
    type: data.type,

    // Status & lifecycle
    status: data.status,
    inFoster: data.inFoster,
    lastIntakeAt: data.lastIntakeAt,
    lastUpdatedAt: data.lastUpdatedAt,

    // Physical
    physical: data.physical,

    // Location
    location: data.location,

    // People / relationships
    foster: data.foster,

    // Media
    media: data.media,

    // Attributes & tags
    attributes: data.attributes,

    // Medical / identification
    medical: data.medical,

    // Content
    content: data.content,

    // Admin / misc
    admin: data.admin,

    // Source metadata
    source: data.source,
  };

  // Add computed display fields to make components completely dumb
  dog.primaryPhotoUrl = getPrimaryPhoto(dog);
  dog.statusDisplay = getStatusDisplay(dog.status);

  // Add legacy computed fields for backward compatibility during transition
  dog.ageDisplay = getAgeDisplay(dog.physical.ageDays);
  dog.isInCustody = dog.status !== 'adopted';
  dog.isAvailableForAdoption = dog.status === 'available';
  dog.isHospice = false; // TODO: derive from attributes or admin fields
  dog.isEventDog = false; // TODO: derive from attributes or admin fields

  return dog;
}

/**
 * Normalizes a Firestore document into a Dog object.
 * All semantic flags are computed by ETL and stored in Firestore - no recomputation here.
 * ETL contract: required fields must always be present. Validates contract in development only.
 * Production trusts ETL to provide valid data - no defensive defaults needed.
 * @param {Object} doc - Firestore document
 * @returns {Dog} Normalized dog object with ETL-computed flags
 */
export function normalizeDog(doc) {
  const data = doc.data();

  if (!data) {
    throw new Error('Dog document missing data');
  }

  // Only validate ETL contract in development - production trusts ETL
  if (import.meta.env.MODE !== 'production') {
    validateRequiredFields(doc, data);
    validateETLContract(doc, data);
  }

  return buildNormalizedDogObject(doc, data);
}

/**
 * Gets the primary photo URL from a dog object
 * @param {Dog} dog - Dog object
 * @returns {string|null} Primary photo URL or null if no photos
 */
export function getPrimaryPhoto(dog) {
  return dog.media?.coverPhoto || (dog.media?.photos && dog.media.photos[0]) || null;
}

/**
 * Gets human-readable age display from age in days
 * @param {number} ageDays - Age in days
 * @returns {string} Human-readable age string
 */
export function getAgeDisplay(ageDays) {
  if (!ageDays || ageDays < 0) return 'Unknown';

  const years = Math.floor(ageDays / 365);
  const months = Math.floor((ageDays % 365) / 30);
  const weeks = Math.floor((ageDays % 365 % 30) / 7);

  if (years > 0) {
    return years === 1 ? '1 year' : `${years} years`;
  } else if (months > 0) {
    return months === 1 ? '1 month' : `${months} months`;
  } else if (weeks > 0) {
    return weeks === 1 ? '1 week' : `${weeks} weeks`;
  } else {
    const days = Math.floor(ageDays);
    return days === 1 ? '1 day' : `${days} days`;
  }
}
