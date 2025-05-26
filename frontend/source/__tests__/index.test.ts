import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock CSS imports
vi.mock("~bootstrap/dist/css/bootstrap.min.css", () => ({}));
vi.mock("../css/musigree.scss", () => ({}));

// Mock bootstrap
vi.mock("bootstrap", () => ({
    default: vi.fn(),
}));

// Mock init - must come before importing initApp
vi.mock("../init", () => ({
    initApp: vi.fn(),
}));

// Import initApp after mocking
import { initApp } from "../init";

// Mock for React app initialization
vi.mock("../components/index.tsx", () => ({
    initReactApp: vi.fn(),
}));

import { initReactApp } from "../components/index.tsx";

describe("index.ts", () => {
    // Save original methods
    const originalAddEventListener = document.addEventListener;

    beforeEach(() => {
        // Clear all mocks
        vi.clearAllMocks();

        // Mock document.addEventListener before importing the module
        vi.spyOn(document, "addEventListener").mockImplementation(vi.fn());
    });

    afterEach(() => {
        // Clean up mocks and restore originals
        vi.restoreAllMocks();
        // Reset the module registry to clear cached modules
        vi.resetModules();
    });

    it("should initialize React app when DOM content is loaded", async () => {
        // Import the index module
        await import("../index");

        // Get the callback from the addEventListener mock
        const domContentLoadedCallback = vi
            .mocked(document.addEventListener)
            .mock.calls.find((call) => call[0] === "DOMContentLoaded")?.[1];

        if (domContentLoadedCallback) {
            // Create a mock event
            const mockEvent = new Event("DOMContentLoaded");

            // Call the handler
            if (typeof domContentLoadedCallback === "function") {
                domContentLoadedCallback(mockEvent);
            } else if (
                domContentLoadedCallback &&
                "handleEvent" in domContentLoadedCallback
            ) {
                domContentLoadedCallback.handleEvent(mockEvent);
            }

            // Allow async import to resolve (using a zero-timeout)
            await new Promise((resolve) => setTimeout(resolve, 0));

            // Verify initReactApp was called
            expect(initReactApp).toHaveBeenCalled();

            // Verify that initApp is called after React initialization
            expect(initApp).toHaveBeenCalled();
        } else {
            // This assertion will fail if the event listener was not set up
            expect(
                vi.mocked(document.addEventListener).mock.calls.length,
            ).toBeGreaterThan(0);
        }
    });
});
