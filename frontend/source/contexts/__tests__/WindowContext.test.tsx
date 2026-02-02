/** @jsxImportSource react */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, act, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { WindowProvider } from "../WindowContext";
import { WindowContext } from "../windowContextInstance";
import { INIT, SVG } from "../../constants";
import { resetNetworkTransform } from "../../network/init";
import { ResizeEvent } from "../../network/events";
import { musigreeManager } from "../../core/singletons";

const NAVBAR_HEIGHT = 56;

// Mock dependencies
vi.mock("debounce", () => ({
    default: vi.fn((fn) => fn),
}));

vi.mock("../../core/singletons", () => ({
    musigreeManager: {
        dpr: 1,
        dimensions: [0, 0],
        svgDimensions: [0, 0],
        setIsMobileGetter: vi.fn(),
    },
}));

vi.mock("../../network/init", () => ({
    resetNetworkTransform: vi.fn(),
}));

vi.mock("@/svg", () => ({
    setSvgSize: vi.fn(),
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
        Object.defineProperty(window, "innerWidth", {
            value: 1024,
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
            configurable: true,
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
            isMobile: false,
        });

        // Single resize listener only (client-event-listeners: dimensions + navbar height)
        expect(window.addEventListener).toHaveBeenCalledTimes(1);
        expect(window.addEventListener).toHaveBeenCalledWith(
            "resize",
            expect.any(Function),
        );
    });

    it("updates --navbar-height CSS variable on mount when navbar exists", () => {
        const mockNavbar = document.createElement("nav");
        mockNavbar.className = "navbar";
        mockNavbar.getBoundingClientRect = vi.fn().mockReturnValue({
            height: NAVBAR_HEIGHT,
            width: 0,
            top: 0,
            left: 0,
            bottom: 0,
            right: 0,
            x: 0,
            y: 0,
            toJSON: () => ({}),
        });
        vi.spyOn(document, "querySelector").mockImplementation(
            (selector: string) => {
                if (selector === "nav.navbar") return mockNavbar;
                return null;
            },
        );
        const setPropertySpy = vi.spyOn(
            document.documentElement.style,
            "setProperty",
        );

        render(
            <WindowProvider>
                <div>Test</div>
            </WindowProvider>,
        );

        expect(setPropertySpy).toHaveBeenCalledWith(
            "--navbar-height",
            `${NAVBAR_HEIGHT}px`,
        );
        setPropertySpy.mockRestore();
    });

    it("handleResize updates --navbar-height CSS variable when navbar exists", async () => {
        const mockNavbar = document.createElement("nav");
        mockNavbar.className = "navbar";
        mockNavbar.getBoundingClientRect = vi.fn().mockReturnValue({
            height: NAVBAR_HEIGHT,
            width: 0,
            top: 0,
            left: 0,
            bottom: 0,
            right: 0,
            x: 0,
            y: 0,
            toJSON: () => ({}),
        });
        vi.spyOn(document, "querySelector").mockImplementation(
            (selector: string) => {
                if (selector === "nav.navbar") return mockNavbar;
                return null;
            },
        );
        const setPropertySpy = vi.spyOn(
            document.documentElement.style,
            "setProperty",
        );
        let contextValue: { handleResize: () => void };

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
        setPropertySpy.mockClear();

        await act(async () => {
            contextValue.handleResize();
        });

        expect(setPropertySpy).toHaveBeenCalledWith(
            "--navbar-height",
            `${NAVBAR_HEIGHT}px`,
        );
        setPropertySpy.mockRestore();
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

    it("handleResize updates state and resets network", async () => {
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
        await act(async () => {
            contextValue.handleResize();
        });

        // Wait for state to update and check that state was updated
        await waitFor(() => {
            expect(contextValue.state).toEqual({
                width: 800,
                height: 600,
                dpr: 2,
                dimensions: [800, 600],
                svgDimensions: [
                    800 * SVG.VIEWPORT_SIZE_MULTIPLIER * 2,
                    600 * SVG.VIEWPORT_SIZE_MULTIPLIER * 2,
                ],
                isMobile: false,
            });
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
            isMobile: false,
        });
    });

    it("catches and logs errors during resize", async () => {
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

        // Mock resetNetworkTransform to throw an error AFTER component is rendered
        vi.mocked(resetNetworkTransform).mockImplementation(() => {
            throw new Error("Test error");
        });

        // Call handleResize which should now throw an error
        await act(async () => {
            contextValue.handleResize();
        });

        // Wait a bit for the error to be logged (debounce might delay it)
        await waitFor(() => {
            expect(console.error).toHaveBeenCalledWith(
                "Error during window resize:",
                "Test error",
            );
        });
    });
});
