/**
 * Network Graph Event Handlers
 * This file contains event handlers and control functions for a force-directed network graph,
 * implemented using D3.js. It manages node dragging behavior and layout controls.
 */

import { nodeTooltip } from "./tooltips";
import { onTick } from "./tick";
import { restartForceLayout, stopForceLayout } from "./forceLayout";
import type * as d3 from "d3";
import type { SimNode } from "./data";
import { networkManager } from "../core/singletons";

interface D3DragEventWithSource<GElement extends Element, Datum, Subject>
    extends d3.D3DragEvent<GElement, Datum, Subject> {
    sourceEvent: MouseEvent | TouchEvent;
}

/**
 * Reheat the simulation when drag starts, and fix the subject position.
 * @param {D3DragEventWithSource<SVGGElement, SimNode, SimNode>} event - The drag event object
 */
export const onDragStart = (
    event: D3DragEventWithSource<SVGGElement, SimNode, SimNode>,
): void => {
    const node = event.subject;
    node.fx = node.x;
    node.fy = node.y;
    node.dragx = node.x;
    node.dragy = node.y;
    if (event.sourceEvent.type === "mousedown") {
        nodeTooltip.hide();
    }
};

/**
 * Updates node position during drag operation
 * @param {d3.D3DragEvent<SVGGElement, DraggableNode, DraggableNode>} event - The drag event object
 */
export const onDrag = (
    event: d3.D3DragEvent<SVGGElement, SimNode, SimNode>,
): void => {
    const node = event.subject;
    node.fx = event.x;
    node.fy = event.y;
    if (node.dragx !== node.x || node.dragy !== node.y) {
        node.dragx = node.x;
        node.dragy = node.y;
        if (!event.active) {
            restartForceLayout(0.3);
        }
    }
};

/**
 * Handles the end of a node drag operation
 * Releases the fixed position of the node and allows the simulation to continue
 * @param {D3DragEventWithSource<SVGGElement, DraggableNode, DraggableNode>} event - The drag event object
 */
export const onDragEnd = (
    event: D3DragEventWithSource<SVGGElement, SimNode, SimNode>,
): void => {
    const node = event.subject;
    if (node.dragx === node.x && node.dragy === node.y) {
        return;
    }
    if (!event.active) stopForceLayout();
    node.fx = null;
    node.fy = null;
    if (event.sourceEvent.type === "mouseup") {
        nodeTooltip.hide();
    }
};

/**
 * Initiates the network layout simulation
 * Shows the running indicator and enables interaction with nodes and links
 */
export const onNetworkStart = (): void => {
    // console.log("onNetworkStart()");
    networkManager.isRunningLayout = true;
    networkManager.tick = 0;

    networkManager.layers.link
        ?.selectAll(".link")
        .classed("noninteractive", false);
    networkManager.layers.node
        ?.selectAll(".node")
        .classed("noninteractive", false);
};

/**
 * Handles the completion of network layout simulation
 * Hides the running indicator and ensures nodes and links remain interactive
 * @param {d3.Simulation<DraggableNode, undefined>} event - The completion event object
 */
export const onNetworkEnd = (
    event: d3.Simulation<SimNode, undefined>,
): void => {
    console.log("onNetworkEnd()");
    networkManager.layers.link
        ?.selectAll(".link")
        .classed("noninteractive", false);
    networkManager.layers.node
        ?.selectAll(".node")
        .classed("noninteractive", false);
    networkManager.isRunningLayout = false;
    onTick(event);
};

interface RequestNetworkEventDetail {
    entityKey: string;
    pushHistory: boolean;
}

/**
 * Custom event for requesting a network layout
 * @extends CustomEvent
 */
export class RequestNetworkEvent extends CustomEvent<RequestNetworkEventDetail> {
    static readonly EVENT_NAME = "musigree:request-network";

    /**
     * Creates a new RequestNetworkEvent
     * @param {string} entityKey - The key of the entity to request
     * @param {boolean} pushHistory - Whether to push the network layout to the history stack
     */
    constructor(entityKey: string, pushHistory: boolean) {
        super(RequestNetworkEvent.EVENT_NAME, {
            bubbles: true,
            detail: {
                entityKey,
                pushHistory,
            },
        });
    }
}

interface SelectEntityEventDetail {
    entityKey: string;
    fixed: boolean;
}

/**
 * Custom event for selecting an entity
 * @extends CustomEvent
 */
export class SelectEntityEvent extends CustomEvent<SelectEntityEventDetail> {
    /**
     * Creates a new SelectEntityEvent
     * @param {string} entityKey - The key of the entity to select
     * @param {boolean} fixed - Whether to fix the entity position
     */
    constructor(entityKey: string, fixed: boolean) {
        super("musigree:select-entity", {
            bubbles: true,
            detail: {
                entityKey,
                fixed,
            },
        });
    }
}

/**
 * Custom event for resizing the network window
 * @extends CustomEvent
 */
export class ResizeEvent extends CustomEvent<Record<string, never>> {
    /**
     * Creates a new ResizeEvent
     */
    constructor() {
        super("musigree:resize", {
            bubbles: true,
            detail: {},
        });
    }
}

/**
 * Custom event for setting network forces
 * @extends CustomEvent
 */
export class SetForcesEvent extends CustomEvent<Record<string, never>> {
    /**
     * Creates a new SetForcesEvent
     */
    constructor() {
        super("musigree:set-forces", {
            bubbles: true,
            detail: {},
        });
    }
}

/**
 * Custom event for resetting network forces
 * @extends CustomEvent
 */
export class ResetForcesEvent extends CustomEvent<Record<string, never>> {
    /**
     * Creates a new ResetForcesEvent
     */
    constructor() {
        super("musigree:reset-forces", {
            bubbles: true,
            detail: {},
        });
    }
}

// Add type declarations for custom events
declare global {
    interface WindowEventMap {
        "musigree:request-network": RequestNetworkEvent;
        "musigree:select-entity": SelectEntityEvent;
        "musigree:resize": ResizeEvent;
        "musigree:set-forces": SetForcesEvent;
        "musigree:reset-forces": ResetForcesEvent;
    }
}
