/**
 * Pure validation functions for user data.
 * No side effects, no I/O operations.
 */

const { assertValidRole } = require('./userRoles');

/**
 * Validate email format and domain.
 * @param {string} email - Email to validate
 * @param {string[]} allowedDomains - Array of allowed domains
 * @returns {Object} { success: true, email: string } or { success: false, error: string }
 */
function validateEmail(email, allowedDomains = ['muttville.org']) {
  try {
    if (!email || typeof email !== 'string') {
      return { success: false, error: 'Invalid email format' };
    }

    const trimmed = email.trim();
    if (!trimmed.includes('@') || trimmed.startsWith('@') || trimmed.endsWith('@')) {
      return { success: false, error: 'Invalid email format' };
    }

    const [localPart, domain] = trimmed.split('@');
    if (!localPart || !domain) {
      return { success: false, error: 'Invalid email format' };
    }

    if (!allowedDomains.some(allowed => domain.toLowerCase() === allowed.toLowerCase())) {
      return { success: false, error: `Email must be from one of these domains: ${allowedDomains.join(', ')}` };
    }

    return { success: true, email: trimmed.toLowerCase() };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Validate user role using centralized role validation.
 * @param {string} role - Role to validate
 * @returns {Object} { success: true, role: string } or { success: false, error: string }
 */
function validateRole(role) {
  try {
    assertValidRole(role);
    return { success: true, role };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

/**
 * Check if an email belongs to a test user.
 * @param {string} email - Email to check
 * @param {Array} testUsers - Array of test user objects with email property
 * @returns {boolean} True if email belongs to a test user
 */
function isTestUserEmail(email, testUsers) {
  return testUsers.some(testUser => testUser.email === email);
}

module.exports = {
  validateEmail,
  validateRole,
  isTestUserEmail
};
