import type * as d3 from "d3";
import type {
    NodeKey,
    LinkKey,
    SimData,
    SimNode,
    SimLink,
} from "../network/data";
import { RequestNetworkEvent } from "../network/events";

/**
 * SVG layer containers for network visualization
 */
interface NetworkLayers {
    root: d3.Selection<SVGGElement, unknown, HTMLElement, unknown> | null;
    halo: d3.Selection<SVGGElement, unknown, HTMLElement, unknown> | null;
    text: d3.Selection<SVGGElement, unknown, HTMLElement, unknown> | null;
    node: d3.Selection<SVGGElement, unknown, HTMLElement, unknown> | null;
    link: d3.Selection<SVGGElement, unknown, HTMLElement, unknown> | null;
}

/**
 * NetworkManager configuration options
 */
export interface NetworkManagerConfig {
    /** Initial network data */
    initialData?: SimData;
}

/**
 * Manages the network visualization and state
 */
export class NetworkManager {
    /** Force layout simulation */
    private _forceLayout: d3.Simulation<SimNode, SimLink>;
    /** Flag indicating if the force layout is currently running */
    private _isRunningLayout: boolean;
    /** Counter for animation/simulation ticks */
    private _tick: number;
    /** Coordinates [x, y] for placing new nodes */
    private _newNodeCoords: [number, number];
    /** Zoom behavior */
    private _zoom: d3.ZoomBehavior<SVGGElement, unknown> | null;
    /** Core data storage for the network */
    private _data: SimData;
    /** SVG layer containers for different visual elements */
    private _layers: NetworkLayers;
    /** Bound event handler for request network events */
    private _boundRequestNetworkHandler: (this: Window, ev: Event) => void;
    /** Currently selected node key */
    private _selectedNodeKey: NodeKey | undefined;

    /**
     * Creates a new NetworkManager instance
     * @param {NetworkManagerConfig} config - Configuration options
     */
    constructor(config: NetworkManagerConfig = {}) {
        this._forceLayout = null;
        this._isRunningLayout = false;
        this._tick = 0;
        this._newNodeCoords = [0, 0];
        this._zoom = null;
        this._data = config.initialData || this._createEmptyData();
        this._layers = {
            root: null,
            halo: null,
            text: null,
            node: null,
            link: null,
        };
        this._selectedNodeKey = undefined;

        // Bind event handlers to this instance
        // this._boundRequestNetworkHandler = this._handleRequestNetwork.bind(
        //     this,
        // ) as (this: Window, ev: Event) => void;
    }

    /**
     * Gets the force layout simulation
     * @returns {d3.Simulation<SimNode, SimLink>} The force layout
     */
    get forceLayout(): d3.Simulation<SimNode, SimLink> {
        return this._forceLayout;
    }

    /**
     * Sets the force layout simulation
     * @param {d3.Simulation<SimNode, SimLink>} layout - The new force layout
     */
    set forceLayout(layout: d3.Simulation<SimNode, SimLink>) {
        this._forceLayout = layout;
    }

    /**
     * Gets whether the force layout is running
     * @returns {boolean} Whether the force layout is running
     */
    get isRunningLayout(): boolean {
        return this._isRunningLayout;
    }

    /**
     * Sets whether the force layout is running
     * @param {boolean} value - The new running state
     */
    set isRunningLayout(value: boolean) {
        this._isRunningLayout = value;
    }

    /**
     * Gets the current tick count
     * @returns {number} The tick count
     */
    get tick(): number {
        return this._tick;
    }

    /**
     * Sets the current tick count
     * @param {number} value - The new tick count
     */
    set tick(value: number) {
        this._tick = value;
    }

    /**
     * Gets the coordinates for placing new nodes
     * @returns {[number, number]} The coordinates [x, y]
     */
    get newNodeCoords(): [number, number] {
        return this._newNodeCoords;
    }

    /**
     * Sets the coordinates for placing new nodes
     * @param {[number, number]} coords - The new coordinates [x, y]
     */
    set newNodeCoords(coords: [number, number]) {
        this._newNodeCoords = coords;
    }

    /**
     * Gets the zoom behavior
     * @returns {d3.ZoomBehavior<SVGGElement, unknown> | null} The zoom behavior
     */
    get zoom(): d3.ZoomBehavior<SVGGElement, unknown> | null {
        return this._zoom;
    }

    /**
     * Sets the zoom behavior
     * @param {d3.ZoomBehavior<SVGGElement, unknown> | null} zoom - The new zoom behavior
     */
    set zoom(zoom: d3.ZoomBehavior<SVGGElement, unknown> | null) {
        this._zoom = zoom;
    }

    /**
     * Gets the network data
     * @returns {SimData} The network data
     */
    get data(): SimData {
        return this._data;
    }

    /**
     * Sets the network data
     * @param {SimData} data - The new network data
     */
    set data(data: SimData) {
        this._data = data;
    }

    /**
     * Gets the network layers
     * @returns {NetworkLayers} The network layers
     */
    get layers(): NetworkLayers {
        return this._layers;
    }

    /**
     * Gets the currently selected node key
     * @returns {NodeKey | undefined} The selected node key, or undefined if no node is selected
     */
    get selectedNodeKey(): NodeKey | undefined {
        return this._selectedNodeKey;
    }

    /**
     * Sets the currently selected node key
     * @param {NodeKey | undefined} key - The new selected node key
     */
    set selectedNodeKey(key: NodeKey | undefined) {
        this._selectedNodeKey = key;
    }

    /**
     * Creates empty network data
     * @returns {SimData} Empty network data
     */
    private _createEmptyData(): SimData {
        const emptyCenter = {
            x: 0,
            y: 0,
            type: "artist",
            key: "",
            name: "",
            size: 0,
            missing: 0,
            hasMissing: false,
            distance: 0,
            radius: 0,
            lastClickTime: 0,
            lastTouchTime: 0,
            links: [],
            cluster: 0,
            fixed: false,
            isIntermediate: false,
        };

        return {
            center: emptyCenter,
            nodeMap: new Map<NodeKey, SimNode>(),
            linkMap: new Map<LinkKey, SimLink>(),
            maxDistance: 0,
        } as SimData;
    }

    /**
     * Cleans up resources used by the network manager
     */
    dispose(): void {
        try {
            // Remove event listeners (also with error handling for tests)
            const eventName =
                RequestNetworkEvent && RequestNetworkEvent.EVENT_NAME
                    ? RequestNetworkEvent.EVENT_NAME
                    : "musigree:request-network";

            window.removeEventListener(
                eventName,
                this._boundRequestNetworkHandler,
            );
        } catch (error) {
            console.warn("Failed to clean up network event listeners:", error);
        }

        // Stop force layout
        if (this._forceLayout) {
            this._forceLayout.stop();
        }

        // Clear data
        this._data.nodeMap.clear();
        this._data.linkMap.clear();
    }
}
