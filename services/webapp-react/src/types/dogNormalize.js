/**
 * @typedef {import('./Dog.types').Dog} Dog
 */

import { createMissingRequiredFieldError, createMissingETLFieldsError } from './dogErrors';
import { getStatusDisplay } from '../statusMapping.js';

/**
 * Normalization functions for Dog objects
 *
 * ETL is the single source of truth for all semantic flags (IsInCustody, IsAvailableForAdoption, IsHospice, IsEventDog).
 * This function only normalizes shape and passes through ETL-computed flags.
 */

function validateRequiredFields(doc, data) {
  if (!data["Internal-ID"]) {
    throw createMissingRequiredFieldError(doc.id, 'Internal-ID');
  }
}

function validateETLContract(doc, data) {
  const requiredETLFields = [
    'AgeYears', 'AgeDisplay', 'IsInCustody',
    'IsAvailableForAdoption', 'IsHospice', 'IsEventDog'
  ];

  const missingFields = requiredETLFields.filter(field => data[field] === undefined);
  if (missingFields.length > 0) {
    throw createMissingETLFieldsError(doc.id, missingFields);
  }
}

function buildNormalizedDogObject(doc, data) {
  // All fields passed through from ETL - no transformation needed
  const dog = {
    id: doc.id,
    "Internal-ID": data["Internal-ID"], "ID": data["ID"], "Name": data["Name"],
    "Status": data["Status"], "AgeYears": data["AgeYears"], "AgeDisplay": data["AgeDisplay"],
    "IsInCustody": data["IsInCustody"], "IsAvailableForAdoption": data["IsAvailableForAdoption"],
    "IsHospice": data["IsHospice"], "IsEventDog": data["IsEventDog"],
    "Breed": data["Breed"], "Size": data["Size"], "Gender": data["Gender"],
    "Description": data["Description"], "Photos": data["Photos"],
    "CaseManager": data["CaseManager"], "Location": data["Location"], "Stage": data["Stage"],
    "Weight": data["Weight"], "FosterName": data["FosterName"], "FosterPhone": data["FosterPhone"],
    "FosterEmail": data["FosterEmail"], "Treatments": data["Treatments"],
    "Attributes": data["Attributes"], "BehavioralAttributes": data["BehavioralAttributes"],
    "PhysicalAttributes": data["PhysicalAttributes"], "ScrapeError": data["ScrapeError"],
    "MemosRawHTML": data["MemosRawHTML"], "PersonalityNotes": data["PersonalityNotes"],
    "IntakeNotes": data["IntakeNotes"], "MedicalNotes": data["MedicalNotes"],
    "MedicalHistory": data["MedicalHistory"] || null,
    "AdoptionCategory": data["AdoptionCategory"], "MedicalCategory": data["MedicalCategory"],
    "BehaviorCategory": data["BehaviorCategory"], "VolunteerCategory": data["VolunteerCategory"],
    "FullAnimalProfile": data["FullAnimalProfile"], "IntakeDate": data["IntakeDate"],
    "Species": data["Species"], "Color": data["Color"], "Pattern": data["Pattern"],
    "DistinguishingMarks": data["DistinguishingMarks"], "AdoptionPrice": data["AdoptionPrice"],
    "MicrochipNumber": data["MicrochipNumber"], "MicrochipIssuer": data["MicrochipIssuer"],
    "MicrochipImplantDate": data["MicrochipImplantDate"], "AlteredBeforeArrival": data["AlteredBeforeArrival"],
    "AlteredInCare": data["AlteredInCare"], "AgeGroup": data["AgeGroup"], "EstBirthdate": data["EstBirthdate"],
    "IntakeType": data["IntakeType"], "IntakeSubtype": data["IntakeSubtype"],
    "OutcomeType": data["OutcomeType"], "OutcomeSubtype": data["OutcomeSubtype"],
    "AsilomarIntake": data["AsilomarIntake"], "AsilomarOutcome": data["AsilomarOutcome"],
    "ConditionAtIntake": data["ConditionAtIntake"], "JurisdictionIntake": data["JurisdictionIntake"],
    "JurisdictionOutcome": data["JurisdictionOutcome"], "RabiesTagNumber": data["RabiesTagNumber"],
    "PreviousShelterId": data["PreviousShelterId"], "PreviousShelterType": data["PreviousShelterType"],
    "PreviousShelterIssuer": data["PreviousShelterIssuer"]
  };

  // Add computed display fields to make components completely dumb
  dog.primaryPhotoUrl = getPrimaryPhoto(dog);
  dog.statusDisplay = getStatusDisplay(dog.Status);

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
  return (dog.Photos && dog.Photos[0]) || null;
}
