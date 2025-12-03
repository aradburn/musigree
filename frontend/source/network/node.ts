/**
 * Network Node Configuration and Event Handling
 *
 * This module manages the creation, updating, and interaction of nodes in a D3.js network visualization.
 * It handles both artist and label nodes with different visual representations and behaviors.
 */

import * as d3 from "d3";
import { symbol, symbolCross, now } from "d3";

import debounce from "debounce";
import { getNodeColorClass } from "../color";
import { networkManager } from "../core/singletons";
import { onDragStart, onDragEnd, onDrag, RequestNetworkEvent } from "./events";
import { hideAllTooltips } from "./tooltips";
import { SelectEntityEvent } from "./events";
import { nodeTooltip } from "./tooltips";
import type { SimNode } from "./data";
import { NodeType } from "./data";

// Configuration Constants
/**
 * @const {number} NODE_DEBOUNCE_TIME - Delay in milliseconds for debouncing node events (250ms)
 * @const {number} NODE_OUT_TRANSITION_TIME - Duration for node exit transitions (500ms)
 * @const {number} NODE_UPDATE_TRANSITION_TIME - Duration for node update transitions (5000ms)
 * @const {string} NODE_ARTIST_PALETTE - Color palette identifier for artist nodes
 * @const {string} NODE_LABEL_PALETTE - Color palette identifier for label nodes
 */

// Constants
export const NODE_INNER_RADIUS = 8;
export const NODE_OUTER_RADIUS = 11;
const NODE_DEBOUNCE_TIME = 250;
const _NODE_OUT_TRANSITION_TIME = 500;
const _NODE_UPDATE_TRANSITION_TIME = 5000;
const NODE_ARTIST_PALETTE = "Palette3";
const NODE_LABEL_PALETTE = "Palette4";

type NodeEnterSelection = d3.Selection<
    d3.EnterElement,
    SimNode,
    SVGGElement,
    unknown
>;

type NodeUpdateSelection = d3.Selection<
    SVGGElement,
    SimNode,
    SVGGElement,
    unknown
>;

type NodeExitSelection = d3.Selection<
    SVGGElement,
    SimNode,
    SVGGElement,
    unknown
>;

/**
 * Calculates the base radius for a node based on its properties
 * @param {number} size - Size of the node
 * @param {number} distance - Distance of the node from the center node
 * @param {number} numLinks - Number of links associated with the node
 * @param {number} cluster - Indicates if the node is part of a cluster
 * @returns {number} - Calculated radius for the node
 */
export const getRadius = (
    size: number,
    distance: number,
    numLinks: number,
    cluster: number,
): number => {
    const boost1 = distance === 0 ? 10 : distance === 1 ? 5 : 0;
    const boost2 = numLinks >= 20 ? 10 : numLinks >= 10 ? 5 : 0;
    const alias = cluster !== undefined ? 2 : 1;
    return Math.round((Math.sqrt(size) * 2 + boost1 + boost2) / alias);
};

/**
 * Calculates the outer radius of a node
 * @param {SimNode} d - Node data
 * @returns {number} - Outer radius value
 */
export const getOuterRadius = (d: SimNode): number => {
    return (
        NODE_OUTER_RADIUS +
        getRadius(d.size, d.distance ?? 0, (d.links ?? []).length, d.cluster)
    );
};

/**
 * Calculates the inner radius of a node
 * @param {SimNode} d - Node data
 * @returns {number} - Inner radius value
 */
export const getInnerRadius = (d: SimNode): number => {
    return (
        NODE_INNER_RADIUS +
        getRadius(d.size, d.distance ?? 0, (d.links ?? []).length, d.cluster)
    );
};

/**
 * Handles the enter phase for new nodes in the D3 update pattern
 * @param {NodeEnterSelection} nodeEnter - D3 selection of entering nodes
 */
export const onNodeEnter = (
    nodeEnter: NodeEnterSelection,
): NodeEnterSelection => {
    const nodeEnterSelection = nodeEnter
        .append("g")
        .attr("id", (d) => `node-${d.key}`)
        .attr("class", (d) => {
            const entity_type = d.key.split("-")[0];
            const classes = [
                "node",
                entity_type,
                entity_type === "artist"
                    ? NODE_ARTIST_PALETTE
                    : NODE_LABEL_PALETTE,
            ];
            return classes.join(" ");
        })
        .call(
            d3
                .drag<SVGGElement, SimNode>()
                .on("start", onDragStart)
                .on("drag", onDrag)
                .on("end", onDragEnd),
        );

    onNodeEnterElementConstruction(nodeEnterSelection);
    onNodeEnterEventBindings(nodeEnterSelection);

    return nodeEnterSelection;
};

/**
 * Constructs the visual elements for nodes
 * @param {NodeEnterSelection} nodeEnter - D3 selection of entering nodes
 *
 * For Artist nodes:
 * - Adds shadow circle
 * - Adds outer circle with size based on node data
 * - Adds inner circle
 *
 * For Label nodes:
 * - Adds rectangular shape
 *
 * For all nodes:
 * - Adds "more" indicator (+) symbol if node has hidden connections
 */
