/**
 * Tests for userManagement.js
 */

const { validateEmail, validateRole, addOrUpdateUser, checkUsers } = require('./userManagement');

// Mock Firebase Admin SDK
jest.mock('firebase-admin', () => ({
  firestore: {
    FieldValue: {
      serverTimestamp: () => ({ _type: 'serverTimestamp' })
    }
  }
}));

describe('validateEmail', () => {
  test('validates correct email format', () => {
    expect(validateEmail('test@muttville.org')).toEqual({
      success: true,
      email: 'test@muttville.org'
    });
    expect(validateEmail('Test.User@muttville.org')).toEqual({
      success: true,
      email: 'test.user@muttville.org'
    });
  });

  test('returns error on invalid email format', () => {
    expect(validateEmail('invalid')).toEqual({
      success: false,
      error: 'Invalid email format'
    });
    expect(validateEmail('')).toEqual({
      success: false,
      error: 'Invalid email format'
    });
    expect(validateEmail('@domain.com')).toEqual({
      success: false,
      error: 'Invalid email format'
    });
  });

  test('returns error on disallowed domain', () => {
    expect(validateEmail('test@example.com')).toEqual({
      success: false,
      error: 'Email must be from one of these domains: muttville.org'
    });
    expect(validateEmail('test@other.org')).toEqual({
      success: false,
      error: 'Email must be from one of these domains: muttville.org'
    });
  });

  test('accepts custom allowed domains', () => {
    expect(validateEmail('test@example.com', ['example.com'])).toEqual({
      success: true,
      email: 'test@example.com'
    });
    expect(validateEmail('user@custom.org', ['custom.org', 'example.com'])).toEqual({
      success: true,
      email: 'user@custom.org'
    });
  });
});

describe('validateRole', () => {
  test('accepts valid roles', () => {
    expect(validateRole('viewer')).toEqual({
      success: true,
      role: 'viewer'
    });
    expect(validateRole('closer')).toEqual({
      success: true,
      role: 'closer'
    });
    expect(validateRole('staff')).toEqual({
      success: true,
      role: 'staff'
    });
  });

  test('returns error on invalid role', () => {
    expect(validateRole('admin')).toEqual({
      success: false,
      error: 'Invalid role "admin"'
    });
    expect(validateRole('')).toEqual({
      success: false,
      error: 'Invalid role ""'
    });
    expect(validateRole('invalid')).toEqual({
      success: false,
      error: 'Invalid role "invalid"'
    });
  });
});

