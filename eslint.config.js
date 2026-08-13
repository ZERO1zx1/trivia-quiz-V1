import js from '@eslint/js';

export default [
  js.configs.recommended,
  {
    files: ['frontend/**/*.js', 'app/static/js/**/*.js'],
    languageOptions: {
      ecmaVersion: 2024,
      sourceType: 'module',
      globals: {
        console: 'readonly',
        document: 'readonly',
        fetch: 'readonly',
        window: 'readonly',
        navigator: 'readonly',
        localStorage: 'readonly',
        HTMLInputElement: 'readonly',
        HTMLTextAreaElement: 'readonly',
      },
    },
  },
];
