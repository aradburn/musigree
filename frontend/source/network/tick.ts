/**
 * Network Visualization Constants and Functions
 * This module provides functionality for rendering and manipulating network graphs,
 * particularly focused on node positioning, link rendering, and visual calculations.
 */

import * as d3 from "d3";
import { hideAllTooltips } from "./tooltips";
import { musigreeManager, networkManager } from "../core";
import type { SimNode, SimLink } from "./data";

// Array of roles that should not be labeled in the visualization
export const unlabeledRoles = ["Alias", "Member Of", "Sublabel Of"];

// Performance optimization constants
export const TICK_THROTTLE = 3; // Only process every Nth tick
export const HULL_THROTTLE = 6; // Update hulls less frequently than other elements

/**
 * Calculates spline intersection points for curved edges
 * @param {number} sX - Source X coordinate
 * @param {number} sY - Source Y coordinate
 * @param {number} sR - Source radius
 * @param {number} cX - Control point X coordinate
 * @param {number} cY - Control point Y coordinate
 * @returns {[number, number]} - [x, y] coordinates of the intersection point
 */
export const calculateSplineInner = (
    sX: number,
    sY: number,
    sR: number,
    cX: number,
    cY: number,
): [number, number] => {
    const dX = sX - cX;
    const dY = sY - cY;
    const angle = Math.atan(dY / dX);
    const deltaX = Math.abs(Math.cos(angle) * sR);
    const deltaY = Math.abs(Math.sin(angle) * sR);
    const newSX = sX < cX ? sX + deltaX : sX - deltaX;
    const newSY = sY < cY ? sY + deltaY : sY - deltaY;
    return [newSX, newSY];
};

/**
 * Generates SVG path data for edges between nodes
 * @param {SimLink} d - The edge data object
 * @returns {string} - SVG path data string
 */
export const generateSpline = (d: SimLink): string => {
    const { x: sX, y: sY, radius: sR } = d.source;
    const { x: tX, y: tY, radius: tR } = d.target;

    if (d.intermediate) {
        const { x: cX, y: cY } = d.intermediate;
        const [sXY0, sXY1] = calculateSplineInner(sX, sY, sR, cX, cY);
        const [tXY0, tXY1] = calculateSplineInner(tX, tY, tR, cX, cY);
        return `M ${sXY0},${sXY1} S ${cX},${cY} ${tXY0},${tXY1}`;
    }

    return `M ${sX},${sY} L ${tX},${tY}`;
};

/**
 * Calculates vertices for hull (outline) around node clusters
 * Optimized to use fewer points per node for better performance
 * @param {SimNode[]} nodes - Array of nodes in the cluster
 * @returns {[number, number][]} - Array of vertex coordinates for hull calculation
 */
export const getHullVertices = (nodes: SimNode[]): [number, number][] => {
    // Use only 4 points per node instead of creating more
    return nodes.flatMap((d) => {
        const radius = d.radius / 3;
        return [
            [d.x + radius, d.y + radius],
            [d.x + radius, d.y - radius],
            [d.x - radius, d.y + radius],
            [d.x - radius, d.y - radius],
        ] as [number, number][];
    });
};

/**
 * Updates link positions and labels during force simulation
 * @this {Element}
 * @param {SimLink} d - The link data object with source and target coordinates
 * @param {number} i - Index of the link
 */
const onTickLink = function (this: Element, d: SimLink, _i: number): void {
    const group = d3.select(this);
    const path = group.select("path");
    path.attr("d", generateSpline(d));

    // Only update text labels if they exist and the link has a significant length
    const textLabels = group.selectAll("text");
    if (!textLabels.empty()) {
        const { x: x1, y: y1 } = d.source;
        const { x: x2, y: y2 } = d.target;
        const pathNode = path.node();
        const node = pathNode instanceof SVGPathElement ? pathNode : null;

        if (node && node.getTotalLength() > 0) {
            const point = node.getPointAtLength(node.getTotalLength() / 2);
            const angle = Math.atan2(y2 - y1, x2 - x1) * (180 / Math.PI);
            textLabels.attr(
                "transform",
                `rotate(${angle} ${point.x} ${point.y}) translate(${point.x},${point.y})`,
            );
        }
    }
};

/**
 * Helper function to generate transform attribute for node positioning
 * @param {SimNode} d - Node data object with x,y coordinates
 * @returns {string} - Transform attribute value
 */
const translate = (d: SimNode): string => `translate(${d.x},${d.y})`;

/**
 * Main tick function for force simulation
 * Updates positions of all visual elements (nodes, links, hulls) each tick
 * Optimized to reduce update frequency with throttling
 * @param {d3.Simulation<SimNode, undefined>} e - The tick event object
 */
export const onTick = (_e: d3.Simulation<SimNode, undefined>): void => {
    networkManager.tick += 1;

    // Throttle updates to reduce CPU usage
    // Still process every tick for physics but only update the DOM periodically
    const shouldUpdateDOM = networkManager.tick % TICK_THROTTLE === 0;
    const shouldUpdateHulls = networkManager.tick % HULL_THROTTLE === 0;

    if (!shouldUpdateDOM && !shouldUpdateHulls) {
        return;
    }

    const k = 1.0; // Force multiplier

    // Center the main node if not fixed
    if (networkManager.data.center) {
        const centerNode = networkManager.data.nodeMap.get(
            networkManager.data.center.key,
        );
        if (centerNode && !centerNode.fixed) {
            const [svgWidth, svgHeight] = musigreeManager.svgDimensions;
            const dx = (svgWidth / 2 - centerNode.x) * k;
            const dy = (svgHeight / 2 - centerNode.y) * k;
            centerNode.x += dx;
            centerNode.y += dy;
        }
    }

    if (shouldUpdateDOM) {
        // Update positions of links
        networkManager.layers.link
            ?.selectAll<SVGGElement, SimLink>(".link")
            ?.each(onTickLink);

        // Update positions of nodes - without movement optimization
        networkManager.layers.halo
            ?.selectAll(".node")
            .attr("transform", translate);
        networkManager.layers.node
            ?.selectAll(".node")
            .attr("transform", translate);
        networkManager.layers.text
            ?.selectAll(".node")
            .attr("transform", translate);

        hideAllTooltips();
    }

    // Update hull (cluster outline) paths - less frequently for better performance
    if (shouldUpdateHulls) {
        networkManager.layers.halo
            ?.selectAll(".hull")
            .select("path")
            .attr("d", function (d: SimNode[]) {
                const vertices = d3.polygonHull(getHullVertices(d));
                return vertices ? "M" + vertices.join("L") + "Z" : "";
            });
    }
};
