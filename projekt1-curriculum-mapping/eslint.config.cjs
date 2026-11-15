// Regeln für die Browser-Skripte, alle als ES-Module eingebunden.
// CommonJS, damit require() die Pakete der pre-commit-Umgebung über NODE_PATH findet.
const js = require("@eslint/js");
const globals = require("globals");

module.exports = [
  js.configs.recommended,
  {
    files: ["app/static/**/*.js"],
    languageOptions: {
      ecmaVersion: "latest",
      sourceType: "module",
      globals: globals.browser,
    },
    rules: {
      eqeqeq: "error",
      "no-var": "error",
      "prefer-const": "error",
    },
  },
];
