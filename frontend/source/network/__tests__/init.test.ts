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

// Define mock handlers using vi.hoisted to ensure they're properly initialized before use
const mockLayers = vi.hoisted(() => ({
    root: null as unknown as MockSelection | null,
    halo: null as unknown as MockSelection | null,
    link: null as unknown as MockSelection | null,
    node: null as unknown as MockSelection | null,
    text: null as unknown as MockSelection | null,
}));

const mockZoomBehavior = vi.hoisted(() => ({
    extent: vi.fn().mockReturnThis(),
    scaleExtent: vi.fn().mockReturnThis(),
    on: vi.fn(),
    transform: {
        bind: vi.fn(),
    },
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
        call: vi.fn().mockReturnThis(),
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
import { musigreeManager, networkManager } from "../../core";

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
        const mockRoot = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
        };

        const mockHalo = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
        };

        const mockLink = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
        };

        const mockNode = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
        };

        const mockText = {
            append: vi.fn().mockReturnThis(),
            attr: vi.fn().mockReturnThis(),
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

            // Setup mockZoomBehavior.transform.bind
            mockZoomBehavior.transform.bind.mockReturnValue(
                (selection: unknown, transform: unknown) => selection,
            );

            // Call the function being tested
            resetNetworkTransform();

            // Verify the center coordinates are set as expected
            expect(networkManager.newNodeCoords).toEqual(expectedCenter);

            // Verify the correct methods were called
            expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_ID);
            expect(mockD3SelectResult.transition).toHaveBeenCalled();
            expect(mockD3SelectResult.duration).toHaveBeenCalledWith(750);
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

            // Verify layer transform was updated
            expect(mockLayers.root).not.toBeNull();
        });
    });
});
