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

/** Category name from the server role tree. Its children are structural links. */
export const STRUCTURAL_RELATIONSHIPS_CATEGORY = "Structural Relationships";

/** Checkboxes above the roles tree, in display order. */
export const STANDALONE_RELATIONSHIP_NAMES = [
    "Alias",
    "Member Of",
    "Released On",
    "Sublabel Of",
] as const;

/**
 * Home and artist pages start with these relationships checked.
 * Matches the server `UI_DEFAULT_ARTIST_ROLES` list.
 */
export const DEFAULT_ARTIST_RELATIONSHIP_NAMES = [
    "Alias",
    "Member Of",
] as const;

/**
 * Label pages start with this relationship checked.
 * Matches the server `UI_DEFAULT_LABEL_ROLES` list.
 */
export const DEFAULT_LABEL_RELATIONSHIP_NAMES = ["Released On"] as const;

/**
 * Relationships that still apply when Random loads an artist.
 * Released On and Sublabel Of describe labels, so they are turned off.
 */
export const RANDOM_ARTIST_RELATIONSHIP_NAMES =
    DEFAULT_ARTIST_RELATIONSHIP_NAMES;

const LABEL_ENTITY_TYPE = "label";
const ARTIST_ENTITY_TYPE = "artist";

/**
 * Relationship names restored by the relationships reset button.
 * The open entity wins over the address bar. A label uses Released On.
 * Home, artist, and any other page use Alias and Member Of.
 */
export const defaultRelationshipNames = (
    entityKey: string | null | undefined,
    pathname: string,
): readonly string[] => {
    const entityType = entityKey?.split("-")[0];
    if (entityType === ARTIST_ENTITY_TYPE) {
        return DEFAULT_ARTIST_RELATIONSHIP_NAMES;
    }
    if (
        entityType === LABEL_ENTITY_TYPE ||
        pathname === `/${LABEL_ENTITY_TYPE}` ||
        pathname.startsWith(`/${LABEL_ENTITY_TYPE}/`)
    ) {
        return DEFAULT_LABEL_RELATIONSHIP_NAMES;
    }
    return DEFAULT_ARTIST_RELATIONSHIP_NAMES;
};

/** Tells the open filters to match {@link resetFiltersForRandomArtist}. */
export const RANDOM_ARTIST_FILTER_RESET_EVENT =
    "musigree:random-artist-filter-reset";

const ROLE_TREE_RELATIONSHIP_ORDER = [
    "Collaborated With",
    "Compiled On",
    "Split With",
    "Other",
] as const;

const ROLE_TREE_RELATIONSHIP_INDEX = new Map<string, number>(
    ROLE_TREE_RELATIONSHIP_ORDER.map((name, index) => [name, index]),
);

export interface SplitRoleTree {
    relationships: TreeNode[];
    roles?: TreeConfig;
}

// Keep track of the selected role IDs when using react-arborist
let selectedRoleIds: Set<string | number> = new Set();

// Map of role IDs to their names for looking up text values
const roleIdToNameMap: Map<string | number, string> = new Map();

/** Ids of the relationship checkboxes, in display order. */
const standaloneRelationshipIds: (string | number)[] = [];

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

    // The roles tree rebuild drops every label. Keep the relationship
    // checkbox names so a later random reset can still find Alias and Member Of.
    const preservedRelationshipNames = new Map<string | number, string>();
    for (const id of standaloneRelationshipIds) {
        const name = roleIdToNameMap.get(id);
        if (name !== undefined) {
            preservedRelationshipNames.set(id, name);
        }
    }

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

    for (const [id, name] of preservedRelationshipNames) {
        roleIdToNameMap.set(id, name);
    }

    return rootNodes;
};

const isStructuralCategory = (node: TreeNode): boolean =>
    node.id === STRUCTURAL_RELATIONSHIPS_CATEGORY ||
    node.text === STRUCTURAL_RELATIONSHIPS_CATEGORY;

