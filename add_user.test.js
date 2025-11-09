/**
 * Tests for add_user.js script
 * Tests argument parsing, safety checks, and business logic
 */

const { parseArgs } = require('./add_user');
const { assertSafeForDestructiveOps } = require('./common/devScriptSafety');
const { VALID_ROLES } = require('./common/userRoles');
const { spawn } = require('child_process');

describe('add_user script', () => {
  describe('parseArgs', () => {
    test('parses basic arguments correctly', () => {
      // Mock process.argv for testing
      const originalArgv = process.argv;
      process.argv = ['node', 'add_user.js', 'test@example.com', 'uid123', 'staff'];

      const result = parseArgs();
      expect(result).toEqual({
        email: 'test@example.com',
        uid: 'uid123',
        role: 'staff',
        dryRun: false,
        domain: null
      });

      process.argv = originalArgv;
    });

    test('parses dry-run flag', () => {
      const originalArgv = process.argv;
      process.argv = ['node', 'add_user.js', 'test@example.com', 'uid123', 'staff', '--dry-run'];

      const result = parseArgs();
      expect(result.dryRun).toBe(true);

      process.argv = originalArgv;
    });

    test('parses domain flag', () => {
      const originalArgv = process.argv;
      process.argv = ['node', 'add_user.js', 'test@example.com', 'uid123', 'staff', '--domain', 'example.com'];

      const result = parseArgs();
      expect(result.domain).toBe('example.com');

      process.argv = originalArgv;
    });

    test('throws on insufficient arguments', () => {
      const originalArgv = process.argv;
      process.argv = ['node', 'add_user.js', 'test@example.com'];

      expect(() => parseArgs()).toThrow();

      process.argv = originalArgv;
    });

    test('ignores extra arguments after flags', () => {
      const originalArgv = process.argv;
      process.argv = ['node', 'add_user.js', 'test@example.com', 'uid123', 'staff', '--dry-run', 'extra'];

      const result = parseArgs();
      expect(result).toEqual({
        email: 'test@example.com',
        uid: 'uid123',
        role: 'staff',
        dryRun: true,
        domain: null
      });

      process.argv = originalArgv;
    });
  });

  describe('run function', () => {
    let originalEnv;
    let mockExit;
    let mockConsoleLog;
    let mockConsoleError;

    beforeEach(() => {
      // Mock environment
      originalEnv = { ...process.env };
      process.env.DEV_SCRIPTS_ENABLED = '1';
      process.env.VITE_FIREBASE_PROJECT_ID = 'dev-muttville';

      // Mock console methods
      mockExit = jest.spyOn(process, 'exit').mockImplementation(() => {});
      mockConsoleLog = jest.spyOn(console, 'log').mockImplementation(() => {});
      mockConsoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
    });

    afterEach(() => {
      // Restore environment and mocks
      process.env = originalEnv;
      mockExit.mockRestore();
      mockConsoleLog.mockRestore();
      mockConsoleError.mockRestore();
    });

    test('fails when DEV_SCRIPTS_ENABLED is not set', async () => {
      delete process.env.DEV_SCRIPTS_ENABLED;

      const { run } = require('./add_user');
      await run({ email: 'test@muttville.org', uid: 'uid123', role: 'staff' });

      expect(mockConsoleError).toHaveBeenCalledWith(
        expect.stringContaining('DEV_SCRIPTS_ENABLED=1 environment variable required')
      );
      expect(mockExit).toHaveBeenCalledWith(1);
    });

    test('fails with invalid role', async () => {
      const { run } = require('./add_user');
      await run({ email: 'test@muttville.org', uid: 'uid123', role: 'invalid_role' });

      expect(mockConsoleError).toHaveBeenCalledWith(
        expect.stringContaining('Valid roles:')
      );
      expect(mockExit).toHaveBeenCalledWith(1);
    });

    test('fails with invalid email domain', async () => {
      const { run } = require('./add_user');
      await run({ email: 'test@gmail.com', uid: 'uid123', role: 'staff' });

      expect(mockConsoleError).toHaveBeenCalledWith(
        expect.stringContaining('Invalid email format')
      );
      expect(mockExit).toHaveBeenCalledWith(1);
    });

    test('succeeds with valid inputs and mocked dependencies', async () => {
      // Mock the Firebase admin and user management functions
      const mockGetAdminDb = jest.fn().mockReturnValue({});
      const mockAddOrUpdateUser = jest.fn().mockResolvedValue({ success: true });

      jest.doMock('./common/adminInit', () => ({ getAdminDb: mockGetAdminDb }));
      jest.doMock('./common/userManagement', () => ({ addOrUpdateUser: mockAddOrUpdateUser }));

      // Re-require the module to get the mocked version
      const { run } = require('./add_user');

      await run({ email: 'test@muttville.org', uid: 'uid123', role: 'staff' });

      expect(mockGetAdminDb).toHaveBeenCalled();
      expect(mockAddOrUpdateUser).toHaveBeenCalledWith(
        {},
        expect.any(Object),
        'test@muttville.org',
        'uid123',
        'staff',
        { allowedDomains: ['muttville.org'] }
      );
      expect(mockExit).not.toHaveBeenCalled();
    });

    test('uses custom domain when provided', async () => {
      const mockAddOrUpdateUser = jest.fn().mockResolvedValue({ success: true });
      jest.doMock('./common/userManagement', () => ({ addOrUpdateUser: mockAddOrUpdateUser }));

      const { run } = require('./add_user');
      await run({ email: 'test@example.com', uid: 'uid123', role: 'staff', domain: 'example.com' });

      expect(mockAddOrUpdateUser).toHaveBeenCalledWith(
        expect.any(Object),
        expect.any(Object),
        'test@example.com',
        'uid123',
        'staff',
        { allowedDomains: ['example.com'] }
      );
    });

    test('handles Firestore errors gracefully', async () => {
      const mockAddOrUpdateUser = jest.fn().mockResolvedValue({
        success: false,
        error: 'Firestore write failed'
      });
      jest.doMock('./common/userManagement', () => ({ addOrUpdateUser: mockAddOrUpdateUser }));

      const { run } = require('./add_user');
      const result = await run({ email: 'test@muttville.org', uid: 'uid123', role: 'staff' });

      expect(result.success).toBe(false);
      expect(mockConsoleError).toHaveBeenCalledWith(
        expect.stringContaining('Error adding/updating user')
      );
      expect(mockExit).toHaveBeenCalledWith(1);
    });

    test('returns success: false when addOrUpdateUser fails', async () => {
      const mockAddOrUpdateUser = jest.fn().mockResolvedValue({
        success: false,
        error: 'User creation failed'
      });
      jest.doMock('./common/userManagement', () => ({ addOrUpdateUser: mockAddOrUpdateUser }));

      const { run } = require('./add_user');
      const result = await run({ email: 'test@muttville.org', uid: 'uid123', role: 'staff' });

      expect(result.success).toBe(false);
      expect(result.error).toBe('User creation failed');
      expect(mockConsoleError).toHaveBeenCalledWith(
        '❌ Failed to add/update user: User creation failed'
      );
    });
  });

  describe('integration tests', () => {
    test('--help flag shows usage and exits successfully', (done) => {
      const child = spawn('node', ['add_user.js', '--help'], {
        cwd: process.cwd(),
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        expect(code).toBe(0);
        expect(stdout).toContain('DEV-ONLY SCRIPT: Add/Update User in Firestore');
        expect(stdout).toContain('Usage: node add_user.js <email> <uid> <role> [options]');
        expect(stdout).toContain('--help, -h   Show this help message');
        expect(stderr).toBe('');
        done();
      });
    });

    test('--dry-run with valid arguments succeeds', (done) => {
      const child = spawn('node', [
        'add_user.js',
        'test@muttville.org',
        'test-uid-123',
        'staff',
        '--dry-run'
      ], {
        cwd: process.cwd(),
        env: {
          ...process.env,
          DEV_SCRIPTS_ENABLED: '1',
          FIREBASE_PROJECT_ID: 'dev-muttville'
        },
        stdio: ['pipe', 'pipe', 'pipe']
      });

      let stdout = '';
      let stderr = '';

      child.stdout.on('data', (data) => {
        stdout += data.toString();
      });

      child.stderr.on('data', (data) => {
        stderr += data.toString();
      });

      child.on('close', (code) => {
        expect(code).toBe(0);
        expect(stdout).toContain('DRY RUN: Would add/update');
        expect(stdout).toContain('✅ Dry run completed');
        expect(stderr).toBe('');
        done();
      });
    });
  });
});
