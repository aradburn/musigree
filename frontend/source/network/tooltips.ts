/**
 * Network Tooltip Manager
 * Manages dynamic Bootstrap tooltips for D3.js network visualization elements
 */

import { Tooltip } from "bootstrap";
import type { SimNode, SimLink } from "./data";

interface TooltipOptions {
    placement?: "top" | "bottom" | "left" | "right";
    container?: string;
    customClass?: string;
    html?: boolean;
    trigger?: "hover" | "click" | "focus" | "manual";
    delay?: number | { show: number; hide: number };
    offset?: [number, number];
}

/**
 * Manages dynamic tooltips for network elements using Bootstrap's Tooltip
 */
export class TooltipManager<T extends SimNode | SimLink> {
    private tooltip: Tooltip | null = null;
    private element: Element | null = null;
    private readonly options: TooltipOptions;
    private readonly contentFn: (data: T) => string;

    /**
     * Creates a new TooltipManager instance
     * @param contentFn - Function that generates tooltip content from data
     * @param options - Bootstrap tooltip options
     */
    constructor(contentFn: (data: T) => string, options: TooltipOptions = {}) {
        this.contentFn = contentFn;
        this.options = {
            ...options,
        };
    }

    /**
     * Shows the tooltip for a given element and data
     * @param data - The data to generate tooltip content from
     * @param element - The DOM element to attach the tooltip to
     */
    show(data: T, element: Element): void {
        hideAllTooltips(); // Clean up any existing tooltip

        // Initialize new tooltip
        this.element = element;
        this.tooltip = new Tooltip(element, {
            ...this.options,
            template: '<div class="tooltip-inner"></div>',
            title: this.contentFn(data),
        });

        this.tooltip.show();
    }

    /**
     * Hides and disposes of the current tooltip
     */
    hide(): void {
        if (this.tooltip) {
            this.tooltip.dispose();
            this.tooltip = null;
        }
        this.element = null;
    }

    /**
     * Updates the content of the current tooltip if it exists
     * @param data - The new data to generate tooltip content from
     */
    update(data: T): void {
        if (this.tooltip && this.element) {
            this.show(data, this.element);
        }
    }

    /**
     * Disposes of the tooltip and cleans up resources
     */
    dispose(): void {
        this.hide();
    }
}

// Create tooltip managers for nodes and links
export const nodeTooltip = new TooltipManager<SimNode>(
    (node) => `<span>${node.name}</span>`,
    {
        placement: "bottom",
        customClass: "d3-node-tooltip",
        html: true,
        offset: [0, -16],
        delay: { show: 100, hide: 100 },
        trigger: "manual",
    },
);

export const linkTooltip = new TooltipManager<SimLink>(
    (link) => `
    <div>${link.source.name}</div>
    <div>${link.role}</div>
    <div>${link.target.name}</div>
  `,
    {
        placement: "top",
        customClass: "d3-link-tooltip",
        html: true,
        offset: [0, 0],
        delay: { show: 100, hide: 100 },
        trigger: "manual",
    },
);

/**
 * Hides all active tooltips
 */
export const hideAllTooltips = (): void => {
    nodeTooltip.hide();
    linkTooltip.hide();
};
