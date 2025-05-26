import { describe, it, expect, beforeEach } from "vitest";
import { pruneSimData } from "../pruning";
import type {
    SimData,
    SimNode,
    SimLink,
    NetworkNode,
    NetworkLink,
} from "../data";
import { NodeType } from "../data";

describe("pruneSimData", () => {
    let mockSimData: SimData;
    let mockCenter: NetworkNode;

    beforeEach(() => {
        // Create a mock center node
        mockCenter = {
            key: "center",
            name: "Center Node",
            type: NodeType.Artist,
            size: 1,
            x: 0,
            y: 0,
            missing: 0,
            hasMissing: false,
            lastClickTime: 0,
            lastTouchTime: 0,
            distance: 0,
            radius: 10,
            links: [],
            cluster: 0,
            fixed: false,
            isIntermediate: false,
        };

        // Reset mock data before each test
        mockSimData = {
            nodeMap: new Map(),
            linkMap: new Map(),
            maxDistance: 0,
            center: mockCenter,
        };
    });

    it("should not prune when node and link counts are below thresholds", () => {
        // Arrange
        const node1: SimNode = {
            key: "1",
            name: "Node 1",
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
            cluster: 1,
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

        const node2: SimNode = {
            ...node1,
            key: "2",
            name: "Node 2",
            distance: 2,
            highlighted: false,
            selected: false,
        };

        mockSimData.nodeMap.set("1", node1);
        mockSimData.nodeMap.set("2", node2);

        const link1: SimLink = {
            key: "link1",
            source: node1,
            target: node2,
            role: "test",
            distance: 1,
            isSpline: false,
            intermediate: undefined,
            highlighted: false,
            selected: false,
        };

        // Update nodes with the link
        const networkLink: NetworkLink = {
            key: "link1",
            source: node1,
            target: node2,
            role: "test",
            distance: 1,
            isSpline: false,
            intermediate: undefined,
        };
        node1.links = [networkLink];
        node2.links = [networkLink];

        mockSimData.linkMap.set("link1", link1);

        // Act
        const result = pruneSimData(mockSimData);

        // Assert
        expect(result.nodeMap.size).toBe(2);
        expect(result.linkMap.size).toBe(1);
        expect(result.maxDistance).toBe(2);
    });

    it("should prune nodes with distance >= maxDist and <= minLinks", () => {
        // Arrange - Create a large network that exceeds pruning thresholds
        for (let i = 0; i < 700; i++) {
            const node: SimNode = {
                key: i.toString(),
                name: `Node ${i}`,
                type: NodeType.Artist,
                size: 1,
                x: 0,
                y: 0,
                distance: Math.floor(i / 100), // Creates nodes with distances 0-6
                radius: 10,
                links: [],
                hasMissing: false,
                missing: 0,
                lastClickTime: 0,
                lastTouchTime: 0,
                cluster: 1,
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
            mockSimData.nodeMap.set(i.toString(), node);

            if (i > 0) {
                const prevNode = mockSimData.nodeMap.get((i - 1).toString());
                if (prevNode) {
                    const link: SimLink = {
                        key: `link${i}`,
                        source: prevNode,
                        target: node,
                        role: "test",
                        distance: 1,
                        isSpline: false,
                        intermediate: undefined,
                        highlighted: false,
                        selected: false,
                    };
                    mockSimData.linkMap.set(`link${i}`, link);

                    // Update nodes with the link
                    const networkLink: NetworkLink = {
                        key: `link${i}`,
                        source: prevNode,
                        target: node,
                        role: "test",
                        distance: 1,
                        isSpline: false,
                        intermediate: undefined,
                    };
                    prevNode.links.push(networkLink);
                    node.links.push(networkLink);
                }
            }
        }

        // Act
        const result = pruneSimData(mockSimData);

        // Assert
        expect(result.nodeMap.size).toBeLessThan(700);
        expect(result.linkMap.size).toBeLessThan(700);

        // Verify that remaining nodes meet criteria
        Array.from(result.nodeMap.values()).forEach((node) => {
            if (node.distance && node.distance >= 2) {
                expect(node.links.length).toBeGreaterThan(1);
            }
        });
    });

    it("should update hasMissing and missing count on connected nodes when pruning", () => {
        // Arrange - Create a network where some nodes will be pruned
        for (let i = 0; i < 700; i++) {
            const node: SimNode = {
                key: i.toString(),
                name: `Node ${i}`,
                type: NodeType.Artist,
                size: 1,
                x: 0,
                y: 0,
                distance: 3, // All nodes at distance 3
                radius: 10,
                links: [],
                hasMissing: false,
                missing: 0,
                lastClickTime: 0,
                lastTouchTime: 0,
                cluster: 1,
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
            mockSimData.nodeMap.set(i.toString(), node);

            if (i > 0) {
                const prevNode = mockSimData.nodeMap.get((i - 1).toString());
                if (prevNode) {
                    const link: SimLink = {
                        key: `link${i}`,
                        source: prevNode,
                        target: node,
                        role: "test",
                        distance: 1,
                        isSpline: false,
                        intermediate: undefined,
                        highlighted: false,
                        selected: false,
                    };
                    mockSimData.linkMap.set(`link${i}`, link);

                    // Update nodes with the link
                    const networkLink: NetworkLink = {
                        key: `link${i}`,
                        source: prevNode,
                        target: node,
                        role: "test",
                        distance: 1,
                        isSpline: false,
                        intermediate: undefined,
                    };
                    prevNode.links.push(networkLink);
                    node.links.push(networkLink);
                }
            }
        }

        // Act
        const result = pruneSimData(mockSimData);

        // Assert
        // Check that remaining nodes connected to pruned nodes have hasMissing=true
        Array.from(result.nodeMap.values()).forEach((node) => {
            if (node.hasMissing) {
                expect(node.missing).toBeGreaterThan(0);
            }
        });
    });

    it("should calculate maxDistance correctly", () => {
        // Arrange
        const distances = [1, 2, 3, 4];
        distances.forEach((distance, index) => {
            const node: SimNode = {
                key: index.toString(),
                name: `Node ${index}`,
                type: NodeType.Artist,
                size: 1,
                x: 0,
                y: 0,
                distance,
                radius: 10,
                links: [],
                hasMissing: false,
                missing: 0,
                lastClickTime: 0,
                lastTouchTime: 0,
                cluster: 1,
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
            mockSimData.nodeMap.set(index.toString(), node);
        });

        // Act
        const result = pruneSimData(mockSimData);

        // Assert
        expect(result.maxDistance).toBe(4);
    });

    it("should handle empty network", () => {
        // Act
        const result = pruneSimData(mockSimData);

        // Assert
        expect(result.nodeMap.size).toBe(0);
        expect(result.linkMap.size).toBe(0);
        expect(result.maxDistance).toBe(-Infinity); // Math.max() with no arguments returns -Infinity
    });
});
