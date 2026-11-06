/**
 * forceLayout.ts
 * This file implements a force-directed graph layout system using D3.js for the Musigree application.
 * It handles node positioning, link creation, and graph simulation with various forces applied.
 */

import * as d3 from "d3";
import type {SimLink, SimNode} from "./data";
import {onHullEnter, onHullExit, onHullUpdate} from "./hull";
import {onHaloEnter, onHaloExit, onHaloUpdate} from "./halo";
import {onNodeEnter, onNodeExit, onNodeUpdate} from "./node";
import {onTextEnter, onTextExit, onTextUpdate} from "./text";
import {onLinkEnter, onLinkExit, onLinkUpdate} from "./link";
import {onTick} from "./tick";
import {
    onNetworkEnd,
    onNetworkStart,
    ResetForcesEvent,
    SetForcesEvent,
} from "./events";
import {musigreeManager, networkManager} from "@/core";
import {FORCE} from "../constants";

/**
 * Numerical Recipes LCG parameters, the same generator d3-force uses by default.
 * The simulation stores one generator for its lifetime, so each layout run
 * installs a fresh copy and coincident nodes are jiggled identically.
 */
const FORCE_LAYOUT_RANDOM_MULTIPLIER = 1664525;
const FORCE_LAYOUT_RANDOM_INCREMENT = 1013904223;
const FORCE_LAYOUT_RANDOM_MODULUS = 4294967296;
const FORCE_LAYOUT_RANDOM_SEED = 1;

/**
 * Returns a random source in [0, 1) that always starts at the same seed.
 */
export const createForceLayoutRandom = (): (() => number) => {
    let state = FORCE_LAYOUT_RANDOM_SEED;
    return (): number => {
        state =
            (FORCE_LAYOUT_RANDOM_MULTIPLIER * state +
                FORCE_LAYOUT_RANDOM_INCREMENT) %
            FORCE_LAYOUT_RANDOM_MODULUS;
        return state / FORCE_LAYOUT_RANDOM_MODULUS;
    };
};

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

/** Places a node group at the coordinates assigned before the simulation runs. */
const translateNode = (d: SimNode): string => `translate(${d.x},${d.y})`;

/**
 * Draws node groups at their starting coordinates.
 * Groups with no transform sit at the network-layer origin, which the zoom
 * transform places above the viewport.
 */
const applyInitialNodeTransform = (): void => {
    networkManager.layers.halo
        ?.selectAll<SVGGElement, SimNode>(".node")
        .attr("transform", translateNode);
    networkManager.layers.node
        ?.selectAll<SVGGElement, SimNode>(".node")
        .attr("transform", translateNode);
    networkManager.layers.text
        ?.selectAll<SVGGElement, SimNode>(".node")
        .attr("transform", translateNode);
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

    applyInitialNodeTransform();

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

/** Timer used when simulation steps are spaced out for slower playback. */
let simulationTimer: d3.Timer | null = null;

const stopSimulationTimer = (): void => {
    simulationTimer?.stop();
    simulationTimer = null;
};

/**
 * Advances the simulation on a fixed interval and draws every step.
 * The built-in timer runs once per frame, which hides the opening movement.
 */
const startSlowedSimulation = (
    simulation: d3.Simulation<SimNode, SimLink>,
): void => {
    simulationTimer = d3.interval(() => {
        simulation.tick();
        onTick(simulation, true);
        if (simulation.alpha() < simulation.alphaMin()) {
            stopSimulationTimer();
            simulation.stop();
            onNetworkEnd(simulation);
        }
    }, FORCE.SIMULATION.TICK_INTERVAL_MS);
};

/**
 * Restarts the force layout simulation with a new alpha value
 * @param {number} alpha - The new alpha value for the simulation
 */
export const restartForceLayout = (alpha: number): void => {
    console.log("restartForceLayout alpha:", alpha);

    if (networkManager.forceLayout) {
        onNetworkStart();
        const simulation = networkManager.forceLayout
            .randomSource(createForceLayoutRandom())
            .alpha(alpha)
            .stop();
        stopSimulationTimer();
        if (FORCE.SIMULATION.TICK_INTERVAL_MS <= 0) {
            simulation.restart();
            return;
        }
        startSlowedSimulation(simulation);
    } else {
        console.error("Force layout is not initialized");
    }
};

/**
 * Stops the force layout simulation
 */
export const stopForceLayout = (): void => {
    console.log("stopForceLayout");
    stopSimulationTimer();
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
