import { vi, describe, it, expect, beforeEach, afterEach } from "vitest";
import type { Selection, ZoomBehavior, D3ZoomEvent } from "d3";
import { DOM_IDS, SVG } from "../../constants";

// Define types for our mock Selection
type MockSelection = Selection<SVGGElement, unknown, HTMLElement, unknown>;

// Define interface for our d3 mock
interface MockD3Select {
    append: ReturnType<typeof vi.fn>;
    attr: ReturnType<typeof vi.fn>;
    call: ReturnType<typeof vi.fn>;
    node: ReturnType<typeof vi.fn>;
    transition: ReturnType<typeof vi.fn>;
    duration: ReturnType<typeof vi.fn>;
}

// Define interface for our layer mock
interface MockLayer {
    append: ReturnType<typeof vi.fn>;
    attr: ReturnType<typeof vi.fn>;
    transition: ReturnType<typeof vi.fn>;
    duration: ReturnType<typeof vi.fn>;
}

// Define mock handlers using vi.hoisted to ensure they're properly initialized before use
const mockLayers = vi.hoisted(() => ({
    root: null as unknown as MockLayer | null,
    halo: null as unknown as MockLayer | null,
    link: null as unknown as MockLayer | null,
    node: null as unknown as MockLayer | null,
    text: null as unknown as MockLayer | null,
}));

const mockZoomBehavior = vi.hoisted(() => ({
    extent: vi.fn().mockReturnThis(),
    scaleExtent: vi.fn().mockReturnThis(),
    on: vi.fn(),
    transform: vi.fn().mockReturnThis(),
}));

// Use hoisted objects in all mocks
vi.mock("../../core", () => ({
    networkManager: {
        layers: mockLayers,
        zoom: mockZoomBehavior,
        newNodeCoords: [0, 0],
    },
    musigreeManager: {
        svgDimensions: [800, 600],
        dimensions: [1000, 800],
    },
}));

// Mock d3 with custom behavior
const capturedZoomHandler = vi.hoisted(() => ({
    handler: null as ((event: D3ZoomEvent<SVGElement, unknown>) => void) | null,
}));

// Store a reference to our mock d3 select result
const mockD3SelectResult = vi.hoisted(() => {
    const result = {
        append: vi.fn().mockReturnThis(),
        attr: vi.fn().mockReturnThis(),
        node: vi.fn().mockReturnValue(document.createElement("div")),
        call: vi.fn().mockImplementation((fn, ...args) => {
            if (fn === mockZoomBehavior.transform) {
                // For zoom.transform method calls
                mockZoomBehavior.transform(...args);
            } else if (fn === mockZoomBehavior) {
                // For zoom behavior application
                return mockD3SelectResult;
            } else if (typeof fn === "function") {
                // For other function calls
                fn(mockD3SelectResult, ...args);
            }
            return mockD3SelectResult;
        }),
        transition: vi.fn().mockReturnThis(),
        duration: vi.fn().mockReturnThis(),
    };
    return result as MockD3Select;
});

// Mock for d3 module
vi.mock("d3", () => {
    const mockD3 = {
        select: vi.fn().mockReturnValue(mockD3SelectResult),
        zoom: vi.fn().mockImplementation(() => {
            mockZoomBehavior.on.mockImplementation(
                (
                    event: string,
                    handler: (event: D3ZoomEvent<SVGElement, unknown>) => void,
                ) => {
                    if (event === "zoom") {
                        capturedZoomHandler.handler = handler;
                    }
                    return mockZoomBehavior;
                },
            );
            return mockZoomBehavior;
        }),
        zoomIdentity: {
            scale: vi.fn().mockReturnThis(),
            translate: vi.fn().mockReturnThis(),
        },
        zoomTransform: vi.fn().mockReturnValue({
            invert: vi.fn().mockReturnValue([0, 0]),
            toString: vi.fn().mockReturnValue("translate(0,0) scale(1)"),
        }),
        arc: vi.fn().mockReturnValue({
            innerRadius: vi.fn().mockReturnThis(),
            outerRadius: vi.fn().mockReturnThis(),
            startAngle: vi.fn().mockReturnThis(),
            endAngle: vi.fn().mockReturnThis(),
            centroid: vi.fn().mockReturnValue([0, 0]),
        }),
    };
    return mockD3;
});

// Mock other dependencies
vi.mock("../forceLayout", () => ({
    initForceLayout: vi.fn(),
}));

vi.mock("../tooltips", () => ({
    hideAllTooltips: vi.fn(),
}));

// Import the functions we want to test
import { initNetwork, resetNetworkTransform } from "../init";
import { initForceLayout } from "../forceLayout";
import { hideAllTooltips } from "../tooltips";
import * as d3 from "d3";
import { musigreeManager, networkManager } from "../../core/singletons";

