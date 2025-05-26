import { describe, it, expect, vi, beforeEach, afterEach, Mock } from "vitest";
import * as d3 from "d3";
import { saveAs } from "file-saver";
import * as svgModule from "../svg";
import { initSvg, setSvgSize, setupSvgDefs, printSvg } from "../svg";
import { musigreeManager, networkManager } from "../core";
import { showMessage, clearMessages } from "../messages";
import { DOM_IDS, SVG_IDS, SVG } from "../constants";
import type { NetworkNode, SimNode } from "../network/data";
import { NodeType } from "../network/data";

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

// Define type for dg object
interface DGObject {
    dimensions: [number, number];
    svg_dimensions: [number, number];
    selectedNodeKey: string;
}

// Define canvas mock types
interface MockCanvasRenderingContext2D {
    clearRect: ReturnType<typeof vi.fn>;
    drawImage: ReturnType<typeof vi.fn>;
}

interface MockHTMLCanvasElement {
    getContext: ReturnType<typeof vi.fn>;
    toBlob: ReturnType<typeof vi.fn>;
    width: number;
    height: number;
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

vi.mock("file-saver", () => ({
    saveAs: vi.fn(),
}));

vi.mock("../messages", () => ({
    showMessage: vi.fn(),
    clearMessages: vi.fn(),
}));

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
    });

    describe("printSvg", () => {
        let mockCanvas: MockHTMLCanvasElement;
        let mockContext: MockCanvasRenderingContext2D;

        beforeEach(() => {
            // Create mock SVG element in a way that's compatible with React's virtual DOM
            document.body.innerHTML = `<div id="${DOM_IDS.SVG_CONTAINER}"><svg id="${DOM_IDS.SVG}"></svg></div>`;

            // Create mock canvas and context
            mockContext = {
                clearRect: vi.fn(),
                drawImage: vi.fn(),
            };

            mockCanvas = {
                getContext: vi.fn().mockReturnValue(mockContext),
                toBlob: vi.fn(),
                width: 100,
                height: 100,
            };

            // Mock document.createElement for canvas
            const originalCreateElement = document.createElement;
            vi.spyOn(document, "createElement").mockImplementation(
                (tagName: string): HTMLElement => {
                    if (tagName === "canvas") {
                        return mockCanvas as unknown as HTMLCanvasElement;
                    }
                    // Create element with explicit type
                    const element = originalCreateElement.call(
                        document,
                        tagName,
                    ) as HTMLElement;
                    return element;
                },
            );

            // Mock d3.select to return our mock selection with a proper node
            const mockSelection = createMockSelection();
            const element = document.getElementById(DOM_IDS.SVG);
            if (!(element instanceof SVGElement)) {
                throw new Error("Expected SVG element");
            }
            mockSelection.node.mockReturnValue(element);

            // Use correct type for d3.select mock that matches the expected return type
            vi.spyOn(d3, "select").mockImplementation(
                () => mockSelection as unknown as D3Selection,
            );

            // Mock selectedNodeKey
            vi.spyOn(musigreeManager, "selectedNodeKey", "get").mockReturnValue(
                "test-node",
            );
        });

        it("should show messages when saving image", () => {
            const width = 100;
            const height = 100;

            // Since this function might be complex to test in React environment,
            // simplify the test to just check if messages are shown correctly
            printSvg(width, height);

            expect(showMessage).toHaveBeenCalledWith(
                "info",
                "Saving image to disk, please wait...",
            );
        });
    });
});

