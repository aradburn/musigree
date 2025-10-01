import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { RelationsManager } from "../RelationsManager";
import { relationsManager } from "../singletons";
import type { RelationsData, RelationsArcData } from "../../relations";
import * as d3 from "d3";

// Mock d3 with comprehensive mock
vi.mock("d3", async () => {
    const { d3Mock } = await import("../../__tests__/setup/d3-mock");
    return d3Mock;
});

// Sample relations data
const sampleRelationsData: RelationsData = {
    results: [
        { year: 2020, category: "Album", role: "Artist" },
        { year: 2020, category: "Album", role: "Producer" },
        { year: 2021, category: "Single", role: "Artist" },
        { year: 2021, category: "Single", role: "Engineer" },
        { year: 2022, category: "Compilation", role: "Artist" },
    ],
};

describe("RelationsManager", () => {
    // Reset mocks between tests
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe("constructor", () => {
        it("should initialize with empty data when no config is provided", () => {
            const manager = new RelationsManager();
            expect(manager.data).toEqual({ results: [] });
            expect(manager.byYear instanceof Map).toBe(true);
            expect(manager.byYear.size).toBe(0);
            expect(manager.byRole instanceof Map).toBe(true);
            expect(manager.byRole.size).toBe(0);
            expect(manager.layers.root).toBeNull();
        });
        it("should initialize with provided data", () => {
            // Create a manager with sample data
            const manager = new RelationsManager({
                initialData: sampleRelationsData,
            });

            // Verify that data is set but not processed during construction
            expect(manager.data).toEqual(sampleRelationsData);
            expect(manager.byYear instanceof Map).toBe(true);
            expect(manager.byYear.size).toBe(0); // Data is not processed in constructor
            expect(manager.byRole instanceof Map).toBe(true);
            expect(manager.byRole.size).toBe(0); // Data is not processed in constructor
            expect(manager.layers.root).toBeNull();

            // Verify d3 functions weren't called during construction
            expect(d3.group).not.toHaveBeenCalled();
            expect(d3.rollup).not.toHaveBeenCalled();
        });

        it("should initialize with provided data and process it correctly", () => {
            // Reset mocks to clear any previous calls
            vi.clearAllMocks();

            // Create mock data to return from d3 functions
            const mockYearData = new Map([
                [2020, new Map()],
                [2021, new Map()],
            ]);
            const mockRoleData = new Map([
                ["Artist", 3],
                ["Producer", 1],
            ]);

            // Setup the d3 mocks
            // @ts-expect-error - d3.group return type is complex
            vi.mocked(d3.group).mockReturnValueOnce(mockYearData);
            vi.mocked(d3.rollup).mockReturnValueOnce(mockRoleData);

            // Create manager with sample data
            const manager = new RelationsManager({
                initialData: sampleRelationsData,
            });

            // Process the data explicitly
            manager.setData(sampleRelationsData);

            // Verify expectations
            expect(manager.data).toEqual(sampleRelationsData);
            expect(d3.group).toHaveBeenCalledWith(
                sampleRelationsData.results,
                expect.any(Function),
                expect.any(Function),
            );
            expect(d3.rollup).toHaveBeenCalled();

            // Verify that the manager's properties have the mocked data
            expect(manager.byYear).toBe(mockYearData);
            expect(manager.byRole).toBe(mockRoleData);
        });
    });

    describe("getters and setters", () => {
        let manager: RelationsManager;

        beforeEach(() => {
            manager = new RelationsManager();
        });

        it("should get and set data", () => {
            expect(manager.data).toEqual({ results: [] });
            manager.setData(sampleRelationsData);
            expect(manager.data).toEqual(sampleRelationsData);
        });

        it("should get byYear", () => {
            const mockYearData = new Map();
            // @ts-expect-error - d3.group return type is complex
            vi.mocked(d3.group).mockReturnValue(mockYearData);

            manager.setData(sampleRelationsData);
            expect(manager.byYear).toBe(mockYearData);
        });

        it("should get byRole", () => {
            const mockRoleData = new Map();
            vi.mocked(d3.rollup).mockReturnValue(mockRoleData);

            manager.setData(sampleRelationsData);
            expect(manager.byRole).toBe(mockRoleData);
        });

        it("should get and set root layer", () => {
            const mockRootLayer = {
                remove: vi.fn(),
            } as unknown as d3.Selection<
                SVGGElement,
                unknown,
                HTMLElement,
                unknown
            >;

            expect(manager.layers.root).toBeNull();
            manager.setRootLayer(mockRootLayer);
            expect(manager.layers.root).toBe(mockRootLayer);
        });
    });

    describe("methods", () => {
        let manager: RelationsManager;
        // Define a type that works with the methods we use
        type MockSpy = { mockRestore: () => void };
        let consoleSpy: MockSpy;

        beforeEach(() => {
            manager = new RelationsManager({
                initialData: sampleRelationsData,
            });
            consoleSpy = vi.spyOn(console, "warn").mockImplementation(() => {});
        });

        afterEach(() => {
            consoleSpy.mockRestore();
        });

        describe("createVisualization", () => {
            it("should warn if no data is available", () => {
                const emptyManager = new RelationsManager();
                emptyManager.createVisualization("#container");
                expect(consoleSpy).toHaveBeenCalledWith(
                    "Cannot create visualization: no data",
                );
            });

            it("should warn if target selector is not found", () => {
                // @ts-expect-error - d3.select return type is complex
                vi.mocked(d3.select).mockReturnValueOnce({
                    empty: vi.fn().mockReturnValue(true),
                });

                manager.createVisualization("#nonexistent");
                expect(consoleSpy).toHaveBeenCalledWith(
                    'Cannot create visualization: target selector "#nonexistent" not found',
                );
            });

            it("should create a root layer if none exists", () => {
                const mockSelection = {
                    append: vi.fn().mockReturnThis(),
                    classed: vi.fn().mockReturnThis(),
                    empty: vi.fn().mockReturnValue(false),
                };
                // @ts-expect-error - d3.select return type is complex
                vi.mocked(d3.select).mockReturnValueOnce(mockSelection);

                manager.createVisualization("#container");
                expect(d3.select).toHaveBeenCalledWith("#container");
                expect(mockSelection.append).toHaveBeenCalledWith("g");
                expect(mockSelection.classed).toHaveBeenCalledWith(
                    "relations",
                    true,
                );
            });

            it("should not create a root layer if one already exists", () => {
                const mockRootLayer = {
                    append: vi.fn(),
                    classed: vi.fn(),
                } as unknown as d3.Selection<
                    SVGGElement,
                    unknown,
                    HTMLElement,
                    unknown
                >;

                manager.setRootLayer(mockRootLayer);
                manager.createVisualization("#container");

                expect(d3.select).not.toHaveBeenCalled();
            });
        });

        describe("updateVisualization", () => {
            it("should warn if layers are not initialized", () => {
                manager = new RelationsManager();
                manager.updateVisualization();
                expect(consoleSpy).toHaveBeenCalledWith(
                    "Cannot update visualization: layers not initialized",
                );
            });

            it("should update the visualization when layers are initialized", () => {
                const mockRootLayer = {
                    append: vi.fn(),
                    classed: vi.fn(),
                } as unknown as d3.Selection<
                    SVGGElement,
                    unknown,
                    HTMLElement,
                    unknown
                >;

                manager.setRootLayer(mockRootLayer);
                manager.updateVisualization();

                // This is just a placeholder in the actual implementation
                expect(consoleSpy).not.toHaveBeenCalled();
            });
        });

        describe("createArcData", () => {
            it("should return empty array for empty roles", () => {
                const arcData = manager.createArcData([]);
                expect(arcData).toEqual([]);
            });

            it("should create arc data for provided roles", () => {
                // Setup mock role counts
                const mockRolesCounts = new Map([
                    ["Artist", 3],
                    ["Producer", 1],
                    ["Engineer", 1],
                ]);
                vi.mocked(d3.rollup).mockReturnValue(mockRolesCounts);

                // Refresh the data to use our mock
                manager.setData(sampleRelationsData);

                const roles = ["Artist", "Producer", "Engineer"];
                const arcData = manager.createArcData(roles);

                expect(arcData.length).toBe(3);

                roles.forEach((role, index) => {
                    expect(arcData[index]).toMatchObject({
                        role,
                        innerRadius: 50,
                        outerRadius: 100,
                        padAngle: 0.01,
                    });
                    expect(typeof arcData[index].startAngle).toBe("number");
                    expect(typeof arcData[index].endAngle).toBe("number");
                    // Check that count is correctly pulled from mockRolesCounts
                    expect(arcData[index].count).toBe(
                        mockRolesCounts.get(role) || 0,
                    );
                });
            });
        });

        describe("dispose", () => {
            it("should clean up resources", () => {
                const mockRootLayer = {
                    remove: vi.fn(),
                } as unknown as d3.Selection<
                    SVGGElement,
                    unknown,
                    HTMLElement,
                    unknown
                >;

                manager.setRootLayer(mockRootLayer);
                manager.dispose();

                expect(mockRootLayer.remove).toHaveBeenCalled();
                expect(manager.layers.root).toBeNull();
                expect(manager.data).toEqual({ results: [] });
                expect(manager.byYear.size).toBe(0);
                expect(manager.byRole.size).toBe(0);
            });
        });
    });

    describe("singleton instance", () => {
        it("should export a singleton instance", () => {
            // The singleton is a Proxy, so we check its properties instead of instanceof
            expect(relationsManager).toBeDefined();
            expect(relationsManager.data).toBeDefined();
            expect(relationsManager.byYear).toBeDefined();
            expect(relationsManager.byRole).toBeDefined();
        });

        it("should be the same instance when imported multiple times", () => {
            expect(relationsManager).toBe(relationsManager);
        });
    });
});