// Test suite
describe("Network Initialization Module", () => {
    beforeEach(() => {
        // Reset mocks
        vi.clearAllMocks();
        capturedZoomHandler.handler = null;

        // Reset layers
        mockLayers.root = null;
        mockLayers.halo = null;
        mockLayers.link = null;
        mockLayers.node = null;
        mockLayers.text = null;

        // Reset network manager state
        networkManager.newNodeCoords = [0, 0];

        // Set up mock append chain for layers
        const mockRoot: MockLayer = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
            transition: vi.fn().mockReturnThis(),
            duration: vi.fn().mockReturnThis(),
        };

        const mockHalo: MockLayer = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
            transition: vi.fn().mockReturnThis(),
            duration: vi.fn().mockReturnThis(),
        };

        const mockLink: MockLayer = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
            transition: vi.fn().mockReturnThis(),
            duration: vi.fn().mockReturnThis(),
        };

        const mockNode: MockLayer = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
            transition: vi.fn().mockReturnThis(),
            duration: vi.fn().mockReturnThis(),
        };

        const mockText: MockLayer = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
            transition: vi.fn().mockReturnThis(),
            duration: vi.fn().mockReturnThis(),
        };

        // Setup append chain for initNetwork
        const mockAppend = vi
            .fn()
            .mockReturnValueOnce(mockRoot)
            .mockReturnValueOnce(mockHalo)
            .mockReturnValueOnce(mockLink)
            .mockReturnValueOnce(mockNode)
            .mockReturnValueOnce(mockText);

        // Update mock d3.select return value with our configured mock
        mockD3SelectResult.append = mockAppend;

        // Mock console methods
        vi.spyOn(console, "log").mockImplementation(() => {});
        vi.spyOn(console, "error").mockImplementation(() => {});
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    // Test the main functionality of initNetwork
    describe("initNetwork function", () => {
        it("should call the layout initialization functions", () => {
            // Set up a spy to capture the custom event dispatch
            const dispatchEventSpy = vi.spyOn(window, "dispatchEvent");

            // Call the function we're testing
            initNetwork("#svg");

            // Verify d3.select was called
            expect(d3.select).toHaveBeenCalledWith("#svg");

            // Verify append was called for creating layers
            expect(mockD3SelectResult.append).toHaveBeenCalledWith("g");

            // Verify force layout functions were called
            expect(initForceLayout).toHaveBeenCalled();

            // Verify zoom behavior was set up
            expect(d3.zoom).toHaveBeenCalled();
            expect(mockZoomBehavior.on).toHaveBeenCalledWith(
                "zoom",
                expect.any(Function),
            );

            // Verify that the force layout initialization event was dispatched
            expect(dispatchEventSpy).toHaveBeenCalledWith(
                expect.objectContaining({
                    type: "musigree:force-layout-initialized",
                }),
            );

            // Clean up the spy
            dispatchEventSpy.mockRestore();
        });
    });

    // Test resetNetworkTransform
    describe("resetNetworkTransform function", () => {
        it("should update newNodeCoords with SVG center", () => {
            // Setup - Calculate the expected center coordinates
            const expectedCenter: [number, number] = [
                musigreeManager.svgDimensions[0] / 2,
                musigreeManager.svgDimensions[1] / 2,
            ];

            // Call the function being tested
            resetNetworkTransform();

            // Verify the center coordinates are set as expected
            expect(networkManager.newNodeCoords).toEqual(expectedCenter);

            // Verify the correct methods were called
            expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_ID);

            // Verify that the root layer transition was called
            expect(
                (networkManager.layers.root as unknown as MockLayer)
                    ?.transition,
            ).toHaveBeenCalled();
            expect(
                (networkManager.layers.root as unknown as MockLayer)?.duration,
            ).toHaveBeenCalledWith(1000);
            expect(
                (networkManager.layers.root as unknown as MockLayer)?.attr,
            ).toHaveBeenCalledWith("transform", expect.any(String));
        });

        it("should handle missing SVG node gracefully", () => {
            // Setup mock to return null for node()
            mockD3SelectResult.node.mockReturnValueOnce(null);

            // Call the function being tested
            resetNetworkTransform();

            // Verify error was logged
            expect(console.error).toHaveBeenCalledWith(
                "SVG node is not an instance of Element",
            );
        });

        it("should handle missing zoom behavior gracefully", () => {
            // Mock console.warn
            vi.spyOn(console, "warn").mockImplementation(() => {});

            // Temporarily set zoom to null to test the null check
            const originalZoom = networkManager.zoom;
            networkManager.zoom = null;

            // Call the function being tested
            resetNetworkTransform();

            // Since the zoom behavior check is commented out in the implementation,
            // the function should continue to execute normally
            // Verify that d3.select was called for DOM_IDS.SVG_ID
            expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_ID);

            // Verify the center coordinates are still set
            const expectedCenter: [number, number] = [
                musigreeManager.svgDimensions[0] / 2,
                musigreeManager.svgDimensions[1] / 2,
            ];
            expect(networkManager.newNodeCoords).toEqual(expectedCenter);

            // Restore original zoom
            networkManager.zoom = originalZoom;
        });
    });

    // Test the handleZoom behavior
    describe("handleZoom behavior", () => {
        it("should update layer transform and hide tooltips when zoom event occurs", () => {
            // First initialize the network to capture the zoom handler
            initNetwork("#svg");

            // Make sure the handler was captured
            expect(capturedZoomHandler.handler).not.toBeNull();

            // Create a mock zoom event
            const mockEvent = {
                transform: {
                    toString: () => "translate(10,20) scale(1.5)",
                },
            } as unknown as D3ZoomEvent<SVGElement, unknown>;

            // Call the captured zoom handler with our mock event
            if (capturedZoomHandler.handler) {
                capturedZoomHandler.handler(mockEvent);
            }

            // Verify tooltips were hidden
            expect(hideAllTooltips).toHaveBeenCalled();

            // Verify that initNetwork was called and the root layer was set up
            expect(networkManager.layers.root).not.toBeNull();

            // Verify that attr was called with transform on the root layer
            expect(networkManager.layers.root?.attr).toHaveBeenCalledWith(
                "transform",
                "translate(10,20) scale(1.5)",
            );
        });
    });
});
