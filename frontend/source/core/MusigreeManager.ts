import * as d3 from "d3";
import type { NodeKey } from "../network/data";
import type { RelationsArcData } from "../relations";
import { SVG } from "../constants";

/**
 * Core Musigree configuration
 */
export interface MusigreeConfig {
    /** Debug mode flag */
    debug?: boolean;
    /** Version information */
    version?: string;
    /** Device pixel ratio override (mainly for testing) */
    dpr?: number;
    /** Mobile device flag override (mainly for testing) */
    isMobile?: boolean;
}

/**
 * Core Musigree application manager
 * Responsible for managing global application state and configuration
 */
export class MusigreeManager {
    /** Version number */
    private _version: string;
    /** Debug mode flag */
    private _debug: boolean;
    /** Device pixel ratio */
    private _dpr: number;
    /** SVG container dimensions [width, height] */
    private _dimensions: [number, number];
    /** SVG dimensions [width, height] */
    private _svgDimensions: [number, number];
    /** Currently selected node key */
    private _selectedNodeKey: NodeKey;
    /** Right sidebar collapsed state */
    private _isSidebarRightCollapsed: boolean;
    /** Mobile device flag */
    private _isMobile: boolean;
    /** Getter function to retrieve isMobile from WindowContext */
    private _isMobileGetter: (() => boolean) | null = null;
    /** D3 arc generator for relations visualization */
    private _arc: d3.Arc<RelationsArcData, RelationsArcData>;

    /**
     * Creates a new MusigreeManager instance
     * @param {MusigreeConfig} config - Configuration options
     */
    constructor(config: MusigreeConfig = {}) {
        this._version = config.version || "2.1.0";
        this._debug = config.debug || false;
        this._dpr =
            config.dpr !== undefined ? config.dpr : window.devicePixelRatio;
        this._dimensions = [0, 0];
        this._svgDimensions = [0, 0];
        this._selectedNodeKey = null;
        this._isSidebarRightCollapsed = false;
        this._isMobile =
            config.isMobile !== undefined
                ? config.isMobile
                : typeof window !== "undefined" && window.innerWidth < 768;
        this._arc = d3.arc<RelationsArcData, RelationsArcData>();
    }

    /**
     * Gets the current version
     * @returns {string} The version number
     */
    get version(): string {
        return this._version;
    }

    /**
     * Gets the debug mode state
     * @returns {boolean} Whether debug mode is enabled
     */
    get debug(): boolean {
        return this._debug;
    }

    /**
     * Sets the debug mode state
     * @param {boolean} value - The new debug mode state
     */
    set debug(value: boolean) {
        this._debug = value;
    }

    /**
     * Gets the device pixel ratio
     * @returns {number} The device pixel ratio
     */
    get dpr(): number {
        return this._dpr;
    }

    /**
     * Sets the device pixel ratio
     * @param {number} value - The new device pixel ratio
     */
    set dpr(value: number) {
        this._dpr = value;
    }

    /**
     * Gets the current dimensions
     * @returns {[number, number]} The width and height
     */
    get dimensions(): [number, number] {
        return this._dimensions;
    }

    /**
     * Sets the current dimensions
     * @param {[number, number]} dimensions - The new width and height
     */
    set dimensions(dimensions: [number, number]) {
        this._dimensions = dimensions;
    }

    /**
     * Gets the current SVG dimensions
     * @returns {[number, number]} The SVG width and height
     */
    get svgDimensions(): [number, number] {
        return this._svgDimensions;
    }

    /**
     * Sets the current SVG dimensions
     * @param {[number, number]} dimensions - The new SVG width and height
     */
    set svgDimensions(dimensions: [number, number]) {
        this._svgDimensions = dimensions;
    }

    /**
     * Gets the currently selected node key
     * @returns {NodeKey} The selected node key
     */
    get selectedNodeKey(): NodeKey {
        return this._selectedNodeKey;
    }

    /**
     * Sets the currently selected node key
     * @param {NodeKey} nodeKey - The node key to select
     */
    set selectedNodeKey(nodeKey: NodeKey) {
        this._selectedNodeKey = nodeKey;
    }

    /**
     * Gets the right sidebar collapsed state
     * @returns {boolean} Whether the right sidebar is collapsed
     */
    get isSidebarRightCollapsed(): boolean {
        return this._isSidebarRightCollapsed;
    }

    /**
     * Sets the right sidebar collapsed state
     * @param {boolean} value - The new collapsed state
     */
    set isSidebarRightCollapsed(value: boolean) {
        this._isSidebarRightCollapsed = value;
    }

    /**
     * Gets the mobile device state
     * Uses the WindowContext getter if available, otherwise falls back to stored value
     * @returns {boolean} Whether the device is mobile
     */
    get isMobile(): boolean {
        return this._isMobileGetter ? this._isMobileGetter() : this._isMobile;
    }

    /**
     * Sets the mobile device state
     * @param {boolean} value - The new mobile state
     */
    set isMobile(value: boolean) {
        this._isMobile = value;
    }

    /**
     * Sets the getter function to retrieve isMobile from WindowContext
     * @param {() => boolean} getter - Function that returns the current isMobile value from WindowContext
     */
    setIsMobileGetter(getter: () => boolean): void {
        this._isMobileGetter = getter;
    }

    /**
     * Gets the D3 arc generator
     * @returns {d3.Arc<RelationsArcData, RelationsArcData>} The arc generator
     */
    get arc(): d3.Arc<RelationsArcData, RelationsArcData> {
        return this._arc;
    }

    /**
     * Sets the D3 arc generator
     * @param {d3.Arc<RelationsArcData, RelationsArcData>} arc - The new arc generator
     */
    set arc(arc: d3.Arc<RelationsArcData, RelationsArcData>) {
        this._arc = arc;
    }

    /**
     * Updates the dimensions based on the container
     * @param {number} width - Container width
     * @param {number} height - Container height
     */
    updateDimensions(width: number, height: number): void {
        this._dimensions = [width, height];
        this._svgDimensions = [
            width * SVG.VIEWPORT_SIZE_MULTIPLIER * this._dpr,
            height * SVG.VIEWPORT_SIZE_MULTIPLIER * this._dpr,
        ];
    }

    /**
     * Resets the selected node
     */
    clearSelection(): void {
        this._selectedNodeKey = null;
    }
}