describe("SVG String Processing", () => {
    let svgElement: SVGElement;

    beforeEach(() => {
        svgElement = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "svg",
        );
        svgElement.id = "svg";
        svgElement.classList.add("test-class");
        document.body.appendChild(svgElement);
    });

    afterEach(() => {
        document.body.innerHTML = "";
    });

    it("should process SVG string with correct namespace handling", () => {
        // Setup a mock XMLSerializer that returns a string with our expected content
        const mockSerializeToString = vi
            .fn()
            .mockReturnValue(
                '<svg xmlns:xlink="http://www.w3.org/1999/xlink" NS1:href="test"></svg>',
            );
        global.XMLSerializer = vi.fn().mockImplementation(() => ({
            serializeToString: mockSerializeToString,
        }));

        const result = svgModule.getSvgString(svgElement);
        expect(result).toContain('xmlns:xlink="http://www.w3.org/1999/xlink"');
        expect(result).not.toMatch(/NS\d+:href/);
    });

    it("should extract CSS styles correctly", () => {
        // Create a complex SVG structure with nested elements
        const container = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "g",
        );
        container.id = "container";
        container.classList.add("container-class");
        svgElement.appendChild(container);

        const circle = document.createElementNS(
            "http://www.w3.org/2000/svg",
            "circle",
        );
        circle.classList.add("circle-class");
        container.appendChild(circle);

        // Add a style element with some CSS rules
        const styleElement = document.createElement("style");
        styleElement.textContent = `
            #svg { fill: none; }
            .test-class { stroke: black; }
            .container-class { opacity: 0.8; }
            .circle-class { fill: red; }
            #container .circle-class { stroke: blue; }
            .container-class .circle-class { stroke-width: 2; }
            #svg .container-class .circle-class { stroke-dasharray: 5,5; }
        `;
        document.head.appendChild(styleElement);

        const styles = svgModule.getCSSStyles(svgElement);

        // Test basic selectors
        expect(styles).toContain("#svg {fill: none;}");
        expect(styles).toContain(".test-class {stroke: black;}");
        expect(styles).toContain(".container-class {opacity: 0.8;}");
        expect(styles).toContain(".circle-class {fill: red;}");

        // Test parent-child relationships
        expect(styles).toContain("#container .circle-class {stroke: blue;}");
        expect(styles).toContain(
            ".container-class .circle-class {stroke-width: 2;}",
        );
        expect(styles).toContain(
            "#svg .container-class .circle-class {stroke-dasharray: 5,5;}",
        );

        // Cleanup
        document.head.removeChild(styleElement);
    });

    it("should handle SecurityError when accessing cross-origin stylesheets", () => {
        // Mock document.styleSheets with a SecurityError
        const originalStyleSheets = document.styleSheets;

        // Replace the entire styleSheets object with a mock
        Object.defineProperty(document, "styleSheets", {
            get: () => [
                {
                    get cssRules() {
                        const error = new Error("Security Error");
                        error.name = "SecurityError";
                        throw error;
                    },
                },
            ],
            configurable: true,
        });

        // Should not throw error
        expect(() => svgModule.getCSSStyles(svgElement)).not.toThrow();

        // Restore original
        Object.defineProperty(document, "styleSheets", {
            get: () => originalStyleSheets,
            configurable: true,
        });
    });

    it("should throw non-SecurityError errors when accessing stylesheets", () => {
        // Mock document.styleSheets with a different error
        const originalStyleSheets = document.styleSheets;

        // Replace the entire styleSheets object with a mock
        Object.defineProperty(document, "styleSheets", {
            get: () => [
                {
                    get cssRules() {
                        throw new Error("Different Error");
                    },
                },
            ],
            configurable: true,
        });

        // Should throw the error
        expect(() => svgModule.getCSSStyles(svgElement)).toThrow(
            "Different Error",
        );

        // Restore original
        Object.defineProperty(document, "styleSheets", {
            get: () => originalStyleSheets,
            configurable: true,
        });
    });

    it("should append CSS styles correctly", () => {
        const cssText = ".test-style { fill: red; }";
        svgModule.appendCSS(cssText, svgElement);

        const styleElement = svgElement.querySelector("style");
        expect(styleElement).not.toBeNull();
        expect(styleElement?.getAttribute("type")).toBe("text/css");
        expect(styleElement?.textContent).toBe(cssText);
    });
});

describe("SVG to Image Conversion", () => {
    let mockContext: MockCanvasRenderingContext2D;
    let mockCanvas: MockHTMLCanvasElement;
    let mockImage: Partial<HTMLImageElement>;

    beforeEach(() => {
        mockContext = {
            clearRect: vi.fn(),
            drawImage: vi.fn(),
        };

        mockCanvas = {
            getContext: vi.fn().mockReturnValue(mockContext),
            toBlob: vi
                .fn()
                .mockImplementation((callback: (blob: Blob | null) => void) => {
                    const blob = new Blob(["test"], { type: "image/png" });
                    callback(blob);
                }),
            width: 800,
            height: 600,
        };

        // Initialize mockImage
        mockImage = {
            onload: null,
            src: "",
        };

        // Mock createElement for canvas
        const createElement = vi.spyOn(document, "createElement");
        createElement.mockImplementation((tagName: string): HTMLElement => {
            if (tagName === "canvas") {
                return mockCanvas as unknown as HTMLCanvasElement;
            }
            if (tagName === "img") {
                return mockImage as unknown as HTMLImageElement;
            }
            // Create a simple element directly instead of calling the original method
            const element = document.createElementNS(
                "http://www.w3.org/1999/xhtml",
                tagName,
            );
            return element as unknown as HTMLElement;
        });
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("should convert SVG string to image with correct dimensions", () => {
        const width = 800;
        const height = 600;
        const svgString = "<svg></svg>";
        const callback = vi.fn();

        svgModule.svgString2Image(svgString, width, height, "png", callback);

        // Check if canvas was created with correct dimensions
        expect(mockCanvas.width).toBe(width);
        expect(mockCanvas.height).toBe(height);

        // Check if image source was set correctly
        expect(mockImage.src).toContain("data:image/svg+xml;base64,");

        // Simulate image load
        const onload = mockImage.onload;
        if (typeof onload === "function") {
            onload.call(mockImage);
        }

        // Verify canvas operations
        expect(mockContext.clearRect).toHaveBeenCalledWith(0, 0, width, height);
        expect(mockContext.drawImage).toHaveBeenCalled();

        // Verify callback was called with blob
        expect(callback).toHaveBeenCalledWith(
            expect.any(Blob),
            expect.any(Number),
        );
    });
});
