/**
 * @fileoverview Main entry point for the Musigree application.
 * This module initializes the application and sets up module exports.
 * @module musigree
 * @version 0.2
 */

import "~bootstrap/dist/css/bootstrap.min.css";

// Import our custom CSS
import "./css/musigree.scss";

// Import all of Bootstrap's JS
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import * as bootstrap from "bootstrap";

import { initApp } from "./init";

// Initialize the application when the DOM is loaded
document.addEventListener("DOMContentLoaded", (): void => {
    // Remove toggle button as we're now fully using React
    // const toggleButton = document.createElement("button");
    // toggleButton.textContent = "Toggle React UI";
    // toggleButton.style.position = "fixed";
    // toggleButton.style.top = "10px";
    // toggleButton.style.left = "10px";
    // toggleButton.style.zIndex = "2000";
    // toggleButton.onclick = (): void => {
    //     const container = document.getElementById("react-app-container");
    //     if (container) {
    //         container.style.display =
    //             container.style.display === "none" ? "block" : "none";
    //     }
    // };
    // document.body.appendChild(toggleButton);

    // Initialize React app using dynamic import
    import("./components/index.tsx")
        .then((module) => {
            if (typeof module.initReactApp === "function") {
                try {
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
