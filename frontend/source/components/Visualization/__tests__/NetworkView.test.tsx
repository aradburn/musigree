import React from "react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, cleanup } from "@testing-library/react";

// Define mocks
const initNetworkMock = vi.fn();
const initSvgMock = vi.fn();
const dispatchMock = vi.fn();

// Mock console.log
vi.spyOn(console, "log").mockImplementation(() => {});

// Mock dependencies
vi.mock("../../../network/init", () => ({
    initNetwork: () => initNetworkMock(),
}));

vi.mock("../../../svg", () => ({
    initSvg: () => initSvgMock(),
}));

vi.mock("../../../core", () => ({
    networkManager: {
        layers: {
            root: {
                remove: vi.fn(),
            },
        },
        forceLayout: {
            stop: vi.fn(),
        },
    },
}));

vi.mock("../../../contexts/useNetwork", () => ({
    useNetwork: () => ({
        dispatch: dispatchMock,
    }),
}));

// Import components
import NetworkView from "../NetworkView";
import { DOM_IDS } from "../../../constants";

describe("NetworkView Component", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        cleanup();
    });

    it("renders with the correct ID and classes", () => {
        const { container } = render(<NetworkView />);
        const mainElement = container.querySelector("main");

        expect(mainElement).toBeTruthy();
        expect(mainElement?.id).toBe(DOM_IDS.SVG_CONTAINER);
        expect(mainElement?.className).toContain("h-100");
        expect(mainElement?.className).toContain("flex-grow-1");
        expect(mainElement?.className).toContain("flex-shrink-1");
        expect(mainElement?.className).toContain("px-0");
    });

    it("initializes network visualization on mount", () => {
        render(<NetworkView />);
        expect(initSvgMock).toHaveBeenCalled();
        expect(initNetworkMock).toHaveBeenCalled();
    });

    it("does not reinitialize if already initialized", () => {
        const { rerender } = render(<NetworkView />);

        // Clear the mocks to check if they're called again
        vi.clearAllMocks();

        // Rerender the component
        rerender(<NetworkView />);

        // Should not initialize again
        expect(initSvgMock).not.toHaveBeenCalled();
        expect(initNetworkMock).not.toHaveBeenCalled();
    });

    it("assigns the required ID to the container", () => {
        const { container } = render(<NetworkView />);

        // Get the main element and verify its ID
        const mainElement = container.querySelector("main");
        expect(mainElement?.id).toBe(DOM_IDS.SVG_CONTAINER);
    });

    it("uses the dispatch function from useNetwork context", () => {
        render(<NetworkView />);

        // Currently, the component doesn't make any dispatch calls
        expect(dispatchMock).not.toHaveBeenCalled();
    });
});
