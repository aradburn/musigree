/**
 * Network visualization initialization module
 * Sets up the SVG layers, zoom behavior, and force layout for the network visualization.
 * Creates a hierarchical structure of SVG groups for different visualization elements.
 */

import { initForceLayout } from "./forceLayout";
import { musigreeManager, networkManager } from "../core/singletons";
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

function getInitialTransform(): d3.ZoomTransform {
    const scale =
        Math.min(
            musigreeManager.svgDimensions[0] / musigreeManager.dimensions[0],
            musigreeManager.svgDimensions[1] / musigreeManager.dimensions[1],
        ) * SVG.SCALING_MULTIPLIER;
    console.log("scale: ", scale);

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
    console.log("initialTransform: ", initialTransform);
    return initialTransform;
}

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

    const root = svgElement.append("g").attr("id", "network-layer");
    networkManager.layers.root = root;
    networkManager.layers.halo = root.append("g").attr("id", "halo-layer");
    networkManager.layers.link = root.append("g").attr("id", "link-layer");
    networkManager.layers.node = root.append("g").attr("id", "node-layer");
    networkManager.layers.text = root.append("g").attr("id", "text-layer");

    const w = musigreeManager.svgDimensions[0];
    const h = musigreeManager.svgDimensions[1];

    // Initialize where new nodes will be placed
    const svgCenter: [number, number] = [
        musigreeManager.svgDimensions[0] / 2,
        musigreeManager.svgDimensions[1] / 2,
    ];
    //     console.log("svg newNodeCoords: ", svgCenter);
    networkManager.newNodeCoords = svgCenter;

    // Initialize zoom behavior before calling resetNetworkTransform

    const zoom = d3
        .zoom<SVGSVGElement, unknown>()
        .extent([
            [0, 0],
            [w, h],
        ])
        .scaleExtent([1, 8])
        .on("zoom", handleZoom);
    console.log("init zoom", zoom);
    //     networkManager.zoom = zoom;
    // console.log("zoom.transform method:", networkManager.zoom.transform);
    // console.log(
    //     "zoom methods:",
    //     Object.getOwnPropertyNames(networkManager.zoom),
    // );

    // Apply zoom behavior to the SVG element
    svgElement.call(zoom);

    const initialTransform = getInitialTransform();

    const transform = zoom.transform.bind(zoom) as TransformFunction;

    svgElement.transition().duration(750).call(
        transform,
        initialTransform,
        // invertedPoint,
    );

    // Now that zoom is initialized, we can safely reset the transform
    //     resetNetworkTransform();

    initForceLayout();

    // Dispatch a custom event to notify that the force layout is now initialized
    const forceLayoutInitEvent = new CustomEvent(
        "musigree:force-layout-initialized",
    );
    window.dispatchEvent(forceLayoutInitEvent);
};

/**
 * Resets the network visualization's transform to its default state.
 * Animates the transition over 750ms, centering the view based on the viewport size multiplier.
 * Uses the current zoom state to calculate the proper inversion for smooth animation.
 */
export const resetNetworkTransform = (): void => {
    // Check if zoom behavior is initialized
    //     if (!networkManager.zoom) {
    //         console.warn(
    //             "Cannot reset network transform: zoom behavior not initialized",
    //         );
    //         return;
    //     }

    //     const scale =
    //         Math.min(
    //             musigreeManager.svgDimensions[0] / musigreeManager.dimensions[0],
    //             musigreeManager.svgDimensions[1] / musigreeManager.dimensions[1],
    //         ) * SVG.SCALING_MULTIPLIER;
    //     console.log("scale: ", scale);

    const svgElement = d3.select<SVGSVGElement, unknown>(DOM_IDS.SVG_ID);
    const initialTransform = getInitialTransform();
    //     const initialTransform = d3.zoomIdentity
    //         .scale(scale)
    //         .translate(
    //             (musigreeManager.dimensions[0] / SVG.SCALING_MULTIPLIER -
    //                 musigreeManager.svgDimensions[0]) /
    //                 2.0,
    //             (musigreeManager.dimensions[1] / SVG.SCALING_MULTIPLIER -
    //                 musigreeManager.svgDimensions[1]) /
    //                 2.0,
    //         );
    //     console.log("initialTransform: ", initialTransform);

    const svgNode = svgElement.node();
    if (!(svgNode instanceof Element)) {
        console.error("SVG node is not an instance of Element");
        return;
    }
    const currentTransform = d3.zoomTransform(svgNode);
    console.log("currentTransform: ", currentTransform);

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
    console.log("invertedPoint: ", invertedPoint);

    //     networkManager.zoom = d3
    //         .zoom<SVGSVGElement, unknown>()
    //         .extent([
    //             [0, 0],
    //             [w, h],
    //         ])
    //         .scaleExtent([1, 8])
    //         .on("zoom", handleZoom);
    //     const zoom = networkManager.zoom;
    //     console.log("zoom: ", zoom);
    //     console.log("d3.zoom().transform: ", d3.zoom().transform);
    //     const w = musigreeManager.svgDimensions[0];
    //     const h = musigreeManager.svgDimensions[1];
    //     const zoom = d3.zoom()
    //                    .extent([
    //                              [0, 0],
    //                              [w, h],
    //                    ])
    //                    .scaleExtent([1, 8]);
    //     console.log("zoom: ", zoom);
    //     svgElement.call(zoom.scaleTo, initialTransform.k);
    //     svgElement.call(zoom.translateTo, initialTransform.x, initialTransform.y);
    // const transform = networkManager.zoom.transform.bind(
    //     networkManager.zoom,
    // ) as TransformFunction;
    //     svgElement
    //         .transition()
    //         .duration(750)
    //         .call(
    //             zoom.transform,
    //             initialTransform,
    //             invertedPoint,
    //         );
    // networkManager.zoom.transform(svgElement, initialTransform, invertedPoint);
    // const transform = networkManager.zoom.transform.bind(
    //     networkManager.zoom,
    // ) as TransformFunction;
    // svgElement
    //     .transition()
    //     .duration(750)
    //     .call(transform, initialTransform, invertedPoint);

    // Apply the transform to the root network layer
    if (networkManager.layers.root) {
        networkManager.layers.root
            .transition()
            .duration(1000)
            .attr("transform", initialTransform.toString());
    }

    // Update the zoom behavior's internal transform state
    if (svgNode) {
        // This updates D3's internal zoom transform state
        // @ts-expect-error __zoom
        svgNode.__zoom = initialTransform;
    }

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
