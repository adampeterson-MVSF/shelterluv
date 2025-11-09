/**
 * @typedef {import('./Dog.types').Dog} Dog
 */

/**
 * Normalization functions for Dog objects
 *
 * ETL is the single source of truth for all semantic flags (IsInCustody, IsAvailableForAdoption, IsHospice, IsEventDog).
 * This function only normalizes shape and passes through ETL-computed flags.
 */

function validateRequiredFields(doc, data) {
  if (!data["Internal-ID"]) {
    throw new Error(`Dog document ${doc.id} missing required Internal-ID field`);
  }
}

function validateETLContract(doc, data) {
  const requiredETLFields = [
    'AgeYears', 'AgeDisplay', 'IsInCustody',
    'IsAvailableForAdoption', 'IsHospice', 'IsEventDog'
  ];

  const missingFields = requiredETLFields.filter(field => data[field] === undefined);
  if (missingFields.length > 0) {
    const errorMessage =
      `Dog document ${doc.id} missing ETL-required fields: ${missingFields.join(', ')}. ` +
      'ETL schema contract violation - required fields must always be present.';
    throw new Error(errorMessage);
  }
}

function buildNormalizedDogObject(doc, data) {
  return {
    id: doc.id,
    "Internal-ID": data["Internal-ID"],
    "ID": data["ID"],
    "Name": data["Name"],
    "Status": data["Status"],
    "AgeYears": data["AgeYears"],
    "AgeDisplay": data["AgeDisplay"],
    "IsInCustody": data["IsInCustody"],
    "IsAvailableForAdoption": data["IsAvailableForAdoption"],
    "IsHospice": data["IsHospice"],
    "IsEventDog": data["IsEventDog"],
    "Breed": data["Breed"],
    "Size": data["Size"],
    "Gender": data["Gender"],
    "Description": data["Description"],
    "Photos": data["Photos"] || [],
    "CaseManager": data["CaseManager"],
    "MemosRawHTML": data["MemosRawHTML"],
    "PersonalityNotes": data["PersonalityNotes"],
    "IntakeNotes": data["IntakeNotes"],
    "MedicalNotes": data["MedicalNotes"],
    "AdoptionCategory": data["AdoptionCategory"],
    "MedicalCategory": data["MedicalCategory"],
    "BehaviorCategory": data["BehaviorCategory"],
    "FullAnimalProfile": data["FullAnimalProfile"],
    "IntakeDate": data["IntakeDate"],
    "Location": data["Location"],
    "Stage": data["Stage"],
    "Weight": data["Weight"],
    "FosterName": data["FosterName"],
    "FosterPhone": data["FosterPhone"],
    "FosterEmail": data["FosterEmail"],
    "Treatments": data["Treatments"] || [],
    "ScrapeError": data["ScrapeError"]
  };
}

/**
 * Normalizes a Firestore document into a Dog object.
 * All semantic flags are computed by ETL and stored in Firestore - no recomputation here.
 * ETL contract: required fields must always be present. Always throws on contract violations.
 * UI will fail fast if ETL breaks the contract - no defensive defaults.
 * @param {Object} doc - Firestore document
 * @returns {Dog} Normalized dog object with ETL-computed flags
 */
export function normalizeDog(doc) {
  const data = doc.data();

  validateRequiredFields(doc, data);
  validateETLContract(doc, data);

  return buildNormalizedDogObject(doc, data);
}

/**
 * Gets the primary photo URL from a dog object
 * @param {Dog} dog - Dog object
 * @returns {string|null} Primary photo URL or null if no photos
 */
export function getPrimaryPhoto(dog) {
  return (dog.Photos && dog.Photos[0]) || null;
}
