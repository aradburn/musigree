/**
 * @fileoverview SVG manipulation utilities for Musigree
 * This module provides functionality for SVG initialization, sizing, definition setup,
 * and SVG export capabilities. It handles SVG element manipulation, styling, and
 * conversion to other image formats.
 */

import * as d3 from "d3";
import { musigreeManager, networkManager } from "./core/index";
import { SVG, MARKER, SVG_IDS, DOM_IDS, GRADIENT } from "./constants";
import { convertRemToPixels } from "./utils";

/**
 * Initializes the SVG element with basic setup
 * - Sets up window dimensions
 * - Creates SVG definitions (markers, gradients)
 */
export const initSvg = (): void => {
    const svgContainer = document.getElementById(DOM_IDS.SVG_CONTAINER);
    if (!svgContainer) {
        console.error("SVG container not found");
        return;
    }

    // Get the SVG element
    const svgElement = document.getElementById(DOM_IDS.SVG);
    if (svgElement) {
        console.debug("SVG element already exists");
        return;
    }

    const svgSelection = d3.select(DOM_IDS.SVG_CONTAINER_ID);

    // Create the SVG canvas
    // Create the SVG element if it doesn't exist yet
    //                 if (!document.getElementById(DOM_IDS.SVG)) {
    //                     const svg = document.createElementNS(
    //                         "http://www.w3.org/2000/svg",
    //                         "svg",
    //                     );
    //                     svg.id = DOM_IDS.SVG;
    //                     containerRef.current.appendChild(svg);
    //                 }
    svgSelection.append("svg").attr("id", DOM_IDS.SVG);

    // Setup window dimensions on SVG element
    setSvgSize(DOM_IDS.SVG_ID, false);

    // Setup SVG common definitions
    setupSvgDefs(DOM_IDS.SVG_ID);
};

/**
 * Sets the size and viewport attributes of the main SVG element
 * Uses global musigreeManager.dimensions and musigreeManager.svgDimensions for sizing
 */
export const setSvgSize = (svgSelector: string, isSidebarRightCollapsed: bool): void => {
    console.log("setSvgSize isSidebarRightCollapsed: ", isSidebarRightCollapsed);
    try {
        const dpr = window.devicePixelRatio || 1;
        console.log("window devicePixelRatio: ", dpr);

        const svgContainer = document.getElementById(DOM_IDS.SVG_CONTAINER);
        const navTopContainer = document.getElementById(DOM_IDS.NAV_TOP);

        // Add null check to prevent errors when the SVG container doesn't exist
        if (!svgContainer) {
            console.error(
                `SVG container element with ID "${DOM_IDS.SVG_CONTAINER}" not found. Skipping window initialization.`,
            );
            return;
        }

        const calculatedSvgContainerWidth = isSidebarRightCollapsed ?
                     window.innerWidth - convertRemToPixels(20) :
                     window.innerWidth - convertRemToPixels(45);
        const smallSvgContainerHeight = window.innerHeight / 2.0;
        const largeSvgContainerHeight =
            window.innerHeight - navTopContainer.clientHeight;
        const width =
            window.innerWidth >= 576
                ? calculatedSvgContainerWidth
                : window.innerWidth;
        const height =
            window.innerWidth >= 576
                ? largeSvgContainerHeight
                : smallSvgContainerHeight;
        const svgContainerDimensions: [number, number] = [width, height];
        const svgCanvasDimensions: [number, number] = [
            svgContainerDimensions[0] * SVG.VIEWPORT_SIZE_MULTIPLIER * dpr,
            svgContainerDimensions[1] * SVG.VIEWPORT_SIZE_MULTIPLIER * dpr,
        ];
        console.log("svgContainerDimensions: ", svgContainerDimensions);
        console.log("svgCanvasDimensions: ", svgCanvasDimensions);

        musigreeManager.dpr = dpr;
        musigreeManager.dimensions = svgContainerDimensions;
        musigreeManager.svgDimensions = svgCanvasDimensions;

        //         const [width, height] = musigreeManager.dimensions;
        const [svgWidth, svgHeight] = musigreeManager.svgDimensions;

        // Get the SVG element
        const svgSelection = d3.select(svgSelector);

        // Check if we have a valid selection before setting attributes
        if (svgSelection.empty()) {
            console.warn("SVG element or attr function not found");
            return;
        }

        console.log("Set SVG dim: ", width, height);
        console.log("Set SVG size: ", svgWidth, svgHeight);

        // Setup window dimensions on SVG element
        svgSelection
            .attr("width", String(width))
            .attr("height", String(height))
            .attr("viewBox", `0 0 ${svgWidth} ${svgHeight}`)
            .attr("preserveAspectRatio", "none");
    } catch (err) {
        console.error("Error setting SVG size:", err);
    }
};

/**
 * Sets up SVG definitions including:
 * - Arrowhead marker for directed connections
 * - Aggregate marker for relationship indicators
 * - Radial gradient for visual effects
 */
export const setupSvgDefs = (svgSelector: string): void => {
    try {
        // Get the SVG element
        const svgSelection = d3.select(svgSelector);

        // Check if we have a valid selection before setting attributes
        if (svgSelection.empty()) {
            console.warn("SVG element or append function not found");
            return;
        }

        const defs = svgSelection.append("defs");

        // ARROWHEAD
        defs.append("marker")
            .attr("id", SVG_IDS.ARROWHEAD)
            .attr("viewBox", MARKER.VIEWBOX)
            .attr("refX", MARKER.ARROWHEAD_REFX)
            .attr("refY", MARKER.REFY)
            .attr("markerWidth", MARKER.WIDTH)
            .attr("markerHeight", MARKER.HEIGHT)
            .attr("markerUnits", "strokeWidth")
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M 0,0 m -5,-5 L 5,0 L -5,5 L -2.5,0 L -5,-5 Z")
            .attr("stroke-linecap", "round")
            .attr("stroke-linejoin", "round");

        // AGGREGATE
        defs.append("marker")
            .attr("id", SVG_IDS.AGGREGATE)
            .attr("viewBox", MARKER.VIEWBOX)
            .attr("refX", MARKER.AGGREGATE_REFX)
            .attr("refY", MARKER.REFY)
            .attr("markerWidth", MARKER.WIDTH)
            .attr("markerHeight", MARKER.HEIGHT)
            .attr("markerUnits", "strokeWidth")
            .attr("orient", "auto")
            .append("path")
            .attr("d", "M 0,0 m 5,0 L 0,-3 L -5,0 L 0,3 L 5,0 Z")
            .attr("fill", "#fff")
            .attr("stroke", "#000")
            .attr("stroke-linecap", "round")
            .attr("stroke-linejoin", "round")
            .attr("stroke-width", MARKER.STROKE_WIDTH);

        // RADIAL GRADIENT
        const gradient = defs
            .append("radialGradient")
            .attr("id", SVG_IDS.RADIAL_GRADIENT);

        GRADIENT.STOPS.forEach(({ offset, opacity }) => {
            gradient
                .append("stop")
                .attr("offset", offset)
                .attr("stop-color", GRADIENT.COLOR)
                .attr("stop-opacity", opacity);
        });
    } catch (err) {
        console.error("Error setting up SVG definitions:", err);
    }
};
