import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
    root: path.join(__dirname, "./source/"),
    base: "/assets/",
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./source"),
            "~bootstrap": path.resolve(__dirname, "./node_modules/bootstrap"),
            //      "bootstrap-icons/": path.resolve(__dirname, "./node_modules/bootstrap-icons/font"),
        },
        extensions: [".js", ".jsx", ".ts", ".tsx", ".json"],
    },
    plugins: [react()],
    build: {
        cssCodeSplit: false,
        sourcemap: true,
        outDir: path.join(__dirname, "./dist/"),
        manifest: "manifest.json",
        rollupOptions: {
            input: "source/index.ts",
        },
        emptyOutDir: true,
        copyPublicDir: false,
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
        cors: true, // Allow all origins
        headers: {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "X-Requested-With, content-type, Authorization",
        },
        proxy: {
            "/api": {
                target: "http://localhost:5000",
                changeOrigin: true,
                secure: false,
            },
        },
    },
});
