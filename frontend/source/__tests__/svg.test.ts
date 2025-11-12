import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as d3 from "d3";
import * as svgModule from "../svg";
import { initSvg, setSvgSize, setupSvgDefs } from "../svg";
import { musigreeManager } from "../core";
import { DOM_IDS, SVG_IDS, SVG } from "../constants";

// Define types for d3 mocks
type D3Selection = d3.Selection<SVGElement, unknown, null, undefined>;

// Define mock function type that matches vi.fn() return type
type MockFunction = ReturnType<typeof vi.fn>;

interface MockD3Selection {
    node: MockFunction;
    attr: MockFunction;
    empty?: MockFunction;
    select?: MockFunction;
    append?: MockFunction;
}

// Create a properly typed mock selection
function createMockSelection(): MockD3Selection {
    const mockNode = vi.fn();
    const mockAttr = vi.fn().mockReturnThis();
    const mockEmpty = vi.fn();
    const mockSelect = vi.fn();
    const mockAppend = vi.fn().mockReturnThis();

    return {
        node: mockNode,
        attr: mockAttr,
        empty: mockEmpty,
        select: mockSelect,
        append: mockAppend,
    };
}

// Mock external dependencies
vi.mock("d3", () => {
    return {
        select: vi.fn(),
        arc: vi.fn(() => ({
            innerRadius: vi.fn().mockReturnThis(),
            outerRadius: vi.fn().mockReturnThis(),
            startAngle: vi.fn().mockReturnThis(),
            endAngle: vi.fn().mockReturnThis(),
        })),
        InternMap: vi.fn(function (
            this: Map<unknown, unknown>,
            entries?: Iterable<readonly [unknown, unknown]>,
        ) {
            return new Map(entries);
        }),
    };
});

// Mock dg global object
vi.mock("../core", () => {
    const mockMusigreeManager = {
        _dimensions: [800, 600] as [number, number],
        _svgDimensions: [1000, 800] as [number, number],
        selectedNodeKey: "test-node",
        dpr: 1,
        get dimensions() {
            return this._dimensions;
        },
        set dimensions(value) {
            this._dimensions = value;
        },
        get svgDimensions() {
            return this._svgDimensions;
        },
        set svgDimensions(value) {
            this._svgDimensions = value;
        },
    };

    const mockNodeMap = new Map([["test-node", { name: "Test Node" }]]);

    return {
        musigreeManager: mockMusigreeManager,
        getSelectedNodeKey: vi.fn().mockImplementation(() => "test-node"),
        networkManager: {
            data: {
                nodeMap: mockNodeMap,
            },
        },
    };
});