const onNodeEnterElementConstruction = (
    nodeEnter: NodeEnterSelection,
): void => {
    // ARTISTS
    const artistEnter = nodeEnter.filter(function (d) {
        return d.type === NodeType.Artist;
    });
    artistEnter
        .append("circle")
        .attr("class", "shadow")
        .attr("cx", (d) => getOuterRadius(d) / 3 + 1)
        .attr("cy", (d) => getOuterRadius(d) / 3 + 1)
        .attr("r", (d) => getOuterRadius(d) * 1.2);
    artistEnter
        .append("circle")
        .attr("class", (d) => {
            const classes = ["outer", getNodeColorClass(d)];
            return classes.join(" ");
        })
        .attr("r", (d) => getOuterRadius(d));
    artistEnter
        .append("circle")
        .attr("class", (d) => {
            const classes = ["inner", getNodeColorClass(d)];
            return classes.join(" ");
        })
        .attr("r", (d) => getInnerRadius(d));

    // LABELS
    const labelEnter = nodeEnter.filter(function (d) {
        return d.type === NodeType.Label;
    });
    labelEnter
        .append("rect")
        .attr("class", "shadow")
        .attr("height", (d) => 3 * getOuterRadius(d))
        .attr("width", (d) => 3 * getOuterRadius(d))
        .attr("x", (d) => -1 * getOuterRadius(d))
        .attr("y", (d) => -1 * getOuterRadius(d));
    labelEnter
        .append("rect")
        .attr("class", (d) => {
            const classes = ["outer", getNodeColorClass(d)];
            return classes.join(" ");
        })
        .attr("height", (d) => 2 * getOuterRadius(d))
        .attr("width", (d) => 2 * getOuterRadius(d))
        .attr("x", (d) => -1 * getOuterRadius(d))
        .attr("y", (d) => -1 * getOuterRadius(d));
    labelEnter
        .append("rect")
        .attr("class", (d) => {
            const classes = ["inner", getNodeColorClass(d)];
            return classes.join(" ");
        })
        .attr("height", (d) => 2 * getInnerRadius(d))
        .attr("width", (d) => 2 * getInnerRadius(d))
        .attr("x", (d) => -1 * getInnerRadius(d))
        .attr("y", (d) => -1 * getInnerRadius(d));

    // MORE Show a + symbol if there are extra links from this node that are missing / not shown
    nodeEnter
        .append("path")
        .attr("class", "more")
        .attr("d", symbol().type(symbolCross).size(64))
        .style("opacity", (d) => (d.hasMissing || d.missing > 0 ? 1 : 0));
};

/**
 * Binds mouse and touch events to nodes
 * @param {NodeEnterSelection} nodeEnter - D3 selection of entering nodes
 *
 * Events handled:
 * - mouseover: Highlight node
 * - mouseenter: Show tooltip
 * - mouseleave: Hide tooltip
 * - mousedown: Handle single/double click timing
 * - dblclick: Request network update
 * - touchstart: Handle touch interactions
 */
const onNodeEnterEventBindings = (nodeEnter: NodeEnterSelection): void => {
    const debounceToolTip = debounce(
        (element: SVGGElement, d: SimNode, status: boolean) => {
            if (status) {
                nodeTooltip.show(d, element);
                // Hide after 5 seconds
                //                 setTimeout(() => {
                //                     hideAllTooltips();
                //                 }, 5000);
            } else {
                nodeTooltip.hide();
            }
        },
        NODE_DEBOUNCE_TIME,
    );

    nodeEnter
        .on("mouseover", (event: MouseEvent, d: SimNode) =>
            onNodeMouseOver(event, d),
        )
        .on(
            "mouseenter",
            function (this: SVGGElement, event: MouseEvent, d: SimNode) {
                debounceToolTip(this, d, true);
            },
        )
        .on("mouseleave", (_event: MouseEvent, _d: SimNode) => {
            nodeTooltip.hide();
        })
        .on("mousedown", (event: MouseEvent, d: SimNode) =>
            onNodeMouseDown(event, d),
        )
        .on("dblclick", (event: MouseEvent, d: SimNode) =>
            onNodeMouseDoubleClick(event, d),
        )
        .on("touchstart", (event: TouchEvent, d: SimNode) =>
            onNodeTouchStart(event, d),
        );
};

/**
 * Updates existing nodes in the visualization
 * @param {NodeUpdateSelection} nodeUpdate - D3 selection of updating nodes
 */
