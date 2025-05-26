/**
 * Network visualization hull effect handlers
 * This module provides functions for managing convex hulls around groups of nodes
 * @module network/hull
 */

import type { SimNode } from "./data";
import type * as d3 from "d3";

export type HullGroup = SimNode[];

export type HullEnterSelection = d3.Selection<
    d3.EnterElement,
    SimNode[],
    SVGGElement,
    unknown
>;

export type HullUpdateSelection = d3.Selection<
    SVGGElement,
    SimNode[],
    SVGGElement,
    unknown
>;

export type HullExitSelection = d3.Selection<
    SVGGElement,
    SimNode[],
    SVGGElement,
    unknown
>;

/**
 * Handles the enter selection for network hulls (convex hulls around groups of nodes).
 * Creates a new group element for each entering hull and appends a path element to it.
 *
 * @param {HullEnterSelection} hullEnter - The D3 enter selection for hulls
 * @returns {void}
 */
export const onHullEnter = (
    hullEnter: HullEnterSelection,
): HullEnterSelection => {
    const hullGroup = hullEnter.append("g").attr("class", "hull");
    // Note: Commented out for reference
    // .attr("class", (d: HullGroup) => "hull hull-" + d.key);
    hullGroup.append("path");

    return hullGroup;
};

/**
 * Handles the update of hulls when node data is changed
 * @param {HullUpdateSelection} hullUpdate - D3 selection of elements being updated in the visualization
 * @returns {HullUpdateSelection}
 */
export const onHullUpdate = (
    hullUpdate: HullUpdateSelection,
): HullUpdateSelection => {
    // No updates needed, all done in tick
    return hullUpdate;
};

/**
 * Handles the exit selection for network hulls.
 * Removes hull elements that are no longer needed from the DOM.
 *
 * @param {HullExitSelection} hullExit - The D3 exit selection for hulls
 * @returns {void}
 */
export const onHullExit = (hullExit: HullExitSelection): void => {
    hullExit.remove();
};
