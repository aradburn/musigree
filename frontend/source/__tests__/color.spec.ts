import { describe, it, expect } from "vitest";

import { getNodeColorClass, getLinkColorClass } from "../color";
import type { SimNode, SimLink } from "../network/data";
import { NodeType } from "../network/data";

// Minimal mock types for testing purposes
type MockSimNode = Pick<SimNode, "type" | "distance">;
type MockSimLink = {
    source: MockSimNode;
    target: MockSimNode;
};

describe("Color utility functions", () => {
    describe("getNodeColorClass", () => {
        it("should return correct class for artist node within range", () => {
            const node: MockSimNode = { type: NodeType.Artist, distance: 3 };
            expect(getNodeColorClass(node as SimNode)).toBe("color-4");
        });

        it("should return correct class for artist node at min distance", () => {
            const node: MockSimNode = { type: NodeType.Artist, distance: -2 }; // Clamps to 0, index = 0 + 1 = 1
            expect(getNodeColorClass(node as SimNode)).toBe("color-1");
        });

        it("should return correct class for artist node at max distance", () => {
            const node: MockSimNode = { type: NodeType.Artist, distance: 10 }; // Clamps to 8, index = 8
            expect(getNodeColorClass(node as SimNode)).toBe("color-8");
        });

        it("should return correct class for label node within range", () => {
            const node: MockSimNode = { type: NodeType.Label, distance: 3 }; // index = 3 + 2 = 5
            expect(getNodeColorClass(node as SimNode)).toBe("color-5");
        });

        it("should return correct class for label node at min distance", () => {
            const node: MockSimNode = { type: NodeType.Label, distance: -5 }; // Clamps to 0, index = 0 + 2 = 2
            expect(getNodeColorClass(node as SimNode)).toBe("color-2");
        });

        it("should return correct class for label node at max distance", () => {
            const node: MockSimNode = { type: NodeType.Label, distance: 7 }; // Clamps to 8, index = 8
            expect(getNodeColorClass(node as SimNode)).toBe("color-8");
        });

        it("should handle distance 0 for artist", () => {
            const node: MockSimNode = { type: NodeType.Artist, distance: 0 }; // index = 0 + 1 = 1
            expect(getNodeColorClass(node as SimNode)).toBe("color-1");
        });

        it("should handle distance 0 for label", () => {
            const node: MockSimNode = { type: NodeType.Label, distance: 0 }; // index = 0 + 2 = 2
            expect(getNodeColorClass(node as SimNode)).toBe("color-2");
        });
    });

    describe("getLinkColorClass", () => {
        it("should return color-2 if min distance is 0", () => {
            const link: MockSimLink = {
                source: { type: NodeType.Artist, distance: 0 },
                target: { type: NodeType.Label, distance: 3 },
            };
            // min distance = 0 -> effective distance = 2 -> index = 2
            expect(getLinkColorClass(link as SimLink)).toBe("color-2");
        });

        it("should return color-5 if min distance is greater than 0", () => {
            const link: MockSimLink = {
                source: { type: NodeType.Artist, distance: 1 },
                target: { type: NodeType.Label, distance: 3 },
            };
            // min distance = 1 -> effective distance = 5 -> index = 5
            expect(getLinkColorClass(link as SimLink)).toBe("color-5");
        });

        it("should return color-5 even if min distance is large", () => {
            const link: MockSimLink = {
                source: { type: NodeType.Artist, distance: 6 },
                target: { type: NodeType.Label, distance: 8 },
            };
            // min distance = 6 -> effective distance = 5 -> index = 5
            expect(getLinkColorClass(link as SimLink)).toBe("color-5");
        });

        it("should handle negative distances correctly", () => {
            const link: MockSimLink = {
                source: { type: NodeType.Artist, distance: -2 },
                target: { type: NodeType.Label, distance: 1 },
            };
            // min distance = -2 -> effective distance = 5 -> index = 5
            expect(getLinkColorClass(link as SimLink)).toBe("color-5");
        });

        it("should handle one node having distance 0", () => {
            const link: MockSimLink = {
                source: { type: NodeType.Artist, distance: 5 },
                target: { type: NodeType.Label, distance: 0 },
            };
            // min distance = 0 -> effective distance = 2 -> index = 2
            expect(getLinkColorClass(link as SimLink)).toBe("color-2");
        });
    });
});
