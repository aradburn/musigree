/** @jsxImportSource react */
/**
 * Roles Overlay Component
 *
 * This component uses the react-arborist library for rendering
 * a tree view of roles.
 */
import React, { useEffect, useState, useRef } from "react";
import Offcanvas from "react-bootstrap/Offcanvas";
import { DOM_IDS } from "../../constants";
import type { TreeConfig } from "../../roles";
import {
    convertRolesToArboristFormat,
    updateSelectedRoleIds,
} from "../../roles";
// Import the actual component along with types
import { Tree } from "react-arborist";
import type { TreeApi } from "react-arborist";
// eslint-disable-next-line @typescript-eslint/no-unused-vars
import type { NodeApi } from "react-arborist";
import { useResizeObserver } from "../../hooks/useResizeObserver";
import { RequestNetworkEvent } from "../../network/events";

interface RolesOverlayProps {
    roles?: TreeConfig;
    show: boolean;
    onHide: () => void;
}

// Data structure expected by react-arborist
interface NodeData {
    id: string | number;
    name: string;
    children?: NodeData[];
    selected?: boolean;
    isLeaf?: boolean;
}

// Enum for checkbox states (none, some, all)
enum CheckboxState {
    None = 0,
    Some = 1,
    All = 2,
}

export const RolesOverlay: React.FC<RolesOverlayProps> = ({
    roles,
    show,
    onHide,
}): React.ReactElement => {
    const treeRef = useRef<TreeApi<NodeData>>(null);
    const containerRef = useRef<HTMLDivElement>(null);
    const [arboristData, setArboristData] = useState<NodeData[]>([]);
    const [navbarHeight, setNavbarHeight] = useState<number>(0);
    const [initialOpenState, setInitialOpenState] = useState<
        Record<string, boolean>
    >({});
    // Track selected node IDs
    const [selectedIds, setSelectedIds] = useState<Set<string | number>>(
        new Set(),
    );

    // Use the resize observer to get the container height
    const { height: containerHeight = 400 } = useResizeObserver({
        ref: containerRef,
        box: "border-box",
    });

    // Function to recursively get all descendant node IDs
    const getAllDescendantIds = (node: NodeData): (string | number)[] => {
        const ids: (string | number)[] = [];
        if (node.id) {
            ids.push(node.id);
        }

        if (node.children) {
            for (const child of node.children) {
                ids.push(...getAllDescendantIds(child));
            }
        }

        return ids;
    };

    // Function to check if node is parent
    const isParentNode = (node: NodeData): boolean => {
        return !!node.children && node.children.length > 0;
    };

    // Function to get the checkbox state for a node
    const getNodeCheckboxState = (node: NodeData): CheckboxState => {
        if (!isParentNode(node)) {
            // Leaf node - simple selected or not
            return selectedIds.has(node.id)
                ? CheckboxState.All
                : CheckboxState.None;
        }

        // For parent nodes, check all descendants
        const descendantIds = getAllDescendantIds(node).filter(
            (id) => id !== node.id,
        );
        if (descendantIds.length === 0) return CheckboxState.None;

        const selectedDescendants = descendantIds.filter((id) =>
            selectedIds.has(id),
        );

        if (selectedDescendants.length === 0) {
            return CheckboxState.None;
        } else if (selectedDescendants.length === descendantIds.length) {
            return CheckboxState.All;
        } else {
            return CheckboxState.Some;
        }
    };

    // Effect to convert roles data to arborist format
    useEffect(() => {
        if (roles) {
            // Use the conversion function from roles.ts
            const convertedData = convertRolesToArboristFormat(
                roles,
            ) as unknown as NodeData[];

            // Create an initialOpenState map where all nodes are explicitly closed
            const openStateMap: Record<string, boolean> = {};
            // Track initially selected node IDs
            const newSelectedIds = new Set<string | number>();

            // Function to recursively process nodes and set all to closed
            const processNode = (node: NodeData): void => {
                if (node.id) {
                    openStateMap[node.id.toString()] = false;

                    // Track selected nodes
                    if (node.selected) {
                        newSelectedIds.add(node.id);
                    }
                }

                if (node.children) {
                    node.children.forEach(processNode);
                }
            };

            // Process all nodes
            convertedData.forEach((node: NodeData): void => processNode(node));

            setArboristData(convertedData);
            setInitialOpenState(openStateMap);
            setSelectedIds(newSelectedIds);

            // Set initial selected IDs in the global state
            if (newSelectedIds.size > 0) {
                updateSelectedRoleIds(Array.from(newSelectedIds));
            }
        }
    }, [roles]);

    // Effect to measure the navbar height
    useEffect(() => {
        const updateNavbarHeight = (): void => {
            const navbar = document.querySelector("nav.navbar");
            if (navbar) {
                const height = navbar.getBoundingClientRect().height;
                setNavbarHeight(height);
            }
        };

        // Initial measurement
        updateNavbarHeight();

        // Update on window resize
        window.addEventListener("resize", updateNavbarHeight);

        // Cleanup
        return (): void => {
            window.removeEventListener("resize", updateNavbarHeight);
        };
    }, []);

    // Effect to apply selection when the tree is mounted or selectedIds changes
    useEffect(() => {
        // Use a timeout to ensure the tree is fully rendered before trying to select nodes
        const timer = setTimeout(() => {
            if (treeRef.current && selectedIds.size > 0) {
                // Don't try to use the tree's selection methods at all
                // They may not be working properly
            }
        }, 300);

        return (): void => clearTimeout(timer);
    }, [selectedIds, show]);

    // Function to handle node selection with parent-child relationship
    const handleNodeSelection = (
        nodeId: string | number,
        checked: boolean,
        nodeData: NodeData,
    ): void => {
        // Create a new set with current selections
        const newSelectedIds = new Set(selectedIds);

        // Helper to find direct parent of a node
        const findDirectParent = (
            childId: string | number,
            nodes: NodeData[],
        ): NodeData | null => {
            // Flat array to track the search path
            const flatSearch = (
                nodesArray: NodeData[],
                targetId: string | number,
            ): NodeData | null => {
                // First check if any node in this level is a direct parent
                for (const node of nodesArray) {
                    if (
                        node.children &&
                        node.children.some((child) => child.id === targetId)
                    ) {
                        return node; // Direct parent found
                    }
                }

                // If not found at this level, check all children recursively
                for (const node of nodesArray) {
                    if (node.children && node.children.length > 0) {
                        const found = flatSearch(node.children, targetId);
                        if (found) {
                            return found;
                        }
                    }
                }

                return null; // Not found
            };

            return flatSearch(nodes, childId);
        };

        // Process selection/deselection of current node and its descendants
        if (checked) {
            // Add this node to selection
            newSelectedIds.add(nodeId);

            // If node has children, select all descendants
            if (isParentNode(nodeData)) {
                getAllDescendantIds(nodeData)
                    .filter((id) => id !== nodeId)
                    .forEach((id) => newSelectedIds.add(id));
            }
        } else {
            // Remove this node from selection
            newSelectedIds.delete(nodeId);

            // If node has children, deselect all descendants
            if (isParentNode(nodeData)) {
                getAllDescendantIds(nodeData)
                    .filter((id) => id !== nodeId)
                    .forEach((id) => newSelectedIds.delete(id));
            }
        }

        // Function to update all parents in the hierarchy
        const updateAllParents = (startId: string | number): void => {
            let currentId = startId;
            let parent = findDirectParent(currentId, arboristData);

            // Continue until we've processed all parents up to the root
            while (parent) {
                // Find all direct children of this parent
                const childrenIds =
                    parent.children?.map((child) => child.id) || [];

                // Check if all children are selected
                const allChildrenSelected = childrenIds.every((id) =>
                    newSelectedIds.has(id),
                );
                // Check if some children are selected
                const someChildrenSelected = childrenIds.some((id) =>
                    newSelectedIds.has(id),
                );

                // Update parent selection state based on children
                if (allChildrenSelected) {
                    newSelectedIds.add(parent.id);
                } else if (!someChildrenSelected) {
                    newSelectedIds.delete(parent.id);
                }

                // Move up to next parent
                currentId = parent.id;
                parent = findDirectParent(currentId, arboristData);
            }
        };

        // Update all parent nodes in the hierarchy
        updateAllParents(nodeId);

        // Update our state
        setSelectedIds(newSelectedIds);
        // Update global state
        updateSelectedRoleIds(Array.from(newSelectedIds));
    };

    // If roles is undefined, we might not want to render anything
    if (!roles) {
        return <></>; // Empty fragment
    }

    const handleClose = (): void => {
        const event = new CustomEvent("musigree:hide-roles-overlay");
        window.dispatchEvent(event);

        // Dispatch a REQUEST_NETWORK event with empty detail
        window.dispatchEvent(new RequestNetworkEvent("", true));

        onHide();
    };

    // Custom styles for the offcanvas component
    const offcanvasStyle = {
        top: `${navbarHeight}px`,
        height: `calc(100% - ${navbarHeight}px)`,
    };

    // Helper to render the checkbox component based on state
    const renderCheckbox = (node: NodeData): React.ReactNode => {
        const checkboxState = getNodeCheckboxState(node);
        const isSelected = selectedIds.has(node.id);

        // Use a completely custom approach for indeterminate state
        if (checkboxState === CheckboxState.Some) {
            return (
                <div
                    style={{
                        position: "relative",
                        marginRight: "8px",
                        width: "18px",
                        height: "18px",
                        display: "inline-block",
                        backgroundColor: "#0d6efd", // Blue background
                        border: "1px solid #0d6efd",
                        borderRadius: "3px",
                        cursor: "pointer",
                    }}
                    onClick={(e) => {
                        e.stopPropagation();
                        // Toggle to checked state when clicked
                        handleNodeSelection(node.id, true, node);
                    }}
                >
                    <div
                        style={{
                            position: "absolute",
                            top: "50%",
                            left: "4px",
                            right: "4px",
                            height: "2px",
                            backgroundColor: "white",
                            transform: "translateY(-50%)",
                        }}
                    />
                </div>
            );
        }

        // Regular checkbox for selected/unselected states
        return (
            <div
                style={{
                    position: "relative",
                    marginRight: "8px",
                    width: "18px",
                    height: "18px",
                    display: "inline-block",
                }}
            >
                <input
                    type="checkbox"
                    style={{
                        margin: 0,
                        width: "100%",
                        height: "100%",
                        cursor: "pointer",
                    }}
                    checked={isSelected || checkboxState === CheckboxState.All}
                    onChange={(e) => {
                        e.stopPropagation();
                        handleNodeSelection(node.id, e.target.checked, node);
                    }}
                    onClick={(e) => e.stopPropagation()}
                />
            </div>
        );
    };

    return (
        <Offcanvas
            id={DOM_IDS.ROLES_OVERLAY}
            show={show}
            onHide={handleClose}
            placement="start"
            style={offcanvasStyle}
            className="roles-offcanvas"
            backdropClassName="roles-backdrop"
        >
            <Offcanvas.Header closeButton>
                <Offcanvas.Title id="roles-title">Roles</Offcanvas.Title>
            </Offcanvas.Header>

            <Offcanvas.Body>
                <div
                    id={DOM_IDS.ROLES_PANEL}
                    className="roles-panel"
                    style={{ height: "100%" }}
                    ref={containerRef}
                >
                    <Tree<NodeData>
                        ref={treeRef}
                        data={arboristData}
                        rowHeight={32}
                        padding={8}
                        disableDrag={true}
                        disableDrop={true}
                        width="100%"
                        height={containerHeight - 20}
                        selection="none"
                        className="roles-tree"
                        openByDefault={false}
                        initialOpenState={initialOpenState}
                    >
                        {({ node, style, dragHandle }) => {
                            // Get node checkbox state (Selected, Partial, None)
                            const _checkboxState = getNodeCheckboxState(
                                node.data,
                            );

                            return (
                                <div
                                    style={style}
                                    ref={dragHandle}
                                    title={node.data.name}
                                    onClick={(e) => {
                                        // Prevent bubbling to avoid tree selection
                                        e.stopPropagation();
                                    }}
                                >
                                    <div
                                        style={{
                                            display: "flex",
                                            alignItems: "center",
                                            cursor: "pointer",
                                            backgroundColor: selectedIds.has(
                                                node.id,
                                            )
                                                ? "#e0e0e0"
                                                : "transparent",
                                            padding: "4px 8px",
                                        }}
                                    >
                                        {node.isLeaf ? (
                                            <div
                                                style={{
                                                    width: "16px",
                                                    marginRight: "8px",
                                                }}
                                            />
                                        ) : (
                                            <div
                                                style={{
                                                    width: "16px",
                                                    height: "16px",
                                                    display: "flex",
                                                    justifyContent: "center",
                                                    alignItems: "center",
                                                    marginRight: "8px",
                                                    cursor: "pointer",
                                                    fontSize: "10px",
                                                    color: "#555",
                                                    backgroundColor: "white",
                                                }}
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    node.toggle();
                                                }}
                                            >
                                                <span
                                                    style={{
                                                        display: "inline-block",
                                                        backgroundColor:
                                                            "white",
                                                        width: "100%",
                                                        height: "100%",
                                                        textAlign: "center",
                                                        lineHeight: "16px",
                                                    }}
                                                >
                                                    {node.isOpen ? (
                                                        <svg
                                                            width="10"
                                                            height="10"
                                                            viewBox="0 0 10 10"
                                                        >
                                                            <path
                                                                d="M1 4L5 8L9 4"
                                                                fill="none"
                                                                stroke="#555"
                                                                strokeWidth="1.5"
                                                            />
                                                        </svg>
                                                    ) : (
                                                        <svg
                                                            width="10"
                                                            height="10"
                                                            viewBox="0 0 10 10"
                                                        >
                                                            <path
                                                                d="M4 1L8 5L4 9"
                                                                fill="none"
                                                                stroke="#555"
                                                                strokeWidth="1.5"
                                                            />
                                                        </svg>
                                                    )}
                                                </span>
                                            </div>
                                        )}

                                        {/* Use the custom checkbox rendering function */}
                                        {renderCheckbox(node.data)}

                                        <span
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                if (!node.isLeaf) {
                                                    node.toggle();
                                                }
                                            }}
                                        >
                                            {node.data.name}
                                        </span>
                                    </div>
                                </div>
                            );
                        }}
                    </Tree>

                    {/* Temporary placeholder that displays when no data is available */}
                    {arboristData.length === 0 && show && (
                        <div
                            id={DOM_IDS.ROLES_CONTAINER}
                            className="roles-container"
                        >
                            <p>Loading roles data...</p>
                        </div>
                    )}
                </div>
            </Offcanvas.Body>
        </Offcanvas>
    );
};
