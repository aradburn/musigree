/**
 * Network node text visualization handlers
 * This module manages the text labels for network nodes, including their creation,
 * updating, and removal, as well as debug information display.
 */

import type * as d3 from "d3";
import { getOuterRadius } from "./node";
import { getNodeColorClass } from "../color";
import { musigreeManager } from "../core/singletons";
import type { SimNode } from "./data";

type TextEnterSelection = d3.Selection<
    d3.EnterElement,
    SimNode,
    SVGGElement,
    unknown
>;
type TextUpdateSelection = d3.Selection<
    SVGGElement,
    SimNode,
    SVGGElement,
    unknown
>;
type TextExitSelection = d3.Selection<
    SVGGElement,
    SimNode,
    SVGGElement,
    unknown
>;

/**
 * Vertical offset for node labels from their center point
 * @constant {number}
 */
export const ARTIST_TEXT_OFFSET_Y = 10;
export const LABEL_TEXT_OFFSET_Y = 9;

/**
 * Calculates the offset of the text from the node
 * @param {SimNode} d - Node data
 * @returns {number} - Label offset in y direction
 */
export const getLabelOffset = (d: SimNode): number => {
    return d.type === "artist" ? ARTIST_TEXT_OFFSET_Y : LABEL_TEXT_OFFSET_Y;
};

/**
 * Generates the display text for a network node
 * @param {SimNode} d - The node data object
 * @returns {string} Truncated name (with debug info if debug mode is enabled)
 */
export const getNodeText = (d: SimNode): string => {
    let name = d.name;
    if (name.length > 50) {
        name = `${name.slice(0, 50)}...`;
    }
    if (musigreeManager.debug) {
        name = `${name}${getNodeDebug(d)}`;
    }
    return name;
};

/**
 * Generates debug information text for a network node
 * @param {SimNode} d - The node data object
 * @returns {string} Formatted debug information string
 */
export const getNodeDebug = (d: SimNode): string => {
    const links = d.links?.length ?? 0;
    return (
        ` dist: ${d.distance}` +
        ` radi: ${d.radius}` +
        ` link: ${links}` +
        ` miss: ${d.missing}` +
        ` clus: ${d.cluster ?? "undefined"}` +
        ` colr: ${getNodeColorClass(d)}`
    );
};

/**
 * Handles the enter selection for network node text elements
 * Creates the text group and adds both outer and inner text elements
 * @param {TextEnterSelection} textEnter - D3 enter selection for text elements
 */
export const onTextEnter = (
    textEnter: TextEnterSelection,
): TextEnterSelection => {
    const textGroup = textEnter
        .append("g")
        .attr("id", (d: SimNode) => d.key)
        .attr("class", (d: SimNode) => {
            const classes = ["node", d.key.split("-")[0]];
            if (d.cluster !== undefined) {
                classes.push("cluster");
            }
            return classes.join(" ");
        });

    textGroup
        .append("text")
        .attr("class", "outer")
        .attr("dy", (d: SimNode) => getOuterRadius(d) + getLabelOffset(d))
        .attr("width", (d: SimNode) => getOuterRadius(d) * 3)
        .text(getNodeText);

    textGroup
        .append("text")
        .attr("class", "inner")
        .attr("dy", (d: SimNode) => getOuterRadius(d) + getLabelOffset(d))
        .attr("width", (d: SimNode) => getOuterRadius(d) * 3)
        .text(getNodeText);

    return textGroup;
};

/**
 * Handles the update selection for network node text elements
 * Updates the text content of both outer and inner text elements
 * @param {TextUpdateSelection} textUpdate - D3 update selection for text elements
 */
export const onTextUpdate = (
    textUpdate: TextUpdateSelection,
): TextUpdateSelection => {
    textUpdate
        .select(".outer")
        .attr("dy", (d: SimNode) => getOuterRadius(d) + getLabelOffset(d))
        .attr("width", (d: SimNode) => getOuterRadius(d) * 3)
        .text(getNodeText);
    textUpdate
        .select(".inner")
        .attr("dy", (d: SimNode) => getOuterRadius(d) + getLabelOffset(d))
        .attr("width", (d: SimNode) => getOuterRadius(d) * 3)
        .text(getNodeText);
    return textUpdate;
};

/**
 * Handles the exit selection for network node text elements
 * Removes text elements that are no longer needed
 * @param {TextExitSelection} textExit - D3 exit selection for text elements
 */
export const onTextExit = (textExit: TextExitSelection): void => {
    textExit.remove();
};
