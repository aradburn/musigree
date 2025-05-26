/**
 * @fileoverview SVG manipulation utilities for Musigree
 * This module provides functionality for SVG initialization, sizing, definition setup,
 * and SVG export capabilities. It handles SVG element manipulation, styling, and
 * conversion to other image formats.
 */

import * as d3 from "d3";
import { saveAs } from "file-saver";
import { musigreeManager, networkManager } from "./core/index";
import { showMessage, clearMessages } from "./messages";
import {
    SVG,
    MARKER,
    SVG_IDS,
    DOM_IDS,
    GRADIENT,
    TIMING,
    EXPORT,
} from "./constants";

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
    setSvgSize(DOM_IDS.SVG_ID);

    // Setup SVG common definitions
    setupSvgDefs(DOM_IDS.SVG_ID);
};

/**
 * Sets the size and viewport attributes of the main SVG element
 * Uses global musigreeManager.dimensions and musigreeManager.svgDimensions for sizing
 */
export const setSvgSize = (svgSelector: string): void => {
    try {
        const dpr = window.devicePixelRatio || 1;
        console.log("window devicePixelRatio: ", dpr);

        const svgContainer = document.getElementById(DOM_IDS.SVG_CONTAINER);

        // Add null check to prevent errors when the SVG container doesn't exist
        if (!svgContainer) {
            console.error(
                `SVG container element with ID "${DOM_IDS.SVG_CONTAINER}" not found. Skipping window initialization.`,
            );
            return;
        }

        const width = svgContainer.clientWidth;
        const height = svgContainer.clientHeight;
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

/**
 * Exports the SVG as a PNG image file
 * @param width - The desired width of the output image
 * @param height - The desired height of the output image
 */
export const printSvg = (width: number, height: number): void => {
    showMessage("info", "Saving image to disk, please wait...");
    const svgNode = d3.select(DOM_IDS.SVG_ID).node() as SVGElement | null;

    if (!svgNode) {
        throw new Error("SVG element not found");
    }

    // Get the SVG string
    const svgString = getSvgString(svgNode);

    // Check if selected node exists
    const selectedNodeKey = musigreeManager.selectedNodeKey;
    if (selectedNodeKey && !networkManager.data.nodeMap.has(selectedNodeKey)) {
        throw new Error("Selected node not found");
    }

    try {
        svgString2Image(
            svgString,
            EXPORT.SCALE_FACTOR * width,
            EXPORT.SCALE_FACTOR * height,
            "png",
            (blob: Blob | null, filesize: number) => {
                if (!blob) {
                    throw new Error("Failed to create image blob");
                }
                saveBlob(blob, filesize);
            },
        );
    } catch (error) {
        if (error instanceof Error) {
            throw error;
        }
        throw new Error("Failed to create image blob");
    }
};

/**
 * Callback function to save the blob data as a file
 * @param dataBlob - The blob data to save
 * @param filesize - The size of the file
 */
function saveBlob(dataBlob: Blob, _filesize: number): void {
    const entityKey = musigreeManager.selectedNodeKey;
    const node = entityKey ? networkManager.data.nodeMap.get(entityKey) : null;
    if (!node) {
        throw new Error("Selected node not found");
    }

    const filename = `Musigree - ${node.name}.png`;
    saveAs(dataBlob, filename);

    clearMessages(TIMING.QUICK_MESSAGE_CLEAR);
    showMessage("success", "Saving image complete");
    clearMessages(TIMING.LONG_MESSAGE_CLEAR);
}

/**
 * Converts an SVG node to a string representation
 * @param svgNode - The SVG DOM node to convert
 * @returns The serialized SVG string with proper namespace handling
 */
export const getSvgString = (svgNode: SVGElement): string => {
    svgNode.setAttribute("xlink", "http://www.w3.org/1999/xlink");
    const cssStyleText = getCSSStyles(svgNode);
    appendCSS(cssStyleText, svgNode);

    const serializer = new XMLSerializer();
    let svgString = serializer.serializeToString(svgNode);
    svgString = svgString.replace(/(\w+)?:?xlink=/g, "xmlns:xlink="); // Fix root xlink without namespace
    svgString = svgString.replace(/NS\d+:href/g, "xlink:href"); // Safari NS namespace fix

    return svgString;
};

/**
 * Gets CSS styles for SVG elements
 * @param parentElement - The parent SVG element
 * @returns Concatenated CSS rules
 */
export const getCSSStyles = (parentElement: SVGElement): string => {
    const selectorTextArr = new Set<string>();

    // Add Parent element Id and Classes
    if (parentElement.id) {
        selectorTextArr.add(`#${parentElement.id}`);
    }
    Array.from(parentElement.classList).forEach((className) => {
        selectorTextArr.add(`.${className}`);
    });

    // Process all child nodes
    const nodes = parentElement.getElementsByTagName("*");
    Array.from(nodes).forEach((node) => {
        if (node.id) {
            selectorTextArr.add(`#${node.id}`);
        }

        Array.from(node.classList).forEach((className) => {
            // Basic class
            selectorTextArr.add(`.${className}`);

            // Node type with class
            if (node.nodeName) {
                selectorTextArr.add(`${node.nodeName}.${className}`);
            }

            // Parent relationships
            const parentNode = node.parentNode;
            if (parentNode instanceof Element) {
                if (parentNode.id) {
                    selectorTextArr.add(`#${parentNode.id} .${className}`);
                    if (node.nodeName) {
                        selectorTextArr.add(
                            `#${parentNode.id} ${node.nodeName}.${className}`,
                        );
                    }
                }

                Array.from(parentNode.classList).forEach((parentClass) => {
                    selectorTextArr.add(`.${parentClass}`);
                    selectorTextArr.add(`.${parentClass} .${className}`);
                    if (node.nodeName) {
                        selectorTextArr.add(
                            `.${parentClass} ${node.nodeName}.${className}`,
                        );
                    }
                });

                // Grandparent relationships
                const grandParentNode = parentNode.parentNode;
                if (grandParentNode instanceof Element && grandParentNode.id) {
                    selectorTextArr.add(`#${grandParentNode.id} .${className}`);
                    Array.from(parentNode.classList).forEach((parentClass) => {
                        selectorTextArr.add(
                            `#${grandParentNode.id} .${parentClass}`,
                        );
                        selectorTextArr.add(
                            `#${grandParentNode.id} .${parentClass} .${className}`,
                        );
                        if (node.nodeName) {
                            selectorTextArr.add(
                                `#${grandParentNode.id} .${parentClass} ${node.nodeName}.${className}`,
                            );
                        }
                    });
                }
            }
        });
    });

    // Extract CSS Rules
    let extractedCSSText = "";
    for (const sheet of document.styleSheets) {
        try {
            const cssRules = sheet.cssRules;
            if (!cssRules) continue;

            for (const rule of cssRules) {
                if (
                    rule instanceof CSSStyleRule &&
                    selectorTextArr.has(rule.selectorText)
                ) {
                    extractedCSSText += rule.cssText + "\n";
                }
            }
        } catch (e) {
            if (e instanceof Error && e.name !== "SecurityError") throw e; // for Firefox
            continue;
        }
    }

    return extractedCSSText;
};

/**
 * Appends CSS styles to an SVG element
 * @param cssText - The CSS text to append
 * @param element - The target SVG element
 */
export const appendCSS = (cssText: string, element: SVGElement): void => {
    const styleElement = document.createElement("style");
    styleElement.setAttribute("type", "text/css");
    styleElement.textContent = cssText;
    const refNode = element.querySelector("defs") || element.firstChild;
    element.insertBefore(styleElement, refNode);
};

/**
 * Converts an SVG string to an image
 * @param svgString - The SVG string to convert
 * @param width - The desired width of the output image
 * @param height - The desired height of the output image
 * @param format - The output format (default: 'png')
 * @param callback - Callback function to handle the converted image
 */
export const svgString2Image = (
    svgString: string,
    width: number,
    height: number,
    format: string = "png",
    callback: (blob: Blob, filesize: number) => void,
): void => {
    const imgsrc =
        "data:image/svg+xml;base64," +
        btoa(unescape(encodeURIComponent(svgString)));

    const canvas = document.createElement("canvas");
    const context = canvas.getContext("2d");

    if (!context) {
        throw new Error("Could not get canvas context");
    }

    canvas.width = width;
    canvas.height = height;

    const image = new Image();
    image.onload = function (): void {
        context.clearRect(0, 0, width, height);
        context.drawImage(image, 0, 0, width, height);

        canvas.toBlob((blob) => {
            if (!blob) {
                throw new Error("Failed to create blob from canvas");
            }
            callback(blob, blob.size);
        }, "image/" + format);
    };
    image.src = imgsrc;
};
