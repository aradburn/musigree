import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as d3 from "d3";
import {
    initForceLayout,
    displayForceLayout,
    setForceLayoutNodes,
    restartForceLayout,
    stopForceLayout,
    setNetworkForces,
    resetNetworkForces,
} from "../forceLayout";
import type { SimNode, SimLink } from "../data";
import { NodeType } from "../data";
import { musigreeManager, networkManager } from "../../core";
import { FORCE } from "../../constants";

// Mock d3
vi.mock("d3", () => ({
    forceSimulation: vi.fn(() => ({
        force: vi.fn().mockReturnThis(),
        on: vi.fn().mockReturnThis(),
        stop: vi.fn().mockReturnThis(),
        nodes: vi.fn().mockReturnThis(),
        alpha: vi.fn().mockReturnThis(),
        restart: vi.fn().mockReturnThis(),
    })),
    forceCollide: vi.fn(() => ({
        radius: vi.fn().mockReturnThis(),
        iterations: vi.fn(),
    })),
    forceManyBody: vi.fn(() => ({
        strength: vi.fn().mockReturnThis(),
        distanceMax: vi.fn().mockReturnThis(),
        theta: vi.fn(),
    })),
    forceLink: vi.fn(() => ({
        id: vi.fn().mockReturnThis(),
        links: vi.fn().mockReturnThis(),
        distance: vi.fn().mockReturnThis(),
        iterations: vi.fn(),
    })),
    forceX: vi.fn(() => ({
        strength: vi.fn(),
    })),
    forceY: vi.fn(() => ({
        strength: vi.fn(),
    })),
    forceRadial: vi.fn(() => ({
        strength: vi.fn().mockReturnThis(),
    })),
    group: vi.fn(() => new Map()),
    arc: vi.fn(() => ({
        innerRadius: vi.fn().mockReturnThis(),
        outerRadius: vi.fn().mockReturnThis(),
        startAngle: vi.fn().mockReturnThis(),
        endAngle: vi.fn().mockReturnThis(),
    })),
    InternMap: vi.fn(function () {
        return new Map();
    }),
}));

// Mock core module with networkManager
vi.mock("../../core", () => {
    // Create a mock selectAll function inside the mock callback
    const innerMockSelectAll = vi.fn().mockReturnValue({
        data: vi.fn().mockReturnValue({
            join: vi.fn(),
        }),
        classed: vi.fn().mockReturnThis(),
    });

    return {
        musigreeManager: {
            svgDimensions: [800, 600],
        },
        networkManager: {
            data: {
                nodeMap: new Map(),
                linkMap: new Map(),
            },
            layers: {
                root: { selectAll: innerMockSelectAll },
                halo: { selectAll: innerMockSelectAll },
                node: { selectAll: innerMockSelectAll },
                text: { selectAll: innerMockSelectAll },
                link: { selectAll: innerMockSelectAll },
            },
            forceLayout: null,
            isRunningLayout: false,
            tick: 0,
        },
    };
});

// Mock window event dispatching
const dispatchEventSpy = vi
    .spyOn(window, "dispatchEvent")
    .mockImplementation(() => true);

// Create mock nodes and links for testing
const createMockNode = (
    key: string,
    props: Partial<SimNode> = {},
): SimNode => ({
    key,
    name: `Test Node ${key}`,
    type: NodeType.Artist,
    size: 10,
    x: 0,
    y: 0,
    missing: 0,
    hasMissing: false,
    lastClickTime: 0,
    lastTouchTime: 0,
    distance: 0,
    radius: 5,
    links: [],
    cluster: 1,
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
    ...props,
});

const createMockLink = (
    source: SimNode,
    target: SimNode,
    props: Partial<SimLink> = {},
): SimLink => ({
    key: `${source.key}-${target.key}`,
    source,
    target,
    role: "default",
    distance: 1,
    isSpline: false,
    intermediate: createMockNode("intermediate"),
    highlighted: false,
    selected: false,
    ...props,
});

// Mock DOM elements
beforeEach(() => {
    // Reset forceLayout
    networkManager.forceLayout = null;
});

afterEach(() => {
    vi.clearAllMocks();
});

describe("Force Layout Initialization", () => {
    it("should initialize force layout with correct configuration", () => {
        initForceLayout();
        expect(d3.forceSimulation).toHaveBeenCalled();
        expect(networkManager.forceLayout).toBeDefined();
    });

    it("should set up all required forces", () => {
        initForceLayout();
        expect(d3.forceCollide).toHaveBeenCalled();
        expect(networkManager.forceLayout.force).toHaveBeenCalledWith(
            "bbox",
            expect.any(Function),
        );
    });
});

