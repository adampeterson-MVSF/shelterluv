/**
 * New structured Dog schema with nested fields.
 * Matches the backend nested schema for API-first data model.
 */

export interface Dog {
  // Identity
  internalId: string;
  publicId: string;
    name: string;
  type: 'Dog';

  // Status & lifecycle
  status: 'available' | 'adopted' | 'pending' | 'hold' | 'in_custody' | 'unknown';
  inFoster: boolean;
  lastIntakeAt: string | null;
  lastUpdatedAt: string | null;

  // Physical characteristics
  physical: {
    breed: string;
    ageDays: number;
    dob: string | null;
    sex: 'Male' | 'Female' | 'Unknown';
    sizeLabel: string;
    color: string;
    pattern: string;
    weightLbs: number | null;
    altered: boolean | null;
  };

  // Location
  location: {
    raw: any;
    label: string | null;
  };

  // People / relationships
  foster: {
    inFoster: boolean;
    person: {
      firstName: string | null;
      lastName: string | null;
      relationshipType: string | null;
      outDate: string | null;
      email?: string;
      phone?: string;
    } | null;
  };

  // Media
  media: {
    coverPhoto: string | null;
    photos: string[];
    videos: string[];
  };

  // Attributes & tags
  attributes: {
    raw: {
      attributeName: string;
      internalId: string;
      publish: 'Yes' | 'No';
  }[];
    compatibility?: {
      cat?: 'yes' | 'no' | 'unknown';
      dog?: 'yes' | 'no' | 'unknown';
      kid?: 'yes' | 'no' | 'unknown';
    };
  };

  // Medical / identification
  medical: {
    microchips: {
      id: string;
      issuer: string | null;
      implantedAt: string | null;
  }[];
  };

  // Content
  content: {
    description: string;
  };

  // Admin / misc
  admin: {
    adoptionFeeGroup: string | null;
    litterGroupId: string | null;
    previousIds: {
      idValue: string;
      issuingShelter: string | null;
      type: string;
  }[];
  };

  // Source metadata
  source: {
    lastIntakeUnixTime: number | null;
    lastUpdatedUnixTime: number | null;
    dobUnixTime: number | null;
    raw: any;
    syncedAt: string;
  };
}

/**
 * Type guard to check if a value is a valid Dog object.
 * @param value - The value to check
 * @returns True if the value conforms to the Dog interface
 */
export function isDog(value: any): value is Dog {
  return typeof value === 'object' && value !== null &&
    typeof value.internalId === 'string' &&
    typeof value.publicId === 'string' &&
    typeof value.name === 'string' &&
    typeof value.physical === 'object';
}
