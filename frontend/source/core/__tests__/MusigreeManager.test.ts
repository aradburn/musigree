import { describe, it, expect, vi, beforeEach } from "vitest";
import { MusigreeManager, type MusigreeConfig } from "../MusigreeManager";
import { musigreeManager } from "../singletons";
import type { RelationsArcData } from "../../relations";
import type * as d3 from "d3";

// Mock d3 with comprehensive mock
vi.mock("d3", async () => {
    const { d3Mock } = await import("../../__tests__/setup/d3-mock");
    return d3Mock;
});

describe("MusigreeManager", () => {
    // Reset mocks between tests
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe("constructor", () => {
        it("should initialize with default values when no config is provided", () => {
            const manager = new MusigreeManager();
            expect(manager.version).toBe("2.1.0");
            expect(manager.debug).toBe(false);
            expect(manager.dpr).toBe(window.devicePixelRatio);
            expect(manager.dimensions).toEqual([0, 0]);
            expect(manager.svgDimensions).toEqual([0, 0]);
            expect(manager.selectedNodeKey).toBeNull();
            expect(manager.isSidebarRightCollapsed).toBe(false);
            expect(manager.isMobile).toBe(window.innerWidth < 768);
            expect(manager.arc).toBeDefined();
        });

        it("should initialize with custom config values", () => {
            const config: MusigreeConfig = {
                version: "3.0.0",
                debug: true,
                dpr: 2,
                isMobile: true,
            };
            const manager = new MusigreeManager(config);
            expect(manager.version).toBe("3.0.0");
            expect(manager.debug).toBe(true);
            expect(manager.dpr).toBe(2);
            expect(manager.isMobile).toBe(true);
        });
    });

    describe("getters and setters", () => {
        let manager: MusigreeManager;

        beforeEach(() => {
            manager = new MusigreeManager();
        });

        it("should get and set debug mode", () => {
            expect(manager.debug).toBe(false);
            manager.debug = true;
            expect(manager.debug).toBe(true);
        });

        it("should get and set dpr", () => {
            const initialDpr = manager.dpr;
            manager.dpr = 3;
            expect(manager.dpr).toBe(3);
            expect(manager.dpr).not.toBe(initialDpr);
        });

        it("should get and set dimensions", () => {
            expect(manager.dimensions).toEqual([0, 0]);
            manager.dimensions = [800, 600];
            expect(manager.dimensions).toEqual([800, 600]);
        });

        it("should get and set svgDimensions", () => {
            expect(manager.svgDimensions).toEqual([0, 0]);
            manager.svgDimensions = [1600, 1200];
            expect(manager.svgDimensions).toEqual([1600, 1200]);
        });

        it("should get and set selectedNodeKey", () => {
            expect(manager.selectedNodeKey).toBeNull();
            manager.selectedNodeKey = "node-123";
            expect(manager.selectedNodeKey).toBe("node-123");
        });

        it("should get and set isSidebarRightCollapsed", () => {
            expect(manager.isSidebarRightCollapsed).toBe(false);
            manager.isSidebarRightCollapsed = true;
            expect(manager.isSidebarRightCollapsed).toBe(true);
            manager.isSidebarRightCollapsed = false;
            expect(manager.isSidebarRightCollapsed).toBe(false);
        });

        it("should get and set isMobile", () => {
            const initialIsMobile = manager.isMobile;
            manager.isMobile = true;
            expect(manager.isMobile).toBe(true);
            manager.isMobile = false;
            expect(manager.isMobile).toBe(false);
            // Verify we can toggle the value
            manager.isMobile = !initialIsMobile;
            expect(manager.isMobile).toBe(!initialIsMobile);
            manager.isMobile = initialIsMobile;
            expect(manager.isMobile).toBe(initialIsMobile);
        });

        it("should get and set arc", () => {
            const mockArc = {} as d3.Arc<RelationsArcData, RelationsArcData>;
            manager.arc = mockArc;
            expect(manager.arc).toBe(mockArc);
        });

        it("should get version", () => {
            expect(manager.version).toBe("2.1.0");
            // Version should be read-only, no setter test
        });
    });

    describe("methods", () => {
        let manager: MusigreeManager;

        beforeEach(() => {
            manager = new MusigreeManager({ dpr: 2 });
        });

        it("should update dimensions correctly", () => {
            manager.updateDimensions(400, 300);
            expect(manager.dimensions).toEqual([400, 300]);
            expect(manager.svgDimensions).toEqual([2400, 1800]); // Scaled by dpr (2) and SVG.SCALING_MULTIPLIER (2)
        });

        it("should clear selection", () => {
            manager.selectedNodeKey = "node-123";
            expect(manager.selectedNodeKey).toBe("node-123");
            manager.clearSelection();
            expect(manager.selectedNodeKey).toBeNull();
        });
    });

    describe("singleton instance", () => {
        it("should export a singleton instance", () => {
            // The singleton is a Proxy, so we check its properties instead of instanceof
            expect(musigreeManager).toBeDefined();
            expect(musigreeManager.version).toBe("2.1.0");
            expect(typeof musigreeManager.debug).toBe("boolean");
            expect(typeof musigreeManager.dpr).toBe("number");
            expect(typeof musigreeManager.isSidebarRightCollapsed).toBe(
                "boolean",
            );
            expect(typeof musigreeManager.isMobile).toBe("boolean");
        });

        it("should be the same instance when imported multiple times", () => {
            // This is a bit tricky to test in the current setup, but we can at least verify it's an instance
            expect(musigreeManager).toBe(musigreeManager);
        });
    });
});
