/** @jsxImportSource react */
/**
 * Roles filter shown in the left sidebar.
 * The heading reset clears this tree and reloads the network the same way a
 * checkbox change does. Uses react-arborist for the role tree.
 */
import React, { useCallback, useEffect, useRef, useState } from "react";
import { Tree } from "react-arborist";
import type { RowRendererProps, TreeApi } from "react-arborist";
import {
    RANDOM_ARTIST_FILTER_RESET_EVENT,
    convertRolesToArboristFormat,
    replaceManagedRoleSelection,
} from "../../roles";
import type { TreeConfig } from "../../roles";

interface RolesFilterProps {
    roles?: TreeConfig;
    onSelectionChange: () => void;
}

interface NodeData {
    id: string | number;
    name: string;
    children?: NodeData[];
    selected?: boolean;
    isLeaf?: boolean;
}

enum CheckboxState {
    None = 0,
    Some = 1,
    All = 2,
}

/** Row height in rem. The virtual list still positions rows in pixels. */
const ROLE_ROW_HEIGHT_REM = 1.8;
const ROOT_FONT_SIZE_FALLBACK_PX = 16;
/** Offset added to each row's top, plus the same gap below the last row. */
const TREE_VERTICAL_PADDING = 2;

const rootFontSizePx = (): number => {
    if (typeof document === "undefined") {
        return ROOT_FONT_SIZE_FALLBACK_PX;
    }
    const fontSize = Number.parseFloat(
        getComputedStyle(document.documentElement).fontSize,
    );
    return Number.isFinite(fontSize) && fontSize > 0
        ? fontSize
        : ROOT_FONT_SIZE_FALLBACK_PX;
};

const roleRowHeightPx = (): number => ROLE_ROW_HEIGHT_REM * rootFontSizePx();

const treeHeightForRows = (rowCount: number): number =>
    rowCount * roleRowHeightPx() + TREE_VERTICAL_PADDING * 2;

const pxLengthToRem = (value: string | number): string => {
    const pixels = typeof value === "number" ? value : Number.parseFloat(value);
    return `${pixels / rootFontSizePx()}rem`;
};

/** Count rows that are actually shown. The virtual list updates after render. */
const countVisibleRows = (node: TreeApi<NodeData>["root"]): number => {
    const self = node.level >= 0 ? 1 : 0;
    if (!node.isOpen || !node.children) {
        return self;
    }
    let count = self;
    for (const child of node.children) {
        count += countVisibleRows(child);
    }
    return count;
};

/** Writes the virtual list's pixel row height as rem on the treeitem element. */
const RoleTreeRow = ({
    node,
    attrs,
    innerRef,
    children,
}: RowRendererProps<NodeData>): React.ReactElement => {
    const style = { ...attrs.style };
    if (style?.height !== undefined) {
        style.height = pxLengthToRem(style.height);
    }
    return (
        <div
            {...attrs}
            style={style}
            ref={innerRef}
            onFocus={(event) => {
                event.stopPropagation();
            }}
            onClick={(event) => {
                node.handleClick(event);
            }}
        >
            {children}
        </div>
    );
};

const collectNodeIds = (nodes: NodeData[]): (string | number)[] => {
    const ids: (string | number)[] = [];
    const visit = (node: NodeData): void => {
        ids.push(node.id);
        node.children?.forEach(visit);
    };
    nodes.forEach(visit);
    return ids;
};

