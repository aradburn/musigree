/**
 * @fileoverview Main entry point for the Musigree application.
 * This module initializes the application and sets up module exports.
 * @module musigree
 */

import "~bootstrap/dist/css/bootstrap.min.css";

// Import our custom CSS
import "./css/bootstrap-icons.scss";
import "./css/musigree.scss";

// Import all of Bootstrap's JS
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import * as bootstrap from "bootstrap";

import { initApp } from "./init";
import { version } from "./version";

// Initialize the application when the DOM is loaded
document.addEventListener("DOMContentLoaded", (): void => {
    // Initialize React app using dynamic import
    import("./components/index.tsx")
        .then((module) => {
            if (typeof module.initReactApp === "function") {
                try {
                    console.log("Musigree v" + version);
                    module.initReactApp();
                    console.log("React app initialized successfully");

                    // Initialize the original app after React app is ready
                    // to ensure compatibility during transition
                    initApp();
                } catch (error) {
                    console.error("Error initializing React app:", error);
                }
            } else {
                console.error(
                    "initReactApp function not found in module:",
                    module,
                );
            }
        })
        .catch((error) => {
            console.error("Failed to load React initialization module:", error);
        });
});
