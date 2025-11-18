/**
 * Data shaping helpers for dog details UI components.
 * Pure functions that transform Dog objects into display-ready data structures.
 */

import { daysAtMuttville } from './dogDerived';

/**
 * Shape basic attributes for display.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of formatted attribute strings
 */
export function shapeBasicAttributes(dog) {
  const attributes = [];
  const days = daysAtMuttville(dog);

  // Basic attributes from physical section
  if (dog.physical?.breed) attributes.push(`Breed – ${dog.physical.breed}`);
  if (dog.physical?.color) attributes.push(`Color – ${dog.physical.color}`);
  if (dog.physical?.pattern) attributes.push(`Pattern – ${dog.physical.pattern}`);
  if (dog.physical?.sex) attributes.push(`Sex – ${dog.physical.sex}`);
  if (dog.physical?.sizeLabel) attributes.push(`Size – ${dog.physical.sizeLabel}`);
  if (dog.physical?.weightLbs) attributes.push(`Weight – ${dog.physical.weightLbs} lbs`);
  if (dog.physical?.altered !== null && dog.physical?.altered !== undefined) {
    attributes.push(`Altered – ${dog.physical.altered ? 'Yes' : 'No'}`);
  }

  // Location
  if (dog.location?.label) attributes.push(`Location – ${dog.location.label}`);

  // DOB if available
  if (dog.physical?.dob) {
    attributes.push(`Date of Birth – ${new Date(dog.physical.dob).toLocaleDateString()}`);
  }

  if (days > 0) {
    attributes.push(`Days at Muttville – ${days}`);
  }

  return attributes;
}

/**
 * Shape microchip attributes for display.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of formatted microchip attributes
 */
export function shapeMicrochipAttributes(dog) {
  const microchips = dog.medical?.microchips || [];
  return microchips.map(chip =>
    `Microchip – ${chip.id}${chip.issuer ? ` (Issuer: ${chip.issuer})` : ''}${chip.implantedAt ? ` (Implanted: ${new Date(chip.implantedAt).toLocaleDateString()})` : ''}`
  );
}

/**
 * Shape altered status attributes for display.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of formatted altered status attributes
 */
export function shapeAlteredAttributes(dog) {
  // The altered status is now in physical.altered
  // For now, just return the current altered status
  const altered = dog.physical?.altered;
  if (altered !== null && altered !== undefined) {
    return [`Altered – ${altered ? 'Yes' : 'No'}`];
  }
  return [];
}

/**
 * Shape intake attributes for display.
 * @param {Object} dog - Dog object
 * @returns {Object} Object with intakeItems array and hasIntakeNotes boolean
 */
export function shapeIntakeAttributes(dog) {
  const intakeItems = [];

  // Intake date from lastIntakeAt
  if (dog.lastIntakeAt) {
    intakeItems.push(`Intake Date – ${new Date(dog.lastIntakeAt).toLocaleDateString()}`);
  }

  // Previous shelter IDs from admin section
  if (dog.admin?.previousIds && dog.admin.previousIds.length > 0) {
    dog.admin.previousIds.forEach(prevId => {
      intakeItems.push(`Previous ID – ${prevId.idValue}${prevId.issuingShelter ? ` (${prevId.issuingShelter})` : ''}`);
    });
  }

  // TODO: Add other intake fields when they're structured in the schema

  return {
    intakeItems,
    hasIntakeNotes: Boolean(dog.content?.description && dog.content.description.includes('Intake'))
  };
}

/**
 * Shape adoption attributes for display.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of formatted adoption attributes
 */
export function shapeAdoptionAttributes(dog) {
  // TODO: Implement adoption attributes when adoption data is structured
  // For now, show adoption fee group if available
  const items = [];
  if (dog.admin?.adoptionFeeGroup) {
    items.push(`Adoption Fee Group – ${dog.admin.adoptionFeeGroup}`);
  }
  return items;
}

/**
 * Get behavioral attributes from dog object.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of behavioral attributes
 */
export function getBehavioralAttributes(dog) {
  // Return published attributes that might be behavioral
  // For now, return all published attributes - can categorize later
  return (dog.attributes?.raw || [])
    .filter(attr => attr.publish === 'Yes')
    .map(attr => attr.attributeName);
}

/**
 * Get physical attributes from dog object.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of physical attributes
 */
export function getPhysicalAttributes(_dog) {
  // For now, return empty array - physical attributes are handled elsewhere
  // Can categorize attributes by type later if needed
  return [];
}

/**
 * Check if dog has any medical information.
 * @param {Object} dog - Dog object
 * @returns {Object} Object with hasMedicalHistory and hasMedicalNotes booleans
 */
export function checkMedicalInfo(dog) {
  const medicalKeys = [
    'vaccinations',
    'treatments_due',
    'treatment_history',
    'active_diagnoses',
    'resolved_diagnoses',
    'diagnostic_tests',
    'physical_exams',
    'procedures_surgeries'
  ];

  const hasMedicalHistory = medicalKeys.some((key) => dog.MedicalHistory?.[key]?.length > 0);
  const hasMedicalNotes = dog.MedicalNotes && dog.MedicalNotes !== 'Not Available';

  return {
    hasMedicalHistory,
    hasMedicalNotes
  };
}
