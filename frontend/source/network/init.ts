/**
 * Network visualization initialization module
 * Sets up the SVG layers, zoom behavior, and force layout for the network visualization.
 * Creates a hierarchical structure of SVG groups for different visualization elements.
 */

import { initForceLayout } from "./forceLayout";
import { musigreeManager, networkManager } from "../core";
import * as d3 from "d3";
import { hideAllTooltips } from "./tooltips";
import { SVG, DOM_IDS } from "../constants";

type TransformFunction = (
    selection:
        | d3.Selection<d3.BaseType, unknown, d3.BaseType, unknown>
        | d3.Transition<d3.BaseType, unknown, d3.BaseType, unknown>,
    transform: d3.ZoomTransform,
    point?: [number, number],
) => void;

/**
 * Initializes the network visualization by setting up the SVG layers, zoom behavior, and force layout.
 * Creates a hierarchical structure of SVG groups for different visualization elements:
 * - halo: For node highlighting effects
 * - link: For connections between nodes
 * - node: For the actual nodes
 * - text: For node labels
 */
export const initNetwork = (svgSelector: string): void => {
    const svgElement = d3.select(svgSelector);

    const root = svgElement.append("g").attr("id", "networkLayer");
    networkManager.layers.root = root;
    networkManager.layers.halo = root.append("g").attr("id", "haloLayer");
    networkManager.layers.link = root.append("g").attr("id", "linkLayer");
    networkManager.layers.node = root.append("g").attr("id", "nodeLayer");
    networkManager.layers.text = root.append("g").attr("id", "textLayer");

    const w = musigreeManager.svgDimensions[0];
    const h = musigreeManager.svgDimensions[1];

    networkManager.zoom = d3
        .zoom<SVGSVGElement, unknown>()
        .extent([
            [0, 0],
            [w, h],
        ])
        .scaleExtent([1, 8])
        .on("zoom", handleZoom);

    svgElement.call(networkManager.zoom);

    resetNetworkTransform();

    initForceLayout();
};

/**
 * Resets the network visualization's transform to its default state.
 * Animates the transition over 750ms, centering the view based on the viewport size multiplier.
 * Uses the current zoom state to calculate the proper inversion for smooth animation.
 */
export const resetNetworkTransform = (): void => {
    const scale =
        Math.min(
            musigreeManager.svgDimensions[0] / musigreeManager.dimensions[0],
            musigreeManager.svgDimensions[1] / musigreeManager.dimensions[1],
        ) * SVG.SCALING_MULTIPLIER;
    //     console.log("scale: ", scale);

    const svgElement = d3.select(DOM_IDS.SVG_ID);
    const initialTransform = d3.zoomIdentity
        .scale(scale)
        .translate(
            (musigreeManager.dimensions[0] / SVG.SCALING_MULTIPLIER -
                musigreeManager.svgDimensions[0]) /
                2.0,
            (musigreeManager.dimensions[1] / SVG.SCALING_MULTIPLIER -
                musigreeManager.svgDimensions[1]) /
                2.0,
        );

    const svgNode = svgElement.node();
    if (!(svgNode instanceof Element)) {
        console.error("SVG node is not an instance of Element");
        return;
    }
    const currentTransform = d3.zoomTransform(svgNode);
    //     const x = musigreeManager.svg_dimensions[0] / VIEWPORT_SIZE_MULTIPLIER;
    //     const y = musigreeManager.svg_dimensions[1] / VIEWPORT_SIZE_MULTIPLIER;
    //     const invertedPoint = currentTransform.invert([x, y]);
    const invertedPoint = currentTransform.invert([
        -(
            musigreeManager.dimensions[0] / SVG.SCALING_MULTIPLIER -
            musigreeManager.svgDimensions[0]
        ) / 2.0,
        -(
            musigreeManager.dimensions[1] / SVG.SCALING_MULTIPLIER -
            musigreeManager.svgDimensions[1]
        ) / 2.0,
    ]);

    const transform = networkManager.zoom.transform.bind(
        networkManager.zoom,
    ) as TransformFunction;
    svgElement
        .transition()
        .duration(750)
        .call(transform, initialTransform, invertedPoint);

    // Initialize where new nodes will be placed
    const svgCenter: [number, number] = [
        musigreeManager.svgDimensions[0] / 2,
        musigreeManager.svgDimensions[1] / 2,
    ];
    //     console.log("svg newNodeCoords: ", svgCenter);
    networkManager.newNodeCoords = svgCenter;
};

/**
 * Handles zoom events on the network visualization.
 * Updates the root layer's transform to reflect the current zoom state and hides any visible tooltips.
 *
 * @param {d3.D3ZoomEvent<SVGSVGElement, unknown>} event - The zoom event object
 */
const handleZoom = (event: d3.D3ZoomEvent<SVGElement, unknown>): void => {
    if (networkManager.layers.root) {
        networkManager.layers.root.attr(
            "transform",
            event.transform.toString(),
        );
    }
    hideAllTooltips();
};