describe('addOrUpdateUser', () => {
  let mockDb;
  let mockAdmin;
  let mockDocRef;
  let mockDoc;

  beforeEach(() => {
    mockDoc = {
      set: jest.fn().mockResolvedValue(),
      update: jest.fn().mockResolvedValue()
    };

    mockDocRef = {
      set: jest.fn().mockResolvedValue(),
      update: jest.fn().mockResolvedValue()
    };

    mockDb = {
      collection: jest.fn().mockReturnValue({
        doc: jest.fn().mockReturnValue(mockDocRef)
      })
    };

    mockAdmin = {
      firestore: {
        FieldValue: {
          serverTimestamp: jest.fn().mockReturnValue('timestamp')
        }
      }
    };
  });

  test('creates user document with correct data', async () => {
    const result = await addOrUpdateUser(mockDb, mockAdmin, 'test@muttville.org', 'test-uid', 'viewer');

    expect(result.success).toBe(true);
    expect(mockDb.collection).toHaveBeenCalledWith('users');
    expect(mockDocRef.set).toHaveBeenCalledWith({
      email: 'test@muttville.org',
      displayName: 'test',
      role: 'viewer',
      createdAt: expect.any(Object),
      updatedAt: expect.any(Object)
    });
  });

  test('updates existing user document', async () => {
    mockDocRef.get = jest.fn().mockResolvedValue({ exists: true });

    const result = await addOrUpdateUser(mockDb, mockAdmin, 'test@muttville.org', 'test-uid', 'viewer');

    expect(result.success).toBe(true);
    expect(mockDocRef.update).toHaveBeenCalledWith({
      email: 'test@muttville.org',
      role: 'viewer',
      updatedAt: expect.any(Object)
    });
  });

  test('dry run mode returns success without making changes', async () => {
    const result = await addOrUpdateUser(mockDb, mockAdmin, 'test@muttville.org', 'test-uid', 'viewer', { dryRun: true });

    expect(result.success).toBe(true);
    expect(mockDb.collection).not.toHaveBeenCalled();
  });

  test('returns error on invalid email', async () => {
    const result = await addOrUpdateUser(mockDb, mockAdmin, 'invalid-email', 'test-uid', 'viewer');

    expect(result.success).toBe(false);
    expect(result.error).toBe('Invalid email format');
  });

  test('returns error on invalid role', async () => {
    const result = await addOrUpdateUser(mockDb, mockAdmin, 'test@muttville.org', 'test-uid', 'invalid');

    expect(result.success).toBe(false);
    expect(result.error).toBe('Invalid role "invalid"');
  });

  test('handles Firestore errors gracefully', async () => {
    mockDocRef.set.mockRejectedValue(new Error('Firestore connection failed'));

    const result = await addOrUpdateUser(mockDb, mockAdmin, 'test@muttville.org', 'test-uid', 'viewer');

    expect(result.success).toBe(false);
    expect(result.error).toBe('Firestore connection failed');
  });
});

describe('checkUsers', () => {
  let mockDb;
  let mockQuerySnapshot;
  let mockDocs;

  beforeEach(() => {
    mockDocs = [
      {
        id: 'user1',
        data: () => ({ email: 'valid@muttville.org', role: 'viewer' })
      },
      {
        id: 'user2',
        data: () => ({ email: 'invalid@example.com', role: 'viewer' })
      },
      {
        id: 'user3',
        data: () => ({ email: 'valid@muttville.org', role: 'invalid' })
      }
    ];

    mockQuerySnapshot = {
      docs: mockDocs
    };

    mockDb = {
      collection: jest.fn().mockReturnValue({
        get: jest.fn().mockResolvedValue(mockQuerySnapshot)
      })
    };
  });

  test('returns success when all users are valid', async () => {
    mockDocs[0].data = () => ({ email: 'valid@muttville.org', role: 'viewer' });
    mockDocs[1].data = () => ({ email: 'also-valid@muttville.org', role: 'closer' });
    mockDocs[2].data = () => ({ email: 'third@muttville.org', role: 'staff' });

    const result = await checkUsers(mockDb);

    expect(result.success).toBe(true);
    expect(result.totalUsers).toBe(3);
    expect(result.invalidUsers).toHaveLength(0);
    expect(result.roleCounts.viewer).toBe(1);
    expect(result.roleCounts.closer).toBe(1);
    expect(result.roleCounts.staff).toBe(1);
    expect(result.roleCounts.unknown).toBe(0);
  });

  test('detects invalid roles', async () => {
    mockDocs[0].data = () => ({ email: 'valid@muttville.org', role: 'viewer' });
    mockDocs[1].data = () => ({ email: 'also-valid@muttville.org', role: 'closer' });
    // user3 has invalid role

    const result = await checkUsers(mockDb);

    expect(result.success).toBe(false);
    expect(result.invalidUsers).toHaveLength(1);
    expect(result.invalidUsers[0]).toEqual({
      uid: 'user3',
      email: 'valid@muttville.org',
      role: 'invalid'
    });
    expect(result.roleCounts.unknown).toBe(1);
  });

  test('handles Firestore errors', async () => {
    mockDb.collection = jest.fn().mockReturnValue({
      get: jest.fn().mockRejectedValue(new Error('Firestore connection failed'))
    });

    const result = await checkUsers(mockDb);

    expect(result.success).toBe(false);
    expect(result.summary).toContain('Firestore connection failed');
  });
});
