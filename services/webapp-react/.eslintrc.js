module.exports = {
  root: true,
  env: {
    browser: true,
    es2020: true
  },
  globals: {
    vi: 'readonly',
    describe: 'readonly',
    it: 'readonly',
    test: 'readonly',
    expect: 'readonly',
    beforeEach: 'readonly',
    afterEach: 'readonly',
    beforeAll: 'readonly',
    afterAll: 'readonly',
    global: 'readonly',
    process: 'readonly',
    renderWithProviders: 'readonly'
  },
  extends: [
    'eslint:recommended',
    'plugin:react/recommended',
    'plugin:react/jsx-runtime',
    'plugin:react-hooks/recommended',
  ],
  ignorePatterns: ['dist', '.eslintrc.js'],
  parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
  settings: { react: { version: '18.2' } },
  plugins: ['react-refresh'],
  rules: {
    'react/jsx-no-target-blank': 'off',
    'react-refresh/only-export-components': [
      'warn',
      { allowConstantExport: true },
    ],
    // Complexity limits
    'max-lines-per-function': ['error', { max: 50 }],
    'max-params': ['error', { max: 4 }],
    'complexity': ['error', { max: 10 }],
    'max-depth': ['error', { max: 3 }],
    // Data flow enforcement - forbid direct Firestore access in components
    'no-restricted-imports': [
      'error',
      {
        paths: [
          {
            name: 'firebase/firestore',
            message: 'Direct Firestore imports forbidden in components. Use dogRepository.getDogs() → normalizeDog() → dogDerived/dogQuery instead.',
          },
        ],
        patterns: [
          {
            group: ['**/services/firebase'],
            importNames: ['getDogsCollection', 'getDogsCollectionRef'],
            message: 'Direct Firestore collection access forbidden. Use dogRepository.getDogs() instead.',
          },
        ],
      },
    ],
    // Code quality
    'no-nested-ternary': 'error',
    'no-unused-vars': ['error', { argsIgnorePattern: '^_' }],
    'prefer-const': 'error',
    'no-var': 'error',
    // React specific
    'react/prop-types': 'error',
    'react/jsx-key': 'error',
    'react-hooks/exhaustive-deps': 'warn',
  },
  overrides: [
    {
      files: ['**/*.test.jsx', '**/*.test.js'],
      rules: {
        // Relax complexity limits for tests
        'max-lines-per-function': 'off',
        'max-params': 'off',
        'complexity': 'off',
        // Allow prop-types in tests (testing-library handles this)
        'react/prop-types': 'off',
        // Allow Firestore imports in tests
        'no-restricted-imports': 'off',
      },
    },
    {
      files: ['src/repositories/*.js', 'src/services/firebase.js'],
      rules: {
        // Allow Firestore imports in repository and service files
        'no-restricted-imports': 'off',
      },
    },
  ],
}
