import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type * as d3 from "d3";
import {
    calculateSplineInner,
    generateSpline,
    getHullVertices,
    onTick,
    unlabeledRoles,
    TICK_THROTTLE,
    HULL_THROTTLE,
} from "../tick";
import { hideAllTooltips } from "../tooltips";
import type { SimNode, SimLink } from "../data";
import { NodeType } from "../data";
import { musigreeManager, networkManager } from "../../core/singletons";

// Mock dependencies
vi.mock("../tooltips", () => ({
    hideAllTooltips: vi.fn(),
}));

// Mock core managers
vi.mock("../../core", () => {
    const mockNetworkManager = {
        tick: 0,
        data: {
            center: null,
            nodeMap: new Map(),
            linkMap: new Map(),
            maxDistance: 0,
        },
        layers: {
            root: null,
            link: null,
            halo: null,
            node: null,
            text: null,
        },
        dimensions: [800, 600],
        forceLayout: null,
        isRunningLayout: false,
        newNodeCoords: [0, 0],
        zoom: null,
    };

    return {
        musigreeManager: {
            svgDimensions: [800, 600],
        },
        networkManager: mockNetworkManager,
    };
});

// Mock d3 functions we need
vi.mock("d3", async (importOriginal) => {
    const originalModule = await importOriginal();

    const mockAttr = vi.fn().mockReturnThis();
    const mockEach = vi.fn().mockReturnThis();
    const mockSelectInner = vi.fn().mockReturnValue({
        attr: mockAttr,
    });

    const mockSelectAll = vi.fn().mockReturnValue({
        attr: mockAttr,
        each: mockEach,
        select: mockSelectInner,
    });

    const mockSelect = vi.fn().mockReturnValue({
        selectAll: mockSelectAll,
        attr: mockAttr,
        each: mockEach,
    });

    return {
        ...(originalModule as object),
        select: mockSelect as unknown as typeof d3.select,
        polygonHull: vi
            .fn()
            .mockImplementation((points: Array<[number, number]>) => {
                // Simple mock implementation that returns the first and last points to form a hull
                if (!points || points.length < 2) return null;
                return [points[0], points[points.length - 1]] as [
                    number,
                    number,
                ][];
            }),
    };
});

