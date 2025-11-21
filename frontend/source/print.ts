import * as d3 from "d3";
import saveAs from "file-saver";
import { DOM_IDS, EXPORT, TIMING, MESSAGE } from "./constants";
import { musigreeManager, networkManager } from "./core";
import { showMessage, clearMessages } from "./messages";

/**
 * Exports the SVG as a PNG image file
 * @param width - The desired width of the output image
 * @param height - The desired height of the output image
 */
export const printSvg = (width: number, height: number): void => {
    showMessage("Saving image to disk, please wait...", MESSAGE.TYPES.DARK);
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
    showMessage("Saving image complete", MESSAGE.TYPES.SUCCESS);
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

    const root = document.querySelector(":root");
    const rootStyles = getComputedStyle(root);
    const varRegex = /(var\(--.*\))/;
    const dashRegex = /(\()(--.*)(\))/;

    // Extract CSS Rules
    let extractedCSSText = "";
    for (const sheet of document.styleSheets) {
        if (
            sheet.href?.includes("musigree") ||
            sheet.ownerNode?.textContent?.includes("Musigree")
        ) {
            try {
                const cssRules = sheet.cssRules;
                if (!cssRules) continue;

                for (const rule of cssRules) {
                    if (!(rule instanceof CSSStyleRule) || !rule.selectorText)
                        continue;

                    const networkSelectorText = rule.selectorText.includes(
                        "#network-layer ",
                    )
                        ? rule.selectorText.replace("#network-layer ", "")
                        : rule.selectorText;
                    if (selectorTextArr.has(networkSelectorText)) {
                        const varFound = rule.cssText.match(varRegex);
                        if (varFound) {
                            const dashFound = rule.cssText.match(dashRegex);
                            const dash = dashFound[2];
                            const prop = rootStyles.getPropertyValue(dash);
                            const newCssText = rule.cssText.replace(
                                varRegex,
                                prop,
                            );
                            extractedCSSText += newCssText + "\n";
                        } else {
                            extractedCSSText += rule.cssText + "\n";
                        }
                    }
                }
            } catch (e) {
                if (e instanceof Error && e.name !== "SecurityError") throw e; // for Firefox
                continue;
            }
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

        const logo = new Image();
        logo.onload = (): void => {
            // context.imageSmoothingEnabled = false;
            // context.clearRect(0, 0, logo.width, logo.height);
            context.drawImage(logo, 200, 200);

            canvas.toBlob((blob) => {
                if (!blob) {
                    throw new Error("Failed to create blob from canvas");
                }
                callback(blob, blob.size);
            }, "image/" + format);
        };
        logo.src = "/public/img/musigree logo with website v3.png";
    };
    image.src = imgsrc;
};
