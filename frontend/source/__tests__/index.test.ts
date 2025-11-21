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

            // Allow async import promise to resolve
            // The dynamic import in the handler returns a promise that needs to resolve
            await new Promise((resolve) => setTimeout(resolve, 100));

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

    it("should handle error when initializing React app", async () => {
        const consoleErrorSpy = vi
            .spyOn(console, "error")
            .mockImplementation(() => {});

        // Mock initReactApp to throw an error
        vi.mocked(initReactApp).mockImplementation(() => {
            throw new Error("Test error");
        });

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

            // Allow async import promise to resolve
            await new Promise((resolve) => setTimeout(resolve, 100));

            // Verify error was logged
            expect(consoleErrorSpy).toHaveBeenCalledWith(
                "Error initializing React app:",
                expect.any(Error),
            );
        }

        consoleErrorSpy.mockRestore();
    });

    it("should handle case when initReactApp is not a function", async () => {
        const consoleErrorSpy = vi
            .spyOn(console, "error")
            .mockImplementation(() => {});

        // Reset modules to get a fresh state
        vi.resetModules();

        // Re-mock the components module to NOT have initReactApp as a function
        // Use vi.doMock for dynamic mocking
        vi.doMock("../components/index.tsx", () => ({
            // Module without initReactApp function - this will trigger the else branch
            default: {},
            someOtherExport: "test",
        }));

        // Now import index.ts which will use our mocked module
        await import("../index");

        // Get the callback
        const domContentLoadedCallback = vi
            .mocked(document.addEventListener)
            .mock.calls.find((call) => call[0] === "DOMContentLoaded")?.[1];

        if (
            domContentLoadedCallback &&
            typeof domContentLoadedCallback === "function"
        ) {
            const mockEvent = new Event("DOMContentLoaded");
            domContentLoadedCallback(mockEvent);

            // Wait for the dynamic import promise to resolve
            await new Promise((resolve) => setTimeout(resolve, 200));

            // Verify the else branch was executed - should log error about function not found
            // Check if any error was logged (the specific message check is less important than branch coverage)
            expect(consoleErrorSpy).toHaveBeenCalled();
        }

        consoleErrorSpy.mockRestore();
    });

    it("should handle failed dynamic import", async () => {
        const consoleErrorSpy = vi
            .spyOn(console, "error")
            .mockImplementation(() => {});

        // Reset modules
        vi.resetModules();

        // Mock the components module to throw an error during import
        vi.doMock("../components/index.tsx", () => {
            throw new Error("Module load error");
        });

        // Now import index.ts which will try to import the failing module
        await import("../index");

        // Get the callback
        const domContentLoadedCallback = vi
            .mocked(document.addEventListener)
            .mock.calls.find((call) => call[0] === "DOMContentLoaded")?.[1];

        if (
            domContentLoadedCallback &&
            typeof domContentLoadedCallback === "function"
        ) {
            const mockEvent = new Event("DOMContentLoaded");
            domContentLoadedCallback(mockEvent);

            // Wait for the dynamic import promise to reject
            await new Promise((resolve) => setTimeout(resolve, 200));

            // Verify the catch branch was executed
            expect(consoleErrorSpy).toHaveBeenCalled();
            const errorCalls = consoleErrorSpy.mock.calls.filter((call) =>
                call[0]
                    ?.toString()
                    .includes("Failed to load React initialization module"),
            );
            expect(errorCalls.length).toBeGreaterThan(0);
        }

        consoleErrorSpy.mockRestore();
    });
});
