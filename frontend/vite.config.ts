import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import removeConsole from "vite-plugin-remove-console";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
    root: path.join(__dirname, "./source/"),
    base: "/assets/",
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./source"),
            "~bootstrap": path.resolve(__dirname, "./node_modules/bootstrap"),
            "~bootstrap-icons": path.resolve(__dirname, "./node_modules/bootstrap-icons/font/fonts"),
        },
        extensions: [".js", ".jsx", ".ts", ".tsx", ".json", ".woff", ".woff2"],
    },
    plugins: [react(), removeConsole()],
    build: {
        cssCodeSplit: false,
        sourcemap: true,
        outDir: path.join(__dirname, "./dist/"),
        manifest: "manifest.json",
        rollupOptions: {
            input: "source/index.ts",
            output: {
                assetFileNames: (assetInfo) => {
                    if (assetInfo.name == 'style.css')
                        return 'assets/musigree-[hash].css';
                    return assetInfo.name;
                },
            },
            external: [ /public/ ],
        },
        emptyOutDir: true,
        copyPublicDir: false,
        assetsInlineLimit: 0,
    },
    test: {
        environment: "jsdom",
        setupFiles: ["./source/__tests__/setup.ts"],
        globals: true,
        root: __dirname,
        include: [
            // Unit tests in __tests__ directories
            "source/**/__tests__/**/*.{test,spec}.{js,jsx,ts,tsx}",
            // Integration and e2e tests
            "tests/**/*.{test,spec}.{js,jsx,ts,tsx}",
        ],
        coverage: {
            provider: "istanbul",
            include: [
                // Code in source directories
                "source/**/*.ts",
            ],
            exclude: ["public/js/vendor/**", "node_modules/**"],
        },
    },
    css: {
        preprocessorOptions: {
            scss: {
                silenceDeprecations: [
                    "color-functions",
                    "global-builtin",
                    "import",
                ],
            },
        },
    },
//     optimizeDeps: {
//         include: [],
//     },
    server: {
        origin: 'http://localhost:5173',
        host: 'localhost',
        cors: {
            "origin": ["http://localhost:5173", "http://localhost:5000"],
            "methods": "GET, PUT, POST, OPTIONS",
            "preflightContinue": false,
            "optionsSuccessStatus": 204
        },
        headers: {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, PUT, POST, OPTIONS",
            "Access-Control-Allow-Headers": "X-Requested-With, Content-Type, Authorization",
            "Strict-Transport-Security": "max-age=86400; includeSubDomains", // Adds HSTS options to your website, with a expiry time of 1 day
            "X-Content-Type-Options": "nosniff", // Protects from improper scripts runnings
            "X-Frame-Options": "DENY", // Stops your site being used as an iframe
            "X-XSS-Protection": "1; mode=block", // Gives XSS protection to legacy browsers
            "Content-Security-Policy": "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: ws: http://localhost:5173; font-src 'self' data: http://localhost:5173",
        },
        proxy: {
            "/api": {
                target: "http://localhost:5000",
                changeOrigin: true,
                secure: false,
            },
        },
        fs: {
          strict: true,
          // Allow serving files from one level up to the project root
          allow: [
              path.join(__dirname, "./source/"),
              path.join(__dirname, "./node_modules/"),
          ],
        },
    },
});
