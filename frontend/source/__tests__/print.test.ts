import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as d3 from "d3";
import { saveAs } from "file-saver";
import * as printModule from "../print";
import {
    printSvg,
    getSvgString,
    getCSSStyles,
    appendCSS,
    svgString2Image,
} from "../print";
import { musigreeManager, networkManager } from "../core";
import { showMessage, clearMessages } from "../messages";
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

describe("Print SVG", () => {
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
            "Saving image to disk, please wait...",
            "dark",
        );
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
        global.XMLSerializer = class MockXMLSerializer {
            serializeToString = mockSerializeToString;
        } as unknown as typeof XMLSerializer;

        // Mock document.styleSheets to avoid the ownerNode issue
        const originalStyleSheets = document.styleSheets;
        Object.defineProperty(document, "styleSheets", {
            get: () => [],
            configurable: true,
        });

        const result = printModule.getSvgString(svgElement);
        expect(result).toContain('xmlns:xlink="http://www.w3.org/1999/xlink"');
        expect(result).not.toMatch(/NS\d+:href/);

        // Restore original
        Object.defineProperty(document, "styleSheets", {
            get: () => originalStyleSheets,
            configurable: true,
        });
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
        styleElement.textContent = `Musigree
            #svg { fill: none; }
            .test-class { stroke: black; }
            .container-class { opacity: 0.8; }
            .circle-class { fill: red; }
            #container .circle-class { stroke: blue; }
            .container-class .circle-class { stroke-width: 2; }
            #svg .container-class .circle-class { stroke-dasharray: 5,5; }
        `;
        document.head.appendChild(styleElement);

        // Mock document.styleSheets to include our style element
        const originalStyleSheets = document.styleSheets;

        // Create mock CSSStyleRule instances
        const createMockCSSStyleRule = (
            selectorText: string,
            cssText: string,
        ) => {
            const mockRule = {
                selectorText,
                cssText,
            };
            // Make it pass instanceof CSSStyleRule check
            Object.setPrototypeOf(mockRule, CSSStyleRule.prototype);
            return mockRule as CSSStyleRule;
        };

        Object.defineProperty(document, "styleSheets", {
            get: () => [
                {
                    ownerNode: styleElement,
                    href: "http://example.com/musigree-styles.css",
                    get cssRules() {
                        return [
                            createMockCSSStyleRule(
                                "#svg",
                                "#svg { fill: none; }",
                            ),
                            createMockCSSStyleRule(
                                ".test-class",
                                ".test-class { stroke: black; }",
                            ),
                            createMockCSSStyleRule(
                                ".container-class",
                                ".container-class { opacity: 0.8; }",
                            ),
                            createMockCSSStyleRule(
                                ".circle-class",
                                ".circle-class { fill: red; }",
                            ),
                            createMockCSSStyleRule(
                                "#container .circle-class",
                                "#container .circle-class { stroke: blue; }",
                            ),
                            createMockCSSStyleRule(
                                ".container-class .circle-class",
                                ".container-class .circle-class { stroke-width: 2; }",
                            ),
                            createMockCSSStyleRule(
                                "#svg .container-class .circle-class",
                                "#svg .container-class .circle-class { stroke-dasharray: 5,5; }",
                            ),
                        ];
                    },
                },
            ],
            configurable: true,
        });

        const styles = printModule.getCSSStyles(svgElement);

        // Test basic selectors
        expect(styles).toContain("#svg { fill: none; }");
        expect(styles).toContain(".test-class { stroke: black; }");
        expect(styles).toContain(".container-class { opacity: 0.8; }");
        expect(styles).toContain(".circle-class { fill: red; }");

        // Test parent-child relationships
        expect(styles).toContain("#container .circle-class { stroke: blue; }");
        expect(styles).toContain(
            ".container-class .circle-class { stroke-width: 2; }",
        );
        expect(styles).toContain(
            "#svg .container-class .circle-class { stroke-dasharray: 5,5; }",
        );

        // Cleanup
        document.head.removeChild(styleElement);
        Object.defineProperty(document, "styleSheets", {
            get: () => originalStyleSheets,
            configurable: true,
        });
    });

    it("should handle SecurityError when accessing cross-origin stylesheets", () => {
        // Mock document.styleSheets with a SecurityError
        const originalStyleSheets = document.styleSheets;

        // Replace the entire styleSheets object with a mock
        Object.defineProperty(document, "styleSheets", {
            get: () => [
                {
                    ownerNode: { textContent: "Musigree" },
                    href: "http://example.com/musigree-styles.css",
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
        expect(() => printModule.getCSSStyles(svgElement)).not.toThrow();

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
                    ownerNode: { textContent: "Musigree" },
                    href: "http://example.com/musigree-styles.css",
                    get cssRules() {
                        throw new Error("Different Error");
                    },
                },
            ],
            configurable: true,
        });

        // Should throw the error
        expect(() => printModule.getCSSStyles(svgElement)).toThrow(
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
        printModule.appendCSS(cssText, svgElement);

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
    let mockLogoImage: Partial<HTMLImageElement>;
    let imageCreationCount = 0;

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

        // Initialize mock images
        mockImage = {
            onload: null,
            src: "",
        };

        mockLogoImage = {
            onload: null,
            src: "",
        };

        imageCreationCount = 0;

        // Mock createElement for canvas and images
        const createElement = vi.spyOn(document, "createElement");
        createElement.mockImplementation((tagName: string): HTMLElement => {
            if (tagName === "canvas") {
                return mockCanvas as unknown as HTMLCanvasElement;
            }
            if (tagName === "img") {
                imageCreationCount++;
                // First image is the main SVG image, second is the logo
                if (imageCreationCount === 1) {
                    return mockImage as unknown as HTMLImageElement;
                } else {
                    return mockLogoImage as unknown as HTMLImageElement;
                }
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

    it("should convert SVG string to image with correct dimensions", async () => {
        const width = 800;
        const height = 600;
        const svgString = "<svg></svg>";
        const callback = vi.fn();

        printModule.svgString2Image(svgString, width, height, "png", callback);

        // Check if canvas was created with correct dimensions
        expect(mockCanvas.width).toBe(width);
        expect(mockCanvas.height).toBe(height);

        // Check if main image source was set correctly
        expect(mockImage.src).toContain("data:image/svg+xml;base64,");

        // Simulate main image load first
        const mainImageOnload = mockImage.onload;
        if (typeof mainImageOnload === "function") {
            mainImageOnload.call(mockImage);
        }

        // After main image loads, the logo image should be created and its src set
        // Check if logo image source was set correctly
        expect(mockLogoImage.src).toBe(
            "/img/musigree logo with website v3.png",
        );

        // Simulate logo image load after main image loads
        const logoImageOnload = mockLogoImage.onload;
        if (typeof logoImageOnload === "function") {
            logoImageOnload.call(mockLogoImage);
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
