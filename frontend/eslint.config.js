import js from "@eslint/js";
import { defineConfig } from "eslint/config";
import prettierConfig from "eslint-config-prettier";
import reactHooks from "eslint-plugin-react-hooks";
import reactRefresh from "eslint-plugin-react-refresh";
import testingLibrary from "eslint-plugin-testing-library";
import globals from "globals";
import tseslint from "typescript-eslint";

const testFiles = [
    "**/__tests__/**/*.{ts,tsx}",
    "**/tests/**/*.{ts,tsx}",
];

const testingLibraryReact = testingLibrary.configs["flat/react"];

export default defineConfig(
    {
        ignores: ["**/dist/**", "**/node_modules/**"],
        linterOptions: {
            reportUnusedDisableDirectives: true,
        },
    },

    js.configs.recommended,

    // App source: type-aware TypeScript linting (excludes tests)
    {
        files: ["**/*.{ts,tsx}"],
        ignores: testFiles,
        extends: [...tseslint.configs.recommendedTypeChecked],
        languageOptions: {
            parserOptions: {
                projectService: true,
                tsconfigRootDir: import.meta.dirname,
            },
            globals: {
                ...globals.browser,
                ...globals.es2021,
            },
        },
        plugins: {
            "react-hooks": reactHooks,
            "react-refresh": reactRefresh,
        },
        rules: {
            // Classic hooks rules only (not React Compiler rules from flat.recommended)
            "react-hooks/rules-of-hooks": "error",
            "react-hooks/exhaustive-deps": "warn",
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
        },
    },

    // Tests: Testing Library rules; keep TypeScript rules relaxed like before
    {
        files: testFiles,
        extends: [tseslint.configs.disableTypeChecked],
        plugins: {
            "@typescript-eslint": tseslint.plugin,
            ...testingLibraryReact.plugins,
        },
        languageOptions: {
            parser: tseslint.parser,
            parserOptions: {
                projectService: true,
                tsconfigRootDir: import.meta.dirname,
            },
            globals: {
                ...globals.browser,
                ...globals.es2021,
                ...globals.node,
                ...globals.vitest,
            },
        },
        rules: {
            ...testingLibraryReact.rules,
            "@typescript-eslint/no-explicit-any": "off",
            "@typescript-eslint/no-unused-vars": "off",
            "@typescript-eslint/unbound-method": "off",
            "@typescript-eslint/explicit-function-return-type": "off",
            "@typescript-eslint/no-unsafe-return": "off",
            "@typescript-eslint/no-unused-expressions": "off",
            "@typescript-eslint/no-unsafe-function-type": "off",
            "@typescript-eslint/no-non-null-asserted-optional-chain": "off",
            "testing-library/no-node-access": "off",
            "testing-library/no-container": "off",
            "no-unused-expressions": "off",
            "no-unused-vars": "off",
        },
    },

    // Disable Prettier-conflicting rules; formatting stays in the format script
    prettierConfig,
);
