// Debug script to check what data is stored in Firestore for dogs
import { collection, getDocs } from 'firebase/firestore';
import { db } from './src/app.js';

// Temporary workaround for missing firebase services
// We'll simulate what the data looks like based on the ETL output

async function debugDogData() {
  console.log('🔍 Debugging dog data in Firestore...');

  try {
    const dogsCollection = collection(db, 'dogs');
    const dogsSnapshot = await getDocs(dogsCollection);

    console.log(`Found ${dogsSnapshot.docs.length} dogs in Firestore`);

    if (dogsSnapshot.docs.length > 0) {
      // Get the first dog
      const firstDogDoc = dogsSnapshot.docs[0];
      const dogData = firstDogDoc.data();

      console.log('\n=== FIRST DOG DATA ===');
      console.log('Document ID:', firstDogDoc.id);
      console.log('Name:', dogData.Name);
      console.log('Internal-ID:', dogData['Internal-ID']);

      console.log('\n=== ALL FIELDS ===');
      const allFields = Object.keys(dogData).sort();
      console.log('Total fields:', allFields.length);
      console.log('Field names:', allFields);

      console.log('\n=== ATTRIBUTE FIELDS (what DogDetails expects) ===');
      const attributeFields = [
        'Breed', 'Color', 'Pattern', 'DistinguishingMarks', 'AgeGroup', 'EstBirthdate',
        'Location', 'Stage', 'MicrochipNumber', 'MicrochipIssuer', 'MicrochipImplantDate',
        'AlteredBeforeArrival', 'AlteredInCare', 'Species', 'AdoptionPrice'
      ];

      attributeFields.forEach(field => {
        const value = dogData[field];
        const hasValue = value !== undefined && value !== null && value !== '';
        console.log(`${field}: ${hasValue ? `"${value}"` : 'MISSING/EMPTY'} ${hasValue ? '✓' : '✗'}`);
      });

      console.log('\n=== RAW DOG DATA (first 20 fields) ===');
      allFields.slice(0, 20).forEach(field => {
        const value = dogData[field];
        console.log(`${field}: ${JSON.stringify(value)}`);
      });

    } else {
      console.log('No dogs found in Firestore');
    }

  } catch (error) {
    console.error('Error querying Firestore:', error);
  }
}

debugDogData();