export const RolesFilter: React.FC<RolesFilterProps> = ({
    roles,
    onSelectionChange,
}): React.ReactElement => {
    const treeRef = useRef<TreeApi<NodeData>>(null);
    const [arboristData, setArboristData] = useState<NodeData[]>([]);
    const [initialOpenState, setInitialOpenState] = useState<
        Record<string, boolean>
    >({});
    const [selectedIds, setSelectedIds] = useState<Set<string | number>>(
        new Set(),
    );
    const [treeHeight, setTreeHeight] = useState(0);
    const [treeGeneration, setTreeGeneration] = useState(0);

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

    const isParentNode = (node: NodeData): boolean => {
        return !!node.children && node.children.length > 0;
    };

    const getNodeCheckboxState = (node: NodeData): CheckboxState => {
        if (!isParentNode(node)) {
            return selectedIds.has(node.id)
                ? CheckboxState.All
                : CheckboxState.None;
        }

        const descendantIds = getAllDescendantIds(node).filter(
            (id) => id !== node.id,
        );
        if (descendantIds.length === 0) return CheckboxState.None;

        const selectedDescendants = descendantIds.filter((id) =>
            selectedIds.has(id),
        );
        if (selectedDescendants.length === 0) {
            return CheckboxState.None;
        }
        if (selectedDescendants.length === descendantIds.length) {
            return CheckboxState.All;
        }
        return CheckboxState.Some;
    };

    useEffect(() => {
        if (!roles) {
            return;
        }
        const convertedData = convertRolesToArboristFormat(
            roles,
        ) as unknown as NodeData[];
        const openStateMap: Record<string, boolean> = {};
        const newSelectedIds = new Set<string | number>();

        const processNode = (node: NodeData): void => {
            if (node.id) {
                openStateMap[node.id.toString()] = false;
                if (node.selected) {
                    newSelectedIds.add(node.id);
                }
            }
            if (node.children) {
                node.children.forEach(processNode);
            }
        };

        convertedData.forEach((node: NodeData): void => processNode(node));
        setArboristData(convertedData);
        setInitialOpenState(openStateMap);
        setSelectedIds(newSelectedIds);
        setTreeHeight(treeHeightForRows(convertedData.length));
        setTreeGeneration((generation) => generation + 1);
        replaceManagedRoleSelection(
            collectNodeIds(convertedData),
            Array.from(newSelectedIds),
        );
    }, [roles]);

    useEffect(() => {
        const clearRolesForRandomArtist = (): void => {
            setSelectedIds(new Set());
        };
        window.addEventListener(
            RANDOM_ARTIST_FILTER_RESET_EVENT,
            clearRolesForRandomArtist,
        );
        return (): void => {
            window.removeEventListener(
                RANDOM_ARTIST_FILTER_RESET_EVENT,
                clearRolesForRandomArtist,
            );
        };
    }, []);

    const handleToggle = useCallback((): void => {
        const tree = treeRef.current;
        if (!tree) {
            return;
        }
        setTreeHeight(treeHeightForRows(countVisibleRows(tree.root)));
    }, []);

    const handleNodeSelection = (
        nodeId: string | number,
        checked: boolean,
        nodeData: NodeData,
    ): void => {
        const newSelectedIds = new Set(selectedIds);

        const findDirectParent = (
            childId: string | number,
            nodes: NodeData[],
        ): NodeData | undefined => {
            const flatSearch = (
                nodesArray: NodeData[],
                targetId: string | number,
            ): NodeData | undefined => {
                for (const node of nodesArray) {
                    if (
                        node.children &&
                        node.children.some((child) => child.id === targetId)
                    ) {
                        return node;
                    }
                }
                for (const node of nodesArray) {
                    if (node.children && node.children.length > 0) {
                        const found = flatSearch(node.children, targetId);
                        if (found) {
                            return found;
                        }
                    }
                }
                return undefined;
            };
            return flatSearch(nodes, childId);
        };

        if (checked) {
            newSelectedIds.add(nodeId);
            if (isParentNode(nodeData)) {
                getAllDescendantIds(nodeData)
                    .filter((id) => id !== nodeId)
                    .forEach((id) => newSelectedIds.add(id));
            }
        } else {
            newSelectedIds.delete(nodeId);
            if (isParentNode(nodeData)) {
                getAllDescendantIds(nodeData)
                    .filter((id) => id !== nodeId)
                    .forEach((id) => newSelectedIds.delete(id));
            }
        }

        const updateAllParents = (startId: string | number): void => {
            let currentId = startId;
            let parent = findDirectParent(currentId, arboristData);
            while (parent) {
                const childrenIds =
                    parent.children?.map((child) => child.id) || [];
                const allChildrenSelected = childrenIds.every((id) =>
                    newSelectedIds.has(id),
                );
                const someChildrenSelected = childrenIds.some((id) =>
                    newSelectedIds.has(id),
                );
                if (allChildrenSelected) {
                    newSelectedIds.add(parent.id);
                } else if (!someChildrenSelected) {
                    newSelectedIds.delete(parent.id);
                }
                currentId = parent.id;
                parent = findDirectParent(currentId, arboristData);
            }
        };

        updateAllParents(nodeId);
        setSelectedIds(newSelectedIds);
        replaceManagedRoleSelection(
            collectNodeIds(arboristData),
            Array.from(newSelectedIds),
        );
        onSelectionChange();
    };

    /** Drops every role in this tree and reloads the network, same as a checkbox change. */
    const handleResetRoles = (): void => {
        setSelectedIds(new Set());
        replaceManagedRoleSelection(collectNodeIds(arboristData), []);
        onSelectionChange();
    };

    const renderCheckbox = (node: NodeData): React.ReactNode => {
        const checkboxState = getNodeCheckboxState(node);
        const isSelected = selectedIds.has(node.id);

        if (checkboxState === CheckboxState.Some) {
            return (
                <div
                    className="role-checkbox-indeterminate"
                    onClick={(event) => {
                        event.stopPropagation();
                        handleNodeSelection(node.id, true, node);
                    }}
                >
                    <div className="role-checkbox-indeterminate-active" />
                </div>
            );
        }

        return (
            <div className="role-checkbox">
                <input
                    type="checkbox"
                    aria-label={node.name}
                    checked={isSelected || checkboxState === CheckboxState.All}
                    onChange={(event) => {
                        event.stopPropagation();
                        handleNodeSelection(
                            node.id,
                            event.target.checked,
                            node,
                        );
                    }}
                    onClick={(event) => event.stopPropagation()}
                />
            </div>
        );
    };

    return (
        <>
            <div className="roles-heading h6 mt-3 mb-1">
                Roles
                <button
                    type="button"
                    className="roles-reset"
                    aria-label="Reset roles"
                    onClick={handleResetRoles}
                >
                    <i
                        className="bi bi-arrow-counterclockwise"
                        aria-hidden="true"
                    ></i>
                </button>
            </div>
            <div className="roles-filter-tree">
                {roles && arboristData.length > 0 ? (
                    <Tree<NodeData>
                        key={treeGeneration}
                        ref={treeRef}
                        data={arboristData}
                        width="100%"
                        height={treeHeight}
                        rowHeight={roleRowHeightPx()}
                        padding={TREE_VERTICAL_PADDING}
                        renderRow={RoleTreeRow}
                        disableDrag={true}
                        disableDrop={true}
                        selection="none"
                        className="roles-tree w-100"
                        openByDefault={false}
                        initialOpenState={initialOpenState}
                        onToggle={handleToggle}
                    >
                        {({ node, style, dragHandle }) => (
                            <div
                                className="tree-item"
                                style={style}
                                ref={dragHandle}
                                title={node.data.name}
                                onClick={(event) => {
                                    event.stopPropagation();
                                }}
                            >
                                <div className="tree-item-inner">
                                    {node.isLeaf ? (
                                        <div className="tree-item-leaf" />
                                    ) : (
                                        <div
                                            className="tree-expanded-indicator text-primary-emphasis"
                                            onClick={(event) => {
                                                event.stopPropagation();
                                                node.toggle();
                                            }}
                                        >
                                            <span>
                                                {node.isOpen ? (
                                                    <svg
                                                        width="10"
                                                        height="10"
                                                        viewBox="0 0 10 10"
                                                    >
                                                        <path d="M1 4L5 8L9 4" />
                                                    </svg>
                                                ) : (
                                                    <svg
                                                        width="10"
                                                        height="10"
                                                        viewBox="0 0 10 10"
                                                    >
                                                        <path d="M4 1L8 5L4 9" />
                                                    </svg>
                                                )}
                                            </span>
                                        </div>
                                    )}
                                    {renderCheckbox(node.data)}
                                    <span
                                        onClick={(event) => {
                                            event.stopPropagation();
                                            if (!node.isLeaf) {
                                                node.toggle();
                                            }
                                        }}
                                    >
                                        {node.data.name}
                                    </span>
                                </div>
                            </div>
                        )}
                    </Tree>
                ) : null}
            </div>
        </>
    );
};

export default RolesFilter;
