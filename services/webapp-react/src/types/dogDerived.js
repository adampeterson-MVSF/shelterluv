/**
 * @typedef {import('./Dog.types').Dog} Dog
 */

/**
 * Derived property functions for Dog objects
 * Only contains functions actually used in components
 */

/**
 * Calculates number of days the dog has been at Muttville
 * @param {Dog} dog - Dog object
 * @returns {number} Number of days, or 0 if lastIntakeAt not available
 */
export function daysAtMuttville(dog) {
  if (!dog.lastIntakeAt) return 0;

  try {
    const intakeDate = new Date(dog.lastIntakeAt);
    // Check if date is valid
    if (isNaN(intakeDate.getTime())) return 0;

    const today = new Date();
    const diffTime = Math.abs(today - intakeDate);
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  } catch (e) {
    return 0;
  }
}

/**
 * Constructs ShelterLuv URL for a dog
 * @param {Dog} dog - Dog object
 * @returns {string} ShelterLuv URL for the dog
 */
export function getShelterLuvUrl(dog) {
  return `https://new.shelterluv.com/animal/${dog.publicId}`;
}
