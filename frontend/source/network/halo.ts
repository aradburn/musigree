/**
 * Network visualization halo effect handlers
 * This module provides functions for managing halo effects around network nodes
 * @module network/halo
 */

import type { SimNode } from "./data";
import { getOuterRadius } from "./node";
import type * as d3 from "d3";

export type HaloEnterSelection = d3.Selection<
    d3.EnterElement,
    SimNode,
    SVGGElement,
    unknown
>;

export type HaloUpdateSelection = d3.Selection<
    SVGGElement,
    SimNode,
    SVGGElement,
    unknown
>;

export type HaloExitSelection = d3.Selection<
    SVGGElement,
    SimNode,
    SVGGElement,
    unknown
>;

/**
 * Handles the creation and styling of halos when nodes are entered/activated
 * @param {HaloEnterSelection} haloEnter - D3 selection of elements entering the visualization
 * @returns {void}
 *
 * The function:
 * 1. Creates a group (g) element for each halo
 * 2. Assigns an ID based on the node's key
 * 3. Applies CSS classes based on the node type (first part of the key)
 * 4. Adds a circular halo effect around the node
 */
export const onHaloEnter = (
    haloEnter: HaloEnterSelection,
): HaloEnterSelection => {
    const haloGroup = haloEnter
        .append("g")
        .attr("id", (d: SimNode) => d.key)
        .attr("class", (d: SimNode) => {
            const classes = ["node", d.key.split("-")[0]];
            return classes.join(" ");
        });

    haloGroup
        .append("circle")
        .attr("class", "halo")
        .attr("r", (d: SimNode) => getOuterRadius(d) + 40);

    return haloGroup;
};

/**
 * Handles the update of halos when node data is changed
 * @param {HaloUpdateSelection} haloUpdate - D3 selection of elements being updated in the visualization
 * @returns {HaloUpdateSelection}
 */
export const onHaloUpdate = (
    haloUpdate: HaloUpdateSelection,
): HaloUpdateSelection => {
    // No updates needed
    return haloUpdate;
};

/**
 * Handles the removal of halos when nodes are exited/deactivated
 * @param {HaloExitSelection} haloExit - D3 selection of elements being removed from the visualization
 * @returns {void}
 */
export const onHaloExit = (haloExit: HaloExitSelection): void => {
    haloExit.remove();
};
