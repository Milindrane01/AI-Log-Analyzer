module.exports = {
  root: true,
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
    ecmaFeatures: {
      jsx: true,
    },
    project: false,
  },
  env: {
    browser: true,
    es2022: true,
    node: true,
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
  plugins: ['@typescript-eslint', 'unused-imports', 'react', 'react-hooks', 'simple-import-sort'],
  extends: ['eslint:recommended', 'plugin:@typescript-eslint/recommended', 'plugin:react/recommended', 'plugin:react-hooks/recommended'],
  rules: {
    // TypeScript itself catches genuinely undefined symbols; no-undef doesn't
    // understand ambient lib types (Record, ReturnType, RequestInit, the
    // React/JSX UMD namespace, …) and reports false positives for them.
    // https://typescript-eslint.io/troubleshooting/faqs/eslint/#i-get-errors-from-the-no-undef-rule-about-my-typescript-types-eg-t-is-not-defined
    'no-undef': 'off',
    'no-unused-vars': 'off',
    '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_', varsIgnorePattern: '^_' }],
    'unused-imports/no-unused-imports': 'error',
    'unused-imports/no-unused-vars': ['warn', { varsIgnorePattern: '^_', argsIgnorePattern: '^_' }],
    'react/react-in-jsx-scope': 'off',
    'react/jsx-uses-react': 'off',
    // Props are typed via TypeScript interfaces, not the prop-types package
    // (which isn't even a dependency here) — this rule doesn't know that and
    // would flag every typed component prop as undocumented.
    'react/prop-types': 'off',
    'simple-import-sort/imports': 'error',
    'simple-import-sort/exports': 'error',
  },
};
