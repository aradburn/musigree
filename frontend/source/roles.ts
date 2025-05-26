/**
 * Role management functionality for Musigree
 * This file handles role selection using the react-arborist library
 */

/**
 * Interface for tree node state
 */
// TODO - Add more properties as needed, simplify server side
export interface TreeNodeState {
    selected?: boolean;
}

/**
 * Interface for tree node data
 */
export interface TreeNode {
    id: string | number;
    text: string;
    icon?: string;
    parent?: string | number;
    state?: TreeNodeState;
}

/**
 * Interface for tree configuration
 */
export interface TreeConfig {
    core: {
        data: TreeNode[];
    };
    plugins?: string[];
}

/**
 * Interface for react-arborist node data
 */
export interface ArboristNode {
    id: string | number;
    name: string;
    children?: ArboristNode[];
    isLeaf?: boolean;
    selected?: boolean;
}

// Keep track of the selected role IDs when using react-arborist
let selectedRoleIds: Set<string | number> = new Set();

// Map of role IDs to their names for looking up text values
const roleIdToNameMap: Map<string | number, string> = new Map();

// Map to track parent-child relationships
const parentToChildrenMap: Map<
    string | number,
    Set<string | number>
> = new Map();
const childToParentMap: Map<string | number, string | number> = new Map();

/**
 * Converts TreeConfig data to the format expected by react-arborist
 * @param {TreeConfig} config - The tree configuration object
 * @returns {ArboristNode[]} Array of root nodes in react-arborist format
 */
export const convertRolesToArboristFormat = (
    config?: TreeConfig,
): ArboristNode[] => {
    if (!config?.core?.data) return [];

    const rootNodes: ArboristNode[] = [];
    const nodeMap = new Map<string | number, ArboristNode>();

    // Clear and rebuild the ID to name mapping
    roleIdToNameMap.clear();
    // Clear parent-child relationship maps
    parentToChildrenMap.clear();
    childToParentMap.clear();

    // First, create a map of all nodes
    config.core.data.forEach((node: TreeNode) => {
        // Store the mapping of ID to text
        roleIdToNameMap.set(node.id, node.text);

        const arboristNode: ArboristNode = {
            id: node.id,
            name: node.text,
            selected: node.state?.selected,
            children: [],
        };

        // Initialize selected nodes set based on the initial config
        if (node.state?.selected) {
            selectedRoleIds.add(node.id);
        }

        nodeMap.set(node.id, arboristNode);

        // Track parent-child relationships
        if (node.parent !== undefined) {
            // Add this node as a child of its parent
            if (!parentToChildrenMap.has(node.parent)) {
                parentToChildrenMap.set(
                    node.parent,
                    new Set<string | number>(),
                );
            }
            parentToChildrenMap.get(node.parent)?.add(node.id);

            // Record this node's parent
            childToParentMap.set(node.id, node.parent);
        }
    });

    // Then, build the hierarchy
    config.core.data.forEach((node: TreeNode) => {
        const arboristNode = nodeMap.get(node.id);
        if (!arboristNode) return;

        if (node.parent !== undefined && nodeMap.has(node.parent)) {
            const parentNode = nodeMap.get(node.parent);
            if (!parentNode.children) parentNode.children = [];
            parentNode.children.push(arboristNode);
        } else {
            // No parent, this is a root node
            rootNodes.push(arboristNode);
        }
    });

    // Mark leaf nodes
    nodeMap.forEach((node) => {
        if (!node.children || node.children.length === 0) {
            node.isLeaf = true;
            delete node.children;
        }
    });

    return rootNodes;
};

/**
 * Updates the set of selected role IDs
 * @param {string | number[]} ids - Array of selected role IDs
 */
export const updateSelectedRoleIds = (ids: (string | number)[]): void => {
    selectedRoleIds = new Set(ids);
};

/**
 * Gets the selected role names from the selection state
 * @returns {string[]} Array of selected role names, falling back to ID strings if name is not found
 */
export const getSelectedRoles = (): string[] => {
    // Get all the role IDs from the selectedRoleIds Set
    const selectedIds = Array.from(selectedRoleIds);

    // We'll collect roles that should be returned (excluding children of fully selected parents)
    const rolesToReturn = new Set<string | number>();

    // First pass: identify which parents have all their children selected
    const fullySelectedParents = new Set<string | number>();

    parentToChildrenMap.forEach((children, parentId) => {
        // Check if the parent is selected and if all its children are selected
        if (selectedRoleIds.has(parentId)) {
            const allChildrenSelected = Array.from(children).every((childId) =>
                selectedRoleIds.has(childId),
            );

            if (allChildrenSelected) {
                fullySelectedParents.add(parentId);
            }
        }
    });

    // Second pass: add selected roles to the result, excluding children of fully selected parents
    for (const id of selectedIds) {
        const parentId = childToParentMap.get(id);

        // Include the ID if:
        // 1. It has no parent, OR
        // 2. Its parent is not in the fullySelectedParents set, OR
        // 3. It is a parent that is fully selected
        if (
            parentId === undefined ||
            !fullySelectedParents.has(parentId) ||
            fullySelectedParents.has(id)
        ) {
            rolesToReturn.add(id);
        }
    }

    // Map IDs to names using the mapping, fall back to ID string if not found
    return Array.from(rolesToReturn).map((id) => {
        const text = roleIdToNameMap.get(id) || String(id);
        const escapedText = text.replace(/,/g, "\\,");
        return escapedText;
    });
};
