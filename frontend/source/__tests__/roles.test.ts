import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import * as rolesModule from "../roles";
import type { TreeConfig } from "../roles";
import {
    convertRolesToArboristFormat,
    updateSelectedRoleIds,
    getSelectedRoles,
} from "../roles";

/**
 * Test the isNumeric utility function
 * This is a private function in roles.ts, so we'll test it through its usage
 * in other functions rather than directly
 */
describe("roles.ts", () => {
    // Create a mock DOM environment before each test
    let treeContainer: HTMLElement;

    beforeEach(() => {
        // Create a container for the tree
        treeContainer = document.createElement("div");
        treeContainer.id = "jstree_div";
        document.body.appendChild(treeContainer);

        // Mock console methods
        vi.spyOn(console, "warn");
        vi.spyOn(console, "log");
    });

    afterEach(() => {
        // Clean up the DOM
        document.body.innerHTML = "";
        vi.resetAllMocks();

        // Reset any module state by calling with empty array
        updateSelectedRoleIds([]);
    });

    describe("convertRolesToArboristFormat", () => {
        it("should convert role data to arborist format with provided container", () => {
            // Mock the config
            const config: TreeConfig = {
                core: {
                    data: [
                        { id: "1", text: "Role 1" },
                        { id: "2", text: "Role 2", parent: "1" },
                    ],
                },
                plugins: ["checkbox"],
            };

            // Convert roles to arborist format
            const arboristNodes = convertRolesToArboristFormat(config);

            // Verify the conversion
            expect(arboristNodes).toHaveLength(1);
            expect(arboristNodes[0].id).toBe("1");
            expect(arboristNodes[0].name).toBe("Role 1");
            expect(arboristNodes[0].children).toHaveLength(1);
            expect(arboristNodes[0].children?.[0].id).toBe("2");
            expect(arboristNodes[0].children?.[0].name).toBe("Role 2");
        });

        it("should handle undefined config", () => {
            const arboristNodes = convertRolesToArboristFormat(undefined);
            expect(arboristNodes).toEqual([]);
        });

        it("should handle empty data array", () => {
            const config: TreeConfig = {
                core: {
                    data: [],
                },
            };
            const arboristNodes = convertRolesToArboristFormat(config);
            expect(arboristNodes).toEqual([]);
        });

        it("should properly mark selected nodes", () => {
            const config: TreeConfig = {
                core: {
                    data: [
                        {
                            id: "1",
                            text: "Role 1",
                            state: { selected: true },
                        },
                        { id: "2", text: "Role 2" },
                    ],
                },
            };

            const arboristNodes = convertRolesToArboristFormat(config);
            expect(arboristNodes[0].selected).toBe(true);
            expect(arboristNodes[1].selected).toBeUndefined();
        });
    });

    describe("getSelectedRoles", () => {
        it("should return an empty array if no roles are selected", () => {
            // Make sure selected roles are empty
            updateSelectedRoleIds([]);

            // Get selected roles
            const roles = getSelectedRoles();

            // Check result - should be empty array
            expect(roles).toEqual([]);
        });

        it("should return selected roles", () => {
            // Mock the config with pre-selected nodes
            const config: TreeConfig = {
                core: {
                    data: [
                        {
                            id: "parent1",
                            text: "Parent 1",
                            state: { selected: true },
                        },
                        { id: "child1", text: "Child 1", parent: "parent1" },
                        { id: "parent2", text: "Parent 2" },
                        {
                            id: "child2",
                            text: "Child 2",
                            parent: "parent2",
                            state: { selected: true },
                        },
                    ],
                },
                plugins: ["checkbox"],
            };

            // Initialize roles data
            convertRolesToArboristFormat(config);

            // Set the selected roles
            updateSelectedRoleIds(["parent1", "child2"]);

            // Get selected roles
            const roles = getSelectedRoles();

            // Should include both selected roles
            expect(roles).toContain("Parent 1");
            expect(roles).toContain("Child 2");
        });

        it("should handle numeric IDs properly", () => {
            // Create a tree with numeric IDs
            const config: TreeConfig = {
                core: {
                    data: [
                        { id: 1, text: "Role 1" },
                        { id: 2, text: "Role 2", parent: 1 },
                        { id: "3", text: "Role 3" }, // String ID
                    ],
                },
                plugins: ["checkbox"],
            };

            // Initialize roles data
            convertRolesToArboristFormat(config);

            // Set selected roles with both numeric and string IDs
            updateSelectedRoleIds([1, "3"]);

            // Get selected roles
            const roles = getSelectedRoles();

            // Should include both Role 1 and Role 3
            expect(roles).toContain("Role 1");
            expect(roles).toContain("Role 3");
            expect(roles).not.toContain("Role 2");
        });
    });

    // Additional test for edge cases
    describe("Edge Cases", () => {
        it("should handle empty tree data", () => {
            // Initialize with empty data
            const arboristNodes = convertRolesToArboristFormat({
                core: {
                    data: [],
                },
            });

            // Result should be an empty array
            expect(arboristNodes).toEqual([]);

            // Get selected roles should return empty array
            expect(getSelectedRoles()).toEqual([]);
        });

        it("should escape commas in role names", () => {
            // Create a tree with a role that contains a comma
            const config: TreeConfig = {
                core: {
                    data: [{ id: "1", text: "Role, with comma" }],
                },
            };

            // Initialize roles data
            convertRolesToArboristFormat(config);

            // Set the role as selected
            updateSelectedRoleIds(["1"]);

            // Get selected roles
            const roles = getSelectedRoles();

            // Should escape the comma
            expect(roles[0]).toBe("Role\\, with comma");
        });

        it("should handle nodes without parent", () => {
            // All nodes at root level
            const config: TreeConfig = {
                core: {
                    data: [
                        { id: "1", text: "Role 1" },
                        { id: "2", text: "Role 2" },
                        { id: "3", text: "Role 3" },
                    ],
                },
                plugins: ["checkbox"],
            };

            // Convert to arborist format
            const arboristNodes = convertRolesToArboristFormat(config);

            // Should have 3 root nodes
            expect(arboristNodes.length).toBe(3);
        });

        it("should return only parent roles when fully selected, not their children", () => {
            // Create a tree with parent-child relationships
            const config: TreeConfig = {
                core: {
                    data: [
                        { id: "parent1", text: "Parent 1" },
                        { id: "child1", text: "Child 1", parent: "parent1" },
                        { id: "child2", text: "Child 2", parent: "parent1" },
                        { id: "parent2", text: "Parent 2" },
                        { id: "child3", text: "Child 3", parent: "parent2" },
                        { id: "child4", text: "Child 4", parent: "parent2" },
                    ],
                },
                plugins: ["checkbox"],
            };

            // Initialize roles data
            convertRolesToArboristFormat(config);

            // Scenario 1: Select all children of parent1 and the parent itself
            updateSelectedRoleIds(["parent1", "child1", "child2"]);

            // Should only return the parent since it's fully selected
            const roles1 = getSelectedRoles();
            expect(roles1).toContain("Parent 1");
            expect(roles1).not.toContain("Child 1");
            expect(roles1).not.toContain("Child 2");
            expect(roles1.length).toBe(1);

            // Scenario 2: Select parent2 and only one of its children
            updateSelectedRoleIds(["parent2", "child3"]);

            // Should return both the parent and the selected child (not fully selected)
            const roles2 = getSelectedRoles();
            expect(roles2).toContain("Parent 2");
            expect(roles2).toContain("Child 3");
            expect(roles2).not.toContain("Child 4");
            expect(roles2.length).toBe(2);

            // Scenario 3: Mix of fully and partially selected parents
            updateSelectedRoleIds([
                "parent1",
                "child1",
                "child2",
                "parent2",
                "child3",
            ]);

            // Should return the fully selected parent1 (without children) and parent2 with child3
            const roles3 = getSelectedRoles();
            expect(roles3).toContain("Parent 1");
            expect(roles3).not.toContain("Child 1");
            expect(roles3).not.toContain("Child 2");
            expect(roles3).toContain("Parent 2");
            expect(roles3).toContain("Child 3");
            expect(roles3).not.toContain("Child 4");
            expect(roles3.length).toBe(3);
        });
    });
});
