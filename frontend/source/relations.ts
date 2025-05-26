/**
 * @fileoverview Relations visualization module for Musigree
 * This module handles the creation and management of radial/circular relationship visualizations
 * using D3.js. It provides functionality for creating interactive circular charts that display
 * relationships between different roles or entities.
 */

import * as d3 from "d3";
import { musigreeManager, relationsManager } from "./core";
import { DOM_IDS, SVG_IDS, RELATIONS, TIMING } from "./constants";

/**
 * Data structure for individual relations
 */
interface RelationData {
    year: number;
    category: string;
    role: string;
}

/**
 * Collection of relation data
 */
export interface RelationsData {
    results: RelationData[];
}

/**
 * SVG layer containers for relations visualization
 */
export interface RelationsLayers {
    root: d3.Selection<SVGGElement, unknown, HTMLElement, unknown> | null;
}

/**
 * Relations state and functionality
 */
export interface Relations {
    data: RelationsData;
    byYear: d3.InternMap<number, d3.InternMap<string, RelationData[]>>;
    byRole: d3.InternMap<string, number>;
    layers: RelationsLayers;
}

/**
 * Arc data type for relations visualization
 */
export interface RelationsArcData {
    role: string;
    count: number;
    startAngle: number;
    endAngle: number;
    innerRadius: number;
    outerRadius: number;
    padAngle?: number;
}

/**
 * Initializes the relations visualization by setting up the base SVG container
 * Creates a root group element for all relation-based visualizations
 */
export function initRelations(): void {
    const svgElement = d3.select(DOM_IDS.SVG_ID);
    const root = svgElement.append("g").attr("id", SVG_IDS.RELATIONS_LAYER);
    relationsManager.setRootLayer(root);

    // Zoom functionality commented out for now
    // relations.zoom = d3.zoom()
    //     .extent([[0, 0], [musigreeManager.svgDimensions[0], musigreeManager.svgDimensions[1]]])
    //     .scaleExtent([RELATIONS.ZOOM.MIN_SCALE, RELATIONS.ZOOM.MAX_SCALE])
    //     .on("zoom", handleZoom);
    // svgElement.call(relations.zoom)
}

/**
 * Sets the relations data
 * @param {RelationsData} data - The relations data to set
 */
export function setRelationsData(data: RelationsData): void {
    relationsManager.setData(data);
    console.log("relationsManager.byRole: ", relationsManager.byRole);
}

/**
 * Creates a radial chart visualization
 * This function handles the creation of a circular/radial chart that displays data
 * in a circular arrangement with segments sized according to their values
 *
 * Features:
 * - Dynamic segment sizing based on data values
 * - Animated transitions for segment creation
 * - Interactive segments with hover effects
 * - Text labels for each segment (both inner and outer)
 */
