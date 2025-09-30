import eslint from "@eslint/js";
import tseslint from "@typescript-eslint/eslint-plugin";
import tsparser from "@typescript-eslint/parser";
import prettierPlugin from "eslint-plugin-prettier";
import prettierConfig from "eslint-config-prettier";
import globals from "globals";
import testingLibrary from "eslint-plugin-testing-library";
import reactRefresh from "eslint-plugin-react-refresh";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __dirname = dirname(fileURLToPath(import.meta.url));

export default [
    // Base ESLint configuration
    {
        ignores: ["**/dist/**", "**/node_modules/**"],
        linterOptions: {
            reportUnusedDisableDirectives: true,
        },
    },

    // JavaScript files (during transition)
    {
        files: ["**/*.{js,jsx}"],
        languageOptions: {
            ecmaVersion: "latest",
            sourceType: "module",
            globals: {
                ...globals.browser,
                ...globals.es2021,
            },
        },
        plugins: {
            prettier: prettierPlugin,
        },
        rules: {
            ...eslint.configs.recommended.rules,
            "prefer-const": "warn",
            "no-unused-vars": "warn",
            "prettier/prettier": "warn",
        },
    },

    // TypeScript files
    {
        files: ["**/*.{ts,tsx}"],
        ignores: [
            "**/__tests__/*.{test,spec}.{ts,tsx}",
            "**/tests/**/*.{ts,tsx}",
        ],
        languageOptions: {
            parser: tsparser,
            parserOptions: {
                ecmaVersion: "latest",
                sourceType: "module",
                project: "./tsconfig.json",
                tsconfigRootDir: __dirname,
            },
            globals: {
                ...globals.browser,
                ...globals.es2021,
            },
        },
        plugins: {
            "@typescript-eslint": tseslint,
            "react-refresh": reactRefresh,
            prettier: prettierPlugin,
        },
        rules: {
            ...eslint.configs.recommended.rules,
            ...tseslint.configs["recommended"].rules,
            ...tseslint.configs["recommended-requiring-type-checking"].rules,
            "@typescript-eslint/no-explicit-any": "error",
            "@typescript-eslint/explicit-function-return-type": "error",
            "@typescript-eslint/no-unused-vars": [
                "error",
                {
                    argsIgnorePattern: "^_",
                    varsIgnorePattern: "^_",
                },
            ],
            "@typescript-eslint/consistent-type-imports": [
                "error",
                {
                    prefer: "type-imports",
                },
            ],
            "prefer-const": "error",
            "react-refresh/only-export-components": "error",
            "prettier/prettier": "error",
        },
    },

    // Test files specific configuration
    {
        files: [
            "**/__tests__/*.{test,spec}.{ts,tsx}",
            "**/__tests__/setup/*.{ts,tsx}",
            "**/tests/**/*.{ts,tsx}",
        ],
        plugins: {
            "@typescript-eslint": tseslint,
            prettier: prettierPlugin,
            "testing-library": testingLibrary,
        },
        languageOptions: {
            parser: tsparser,
            parserOptions: {
                ecmaVersion: "latest",
                sourceType: "module",
                project: "./tsconfig.json",
                tsconfigRootDir: __dirname,
            },
            globals: {
                ...globals.browser,
                ...globals.es2021,
                ...globals.node,
                describe: "readonly",
                it: "readonly",
                expect: "readonly",
                vi: "readonly",
                beforeEach: "readonly",
                afterEach: "readonly",
                beforeAll: "readonly",
                afterAll: "readonly",
            },
        },
        rules: {
            "@typescript-eslint/no-explicit-any": "off",
            "@typescript-eslint/no-unused-vars": "off",
            "@typescript-eslint/unbound-method": "off",
            "@typescript-eslint/explicit-function-return-type": "off",
            "@typescript-eslint/no-unsafe-return": "off",
            "testing-library/no-node-access": "off",
            "testing-library/no-container": "off",
        },
    },

    // Apply Prettier config last to ensure it takes precedence
    prettierConfig,
];
