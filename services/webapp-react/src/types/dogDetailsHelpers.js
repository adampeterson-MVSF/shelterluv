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

  const basicAttrs = [
    { key: 'Breed', label: 'Breed' },
    { key: 'Color', label: 'Color' },
    { key: 'Pattern', label: 'Pattern' },
    { key: 'DistinguishingMarks', label: 'Distinguishing Marks' },
    { key: 'AgeGroup', label: 'Age Group' },
    { key: 'EstBirthdate', label: 'Est. Birthdate' },
    { key: 'Location', label: 'Location' },
    { key: 'Stage', label: 'Stage' }
  ];

  basicAttrs.forEach(({ key, label }) => {
    if (dog[key]) attributes.push(`${label} – ${dog[key]}`);
  });

  if (dog.Species && dog.Species !== dog.Breed) {
    attributes.push(`Species – ${dog.Species}`);
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
  return [
    dog.MicrochipNumber && `Microchip – ${dog.MicrochipNumber}`,
    dog.MicrochipIssuer && `Issuer – ${dog.MicrochipIssuer}`,
    dog.MicrochipImplantDate && `Implant Date – ${dog.MicrochipImplantDate}`
  ].filter(Boolean);
}

/**
 * Shape altered status attributes for display.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of formatted altered status attributes
 */
export function shapeAlteredAttributes(dog) {
  return [
    dog.AlteredBeforeArrival && `Altered Before Arrival – ${dog.AlteredBeforeArrival}`,
    dog.AlteredInCare && `Altered In Care – ${dog.AlteredInCare}`
  ].filter(Boolean);
}

/**
 * Shape intake attributes for display.
 * @param {Object} dog - Dog object
 * @returns {Object} Object with intakeItems array and hasIntakeNotes boolean
 */
export function shapeIntakeAttributes(dog) {
  const intakeAttrs = [
    { key: 'IntakeType', label: 'Intake Type' },
    { key: 'IntakeSubtype', label: 'Intake Subtype' },
    { key: 'IntakeDate', label: 'Intake Date' },
    { key: 'ConditionAtIntake', label: 'Condition at Intake' },
    { key: 'AsilomarIntake', label: 'Asilomar Intake' },
    { key: 'JurisdictionIntake', label: 'Intake Jurisdiction' },
    { key: 'RabiesTagNumber', label: 'Rabies Tag' },
    { key: 'PreviousShelterId', label: 'Previous Shelter ID' },
    { key: 'PreviousShelterType', label: 'Previous Shelter Type' },
    { key: 'PreviousShelterIssuer', label: 'Previous Shelter Issuer' }
  ];

  const intakeItems = intakeAttrs
    .filter(({ key }) => dog[key])
    .map(({ key, label }) => `${label} – ${dog[key]}`);

  return {
    intakeItems,
    hasIntakeNotes: Boolean(dog.IntakeNotes)
  };
}

/**
 * Shape adoption attributes for display.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of formatted adoption attributes
 */
export function shapeAdoptionAttributes(dog) {
  return [
    dog.AdoptionPrice && `Adoption Price – ${dog.AdoptionPrice}`,
    dog.AdoptionCategory && `Adoption Category – ${dog.AdoptionCategory}`,
    dog.OutcomeType && `Outcome Type – ${dog.OutcomeType}`,
    dog.OutcomeSubtype && `Outcome Subtype – ${dog.OutcomeSubtype}`,
    dog.OutcomeDate && `Outcome Date – ${dog.OutcomeDate}`,
    dog.AsilomarOutcome && `Asilomar Outcome – ${dog.AsilomarOutcome}`,
    dog.JurisdictionOutcome && `Outcome Jurisdiction – ${dog.JurisdictionOutcome}`
  ].filter(Boolean);
}

/**
 * Get behavioral attributes from dog object.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of behavioral attributes
 */
export function getBehavioralAttributes(dog) {
  return dog.BehavioralAttributes || [];
}

/**
 * Get physical attributes from dog object.
 * @param {Object} dog - Dog object
 * @returns {Array<string>} Array of physical attributes
 */
export function getPhysicalAttributes(dog) {
  return dog.PhysicalAttributes || [];
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
