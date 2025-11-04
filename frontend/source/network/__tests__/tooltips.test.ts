import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import {
    TooltipManager,
    nodeTooltip,
    linkTooltip,
    hideAllTooltips,
} from "../tooltips";
import type { SimNode, SimLink } from "../data";
import { Tooltip } from "bootstrap";
import { NodeType } from "../data";

// Define type for mocked tooltip instance
interface MockedTooltip {
    show: () => void;
    dispose: () => void;
}

// Track tooltip instances for testing - use globalThis to avoid hoisting issues
declare global {
    var __tooltipInstances: Array<{
        show: ReturnType<typeof vi.fn>;
        dispose: ReturnType<typeof vi.fn>;
    }>;
}

// Mock Bootstrap's Tooltip class
vi.mock("bootstrap", () => {
    // Create a constructor function that can be spied on
    function MockTooltip(_element: Element, _options?: any) {
        const instance = {
            show: vi.fn(),
            dispose: vi.fn(),
        };
        if (!globalThis.__tooltipInstances) {
            globalThis.__tooltipInstances = [];
        }
        globalThis.__tooltipInstances.push(instance);
        return instance;
    }

    // Create a spy that wraps the constructor
    const TooltipSpy = vi.fn(MockTooltip);
    // Make it work with 'new'
    Object.setPrototypeOf(TooltipSpy, MockTooltip);
    Object.setPrototypeOf(MockTooltip.prototype, Object.prototype);

    return {
        Tooltip: TooltipSpy,
    };
});

// Helper to access tooltip instances
const getTooltipInstances = () => globalThis.__tooltipInstances || [];

// Test fixtures
const mockNode: SimNode = {
    key: "test-123",
    name: "Test Node",
    type: NodeType.Artist,
    size: 1,
    x: 0,
    y: 0,
    vx: 0,
    vy: 0,
    fx: null,
    fy: null,
    distance: 1,
    radius: 10,
    links: [],
    missing: 0,
    cluster: undefined,
    hasMissing: false,
    lastClickTime: 0,
    lastTouchTime: 0,
    fixed: false,
    isIntermediate: false,
    index: 0,
    dragx: 0,
    dragy: 0,
    highlighted: false,
    selected: false,
};

const mockSourceNode: SimNode = {
    ...mockNode,
    key: "source-123",
    name: "Source Node",
};

const mockTargetNode: SimNode = {
    ...mockNode,
    key: "target-123",
    name: "Target Node",
};

const mockLink: SimLink = {
    source: mockSourceNode,
    target: mockTargetNode,
    role: "Test Role",
    key: "test-link",
    isSpline: false,
    distance: 1,
    intermediate: undefined,
    highlighted: false,
    selected: false,
};

describe("TooltipManager", () => {
    let tooltipManager: TooltipManager<SimNode>;
    let element: HTMLDivElement;

    beforeEach(() => {
        // Reset all mocks and instances before each test
        vi.clearAllMocks();
        if (globalThis.__tooltipInstances) {
            globalThis.__tooltipInstances.length = 0;
        }

        // Create a fresh DOM element for each test
        element = document.createElement("div");

        // Create a new TooltipManager instance
        tooltipManager = new TooltipManager<SimNode>(
            (node) => `<span>${node.name}</span>`,
            {
                placement: "bottom",
                html: true,
            },
        );
    });

    afterEach(() => {
        tooltipManager.dispose();
    });

    it("should create a tooltip manager with correct options", () => {
        expect(tooltipManager).toBeInstanceOf(TooltipManager);
    });

    it("should show tooltip with correct content", () => {
        tooltipManager.show(mockNode, element);

        expect(vi.mocked(Tooltip)).toHaveBeenCalledWith(
            element,
            expect.objectContaining({
                placement: "bottom",
                html: true,
                title: "<span>Test Node</span>",
            }),
        );
    });

    it("should hide and dispose tooltip", () => {
        tooltipManager.show(mockNode, element);
        tooltipManager.hide();

        const instances = getTooltipInstances();
        expect(instances.length).toBeGreaterThan(0);
        expect(instances[0].dispose).toHaveBeenCalled();
    });

    it("should update tooltip content", () => {
        tooltipManager.show(mockNode, element);

        const updatedNode = { ...mockNode, name: "Updated Node" };
        tooltipManager.update(updatedNode);

        expect(vi.mocked(Tooltip)).toHaveBeenLastCalledWith(
            element,
            expect.objectContaining({
                title: "<span>Updated Node</span>",
            }),
        );
    });

    it("should not update tooltip if not shown", () => {
        tooltipManager.update(mockNode);
        expect(vi.mocked(Tooltip)).not.toHaveBeenCalled();
    });
});

describe("Exported tooltip instances", () => {
    let element: HTMLDivElement;

    beforeEach(() => {
        vi.clearAllMocks();
        if (globalThis.__tooltipInstances) {
            globalThis.__tooltipInstances.length = 0;
        }
        element = document.createElement("div");
    });

    it("should create node tooltip with correct content", () => {
        nodeTooltip.show(mockNode, element);

        expect(vi.mocked(Tooltip)).toHaveBeenCalledWith(
            element,
            expect.objectContaining({
                placement: "bottom",
                customClass: "d3-node-tooltip",
                title: "<span>Test Node</span>",
            }),
        );
    });

    it("should create link tooltip with correct content", () => {
        linkTooltip.show(mockLink, element);

        expect(vi.mocked(Tooltip)).toHaveBeenCalledWith(
            element,
            expect.objectContaining({
                placement: "top",
                customClass: "d3-link-tooltip",
                title: expect.stringContaining("Source Node"),
            }),
        );
    });

    describe("hideAllTooltips", () => {
        it("should hide node tooltip", () => {
            nodeTooltip.show(mockNode, element);
            hideAllTooltips();

            const instances = getTooltipInstances();
            expect(instances.length).toBeGreaterThanOrEqual(1);
            expect(instances[0].dispose).toHaveBeenCalled();
        });

        it("should hide link tooltip", () => {
            linkTooltip.show(mockLink, element);
            hideAllTooltips();

            const instances = getTooltipInstances();
            expect(instances.length).toBeGreaterThanOrEqual(1);
            expect(instances[0].dispose).toHaveBeenCalled();
        });

        it("should hide both tooltips when both are shown", () => {
            nodeTooltip.show(mockNode, element);
            const element2 = document.createElement("div");
            linkTooltip.show(mockLink, element2);

            hideAllTooltips();

            const instances = getTooltipInstances();
            expect(instances.length).toBeGreaterThanOrEqual(2);
            expect(instances[0].dispose).toHaveBeenCalled();
            expect(instances[1].dispose).toHaveBeenCalled();
        });
    });
});
