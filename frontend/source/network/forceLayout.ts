/**
 * forceLayout.ts
 * This file implements a force-directed graph layout system using D3.js for the Musigree application.
 * It handles node positioning, link creation, and graph simulation with various forces applied.
 */

import * as d3 from "d3";
import type { SimNode, SimLink } from "./data";
import { onHullEnter, onHullUpdate, onHullExit } from "./hull";
import { onHaloEnter, onHaloUpdate, onHaloExit } from "./halo";
import { onNodeEnter, onNodeUpdate, onNodeExit } from "./node";
import { onTextEnter, onTextUpdate, onTextExit } from "./text";
import { onLinkEnter, onLinkUpdate, onLinkExit } from "./link";
import { onTick } from "./tick";
import {
    onNetworkStart,
    onNetworkEnd,
    ResetForcesEvent,
    SetForcesEvent,
} from "./events";
import { musigreeManager, networkManager } from "../core/singletons";
import { FORCE } from "../constants";

/**
 * Sets up the initial force simulation with basic forces
 * and event listeners for tick and end events.
 * More forces are added in NetworkContext.
 */
export const initForceLayout = (): void => {
    console.log("initForceLayout");

    networkManager.forceLayout = d3
        .forceSimulation<SimNode>(
            Array.from(networkManager.data.nodeMap.values()),
        )
        .force(
            "collide",
            d3
                .forceCollide<SimNode>()
                .radius((d) => (d.radius ?? 0) + FORCE.COLLIDE.BUFFER)
                .iterations(FORCE.COLLIDE.ITERATIONS),
        )
        .force("bbox", bboxForce)
        .on("tick", function (this: d3.Simulation<SimNode, SimLink>) {
            onTick(this);
        })
        .on("end", function (this: d3.Simulation<SimNode, SimLink>) {
            onNetworkEnd(this);
        })
        .stop();
};

/**
 * Initializes and starts the force layout simulation
 * Updates node and link selections and applies forces
 */
export const displayForceLayout = (): void => {
    console.log("displayForceLayout() update network layers");

    const keyFunc = (d: SimNode | SimLink): string => d.key;

    const nodeData = Array.from(networkManager.data.nodeMap.values()).filter(
        (d) => !d.isIntermediate,
    );

    const linkData = Array.from(networkManager.data.linkMap.values()).filter(
        (d) => !d.isSpline,
    );

    console.log("nodeData (without intermediate): ", nodeData);
    console.log("linkData (without splines)     : ", linkData);

    networkManager.layers.halo
        .selectAll<SVGGElement, SimNode>(".node")
        .data(nodeData, keyFunc)
        .join(
            (enter) => {
                return onHaloEnter(enter);
            },
            (update) => {
                return onHaloUpdate(update);
            },
            (exit) => {
                return onHaloExit(exit);
            },
        );

    networkManager.layers.node
        .selectAll<SVGGElement, SimNode>(".node")
        .data(nodeData, keyFunc)
        .join(
            (enter) => {
                return onNodeEnter(enter);
            },
            (update) => {
                return onNodeUpdate(update);
            },
            (exit) => {
                return onNodeExit(exit);
            },
        );

    networkManager.layers.text
        .selectAll<SVGGElement, SimNode>(".node")
        .data(nodeData, keyFunc)
        .join(
            (enter) => {
                return onTextEnter(enter);
            },
            (update) => {
                return onTextUpdate(update);
            },
            (exit) => {
                return onTextExit(exit);
            },
        );

    networkManager.layers.link
        .selectAll<SVGGElement, SimLink>(".link")
        .data(linkData, keyFunc)
        .join(
            (enter) => {
                return onLinkEnter(enter);
            },
            (update) => {
                return onLinkUpdate(update);
            },
            (exit) => {
                return onLinkExit(exit);
            },
        );

    const clusterNodes = Array.from(
        networkManager.data.nodeMap.values(),
    ).filter((d) => d.cluster !== undefined);
    const hullGroups = Array.from(
        d3.group(clusterNodes, (d) => d.cluster).values(),
    );
    const hullData = hullGroups.filter((d) => d.length > 1);

    networkManager.layers.halo
        .selectAll<SVGGElement, SimNode[]>(".hull")
        .data(hullData)
        .join(
            (enter) => {
                return onHullEnter(enter);
            },
            (update) => {
                return onHullUpdate(update);
            },
            (exit) => {
                return onHullExit(exit);
            },
        );

    Array.from(networkManager.data.nodeMap.values()).forEach(
        (n) => (n.fixed = false),
    );
};

/**
 * Initializes the force layout simulation nodes
 */
export const setForceLayoutNodes = (nodes: SimNode[]): void => {
    console.log("setForceLayoutNodes:", nodes);

    // Set simulation nodes
    networkManager.forceLayout.nodes(nodes);
};

/**
 * Restarts the force layout simulation with a new alpha value
 * @param {number} alpha - The new alpha value for the simulation
 */
export const restartForceLayout = (alpha: number): void => {
    console.log("restartForceLayout alpha:", alpha);

    if (networkManager.forceLayout) {
        onNetworkStart();
        networkManager.forceLayout.alpha(alpha).restart();
    } else {
        console.error("Force layout is not initialized");
    }
};

/**
 * Stops the force layout simulation
 */
export const stopForceLayout = (): void => {
    console.log("stopForceLayout");
    if (networkManager.forceLayout) {
        networkManager.forceLayout.stop();
    }
};

/**
 * Sets network forces to their current values
 * This dispatches a custom event that the React context will listen for
 */
export const setNetworkForces = (): void => {
    console.log("Setting network forces to current values");
    window.dispatchEvent(new SetForcesEvent());
};

/**
 * Resets network forces to their initial values
 * This dispatches a custom event that the React context will listen for
 */
export const resetNetworkForces = (): void => {
    console.log("Resetting network forces to initial values");
    window.dispatchEvent(new ResetForcesEvent());
};

/**
 * Custom force to keep nodes within the SVG boundaries
 */
const bboxForce = (): void => {
    const bbox = {
        width: musigreeManager.svgDimensions[0],
        height: musigreeManager.svgDimensions[1],
    };

    if (networkManager.forceLayout && networkManager.forceLayout.nodes()) {
        // Update nodes to keep them within bounds
        for (const node of networkManager.forceLayout.nodes()) {
            if (!node.radius) continue;

            const radius = node.radius + FORCE.COLLIDE.BUFFER * 2;
            const maxX = bbox.width - radius;
            const maxY = bbox.height - radius;
            const minX = radius;
            const minY = radius;

            if (node.x > maxX) node.x = maxX;
            if (node.x < minX) node.x = minX;
            if (node.y > maxY) node.y = maxY;
            if (node.y < minY) node.y = minY;
        }
    }
};