const compareTreeRelationships = (left: TreeNode, right: TreeNode): number => {
    const leftIndex =
        ROLE_TREE_RELATIONSHIP_INDEX.get(left.text) ??
        ROLE_TREE_RELATIONSHIP_INDEX.size;
    const rightIndex =
        ROLE_TREE_RELATIONSHIP_INDEX.get(right.text) ??
        ROLE_TREE_RELATIONSHIP_INDEX.size;
    if (leftIndex !== rightIndex) {
        return leftIndex - rightIndex;
    }
    return left.text.localeCompare(right.text);
};

/**
 * Pulls Alias, Member Of, Released On, and Sublabel Of out for the checkbox
 * group. The other structural links stay under Structural Relationships.
 */
export const splitRoleTree = (config?: TreeConfig): SplitRoleTree => {
    if (!config?.core?.data) {
        return { relationships: [] };
    }

    const standaloneNames = new Set<string>(STANDALONE_RELATIONSHIP_NAMES);
    const standaloneByName = new Map<string, TreeNode>();
    const treeRelationships: TreeNode[] = [];

    for (const node of config.core.data) {
        if (isStructuralCategory(node)) {
            continue;
        }
        if (node.parent !== STRUCTURAL_RELATIONSHIPS_CATEGORY) {
            continue;
        }
        if (standaloneNames.has(node.text)) {
            standaloneByName.set(node.text, node);
            continue;
        }
        treeRelationships.push({ ...node });
    }

    treeRelationships.sort(compareTreeRelationships);

    const roleNodes: TreeNode[] = [];
    for (const node of config.core.data) {
        if (isStructuralCategory(node)) {
            if (treeRelationships.length === 0) {
                continue;
            }
            roleNodes.push(node);
            roleNodes.push(...treeRelationships);
            continue;
        }
        if (node.parent === STRUCTURAL_RELATIONSHIPS_CATEGORY) {
            continue;
        }
        roleNodes.push(node);
    }

    const relationships = STANDALONE_RELATIONSHIP_NAMES.flatMap((name) => {
        const node = standaloneByName.get(name);
        return node ? [node] : [];
    });

    return {
        relationships,
        roles: {
            ...config,
            core: {
                ...config.core,
                data: roleNodes,
            },
        },
    };
};

/**
 * Role names from the page's roles query.
 * Undefined when that parameter is missing or empty, so the page tree keeps
 * the selection the server already marked.
 * A backslash escapes a comma inside a name, matching getSelectedRoles.
 */
export const rolesFromSearch = (search: string): string[] | undefined => {
    const params = new URLSearchParams(search);
    if (!params.has("roles")) {
        return undefined;
    }
    const names = splitRoleQuery(params.get("roles") ?? "");
    return names.length > 0 ? names : undefined;
};

const splitRoleQuery = (value: string): string[] => {
    const names: string[] = [];
    let current = "";
    for (let index = 0; index < value.length; index += 1) {
        const char = value[index];
        if (char === "\\" && value[index + 1] === ",") {
            current += ",";
            index += 1;
            continue;
        }
        if (char === ",") {
            const name = current.trim();
            if (name.length > 0) {
                names.push(name);
            }
            current = "";
            continue;
        }
        current += char;
    }
    const name = current.trim();
    if (name.length > 0) {
        names.push(name);
    }
    return names;
};

/**
 * Checks the roles named in the page URL and clears every other checkbox.
 * Alias, Member Of, Released On, and Sublabel Of are relationship
 * checkboxes, and they are named in this same roles parameter.
 * A category name checks that node and every role under it.
 * The tree is returned unchanged when the URL does not define roles.
 */
