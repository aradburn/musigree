import path from "node:path";
import { fileURLToPath } from "node:url";
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export default defineConfig({
    root: path.join(__dirname, "./source/"),
    base: "/assets/",
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./source"),
            "~bootstrap": path.resolve(__dirname, "./node_modules/bootstrap"),
            "~bootstrap-icons": path.resolve(
                __dirname,
                "./node_modules/bootstrap-icons/font/fonts",
            ),
        },
        extensions: [".js", ".jsx", ".ts", ".tsx", ".json"],
    },
    plugins: [react()],
    build: {
        cssCodeSplit: false,
        sourcemap: false,
        outDir: path.join(__dirname, "./dist/"),
        manifest: "manifest.json",
        // Vite 8 uses Rolldown/Oxc; drop console/debugger during minify (prod only)
        rolldownOptions: {
            // Absolute path so Vite 8's dep scanner resolves it correctly
            // (it resolves input relative to `root`, which is ./source/)
            input: path.join(__dirname, "./source/index.ts"),
            output: {
                // Vite's css-post plugin calls this with `names` only (no `name`); Rolldown may omit `name` too.
                assetFileNames: (assetInfo) => {
                    const primary =
                        assetInfo.name ??
                        (Array.isArray(assetInfo.names)
                            ? assetInfo.names[0]
                            : undefined);
                    if (primary === "style.css") {
                        return "assets/musigree-[hash].css";
                    }
                    return primary ?? "assets/[name]-[hash][extname]";
                },
                minify: {
                    compress: {
                        dropConsole: true,
                        dropDebugger: true,
                    },
                },
            },
            external: [/fonts/],
        },
        emptyOutDir: true,
        copyPublicDir: false,
        assetsInlineLimit: 0, // Disable inlining for stricter CSP
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
    server: {
        origin: "http://localhost:5173",
        host: "localhost",
        cors: {
            origin: ["http://localhost:5173", "http://localhost:5000"],
            methods: "GET, PUT, POST, OPTIONS",
            preflightContinue: false,
            optionsSuccessStatus: 204,
        },
        headers: {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, PUT, POST, OPTIONS",
            "Access-Control-Allow-Headers":
                "X-Requested-With, Content-Type, Authorization",
            "Strict-Transport-Security": "max-age=86400; includeSubDomains", // Adds HSTS options to your website, with a expiry time of 1 day
            "X-Content-Type-Options": "nosniff", // Protects from improper scripts runnings
            "X-Frame-Options": "DENY", // Stops your site being used as an iframe
            "X-XSS-Protection": "1; mode=block", // Gives XSS protection to legacy browsers
            "Content-Security-Policy":
                "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: ws: http://localhost:5173;" +
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' data: ws: http://localhost:5173;" +
                "script-src-elem 'self' 'unsafe-inline' 'unsafe-eval' data: ws: http://localhost:5173;" +
                "style-src 'self' 'unsafe-inline' data: ws: http://localhost:5173;" +
                "style-src-elem 'self' 'unsafe-inline' data: ws: http://localhost:5173;" +
                " font-src 'self' data: http://localhost:5173",
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
