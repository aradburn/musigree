import { describe, it, expect, vi, beforeEach } from "vitest";
import { onHullEnter, onHullExit } from "../hull";
import type { HullEnterSelection, HullExitSelection } from "../hull";
import type { Mock } from "vitest";

type MockD3Chainable = {
    append: Mock;
    attr: Mock;
};

describe("Network Hull Module", () => {
    // Mock D3 selections
    let mockAppendFn: Mock;
    let mockAttrFn: Mock;
    let mockRemoveFn: Mock;
    let mockHullEnterSelection: HullEnterSelection;
    let mockHullExitSelection: HullExitSelection;
    let mockChainableSelection: MockD3Chainable;

    beforeEach(() => {
        // Reset all mocks
        vi.clearAllMocks();

        // Create mock D3 selection chain functions
        mockAttrFn = vi.fn().mockReturnThis();
        mockAppendFn = vi.fn();
        mockRemoveFn = vi.fn();

        // Create a chainable mock selection
        mockChainableSelection = {
            append: mockAppendFn,
            attr: mockAttrFn,
        };

        // Set up the append function to return the chainable selection
        mockAppendFn.mockReturnValue(mockChainableSelection);
        mockAttrFn.mockReturnValue(mockChainableSelection);

        // Mock enter selection with chainable methods
        mockHullEnterSelection = {
            append: mockAppendFn,
        } as unknown as HullEnterSelection;

        // Mock exit selection
        mockHullExitSelection = {
            remove: mockRemoveFn,
        } as unknown as HullExitSelection;
    });

    describe("onHullEnter", () => {
        it("should create a new hull group with correct class and path", () => {
            // Act
            onHullEnter(mockHullEnterSelection);

            // Assert
            // Verify group creation and class setting
            expect(mockAppendFn).toHaveBeenCalledWith("g");
            expect(mockAttrFn).toHaveBeenCalledWith("class", "hull");

            // Verify path creation
            expect(mockAppendFn).toHaveBeenCalledWith("path");

            // Verify the order of operations
            expect(mockAppendFn.mock.calls).toHaveLength(2);
            expect(mockAttrFn.mock.calls).toHaveLength(1);
        });
    });

    describe("onHullExit", () => {
        it("should remove hull elements from the DOM", () => {
            // Act
            onHullExit(mockHullExitSelection);

            // Assert
            expect(mockRemoveFn).toHaveBeenCalledTimes(1);
        });
    });
});