export const selectRolesFromSearch = (
    config: TreeConfig,
    search: string,
): TreeConfig => {
    const names = rolesFromSearch(search);
    if (names === undefined) {
        return config;
    }
    const requested = new Set(names);
    const childrenByParent = new Map<string | number, TreeNode[]>();
    for (const node of config.core.data) {
        if (node.parent === undefined || node.parent === "#") {
            continue;
        }
        const siblings = childrenByParent.get(node.parent);
        if (siblings) {
            siblings.push(node);
        } else {
            childrenByParent.set(node.parent, [node]);
        }
    }

    const selectedIds = new Set<string | number>();
    const selectNode = (node: TreeNode): void => {
        if (selectedIds.has(node.id)) {
            return;
        }
        selectedIds.add(node.id);
        for (const child of childrenByParent.get(node.id) ?? []) {
            selectNode(child);
        }
    };
    for (const node of config.core.data) {
        if (requested.has(node.text)) {
            selectNode(node);
        }
    }

    return {
        ...config,
        core: {
            ...config.core,
            data: config.core.data.map((node) => ({
                ...node,
                state: {
                    ...node.state,
                    selected: selectedIds.has(node.id),
                },
            })),
        },
    };
};

/**
 * Seeds Alias, Member Of, Released On, and Sublabel Of from Structural
 * Relationships in the page role tree.
 */
export const initializeStructuralRelationships = (
    config?: TreeConfig,
): void => {
    const { relationships } = splitRoleTree(config);
    rememberRelationships(relationships);
    replaceManagedRoleSelection(
        relationships.map((role) => role.id),
        relationships
            .filter((role) => role.state?.selected)
            .map((role) => role.id),
    );
};

/**
 * Records role labels without resetting names already stored for other nodes.
 */
export const rememberRoleNames = (nodes: TreeNode[]): void => {
    for (const node of nodes) {
        roleIdToNameMap.set(node.id, node.text);
    }
};

/**
 * Records the relationship checkbox ids used when Random resets the filters.
 */
export const rememberRelationships = (nodes: TreeNode[]): void => {
    rememberRoleNames(nodes);
    standaloneRelationshipIds.length = 0;
    for (const node of nodes) {
        standaloneRelationshipIds.push(node.id);
    }
};

/**
 * Clears the roles tree and leaves Alias and Member Of selected.
 * Random loads an artist, so label relationships are turned off.
 * The filter panels update from the event and do not start their own fetch.
 */
export const resetFiltersForRandomArtist = (): void => {
    const artistNames = new Set<string>(RANDOM_ARTIST_RELATIONSHIP_NAMES);
    const next = new Set<string | number>();
    for (const id of standaloneRelationshipIds) {
        const name = roleIdToNameMap.get(id);
        if (name !== undefined && artistNames.has(name)) {
            next.add(id);
        }
    }
    selectedRoleIds = next;
    window.dispatchEvent(new CustomEvent(RANDOM_ARTIST_FILTER_RESET_EVENT));
};

/**
 * Updates the set of selected role IDs
 * @param {string | number[]} ids - Array of selected role IDs
 */
export const updateSelectedRoleIds = (ids: (string | number)[]): void => {
    selectedRoleIds = new Set(ids);
};

/**
 * Replaces selection for one filter while leaving the other filter's ids in place.
 */
export const replaceManagedRoleSelection = (
    managedIds: readonly (string | number)[],
    selectedIds: readonly (string | number)[],
): void => {
    const managed = new Set(managedIds);
    const next = new Set(selectedRoleIds);
    for (const id of managed) {
        next.delete(id);
    }
    for (const id of selectedIds) {
        if (managed.has(id)) {
            next.add(id);
        }
    }
    selectedRoleIds = next;
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
        // The tree section is a grouping label. Send its roles individually
        // so a full selection does not expand to every structural link.
        if (parentId === STRUCTURAL_RELATIONSHIPS_CATEGORY) {
            return;
        }
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
        if (id === STRUCTURAL_RELATIONSHIPS_CATEGORY) {
            continue;
        }
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