describe("Force Layout Display and Control", () => {
    it("should display force layout correctly", () => {
        displayForceLayout();
        expect(networkManager.layers.halo.selectAll).toHaveBeenCalled();
        expect(networkManager.layers.node.selectAll).toHaveBeenCalled();
        expect(networkManager.layers.text.selectAll).toHaveBeenCalled();
        expect(networkManager.layers.link.selectAll).toHaveBeenCalled();
    });

    it("should start force layout with provided nodes", () => {
        const mockNodes: SimNode[] = [
            createMockNode("1", { x: 0, y: 0 }),
            createMockNode("2", { x: 100, y: 100 }),
        ];
        // Initialize force layout first
        networkManager.forceLayout = d3.forceSimulation();
        setForceLayoutNodes(mockNodes);
        expect(networkManager.forceLayout.nodes).toHaveBeenCalledWith(
            mockNodes,
        );
    });

    it("should restart force layout with new alpha value", () => {
        networkManager.forceLayout = d3.forceSimulation();
        restartForceLayout(FORCE.SIMULATION.ALPHA);
        expect(networkManager.forceLayout.alpha).toHaveBeenCalledWith(
            FORCE.SIMULATION.ALPHA,
        );
        expect(networkManager.forceLayout.restart).toHaveBeenCalled();
    });

    it("should stop force layout", () => {
        networkManager.forceLayout = d3.forceSimulation();
        stopForceLayout();
        expect(networkManager.forceLayout.stop).toHaveBeenCalled();
    });

    it("should handle force layout when not initialized", () => {
        networkManager.forceLayout = null;
        const consoleSpy = vi.spyOn(console, "error");
        restartForceLayout(FORCE.SIMULATION.ALPHA);
        expect(consoleSpy).toHaveBeenCalledWith(
            "Force layout is not initialized",
        );
    });
});

describe("Node and Link Processing", () => {
    it("should filter intermediate nodes from display", () => {
        const mockNodes = [
            createMockNode("1"),
            createMockNode("2", { isIntermediate: true }),
            createMockNode("3"),
        ];
        networkManager.data.nodeMap = new Map(
            mockNodes.map((node) => [node.key, node]),
        );

        displayForceLayout();

        // Verify that the layers were updated
        expect(networkManager.layers.node.selectAll).toHaveBeenCalledWith(
            ".node",
        );
        expect(networkManager.layers.halo.selectAll).toHaveBeenCalledWith(
            ".node",
        );
        expect(networkManager.layers.text.selectAll).toHaveBeenCalledWith(
            ".node",
        );
    });

    it("should filter spline links from display", () => {
        const node1 = createMockNode("1");
        const node2 = createMockNode("2");
        const mockLinks = [
            createMockLink(node1, node2),
            createMockLink(node1, node2, { isSpline: true }),
        ];
        networkManager.data.linkMap = new Map(
            mockLinks.map((link) => [link.key, link]),
        );

        displayForceLayout();

        // Verify that the link layer was updated
        expect(networkManager.layers.link.selectAll).toHaveBeenCalledWith(
            ".link",
        );
    });
});

describe("Error Handling", () => {
    it("should handle force layout operations when not initialized", () => {
        networkManager.forceLayout = null;
        const consoleSpy = vi.spyOn(console, "error");

        stopForceLayout();
        expect(consoleSpy).not.toHaveBeenCalled(); // stopForceLayout should handle null case silently

        restartForceLayout(FORCE.SIMULATION.ALPHA);
        expect(consoleSpy).toHaveBeenCalledWith(
            "Force layout is not initialized",
        );
    });
});

describe("Network Forces Control", () => {
    it("should dispatch set forces event", () => {
        setNetworkForces();
        expect(dispatchEventSpy).toHaveBeenCalled();
        const lastCall = dispatchEventSpy.mock.calls[0][0];
        expect(lastCall.type).toBe("musigree:set-forces");
    });

    it("should dispatch reset forces event", () => {
        resetNetworkForces();
        expect(dispatchEventSpy).toHaveBeenCalled();
        const lastCall = dispatchEventSpy.mock.calls[0][0];
        expect(lastCall.type).toBe("musigree:reset-forces");
    });
});

describe("Hull Processing", () => {
    it("should process hull data for clustered nodes", () => {
        const mockNodes = [
            createMockNode("1", { cluster: 1 }),
            createMockNode("2", { cluster: 1 }),
            createMockNode("3", { cluster: 2 }),
        ];
        networkManager.data.nodeMap = new Map(
            mockNodes.map((node) => [node.key, node]),
        );

        displayForceLayout();

        // Verify that the hull layer was updated
        expect(networkManager.layers.halo.selectAll).toHaveBeenCalledWith(
            ".hull",
        );
    });

    // New test for the case where no hull groups have more than one node
    it("should handle case when no hull groups have more than one node", () => {
        const mockNodes = [
            createMockNode("1", { cluster: 1 }),
            createMockNode("2", { cluster: 3 }),
            createMockNode("3", { cluster: 2 }),
        ];
        networkManager.data.nodeMap = new Map(
            mockNodes.map((node) => [node.key, node]),
        );

        displayForceLayout();

        // Verify that the hull layer was still called, but with empty data
        expect(networkManager.layers.halo.selectAll).toHaveBeenCalledWith(
            ".hull",
        );
    });
});

