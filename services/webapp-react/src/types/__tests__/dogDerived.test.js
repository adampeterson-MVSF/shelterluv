/**
 * Tests for dogDerived.js - derived property functions
 */

import { describe, it, expect } from 'vitest';
import {
  daysAtMuttville,
  getShelterLuvUrl
} from '../dogDerived.js';

describe('daysAtMuttville', () => {
  it('should calculate days since intake date', () => {
    const pastDate = new Date();
    pastDate.setDate(pastDate.getDate() - 10); // 10 days ago

    const dog = { IntakeDate: pastDate.toISOString().split('T')[0] };
    const days = daysAtMuttville(dog);
    expect(days).toBe(10);
  });

  it('should return 0 for missing intake date', () => {
    expect(daysAtMuttville({})).toBe(0);
    expect(daysAtMuttville({ IntakeDate: null })).toBe(0);
  });

  it('should return 0 for invalid date strings', () => {
    expect(daysAtMuttville({ IntakeDate: 'invalid-date' })).toBe(0);
  });
});

describe('getShelterLuvUrl', () => {
  it('should construct correct ShelterLuv URL', () => {
    expect(getShelterLuvUrl({ ID: 'A123' })).toBe('https://new.shelterluv.com/animal/A123');
    expect(getShelterLuvUrl({ ID: 'B456' })).toBe('https://new.shelterluv.com/animal/B456');
  });
});
