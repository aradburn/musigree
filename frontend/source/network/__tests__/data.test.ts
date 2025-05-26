import { describe, it, expect, beforeEach, vi } from "vitest";
import {
    processAPINetworkDataResponse,
    convertNetworkDataToSimData,
    updateGlobalData,
    type NetworkData,
    type SimData,
} from "../data";
import type { APINetworkDataResponse } from "../../api";
import { musigreeManager, networkManager } from "../../core";
import { NodeType } from "../data";

// Mock data for testing
const mockAPIResponse: APINetworkDataResponse = {
    nodes: [
        {
            key: "node1",
            name: "Artist 1",
            type: "artist",
            size: 10,
            distance: 0,
            cluster: 1,
            missing: 0,
            id: "1",
        },
        {
            key: "node2",
            name: "Label 1",
            type: "label",
            size: 8,
            distance: 1,
            cluster: 1,
            missing: 2,
            id: "2",
        },
    ],
    links: [
        {
            key: "link1",
            source: "node1",
            target: "node2",
            role: "Released On",
        },
    ],
    center: {
        key: "node1",
        name: "Artist 1",
    },
};

// Reset mock data before each test
beforeEach(() => {
    vi.clearAllMocks();
});

describe("Network Data Processing", () => {
    describe("processAPINetworkDataResponse", () => {
        it("should process valid API response correctly", () => {
            const result = processAPINetworkDataResponse(mockAPIResponse);

            // Check if result has correct structure
            expect(result).toHaveProperty("nodeMap");
            expect(result).toHaveProperty("center");
            expect(result).toHaveProperty("linkMap");
            expect(result).toHaveProperty("maxDistance");

            // Check if nodes are processed correctly
            const node1 = result.nodeMap.get("node1");
            expect(node1).toBeDefined();
            expect(node1.name).toBe("Artist 1");
            expect(node1.type).toBe(NodeType.Artist);
            expect(node1.size).toBe(10);

            // Check if links are processed correctly
            const link = result.linkMap.get("link1");
            expect(link).toBeDefined();
            expect(link.source.key).toBe("node1");
            expect(link.target.key).toBe("node2");
            expect(link.role).toBe("Released On");
        });

        it("should throw error for invalid API response", () => {
            const invalidResponse: APINetworkDataResponse = null;
            expect(() =>
                processAPINetworkDataResponse(invalidResponse),
            ).toThrow("Invalid network data format");
        });

        it("should handle missing nodes or links", () => {
            const incompleteResponse = {
                nodes: [],
                links: [],
                center: { key: "node1", name: "Test Node" },
            } as APINetworkDataResponse;
            expect(() =>
                processAPINetworkDataResponse(incompleteResponse),
            ).toThrow();
        });
    });

    describe("convertNetworkDataToSimData", () => {
        let networkData: NetworkData;

        beforeEach(() => {
            networkData = processAPINetworkDataResponse(mockAPIResponse);
        });

        it("should convert NetworkData to SimData correctly", () => {
            const result = convertNetworkDataToSimData(networkData);

            // Check if result has correct structure
            expect(result).toHaveProperty("nodeMap");
            expect(result).toHaveProperty("center");
            expect(result).toHaveProperty("linkMap");
            expect(result).toHaveProperty("maxDistance");

            // Check if nodes are converted correctly
            const simNode = result.nodeMap.get("node1");
            expect(simNode).toBeDefined();
            expect(simNode.name).toBe("Artist 1");
            expect(simNode.type).toBe(NodeType.Artist);
            expect(simNode.isIntermediate).toBe(false);

            // Check if links are converted correctly with intermediate nodes
            const links = Array.from(result.linkMap.values());
            const splineLinks = links.filter((link) => link.isSpline);
            expect(splineLinks.length).toBeGreaterThan(0);
        });

        it("should handle Alias links differently", () => {
            const aliasResponse = {
                ...mockAPIResponse,
                links: [
                    {
                        key: "aliasLink",
                        source: "node1",
                        target: "node2",
                        role: "Alias",
                    },
                ],
            };
            const aliasNetworkData =
                processAPINetworkDataResponse(aliasResponse);
            const result = convertNetworkDataToSimData(aliasNetworkData);

            // Check if Alias links don't create intermediate nodes
            const aliasLink = result.linkMap.get("aliasLink");
            expect(aliasLink).toBeDefined();
            expect(aliasLink.isSpline).toBe(false);
            expect(aliasLink.intermediate).toBeUndefined();
        });
    });

    describe("updateGlobalData", () => {
        it("should update global data correctly", () => {
            const networkData = processAPINetworkDataResponse(mockAPIResponse);
            const simData = convertNetworkDataToSimData(networkData);

            updateGlobalData(simData);

            // Check if global data is updated
            expect(networkManager.data.nodeMap).toBe(simData.nodeMap);
            expect(networkManager.data.linkMap).toBe(simData.linkMap);
            expect(networkManager.data.maxDistance).toBe(simData.maxDistance);
            expect(networkManager.data.center).toBe(simData.center);
        });
    });
});