describe("Network Visualization Functions", () => {
    describe("unlabeledRoles", () => {
        it("should contain the correct roles", () => {
            expect(unlabeledRoles).toEqual([
                "Alias",
                "Member Of",
                "Sublabel Of",
            ]);
        });
    });

    describe("calculateSplineInner", () => {
        it("should calculate correct intersection points when target is to the right and above", () => {
            const [newSX, newSY] = calculateSplineInner(0, 0, 10, 100, -100);
            expect(newSX).toBeCloseTo(7.071); // cos(45°) * 10
            expect(newSY).toBeCloseTo(-7.071); // sin(45°) * 10
        });

        it("should calculate correct intersection points when target is to the left and below", () => {
            const [newSX, newSY] = calculateSplineInner(0, 0, 10, -100, 100);
            expect(newSX).toBeCloseTo(-7.071);
            expect(newSY).toBeCloseTo(7.071);
        });
    });

    describe("generateSpline", () => {
        it("should generate straight line path when no intermediate point exists", () => {
            const link: SimLink = {
                source: { x: 0, y: 0, radius: 5 },
                target: { x: 100, y: 100, radius: 5 },
            } as SimLink;

            const path = generateSpline(link);
            expect(path).toBe("M 0,0 L 100,100");
        });

        it("should generate curved path when intermediate point exists", () => {
            const link: SimLink = {
                source: { x: 0, y: 0, radius: 5 },
                target: { x: 100, y: 100, radius: 5 },
                intermediate: { x: 50, y: 0 },
            } as SimLink;

            const path = generateSpline(link);
            expect(path).toMatch(/M .+,.+ S 50,0 .+,.+/);
        });
    });

    describe("getHullVertices", () => {
        it("should generate correct vertices for a single node", () => {
            const nodes: SimNode[] = [
                {
                    x: 100,
                    y: 100,
                    radius: 30,
                } as SimNode,
            ];

            const vertices = getHullVertices(nodes);
            expect(vertices).toHaveLength(4);
            expect(vertices).toContainEqual([110, 110]);
            expect(vertices).toContainEqual([110, 90]);
            expect(vertices).toContainEqual([90, 110]);
            expect(vertices).toContainEqual([90, 90]);
        });

        it("should generate correct number of vertices for multiple nodes", () => {
            const nodes: SimNode[] = [
                { x: 100, y: 100, radius: 30 },
                { x: 200, y: 200, radius: 30 },
            ] as SimNode[];

            const vertices = getHullVertices(nodes);
            expect(vertices).toHaveLength(8); // 4 vertices per node
        });
    });

    describe("onTick", () => {
        let mockSimulation: d3.Simulation<SimNode, undefined>;
        const testNodes: SimNode[] = [];

        // Create mock functions for each layer selection
        const mockEach = vi.fn();
        const mockAttr = vi.fn();
        const mockSelectPath = vi.fn().mockReturnValue({
            attr: mockAttr,
        });

        beforeEach(() => {
            mockSimulation = {
                alpha: () => 0.5,
                alphaTarget: vi.fn(),
                stop: vi.fn(),
                restart: vi.fn(),
                nodes: () => testNodes,
                force: vi.fn().mockReturnThis(),
                on: vi.fn(),
            } as unknown as d3.Simulation<SimNode, undefined>;

            // Reset network manager state
            networkManager.tick = 0;

            // Create link layer mock with chainable methods
            networkManager.layers.link = {
                selectAll: vi.fn().mockReturnValue({
                    each: mockEach,
                }),
            } as any;

            // Create halo layer mock with chainable methods
            networkManager.layers.halo = {
                selectAll: vi.fn().mockImplementation((selector) => {
                    if (selector === ".hull") {
                        return {
                            select: mockSelectPath,
                        };
                    }
                    return {
                        attr: mockAttr,
                    };
                }),
            } as any;

            // Create node layer mock with chainable methods
            networkManager.layers.node = {
                selectAll: vi.fn().mockReturnValue({
                    attr: mockAttr,
                }),
            } as any;

            // Create text layer mock with chainable methods
            networkManager.layers.text = {
                selectAll: vi.fn().mockReturnValue({
                    attr: mockAttr,
                }),
            } as any;

            // Clear any previous mock calls
            vi.clearAllMocks();
        });

        afterEach(() => {
            vi.clearAllMocks();
        });

        it("should increment the network tick counter", () => {
            onTick(mockSimulation);
            expect(networkManager.tick).toBe(1);
        });

        it("should call hideAllTooltips when update is needed", () => {
            // Set tick to ensure DOM update
            networkManager.tick = TICK_THROTTLE - 1;

            onTick(mockSimulation);
            expect(hideAllTooltips).toHaveBeenCalled();
        });

        it("should only update DOM elements on throttled ticks", () => {
            // Set tick to just before a throttled tick
            networkManager.tick = TICK_THROTTLE - 1;

            onTick(mockSimulation);
            expect(networkManager.tick).toBe(TICK_THROTTLE);
            expect(networkManager.layers.link.selectAll).toHaveBeenCalledWith(
                ".link",
            );
            expect(networkManager.layers.halo.selectAll).toHaveBeenCalledWith(
                ".node",
            );
            expect(hideAllTooltips).toHaveBeenCalled();

            // Reset mocks
            vi.clearAllMocks();

            // Set tick to non-throttled position
            networkManager.tick = TICK_THROTTLE + 1;

            onTick(mockSimulation);
            expect(networkManager.tick).toBe(TICK_THROTTLE + 2);
            expect(networkManager.layers.link.selectAll).not.toHaveBeenCalled();
            expect(hideAllTooltips).not.toHaveBeenCalled();
        });

        it("should only update hulls on their specific throttle", () => {
            // Set tick to just before a hull throttled tick
            networkManager.tick = HULL_THROTTLE - 1;

            onTick(mockSimulation);
            expect(networkManager.tick).toBe(HULL_THROTTLE);
            expect(networkManager.layers.halo.selectAll).toHaveBeenCalledWith(
                ".hull",
            );
            expect(mockSelectPath).toHaveBeenCalledWith("path");
        });

        it("should center the main node if it exists and is not fixed", () => {
            const centerNode: SimNode = {
                key: "center",
                name: "Center Node",
                type: NodeType.Artist,
                size: 10,
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
                dragx: 0,
                dragy: 0,
                fx: null,
                fy: null,
                vx: 0,
                vy: 0,
                index: 0,
                highlighted: false,
                selected: false,
            };

            // Set the same node object in both center and nodeMap
            networkManager.data.center = centerNode;
            networkManager.data.nodeMap.set("center", centerNode);

            // Set tick to throttled value to ensure processing
            networkManager.tick = TICK_THROTTLE - 1;

            // Ensure svgDimensions is set correctly for the centering logic
            musigreeManager.svgDimensions = [800, 600];

            onTick(mockSimulation);

            // Center node should be moved towards the center of the SVG
            expect(centerNode.x).toBeGreaterThan(0);
            expect(centerNode.y).toBeGreaterThan(0);
        });

        it("should not center the main node if it is fixed", () => {
            const centerNode: SimNode = {
                key: "center",
                name: "Center Node",
                type: NodeType.Artist,
                size: 10,
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
                fixed: true,
                isIntermediate: false,
                dragx: 0,
                dragy: 0,
                fx: null,
                fy: null,
                vx: 0,
                vy: 0,
                index: 0,
                highlighted: false,
                selected: false,
            };

            networkManager.data.center = {
                key: "center",
                name: "Center Node",
                type: NodeType.Artist,
                size: 10,
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
                fixed: true,
                isIntermediate: false,
            };
            networkManager.data.nodeMap.set("center", centerNode);

            // Set tick to throttled value to ensure processing
            networkManager.tick = TICK_THROTTLE - 1;

            onTick(mockSimulation);

            // Fixed node should not move
            expect(centerNode.x).toBe(0);
            expect(centerNode.y).toBe(0);
        });
    });
});
