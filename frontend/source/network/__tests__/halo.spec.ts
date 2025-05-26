import { describe, it, expect, vi, beforeEach } from "vitest";
import { onHaloEnter, onHaloExit } from "../halo";
import type { SimNode } from "../data";
import { getOuterRadius } from "../node";
import type * as d3 from "d3";
import type { Mock } from "vitest";
import { NodeType } from "../data";

// Mock the node module
vi.mock("../node", () => ({
    getOuterRadius: vi.fn().mockReturnValue(10),
}));

type MockD3EnterSelection = d3.Selection<
    d3.EnterElement,
    SimNode,
    SVGGElement,
    unknown
>;
type MockD3ExitSelection = d3.Selection<
    SVGGElement,
    SimNode,
    SVGGElement,
    unknown
>;
type D3AttrFunction = (d: SimNode) => string | number;
type MockD3Chainable = {
    append: Mock;
    attr: Mock;
    text: Mock;
    select: Mock;
    remove: Mock;
};

describe("network/halo", () => {
    let mockEnterSelection: MockD3EnterSelection;
    let mockExitSelection: MockD3ExitSelection;
    let mockNode: SimNode;
    let mockAppendFn: Mock;
    let mockAttrFn: Mock;
    let mockRemoveFn: Mock;
    let mockChainableSelection: MockD3Chainable;

    beforeEach(() => {
        // Reset all mocks
        vi.clearAllMocks();

        // Create a mock node
        mockNode = {
            key: "artist-123",
            name: "Test Artist",
            type: NodeType.Artist,
            size: 1,
            x: 0,
            y: 0,
            distance: 1,
            radius: 10,
            links: [],
            hasMissing: false,
            missing: 0,
            lastClickTime: 0,
            lastTouchTime: 0,
            cluster: undefined,
            fixed: false,
            isIntermediate: false,
            vx: 0,
            vy: 0,
            index: 0,
            dragx: 0,
            dragy: 0,
            fx: null,
            fy: null,
            highlighted: false,
            selected: false,
        };

        // Create mock D3 selection chain functions
        mockAppendFn = vi.fn();
        mockAttrFn = vi.fn();
        mockRemoveFn = vi.fn();

        // Create a chainable mock selection
        mockChainableSelection = {
            append: mockAppendFn,
            attr: mockAttrFn,
            text: vi.fn(),
            select: vi.fn(),
            remove: mockRemoveFn,
        };

        // Set up all functions to return the chainable selection
        mockAppendFn.mockReturnValue(mockChainableSelection);
        mockAttrFn.mockReturnValue(mockChainableSelection);

        // Create mock D3 selections
        mockEnterSelection =
            mockChainableSelection as unknown as MockD3EnterSelection;
        mockExitSelection =
            mockChainableSelection as unknown as MockD3ExitSelection;
    });

    describe("onHaloEnter", () => {
        it("should create a group element with correct ID and classes", () => {
            onHaloEnter(mockEnterSelection);

            // Verify group creation
            expect(mockAppendFn).toHaveBeenCalledWith("g");

            // Verify ID attribute setting
            expect(mockAttrFn).toHaveBeenCalledWith("id", expect.any(Function));
            const idFn = mockAttrFn.mock.calls.find(
                (call) => call[0] === "id",
            )?.[1] as D3AttrFunction;
            if (!idFn) {
                throw new Error("id function not found in mock calls");
            }
            expect(idFn(mockNode)).toBe("artist-123");

            // Verify class attribute setting
            expect(mockAttrFn).toHaveBeenCalledWith(
                "class",
                expect.any(Function),
            );
            const classFn = mockAttrFn.mock.calls.find(
                (call) => call[0] === "class",
            )?.[1] as D3AttrFunction;
            if (!classFn) {
                throw new Error("class function not found in mock calls");
            }
            expect(classFn(mockNode)).toBe("node artist");
        });

        it("should create a halo circle with correct radius", () => {
            onHaloEnter(mockEnterSelection);

            // Verify circle creation
            expect(mockAppendFn).toHaveBeenCalledWith("circle");

            // Verify circle class
            expect(mockAttrFn).toHaveBeenCalledWith("class", "halo");

            // Verify radius calculation
            expect(mockAttrFn).toHaveBeenCalledWith("r", expect.any(Function));
            const radiusFn = mockAttrFn.mock.calls.find(
                (call) => call[0] === "r",
            )?.[1] as D3AttrFunction;
            if (!radiusFn) {
                throw new Error("radius function not found in mock calls");
            }
            expect(radiusFn(mockNode)).toBe(50); // 10 (mocked radius) + 40
            expect(getOuterRadius).toHaveBeenCalledWith(mockNode);
        });
    });

    describe("onHaloExit", () => {
        it("should remove the halo elements", () => {
            onHaloExit(mockExitSelection);
            expect(mockRemoveFn).toHaveBeenCalled();
        });
    });
});