export const onNodeUpdate = (
    nodeUpdate: NodeUpdateSelection,
): NodeUpdateSelection => {
    // ARTISTS
    const artistUpdate = nodeUpdate.filter(function (d) {
        return d.type === NodeType.Artist;
    });
    artistUpdate
        .select<SVGGElement>(".shadow")
        .attr("cx", (d) => getOuterRadius(d) / 3 + 1)
        .attr("cy", (d) => getOuterRadius(d) / 3 + 1)
        .attr("r", (d) => getOuterRadius(d) * 1.2);

    artistUpdate
        .select<SVGGElement>(".outer")
        .attr("class", (d) => {
            const classes = ["outer", getNodeColorClass(d)];
            return classes.join(" ");
        })
        .attr("r", (d) => getOuterRadius(d));

    artistUpdate
        .select<SVGGElement>(".inner")
        .attr("class", (d) => {
            const classes = ["inner", getNodeColorClass(d)];
            return classes.join(" ");
        })
        .attr("r", (d) => getInnerRadius(d));

    // LABELS
    const labelUpdate = nodeUpdate.filter(function (d) {
        return d.type === NodeType.Label;
    });
    labelUpdate
        .select<SVGGElement>(".inner")
        .attr("class", (d) => {
            const classes = ["inner", getNodeColorClass(d)];
            return classes.join(" ");
        })
        .attr("height", (d) => 2 * getInnerRadius(d))
        .attr("width", (d) => 2 * getInnerRadius(d))
        .attr("x", (d) => -1 * getInnerRadius(d))
        .attr("y", (d) => -1 * getInnerRadius(d))
        .style("opacity", (d) => (d.missing > 0 ? 0.5 : 1));

    // Both ARTISTS and LABELS
    nodeUpdate
        .select<SVGGElement>(".more")
        .style("opacity", (d) => (d.hasMissing || d.missing > 0 ? 1 : 0));
    return nodeUpdate;
};

/**
 * Handles node removal from the visualization
 * @param {NodeSelection} nodeExit - D3 selection of exiting nodes
 */
export const onNodeExit = (nodeExit: NodeExitSelection): void => {
    nodeExit.remove();
};

/**
 * Mouse event handlers
 */

/**
 * Handles mouse over events on nodes
 * @param {MouseEvent} event - DOM event object
 * @param {SimNode} d - Node data
 * Raises the hovered node to the top of the visualization
 */
export const onNodeMouseOver = (event: MouseEvent, d: SimNode): void => {
    const debounceHandler = debounce((_d: SimNode) => {
        //console.log("node: ", d);
    }, NODE_DEBOUNCE_TIME);

    debounceHandler(d);

    // Add a safety check to ensure networkStore.layers.node exists before calling selectAll
    if (networkManager.layers?.node) {
        networkManager.layers.node
            .selectAll<SVGGElement, SimNode>(".node")
            .filter((n) => n.key === d.key)
            .raise();
    }

    // Add a safety check to ensure networkStore.layers.text exists before calling selectAll
    if (networkManager.layers?.text) {
        networkManager.layers.text
            .selectAll<SVGGElement, SimNode>(".node")
            .filter((n) => n.key === d.key)
            .raise();
    }
};

/**
 * Handles mouse down events on nodes
 * @param {MouseEvent} event - DOM event object
 * @param {SimNode} d - Node data
 * Implements single/double click timing logic for node selection and network updates
 */
export const onNodeMouseDown = (event: MouseEvent, d: SimNode): void => {
    const thisTime = now();
    const lastTime = d.lastClickTime;
    d.lastClickTime = thisTime;

    if (!lastTime || thisTime - lastTime > 700) {
        window.dispatchEvent(new SelectEntityEvent(d.key, true));
    } else {
        window.dispatchEvent(new RequestNetworkEvent(d.key, true));
    }
};

/**
 * Handles double click events on nodes
 * @param {MouseEvent} event - DOM event object
 * @param {SimNode} d - Node data
 * Triggers network update request and prevents event propagation
 */
export const onNodeMouseDoubleClick = (event: MouseEvent, d: SimNode): void => {
    hideAllTooltips();
    window.dispatchEvent(new RequestNetworkEvent(d.key, true));
    event.stopPropagation();
};

/**
 * Handles touch events on nodes
 * @param {TouchEvent} event - DOM event object
 * @param {SimNode} d - Node data
 * Implements touch timing logic similar to mouse events
 */
export const onNodeTouchStart = (event: TouchEvent, d: SimNode): void => {
    const thisTime = Date.now();
    const lastTime = d.lastTouchTime;
    d.lastTouchTime = thisTime;

    if (!lastTime || 500 < thisTime - lastTime) {
        window.dispatchEvent(new SelectEntityEvent(d.key, true));
    } else if (thisTime - lastTime < 500) {
        window.dispatchEvent(new RequestNetworkEvent(d.key, true));
    }
    event.stopPropagation();
};

export const updateSelectedNodes = (selectedKeys: Array<string>): void => {
    // Add a safety check to ensure networkManager.layers.node exists before calling selectAll
    if (networkManager.layers?.node) {
        networkManager.layers.node
            .selectAll<SVGGElement, SimNode>(".node")
            .classed("selected", (d) => selectedKeys.includes(d.key));
    }

    // Add a safety check to ensure networkManager.layers.text exists before calling selectAll
    if (networkManager.layers?.text) {
        networkManager.layers.text
            .selectAll<SVGGElement, SimNode>(".node")
            .classed("selected", (d) => selectedKeys.includes(d.key));
    }
};
