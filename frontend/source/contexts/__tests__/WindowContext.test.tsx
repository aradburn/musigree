/** @jsxImportSource react */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { WindowProvider, WindowContext } from "../WindowContext";
import { INIT, SVG } from "../../constants";
import { resetNetworkTransform } from "../../network/init";
import { ResizeEvent } from "../../network/events";
import { musigreeManager } from "../../core";

// Mock dependencies
vi.mock("../../utils", () => ({
    debounce: vi.fn((fn) => fn),
}));

vi.mock("../../core", () => ({
    musigreeManager: {
        dpr: 1,
        dimensions: [0, 0],
        svgDimensions: [0, 0],
    },
}));

vi.mock("../../network/init", () => ({
    resetNetworkTransform: vi.fn(),
}));

vi.mock("../../network/events", () => ({
    ResizeEvent: vi.fn().mockImplementation(function () {
        return {
            type: "musigree:resize",
            bubbles: true,
            detail: {},
        };
    }),
}));

describe("WindowContext", () => {
    // Setup mocks for window and document
    const originalAddEventListener = window.addEventListener;
    const originalRemoveEventListener = window.removeEventListener;
    const originalDispatchEvent = window.dispatchEvent;
    const originalDevicePixelRatio = window.devicePixelRatio;
    const originalConsoleError = console.error;
    const mockSvgContainer = document.createElement("div");
    mockSvgContainer.id = "svg-container-fluid";
    mockSvgContainer.style.width = "1024px";
    mockSvgContainer.style.height = "768px";

    beforeEach(() => {
        // Reset mocks
        vi.clearAllMocks();

        // Mock window methods
        window.addEventListener = vi.fn();
        window.removeEventListener = vi.fn();
        window.dispatchEvent = vi.fn();
        Object.defineProperty(window, "devicePixelRatio", {
            value: 2,
            configurable: true,
        });

        // Mock console.error
        console.error = vi.fn();

        // Mock document.getElementById
        vi.spyOn(document, "getElementById").mockImplementation((id) => {
            if (id === "svg-container-fluid") {
                return mockSvgContainer;
            }
            return null;
        });

        // Mock getBoundingClientRect for SVG container
        mockSvgContainer.getBoundingClientRect = vi.fn().mockReturnValue({
            width: 1024,
            height: 768,
        });

        // Mock clientWidth and clientHeight with configurable: true
        Object.defineProperty(mockSvgContainer, "clientWidth", {
            value: 1024,
            configurable: true,
        });
        Object.defineProperty(mockSvgContainer, "clientHeight", {
            value: 768,
            configurable: true,
        });
    });

    afterEach(() => {
        // Restore original methods
        window.addEventListener = originalAddEventListener;
        window.removeEventListener = originalRemoveEventListener;
        window.dispatchEvent = originalDispatchEvent;
        Object.defineProperty(window, "devicePixelRatio", {
            value: originalDevicePixelRatio,
        });
        console.error = originalConsoleError;

        vi.restoreAllMocks();
    });

    it("renders without crashing", () => {
        render(
            <WindowProvider>
                <div>Test</div>
            </WindowProvider>,
        );
        expect(screen.getByText("Test")).toBeInTheDocument();
    });

    it("initializes with correct state and adds resize event listener", () => {
        let contextValue;

        render(
            <WindowProvider>
                <WindowContext.Consumer>
                    {(value) => {
                        contextValue = value;
                        return null;
                    }}
                </WindowContext.Consumer>
            </WindowProvider>,
        );

        // Check initial state
        expect(contextValue).toBeDefined();
        expect(contextValue.state).toEqual({
            width: 1024,
            height: 768,
            dpr: 2,
            dimensions: [1024, 768],
            svgDimensions: [
                1024 * SVG.VIEWPORT_SIZE_MULTIPLIER * 2,
                768 * SVG.VIEWPORT_SIZE_MULTIPLIER * 2,
            ],
        });

        // Check that it adds the resize event listener
        expect(window.addEventListener).toHaveBeenCalledWith(
            "resize",
            expect.any(Function),
        );
    });

    it("updates musigreeManager with dimensions", () => {
        render(
            <WindowProvider>
                <div>Test</div>
            </WindowProvider>,
        );

        expect(musigreeManager.dpr).toBe(2);
        expect(musigreeManager.dimensions).toEqual([1024, 768]);
        expect(musigreeManager.svgDimensions).toEqual([
            1024 * SVG.VIEWPORT_SIZE_MULTIPLIER * 2,
            768 * SVG.VIEWPORT_SIZE_MULTIPLIER * 2,
        ]);
    });

    it("removes resize event listener on unmount", () => {
        const { unmount } = render(
            <WindowProvider>
                <div>Test</div>
            </WindowProvider>,
        );

        unmount();

        expect(window.removeEventListener).toHaveBeenCalledWith(
            "resize",
            expect.any(Function),
        );
    });

    it("handleResize updates state and resets network", () => {
        let contextValue;

        render(
            <WindowProvider>
                <WindowContext.Consumer>
                    {(value) => {
                        contextValue = value;
                        return null;
                    }}
                </WindowContext.Consumer>
            </WindowProvider>,
        );

        // Change container dimensions
        Object.defineProperty(mockSvgContainer, "clientWidth", {
            value: 800,
            configurable: true,
        });
        Object.defineProperty(mockSvgContainer, "clientHeight", {
            value: 600,
            configurable: true,
        });

        // Call handleResize
        act(() => {
            contextValue.handleResize();
        });

        // Check that state was updated
        expect(contextValue.state).toEqual({
            width: 800,
            height: 600,
            dpr: 2,
            dimensions: [800, 600],
            svgDimensions: [
                800 * SVG.VIEWPORT_SIZE_MULTIPLIER * 2,
                600 * SVG.VIEWPORT_SIZE_MULTIPLIER * 2,
            ],
        });

        // Check that network was reset
        expect(resetNetworkTransform).toHaveBeenCalled();

        // Check that resize event was dispatched
        expect(window.dispatchEvent).toHaveBeenCalled();
        expect(ResizeEvent).toHaveBeenCalled();
    });

    it("handles missing SVG container gracefully", () => {
        // Mock document.getElementById to return null for svg-container-fluid
        vi.spyOn(document, "getElementById").mockReturnValue(null);

        let contextValue;

        render(
            <WindowProvider>
                <WindowContext.Consumer>
                    {(value) => {
                        contextValue = value;
                        return null;
                    }}
                </WindowContext.Consumer>
            </WindowProvider>,
        );

        // Should use default state with dpr only
        expect(contextValue.state).toEqual({
            width: 0,
            height: 0,
            dpr: 2,
            dimensions: [0, 0],
            svgDimensions: [0, 0],
        });
    });

    it("catches and logs errors during resize", () => {
        // Mock resetNetworkTransform to throw an error
        vi.mocked(resetNetworkTransform).mockImplementation(() => {
            throw new Error("Test error");
        });

        let contextValue;

        render(
            <WindowProvider>
                <WindowContext.Consumer>
                    {(value) => {
                        contextValue = value;
                        return null;
                    }}
                </WindowContext.Consumer>
            </WindowProvider>,
        );

        // Call handleResize which should now throw an error
        act(() => {
            contextValue.handleResize();
        });

        // Check that error was caught and logged
        expect(console.error).toHaveBeenCalledWith(
            "Error during window resize:",
            expect.any(Error),
        );
    });
});
