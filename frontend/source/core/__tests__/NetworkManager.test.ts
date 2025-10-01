import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type {
    NodeKey,
    LinkKey,
    SimData,
    SimNode,
    SimLink,
} from "../../network/data";
import { NodeType } from "../../network/data";
import { RequestNetworkEvent } from "../../network/events";
import { NetworkManager } from "../NetworkManager";
import { networkManager } from "../singletons";

// Mock d3 with comprehensive mock
vi.mock("d3", async () => {
    const { d3Mock } = await import("../../__tests__/setup/d3-mock");
    return d3Mock;
});

// Mock RequestNetworkEvent
vi.mock("../../network/events", () => ({
    RequestNetworkEvent: {
        EVENT_NAME: "musigree:request-network",
    },
}));

describe("NetworkManager", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe("constructor", () => {
        it("should initialize with default values when no config is provided", () => {
            const manager = new NetworkManager();

            // Check initial property values
            expect(manager.forceLayout).toBeNull();
            expect(manager.isRunningLayout).toBe(false);
            expect(manager.tick).toBe(0);
            expect(manager.newNodeCoords).toEqual([0, 0]);
            expect(manager.zoom).toBeNull();
            expect(manager.layers.root).toBeNull();
            expect(manager.layers.halo).toBeNull();
            expect(manager.layers.text).toBeNull();
            expect(manager.layers.node).toBeNull();
            expect(manager.layers.link).toBeNull();
            expect(manager.selectedNodeKey).toBeUndefined();

            // Check that data was initialized with empty data
            expect(manager.data.nodeMap).toBeInstanceOf(Map);
            expect(manager.data.nodeMap.size).toBe(0);
            expect(manager.data.linkMap).toBeInstanceOf(Map);
            expect(manager.data.linkMap.size).toBe(0);
        });

        it("should initialize with provided data when config is provided", () => {
            // Create mock data
            const mockNode: SimNode = {
                x: 100,
                y: 100,
                type: NodeType.Artist,
                key: "artist1",
                name: "Test Artist",
                size: 5,
                missing: 0,
                hasMissing: false,
                distance: 0,
                radius: 10,
                lastClickTime: 0,
                lastTouchTime: 0,
                links: [],
                cluster: 0,
                fixed: false,
                isIntermediate: false,
                vx: 0,
                vy: 0,
                index: 0,
                fx: null,
                fy: null,
                dragx: 0,
                dragy: 0,
                selected: false,
                highlighted: false,
            };

            const mockNodeMap = new Map<NodeKey, SimNode>();
            mockNodeMap.set("artist1", mockNode);

            const mockLinkMap = new Map<LinkKey, SimLink>();

            const mockData: SimData = {
                center: mockNode,
                nodeMap: mockNodeMap,
                linkMap: mockLinkMap,
                maxDistance: 1,
            };

            const manager = new NetworkManager({ initialData: mockData });

            // Verify data was set correctly
            expect(manager.data).toBe(mockData);
            expect(manager.data.nodeMap.size).toBe(1);
            expect(manager.data.nodeMap.get("artist1")).toBe(mockNode);
        });
    });

    describe("getters and setters", () => {
        let manager: NetworkManager;

        beforeEach(() => {
            manager = new NetworkManager();
        });

        it("should get and set forceLayout", () => {
            const mockForceLayout = {} as d3.Simulation<SimNode, SimLink>;

            expect(manager.forceLayout).toBeNull();
            manager.forceLayout = mockForceLayout;
            expect(manager.forceLayout).toBe(mockForceLayout);
        });

        it("should get and set isRunningLayout", () => {
            expect(manager.isRunningLayout).toBe(false);
            manager.isRunningLayout = true;
            expect(manager.isRunningLayout).toBe(true);
        });

        it("should get and set tick", () => {
            expect(manager.tick).toBe(0);
            manager.tick = 42;
            expect(manager.tick).toBe(42);
        });

        it("should get and set newNodeCoords", () => {
            expect(manager.newNodeCoords).toEqual([0, 0]);
            manager.newNodeCoords = [100, 200];
            expect(manager.newNodeCoords).toEqual([100, 200]);
        });

        it("should get and set zoom", () => {
            const mockZoom = {} as d3.ZoomBehavior<SVGGElement, unknown>;

            expect(manager.zoom).toBeNull();
            manager.zoom = mockZoom;
            expect(manager.zoom).toBe(mockZoom);
        });

        it("should get and set data", () => {
            const mockData = {
                center: {} as SimNode,
                nodeMap: new Map<NodeKey, SimNode>(),
                linkMap: new Map<LinkKey, SimLink>(),
                maxDistance: 0,
            };

            expect(manager.data).not.toBe(mockData);
            manager.data = mockData;
            expect(manager.data).toBe(mockData);
        });

        it("should get layers", () => {
            expect(manager.layers).toEqual({
                root: null,
                halo: null,
                text: null,
                node: null,
                link: null,
            });
        });

        it("should get and set selectedNodeKey", () => {
            expect(manager.selectedNodeKey).toBeUndefined();
            manager.selectedNodeKey = "test-node";
            expect(manager.selectedNodeKey).toBe("test-node");
            manager.selectedNodeKey = undefined;
            expect(manager.selectedNodeKey).toBeUndefined();
        });
    });

    describe("methods", () => {
        let manager: NetworkManager;
        let consoleSpy: any;

        beforeEach(() => {
            manager = new NetworkManager();
            consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
        });

        afterEach(() => {
            consoleSpy.mockRestore();
        });

        describe("dispose", () => {
            it("should attempt to remove event listeners", () => {
                const removeEventListenerSpy = vi.spyOn(
                    window,
                    "removeEventListener",
                );

                manager.dispose();

                expect(removeEventListenerSpy).toHaveBeenCalledWith(
                    "musigree:request-network",
                    undefined,
                );

                removeEventListenerSpy.mockRestore();
            });

            it("should stop force layout", () => {
                const mockForceLayout = {
                    stop: vi.fn(),
                } as unknown as d3.Simulation<SimNode, SimLink>;

                manager.forceLayout = mockForceLayout;
                manager.dispose();

                expect(mockForceLayout.stop).toHaveBeenCalled();
            });

            it("should clear data", () => {
                // Set up some data
                const mockNodeMap = new Map<NodeKey, SimNode>();
                mockNodeMap.set("node1", {} as SimNode);

                const mockLinkMap = new Map<LinkKey, SimLink>();
                mockLinkMap.set("link1", {} as SimLink);

                const mockData: SimData = {
                    center: {} as SimNode,
                    nodeMap: mockNodeMap,
                    linkMap: mockLinkMap,
                    maxDistance: 1,
                };

                manager.data = mockData;

                // Verify data exists before dispose
                expect(manager.data.nodeMap.size).toBe(1);
                expect(manager.data.linkMap.size).toBe(1);

                // Call dispose
                manager.dispose();

                // Verify data was cleared
                expect(manager.data.nodeMap.size).toBe(0);
                expect(manager.data.linkMap.size).toBe(0);
            });

            it("should handle errors during cleanup", () => {
                // Force an error during removeEventListener
                const removeEventListenerSpy = vi.spyOn(
                    window,
                    "removeEventListener",
                );
                removeEventListenerSpy.mockImplementation(() => {
                    throw new Error("Test error");
                });

                // Should not throw
                expect(() => manager.dispose()).not.toThrow();

                // Should log a warning
                expect(consoleSpy).toHaveBeenCalledWith(
                    "Failed to clean up network event listeners:",
                    expect.any(Error),
                );

                removeEventListenerSpy.mockRestore();
            });
        });
    });

    describe("singleton instance", () => {
        it("should export a singleton instance", () => {
            // The singleton is a Proxy, so we check its properties instead of instanceof
            expect(networkManager).toBeDefined();
            expect(networkManager.forceLayout).toBeNull();
            expect(typeof networkManager.isRunningLayout).toBe("boolean");
            expect(typeof networkManager.tick).toBe("number");
        });
    });
});