// New test suite for bboxForce functionality
describe("Boundary Force (bboxForce)", () => {
    it("should adjust node positions to keep them within SVG boundaries", () => {
        // Setup: Create force layout with nodes outside boundaries
        const outsideNodes: SimNode[] = [
            createMockNode("outside-right", { x: 1000, y: 300, radius: 10 }), // outside right
            createMockNode("outside-bottom", { x: 400, y: 1000, radius: 10 }), // outside bottom
            createMockNode("outside-left", { x: -100, y: 300, radius: 10 }), // outside left
            createMockNode("outside-top", { x: 400, y: -100, radius: 10 }), // outside top
            createMockNode("inside", { x: 400, y: 300, radius: 10 }), // inside boundaries
        ];

        // Initialize force layout and expose bboxForce
        initForceLayout();

        // We need to capture the bboxForce when it's added
        const forceFunction = (
            networkManager.forceLayout.force as any
        ).mock.calls.find((call: any[]) => call[0] === "bbox")[1];

        // Override the nodes in the simulation
        (networkManager.forceLayout as any).nodes = vi.fn(() => outsideNodes);

        // Call the bboxForce function directly
        forceFunction();

        // Assertions: Check that node positions were adjusted to boundaries
        // Right edge
        expect(outsideNodes[0].x).toBeLessThanOrEqual(
            musigreeManager.svgDimensions[0] -
                (outsideNodes[0].radius + FORCE.COLLIDE.BUFFER * 2),
        );

        // Bottom edge
        expect(outsideNodes[1].y).toBeLessThanOrEqual(
            musigreeManager.svgDimensions[1] -
                (outsideNodes[1].radius + FORCE.COLLIDE.BUFFER * 2),
        );

        // Left edge
        expect(outsideNodes[2].x).toBeGreaterThanOrEqual(
            outsideNodes[2].radius + FORCE.COLLIDE.BUFFER * 2,
        );

        // Top edge
        expect(outsideNodes[3].y).toBeGreaterThanOrEqual(
            outsideNodes[3].radius + FORCE.COLLIDE.BUFFER * 2,
        );

        // Inside node should not be changed
        expect(outsideNodes[4].x).toBe(400);
        expect(outsideNodes[4].y).toBe(300);
    });

    it("should handle nodes with undefined radius", () => {
        // Setup: Create force layout with a node that has undefined radius
        const noRadiusNode: SimNode[] = [
            createMockNode("no-radius", { x: 1000, y: 300, radius: undefined }),
        ];

        // Initialize force layout and expose bboxForce
        initForceLayout();

        // We need to capture the bboxForce when it's added
        const forceFunction = (
            networkManager.forceLayout.force as any
        ).mock.calls.find((call: any[]) => call[0] === "bbox")[1];

        // Override the nodes in the simulation
        (networkManager.forceLayout as any).nodes = vi.fn(() => noRadiusNode);

        // Call the bboxForce callback (should not throw error)
        expect(() => forceFunction()).not.toThrow();
    });

    it("should handle case when forceLayout.nodes returns undefined", () => {
        // Initialize force layout and expose bboxForce
        initForceLayout();

        // We need to capture the bboxForce when it's added
        const forceFunction = (
            networkManager.forceLayout.force as any
        ).mock.calls.find((call: any[]) => call[0] === "bbox")[1];

        // Override the nodes in the simulation to return undefined
        (networkManager.forceLayout as any).nodes = vi.fn(() => undefined);

        // Call the bboxForce callback
        expect(() => forceFunction()).not.toThrow();
    });
});

// Test the behavior of displayForceLayout in more detail
describe("ForceLayout Display Detailed Behavior", () => {
    it("should reset fixed flag for all nodes", () => {
        // Create nodes with fixed=true
        const mockNodes = [
            createMockNode("1", { fixed: true }),
            createMockNode("2", { fixed: true }),
        ];
        networkManager.data.nodeMap = new Map(
            mockNodes.map((node) => [node.key, node]),
        );

        displayForceLayout();

        // Verify that all nodes have fixed=false after displayForceLayout
        Array.from(networkManager.data.nodeMap.values()).forEach((node) => {
            expect(node.fixed).toBe(false);
        });
    });
});