export function createRadialChart(): void {
    console.log("createRadialChart()");

    // Check if dimensions are available
    if (!musigreeManager.dimensions) {
        console.error("Error: dimensions not available for radial chart");
        return;
    }

    const textAnchor = (_d: RelationsArcData, i: number): "start" | "end" => {
        const angle = (i + 0.5) / numBars;
        return angle < 0.5 ? "start" : "end";
    };

    const barHeight =
        Math.min(...musigreeManager.dimensions) / RELATIONS.DIMENSIONS.DIVISOR;
    console.log("createRadialChart() barHeight:", barHeight);
    const data = relationsManager.byRole;
    console.log("createRadialChart() data: ", data);

    // Check if data is empty
    if (!data || data.size === 0) {
        console.warn("No data available for radial chart");
        return;
    }

    const extent = d3.extent(Array.from(data.values()));
    console.log("createRadialChart() extent: ", extent);

    // Ensure extent has valid values
    if (!extent || extent.length < 2 || extent.some((v) => v === undefined)) {
        console.error("Invalid data extent for radial chart");
        return;
    }

    const barScale = d3
        .scaleSqrt()
        .domain(extent as [number, number])
        .range([barHeight * RELATIONS.SCALE.MIN_MULTIPLIER, barHeight])
        .exponent(RELATIONS.SCALE.EXPONENT);
    const numBars = data.size;

    const transform = (d: RelationsArcData, i: number): string => {
        console.log("d: ", d);
        console.log("i: ", i);
        const hypotenuse = barScale(d.count) + RELATIONS.DIMENSIONS.TEXT_OFFSET;
        const angle = (i + 0.5) / numBars;
        let degrees = angle * RELATIONS.ANGLES.FULL_CIRCLE;
        if (RELATIONS.ANGLES.HALF_CIRCLE <= degrees) {
            degrees -= RELATIONS.ANGLES.HALF_CIRCLE;
        }
        degrees += RELATIONS.ANGLES.START_DEGREES;
        const radians = angle * RELATIONS.ANGLES.TWO_PI;
        const x = Math.sin(radians) * hypotenuse;
        const y = -Math.cos(radians) * hypotenuse;
        return [`rotate(${degrees},${x},${y})`, `translate(${x},${y})`].join(
            " ",
        );
    };

    initRelations();

    const arc = d3
        .arc<RelationsArcData>()
        .startAngle((_d, i) => (i * RELATIONS.ANGLES.TWO_PI) / numBars)
        .endAngle((_d, i) => ((i + 1) * RELATIONS.ANGLES.TWO_PI) / numBars)
        .innerRadius(0)
        .outerRadius((d) => d.outerRadius);

    console.log("createRadialChart() arc: ", arc);

    const radialGroup = relationsManager.layers.root
        ?.append("g")
        .attr("class", "radial centered")
        .attr(
            "transform",
            `translate(${musigreeManager.dimensions[0] / 2},${musigreeManager.dimensions[1] / 2})`,
        );

    const arcData = Array.from(data.entries()).map(([role, count], index) => ({
        role,
        count,
        outerRadius: 0,
        startAngle: (index * RELATIONS.ANGLES.TWO_PI) / data.size,
        endAngle: ((index + 1) * RELATIONS.ANGLES.TWO_PI) / data.size,
        innerRadius: 0,
    }));

    const segments = radialGroup
        .selectAll<SVGGElement, RelationsArcData>("g")
        .data(arcData)
        .enter()
        .append("g")
        .attr("class", "segment")
        .on("mouseover", () => {
            d3.select(this).raise();
        });

    console.log("createRadialChart() segments: ", segments);

    segments
        .append("path")
        .attr("class", "arc")
        .attr("d", arc)
        .each(function (d) {
            d.outerRadius = 0;
        })
        .transition()
        .ease(d3.easeElastic)
        .duration(TIMING.RADIAL_TRANSITION.DURATION)
        .delay(
            (d, i) => (numBars - i) * TIMING.RADIAL_TRANSITION.DELAY_MULTIPLIER,
        )
        .attrTween("d", function (d) {
            console.log("attrTween d: ", d);
            const outer = d3.interpolate(0, barScale(d.count));
            return function (t): string {
                console.log("attrTween t: ", t);
                d.outerRadius = outer(t);
                return arc(d);
            };
        });

    segments
        .append("text")
        .attr("class", "outer")
        .attr("text-anchor", textAnchor)
        .attr("transform", transform)
        .text((d) => d.role);

    segments
        .append("text")
        .attr("class", "inner")
        .attr("text-anchor", textAnchor)
        .attr("transform", transform)
        .text((d) => d.role);

    console.log("createRadialChart() end");
}

/**
 * Handles zoom events for the relations visualization
 * Applies zoom transformations to the root layer of the visualization
 *
 * @param {Object} param0 - Zoom event parameters
 * @param {d3.ZoomTransform} param0.transform - D3 zoom transform object
 */
export function handleZoom({
    transform,
}: {
    transform: d3.ZoomTransform;
}): void {
    relationsManager.layers.root.attr("transform", transform.toString());
}

/**
 * Clears the relations layer from the SVG
 * Removes the relations layer element from the SVG
 */
export function clearRelationsLayer(): void {
    d3.select(`#${SVG_IDS.RELATIONS_LAYER}`).remove();
}