describe("SVG Utilities", () => {
    let mockSelection: MockD3Selection;
    let mockDimensions: [number, number];
    let mockSvgDimensions: [number, number];
    let originalCreateElement: typeof document.createElement;

    beforeEach(() => {
        // Store original createElement
        originalCreateElement = document.createElement;

        // Reset dimensions
        mockDimensions = [800, 600];
        mockSvgDimensions = [1000, 800];

        // Create mock selection
        mockSelection = createMockSelection();

        // Mock d3.select to return our mock selection
        vi.spyOn(d3, "select").mockImplementation(
            (selector: string | d3.BaseType) => {
                if (
                    typeof selector === "string" &&
                    selector === DOM_IDS.SVG_ID
                ) {
                    // For container selection
                    const containerSelection = createMockSelection();
                    containerSelection.select = vi
                        .fn()
                        .mockReturnValue(mockSelection);
                    return containerSelection as unknown as D3Selection;
                }
                return mockSelection as unknown as D3Selection;
            },
        );
    });

    afterEach(() => {
        // Cleanup
        document.body.innerHTML = "";
        vi.restoreAllMocks();
        // Restore original createElement
        document.createElement = originalCreateElement;
        // Clean up any added style elements
        document.head.querySelectorAll("style").forEach((el) => el.remove());
    });

    describe("initSvg", () => {
        beforeEach(() => {
            // Create a mock container element that simulates React's rendered DOM
            const mockContainer = document.createElement("div");
            mockContainer.id = DOM_IDS.SVG_CONTAINER;
            document.body.appendChild(mockContainer);

            // Mock document.getElementById
            vi.spyOn(document, "getElementById").mockImplementation(
                (id: string): HTMLElement | null => {
                    if (id === DOM_IDS.SVG_CONTAINER) {
                        return mockContainer as HTMLElement;
                    }
                    return null;
                },
            );

            // Reset all mocks
            vi.clearAllMocks();
        });

        it("should initialize SVG with correct dimensions", () => {
            // Run the function
            initSvg();

            // Verify that d3.select was called with the container selector string
            expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_CONTAINER_ID);
        });
    });

    describe("setSvgSize", () => {
        let mockContainer: HTMLDivElement;
        let svgElement: SVGSVGElement;

        beforeEach(() => {
            // Create a mock SVG container
            mockContainer = document.createElement("div");
            mockContainer.id = DOM_IDS.SVG_CONTAINER;
            // Set dimensions without using clientWidth/clientHeight
            mockContainer.style.width = "800px";
            mockContainer.style.height = "600px";
            document.body.appendChild(mockContainer);

            // Create mock SVG element
            svgElement = document.createElementNS(
                "http://www.w3.org/2000/svg",
                "svg",
            );
            svgElement.id = DOM_IDS.SVG;
            mockContainer.appendChild(svgElement);

            // Mock document.getElementById
            vi.spyOn(document, "getElementById").mockImplementation(
                (id: string): HTMLElement | null => {
                    if (id === DOM_IDS.SVG_CONTAINER) {
                        return mockContainer as HTMLElement;
                    }
                    if (id === DOM_IDS.SVG) {
                        return svgElement as unknown as HTMLElement;
                    }
                    return null;
                },
            );

            // Create a proper mock for d3.select that will be used in the test
            const svgSelection = createMockSelection();
            svgSelection.empty.mockReturnValue(false);

            // Mock d3.select
            vi.spyOn(d3, "select").mockReturnValue(
                svgSelection as unknown as D3Selection,
            );

            // Mock getBoundingClientRect to return dimensions
            vi.spyOn(mockContainer, "clientWidth", "get").mockReturnValue(800);
            vi.spyOn(mockContainer, "clientHeight", "get").mockReturnValue(600);
        });

        it("should set SVG dimensions properly", () => {
            // Call setSvgSize
            setSvgSize(DOM_IDS.SVG_ID);

            // Verify that d3.select was called
            expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_ID);

            // Get the mock selection returned by d3.select
            const svgSelection = d3.select(
                DOM_IDS.SVG_ID,
            ) as unknown as MockD3Selection;

            // Verify attr was called with dimensions from the container
            expect(svgSelection.attr).toHaveBeenCalledWith("width", "800");
            expect(svgSelection.attr).toHaveBeenCalledWith("height", "600");

            // Get expected viewBox dimensions
            const svgWidth = 800 * SVG.VIEWPORT_SIZE_MULTIPLIER;
            const svgHeight = 600 * SVG.VIEWPORT_SIZE_MULTIPLIER;

            expect(svgSelection.attr).toHaveBeenCalledWith(
                "viewBox",
                `0 0 ${svgWidth} ${svgHeight}`,
            );
            expect(svgSelection.attr).toHaveBeenCalledWith(
                "preserveAspectRatio",
                "none",
            );
        });

        it("should handle missing SVG container gracefully", () => {
            const consoleErrorSpy = vi
                .spyOn(console, "error")
                .mockImplementation(() => {});

            // Mock getElementById to return null (container not found)
            vi.spyOn(document, "getElementById").mockReturnValue(null);

            // Call setSvgSize
            setSvgSize(DOM_IDS.SVG_ID);

            // Verify error was logged
            expect(consoleErrorSpy).toHaveBeenCalledWith(
                expect.stringContaining("SVG container element"),
            );

            consoleErrorSpy.mockRestore();
        });

        it("should handle empty SVG selection gracefully", () => {
            const consoleWarnSpy = vi
                .spyOn(console, "warn")
                .mockImplementation(() => {});

            // Create a mock selection that returns empty
            const emptySelection = createMockSelection();
            emptySelection.empty.mockReturnValue(true);

            // Mock d3.select to return empty selection
            vi.spyOn(d3, "select").mockReturnValue(
                emptySelection as unknown as D3Selection,
            );

            // Call setSvgSize
            setSvgSize(DOM_IDS.SVG_ID);

            // Verify warning was logged
            expect(consoleWarnSpy).toHaveBeenCalledWith(
                "SVG element or attr function not found",
            );

            consoleWarnSpy.mockRestore();
        });

        it("should handle errors in setSvgSize gracefully", () => {
            const consoleErrorSpy = vi
                .spyOn(console, "error")
                .mockImplementation(() => {});

            // Mock getElementById to throw an error
            vi.spyOn(document, "getElementById").mockImplementation(() => {
                throw new Error("Test error");
            });

            // Call setSvgSize - should not throw
            expect(() => setSvgSize(DOM_IDS.SVG_ID)).not.toThrow();

            // Verify error was logged
            expect(consoleErrorSpy).toHaveBeenCalledWith(
                "Error setting SVG size:",
                expect.any(Error),
            );

            consoleErrorSpy.mockRestore();
        });

        it("should handle different dimensions", () => {
            // Mock different dimensions directly on the mock
            vi.spyOn(mockContainer, "clientWidth", "get").mockReturnValue(1200);
            vi.spyOn(mockContainer, "clientHeight", "get").mockReturnValue(900);

            // Call setSvgSize
            setSvgSize(DOM_IDS.SVG_ID);

            // Get the mock selection returned by d3.select
            const svgSelection = d3.select(
                DOM_IDS.SVG_ID,
            ) as unknown as MockD3Selection;

            // Expected dimensions based on container
            const width = 1200;
            const height = 900;
            const svgWidth = width * SVG.VIEWPORT_SIZE_MULTIPLIER;
            const svgHeight = height * SVG.VIEWPORT_SIZE_MULTIPLIER;

            // Verify attributes were set correctly
            expect(svgSelection.attr).toHaveBeenCalledWith(
                "width",
                String(width),
            );
            expect(svgSelection.attr).toHaveBeenCalledWith(
                "height",
                String(height),
            );
            expect(svgSelection.attr).toHaveBeenCalledWith(
                "viewBox",
                `0 0 ${svgWidth} ${svgHeight}`,
            );
            expect(svgSelection.attr).toHaveBeenCalledWith(
                "preserveAspectRatio",
                "none",
            );
        });
    });

    describe("setupSvgDefs", () => {
        it("should create SVG definitions with correct attributes", () => {
            // Mock empty to return false (SVG exists)
            mockSelection.empty.mockReturnValue(false);

            // Need a deeper nesting for marker > path > attr
            const markerPathAttr = vi.fn().mockReturnThis();

            // For path appended to marker
            const markerAppendPath = vi.fn().mockReturnValue({
                attr: markerPathAttr,
            });

            // For marker attributes
            const markerAttr = vi.fn().mockReturnThis();
            const marker = {
                attr: markerAttr,
                append: markerAppendPath,
            };

            // For defs append marker
            const defsAppendMarker = vi.fn().mockReturnValue(marker);

            // For gradient appends
            const gradientStopAttr = vi.fn().mockReturnThis();
            const gradientAppendStop = vi.fn().mockReturnValue({
                attr: gradientStopAttr,
            });

            // For gradient
            const gradientAttr = vi.fn().mockReturnThis();
            const gradient = {
                attr: gradientAttr,
                append: gradientAppendStop,
            };

            // For defs append gradient
            const defsAppendGradient = vi.fn().mockReturnValue(gradient);

            // For defs
            const defsAppend = vi.fn((type) => {
                if (type === "marker") return marker;
                if (type === "radialGradient") return gradient;
                return {}; // Default case
            });

            // For defs object
            const defs = {
                append: defsAppend,
            };

            // For svg append defs
            const svgAppendDefs = vi.fn().mockReturnValue(defs);

            // Now for d3.select
            const selectSpy = vi.spyOn(d3, "select").mockReturnValue({
                append: svgAppendDefs,
                empty: vi.fn().mockReturnValue(false),
            } as unknown as D3Selection);

            // Now call setupSvgDefs
            setupSvgDefs(DOM_IDS.SVG_ID);

            // Verify d3.select was called
            expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_ID);

            // Verify defs was created
            expect(svgAppendDefs).toHaveBeenCalledWith("defs");

            // Restore mock
            selectSpy.mockRestore();
        });

        it("should handle empty SVG selection gracefully", () => {
            const consoleWarnSpy = vi
                .spyOn(console, "warn")
                .mockImplementation(() => {});

            // Create a mock selection that returns empty
            const emptySelection = createMockSelection();
            emptySelection.empty.mockReturnValue(true);

            // Mock d3.select to return empty selection
            vi.spyOn(d3, "select").mockReturnValue(
                emptySelection as unknown as D3Selection,
            );

            // Call setupSvgDefs
            setupSvgDefs(DOM_IDS.SVG_ID);

            // Verify warning was logged
            expect(consoleWarnSpy).toHaveBeenCalledWith(
                "SVG element or append function not found",
            );

            consoleWarnSpy.mockRestore();
        });

        it("should handle errors in setupSvgDefs gracefully", () => {
            const consoleErrorSpy = vi
                .spyOn(console, "error")
                .mockImplementation(() => {});

            // Mock d3.select to throw an error
            vi.spyOn(d3, "select").mockImplementation(() => {
                throw new Error("Test error");
            });

            // Call setupSvgDefs - should not throw
            expect(() => setupSvgDefs(DOM_IDS.SVG_ID)).not.toThrow();

            // Verify error was logged
            expect(consoleErrorSpy).toHaveBeenCalledWith(
                "Error setting up SVG definitions:",
                expect.any(Error),
            );

            consoleErrorSpy.mockRestore();
        });
    });
});
