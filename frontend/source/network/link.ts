/**
 * Network link visualization handlers
 * This module manages the visual representation of relationships between nodes,
 * including their creation, styling, tooltips, and event handling.
 */

import * as d3 from "d3";
import { debounce } from "../utils";
import type { SimLink } from "./data";
import { getLinkColorClass } from "../color";
import { linkTooltip } from "./tooltips";

type LinkEnterSelection = d3.Selection<
    d3.EnterElement,
    SimLink,
    SVGGElement,
    unknown
>;
type LinkUpdateSelection = d3.Selection<
    SVGGElement,
    SimLink,
    SVGGElement,
    unknown
>;
type LinkExitSelection = d3.Selection<
    SVGGElement,
    SimLink,
    SVGGElement,
    unknown
>;

/**
 * Constants for link behavior and styling
 */
const LINK_DEBOUNCE_TIME = 250; // Debounce time for link interactions in milliseconds
const LINK_IN_TRANSITION_TIME = 50; // Duration of link exit transition in milliseconds
const LINK_OUT_TRANSITION_TIME = 500; // Duration of link exit transition in milliseconds
const LINK_PALETTE = "LinkGreenPalette"; // Default color palette for links

/**
 * Generates HTML content for link annotation, initial letters of the role
 * @param {SimNode} d - Link data object
 * @returns {string} HTML string for link text
 */
const linkAnnotation = (d: SimLink): string => {
    return d.role
        .split(" ")
        .map((x) => x[0])
        .join("");
};

/**
 * Handles the enter selection for new links in the network
 * Creates the basic structure for each link including its visual elements
 * @param {LinkEnterSelection} linkEnter - D3 selection of entering link elements
 */
export const onLinkEnter = (
    linkEnter: LinkEnterSelection,
): LinkEnterSelection => {
    const newLinkEnter = linkEnter
        .append("g")
        .attr("id", (d: SimLink) => `link-${d.key}`)
        .attr("class", (d: SimLink) => {
            const parts = d.key.split("-");
            const role = parts.slice(2, 2 + parts.length - 4).join("-");
            return ["link", role, LINK_PALETTE].join(" ");
        });
    onLinkEnterElementConstruction(newLinkEnter);
    onLinkEnterEventBindings(newLinkEnter);
    return newLinkEnter;
};

/**
 * Constructs the visual elements for each link
 * Creates paths and text elements for link visualization
 * @param {LinkEnterSelection} linkEnter - D3 selection of entering link elements
 */
const onLinkEnterElementConstruction = (
    linkEnter: LinkEnterSelection,
): void => {
    linkEnter.append("path").attr("class", (d: SimLink) => {
        return [
            "inner",
            `distance-${Math.min(d.source.distance, d.target.distance)}`,
            getLinkColorClass(d),
        ].join(" ");
    });
    linkEnter.append("text").attr("class", "outer").text(linkAnnotation);
    linkEnter.append("text").attr("class", "inner").text(linkAnnotation);
};

/**
 * Binds mouse events to link elements
 * Handles mouseover/mouseout events and tooltip display
 * @param {LinkEnterSelection} linkEnter - D3 selection of entering link elements
 */
const onLinkEnterEventBindings = (linkEnter: LinkEnterSelection): void => {
    linkEnter
        .on("mouseover", function (event: MouseEvent, d: SimLink) {
            onLinkMouseOver(event, d);
        })
        .on("mouseout", function (event: MouseEvent, d: SimLink) {
            onLinkMouseOut(event, d);
        });
};

/**
 * Handles updates to existing links in the visualization
 * Currently empty but available for future implementation
 * @param {LinkUpdateSelection} linkSelection - D3 selection of updating link elements
 */
export const onLinkUpdate = (
    linkSelection: LinkUpdateSelection,
): LinkUpdateSelection => {
    // Available for future implementation
    return linkSelection;
};

/**
 * Handles the removal of links from the visualization
 * @param {LinkExitSelection} linkExit - D3 selection of exiting link elements
 */
export const onLinkExit = (linkExit: LinkExitSelection): void => {
    linkExit.remove();
};

/**
 * Mouse event handlers
 */

/**
 * Handles mouse over events on links
 * @param {MouseEvent} event - DOM event object
 * @param {SimLink} d - Link data
 * Shows the tooltip for the hovered link
 */
const onLinkMouseOver = (event: MouseEvent, d: SimLink): void => {
    d3.select(event.target as Element)
        .classed("selected", true)
        .transition()
        .duration(LINK_IN_TRANSITION_TIME);
    handleLinkTooltip(event.target as SVGGElement, d, true);
};

/**
 * Handles mouse out events on links
 * @param {MouseEvent} event - DOM event object
 * @param {SimLink} d - Link data
 * Hides the tooltip for the hovered link
 */
export const onLinkMouseOut = (event: MouseEvent, d: SimLink): void => {
    d3.select(event.target as Element)
        .classed("selected", false)
        .transition()
        .duration(LINK_OUT_TRANSITION_TIME);
    handleLinkTooltip(event.target as SVGGElement, d, false);
};

export const handleLinkTooltip = debounce(
    (element: SVGGElement, d: SimLink, status: boolean) => {
        if (!element) {
            return; // Exit early if element is null or undefined
        }

        if (status) {
            // Try to find a text element to attach the tooltip to
            try {
                // Try different methods to find a text element
                let textElement: Element | null = null;

                // Method 1: Direct querySelector on the element
                if (element.querySelector) {
                    textElement = element.querySelector("text");
                }

                // Method 2: Check parent element if no text found
                if (
                    !textElement &&
                    element.parentElement &&
                    element.parentElement.querySelector
                ) {
                    textElement = element.parentElement.querySelector("text");
                }

                // Method 3: Fallback to the element itself
                if (textElement) {
                    linkTooltip.show(d, textElement);
                } else {
                    linkTooltip.show(d, element);
                }
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
            } catch (_error) {
                // In case of any errors, fallback to just using the element itself
                linkTooltip.show(d, element);
            }
        } else {
            linkTooltip.hide();
        }
    },
    LINK_DEBOUNCE_TIME,
);
