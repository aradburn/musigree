/**
 * @fileoverview Implementation of the Musigree Finite State Machine
 * using the state pattern and actions
 */

import * as d3 from "d3";
import { musigreeManager, networkManager } from "../core/singletons";
import {
    restartForceLayout,
    stopForceLayout,
    displayForceLayout,
    setForceLayoutNodes,
    setNetworkForces,
} from "../network/forceLayout";
import type { NodeKey, NetworkCenter, NetworkData } from "../network/data";
import {
    processAPINetworkDataResponse,
    convertNetworkDataToSimData,
    updateGlobalData,
} from "../network/data";
import { pruneSimData } from "../network/pruning";
import type { RelationsData } from "../relations";
import type { EntityData } from "../entities";
import {
    fetchAPINetwork,
    fetchAPIRandom,
    fetchAPIRelations,
    fetchAPIEntity,
} from "../api";
import { resetNetworkTransform } from "../network/init";
import { FORCE, MESSAGE } from "../constants";
import { FSM, INIT } from "../constants";
import type { SimNode, SimLink } from "../network/data";
import { RequestNetworkEvent, SelectEntityEvent } from "../network/events";
import { showMessage } from "../messages";
import type { Actions } from "./actions/Actions";
import type { State, StateContext } from "./State";
import { ViewingNetworkState } from "./states/ViewingNetworkState";
import { ViewingRadialState } from "./states/ViewingRadialState";
import { RequestingNetworkState } from "./states/RequestingNetworkState";
import { RequestingRelationsState } from "./states/RequestingRelationsState";
import { RequestingRandomState } from "./states/RequestingRandomState";
import { UninitializedState } from "./states/UninitializedState";
import debounce from "debounce";
import {
    AbstractFSM,
    type EventData,
    type TransitionFunction,
} from "./AbstractFSM";
import type { APINetworkDataResponse } from "../api";
import { getSelectedRoles } from "../roles";

// Extend the Window interface to include the dgNetwork property
declare global {
    interface Window {
        dgNetwork?: APINetworkDataResponse;
        bootstrap?: {
            Offcanvas: {
                new (
                    element: Element,
                    options?: unknown,
                ): {
                    show(): void;
                    hide(): void;
                };
                getInstance(element: Element): { hide(): void } | null;
            };
        };
    }
}

/**
 * Implementation of the FSM using the state pattern
 */
export class MusigreeFSM extends AbstractFSM implements Actions {
    /**
     * Handler for showNetwork event
     */
    private _showNetworkHandler?: (event: Event) => void;

    /**
     * Create a new FSM instance
     */
    constructor() {
        super("uninitialized");

        this._states = new Map();
        this._eventHandlers = new Map();

        // Register all states
        this.registerState("uninitialized", new UninitializedState());
        this.registerState("state-viewing-network", new ViewingNetworkState());
        this.registerState("state-viewing-radial", new ViewingRadialState());
        this.registerState(
            "state-requesting-network",
            new RequestingNetworkState(),
        );
        this.registerState(
            "state-requesting-relations",
            new RequestingRelationsState(),
        );
        this.registerState(
            "state-requesting-random",
            new RequestingRandomState(),
        );

        // Initialize the FSM
        this.initialize();
    }

    /**
     * Handle an event with optional data
     */
    handle(
        event: string,
        data:
            | NetworkData
            | RelationsData
            | EntityData
            | NetworkCenter
            | NodeKey
            | undefined,
        pushHistory: boolean,
        fixed: boolean,
    ): void {
        console.log(
            `Handling event ${event} in state ${this._currentStateType}`,
            data,
        );

        const context: StateContext = {
            actions: this,
            transition: this.transition.bind(this) as TransitionFunction,
        };

        // Map events to state methods
        switch (event) {
            case "received-network":
                this._state.receivedNetwork?.(
                    context,
                    data as NetworkData,
                    pushHistory,
                );
                break;
            case "received-relations":
                this._state.receivedRelations?.(context, data as RelationsData);
                break;
            case "received-entity":
                this._state.receivedEntity?.(context, data as EntityData);
                break;
            case "received-random":
                this._state.receivedRandom?.(context, data as NetworkCenter);
                break;
            case "request-network":
                this._state.requestNetwork?.(context, data as NodeKey);
                break;
            case "request-entity":
                this._state.requestEntity?.(context, data as NodeKey);
                break;
            case "request-random":
                this._state.requestRandom?.(context);
                break;
            case "show-network":
                this._state.showNetwork?.(context);
                break;
            case "show-radial":
                this._state.showRadial?.(context);
                break;
            case "select-entity":
                this._state.selectEntity?.(context, data as NodeKey, fixed);
                break;
            case "errored":
                this._state.handleError?.(context, data);
                break;
            default:
                console.warn(`Unhandled event: ${event}`);
        }

        // Emit the event
        this.emit(event, data as EventData);
    }

    /**
     * Create the fallback state for the FSM
     */
    protected createFallbackState(): State {
        return new UninitializedState();
    }

    /**
     * Get the fallback state for the FSM
     */
    protected getFallbackState(): State {
        const fallbackState = this._states.get("uninitialized");
        if (!fallbackState) {
            throw new Error(
                "Uninitialized state not found, FSM is in an invalid state",
            );
        }
        return fallbackState;
    }

    /**
     * Initialize the FSM with event listeners
     */
    protected initialize(): void {
        // Event handlers
        window.addEventListener(FSM.EVENTS.REQUEST_NETWORK, (event: Event) => {
            if (event instanceof RequestNetworkEvent) {
                const { entityKey, pushHistory } = event.detail;
                if (entityKey) {
                    this.requestNetwork(entityKey, pushHistory);
                } else {
                    // Request with updated roles
                    if (musigreeManager.selectedNodeKey) {
                        this.requestNetwork(
                            musigreeManager.selectedNodeKey,
                            true,
                        );
                    } else if (networkManager.data.center.key) {
                        this.requestNetwork(
                            networkManager.data.center.key,
                            true,
                        );
                    }
                }
            }
        });

        window.addEventListener(FSM.EVENTS.REQUEST_RANDOM, () => {
            this.requestRandom();
        });

        window.addEventListener(FSM.EVENTS.SELECT_ENTITY, (event: Event) => {
            if (event instanceof SelectEntityEvent && event.detail) {
                const { entityKey, fixed } = event.detail;
                this.selectEntity(entityKey, fixed);
            }
        });

        window.addEventListener(FSM.EVENTS.SHOW_NETWORK, () => {
            this.handle("show-network", null, false, false);
        });

        window.addEventListener(FSM.EVENTS.SHOW_RADIAL, () => {
            this.handle("show-radial", null, false, false);
        });

        // NOTE: Removed overlay event listeners to prevent circular event references
        // These events are now only dispatched by the FSM and handled by React components

        // Handle browser history navigation
        window.onpopstate = (event: PopStateEvent): void => {
            const state = event?.state as { key: string } | undefined;
            if (state?.key) {
                window.dispatchEvent(new RequestNetworkEvent(state.key, false));
            }
        };

        // Handle window resize events with debounce
        const handleResize = debounce(() => {
            console.log("handleResize fsm");

            // Center the loading visualization
            const transform = `translate(${musigreeManager.svgDimensions[0] / 2},${musigreeManager.svgDimensions[1] / 2})`;
            d3.selectAll(".centered")
                .transition()
                .duration(INIT.DEBOUNCE_DELAY)
                .attr("transform", transform);

            // Center the main node
            if (networkManager.data.center) {
                const centerNode = networkManager.data.nodeMap.get(
                    networkManager.data.center.key,
                );
                if (centerNode) {
                    centerNode.x = networkManager.newNodeCoords[0];
                    centerNode.y = networkManager.newNodeCoords[1];
                }
            }

            // Restart force layout if in network view
            if (this.state === "state-viewing-network") {
                console.log("restartForceLayout fsm");
                restartForceLayout(FORCE.SIMULATION.ALPHA);
            }
        }, INIT.DEBOUNCE_DELAY);

        window.addEventListener(
            FSM.EVENTS.RESIZE,
            handleResize as EventListener,
        );

        // Handle SVG mousedown events
        const svgDocument = document.getElementById("svg");
        if (svgDocument) {
            svgDocument.addEventListener("mousedown", () => {
                if (this.state === "state-viewing-network") {
                    this.selectEntity(null, false);
                } else if (this.state === "state-viewing-radial") {
                    this.handle("show-network", null, false, false);
                }
                this.hideRolesOverlay();
            });
        }

        // Initialize application state
        this.loadInlineData();
        this.toggleRadial(false);
    }

    /**
     * Shows the roles panel overlay
     */
    showRolesOverlay(): void {
        // Dispatch the event for React to handle
        const event = new CustomEvent("musigree:show-roles-overlay");
        window.dispatchEvent(event);
    }

    /**
     * Hides the roles panel overlay
     */
    hideRolesOverlay(): void {
        // Dispatch the event for React to handle
        const event = new CustomEvent("musigree:hide-roles-overlay");
        window.dispatchEvent(event);
    }

    // Action implementations (from Actions interface)
    //

    /**
     * Handle an error that occurred
     */
    handleError(error: unknown): void {
        if (error instanceof Error) {
            showMessage(error.message, MESSAGE.TYPES.ERROR);
        } else {
            showMessage("An unknown error occurred", MESSAGE.TYPES.ERROR);
        }

        this.transition("state-viewing-network");
    }

    /**
     * Load data from the inline dgNetwork global variable
     */
    loadInlineData(): void {
        if (window.dgNetwork) {
            this.transition("state-requesting-network");

            const networkData = processAPINetworkDataResponse(window.dgNetwork);

            this.handle("received-network", networkData, false, false);
        }
    }

    /**
     * Update browser history state
     */
    pushState(entityKey: NodeKey, params?: Record<string, unknown>): void {
        const [entityType, entityId] = entityKey.split("-");
        const title = document.title;
        let url = `/${entityType}/${entityId}`;

        if (params) {
            const searchParams = new URLSearchParams();
            Object.entries(params).forEach(([key, value]) => {
                if (Array.isArray(value)) {
                    searchParams.set(key, value.join(","));
                } else if (typeof value === "object" && value !== null) {
                    // Convert objects to a stable JSON string
                    const sorted = Object.fromEntries(
                        Object.entries(value).sort(([a], [b]) =>
                            a.localeCompare(b),
                        ),
                    );
                    searchParams.set(key, JSON.stringify(sorted));
                } else if (
                    typeof value === "string" ||
                    typeof value === "number" ||
                    typeof value === "boolean"
                ) {
                    searchParams.set(key, String(value));
                }
            });
            url += `?${decodeURIComponent(searchParams.toString())}`;
        }

        const state = { key: entityKey, params };
        window.history.pushState(state, title, url);
    }

    /**
     * Request network data for an entity
     */
    requestNetwork(entityKey: NodeKey, pushHistory: boolean): void {
        console.log("FSM requestNetwork entityKey: ", entityKey);

        this.transition("state-requesting-network");

        const roles = getSelectedRoles() || [];

        fetchAPINetwork(entityKey, roles)
            .then((apiNetworkDataResponse) => {
                const networkData = processAPINetworkDataResponse(
                    apiNetworkDataResponse,
                );

                this.handle(
                    "received-network",
                    networkData,
                    pushHistory,
                    false,
                );
            })
            .catch((error) => {
                console.error("Error fetching network data:", error);

                this.handleError(error);
            });
    }

    /**
     * Request relations data for an entity
     */
    requestRelations(entityKey: NodeKey): void {
        console.log("FSM requestRelations entityKey: ", entityKey);

        this.transition("state-requesting-relations");

        fetchAPIRelations(entityKey)
            .then((relationsData) => {
                this.handle("received-relations", relationsData, false, false);
            })
            .catch((error) => {
                console.error("Error fetching relations data:", error);

                this.handleError(error);
            });
    }

    /**
     * Request entity data
     */
    requestEntity(entityKey: NodeKey): void {
        console.log("FSM requestEntity entityKey: ", entityKey);

        fetchAPIEntity(entityKey)
            .then((entityData) => {
                this.handle("received-entity", entityData, false, false);
            })
            .catch((error) => {
                console.error("Error fetching entity data:", error);

                this.handleError(error);
            });
    }

    /**
     * Request a random entity
     */
    requestRandom(): void {
        console.log("FSM requestRandom");

        this.transition("state-requesting-network");

        const roles = getSelectedRoles() || [];

        fetchAPIRandom(roles)
            .then((networkCenter) => {
                this.handle("received-random", networkCenter, true, false);
            })
            .catch((error) => {
                console.error("Error fetching random data:", error);

                this.handleError(error);
            });
    }

    /**
     * Display the network view
     */
    showNetwork(networkData: NetworkData, pushHistory: boolean): void {
        console.log("FSM showNetwork networkData: ", networkData);

        this.transition("state-viewing-network");

        if (!networkData || !networkData.center?.key) {
            console.error("Invalid network data: missing center key");
            return;
        }

        const filterSelect =
            document.querySelector<HTMLSelectElement>("#filter select");
        const filterValue = filterSelect?.value;
        const params = { roles: Array.isArray(filterValue) ? filterValue : [] };

        // Update the network data
        document.title = "Musigree: " + networkData.center.name;
        //         document.body.setAttribute("id", networkData.center.key);

        if (pushHistory) {
            this.pushState(networkData.center.key, params);
        }

        console.log("FSM received-network convertNetworkDataToSimData");
        const simData = convertNetworkDataToSimData(networkData);

        const prunedSimData = pruneSimData(simData);

        updateGlobalData(prunedSimData);

        console.log("FSM received-network resetNetworkTransform");
        resetNetworkTransform();

        console.log("FSM received-network startForceLayout");
        setForceLayoutNodes(Array.from(prunedSimData.nodeMap.values()));

        setNetworkForces();

        displayForceLayout();

        restartForceLayout(FORCE.SIMULATION.ALPHA);

        this.handle("select-entity", networkData.center.key, false, false);
    }

    /**
     * Display the radial view
     */
    showRadial(data?: RelationsData): void {
        console.log("FSM showRadial relationsData: ", data);

        this.transition("state-viewing-radial");
        this.handle("show-radial", data, false, false);
    }

    /**
     * Select an entity in the network
     */
    updateEntityDetails(data: EntityData): void {
        console.log("FSM updateEntityDetails", data);
        const event = new CustomEvent<EntityData>(
            "musigree:entity-details-updated",
            { detail: data },
        );
        window.dispatchEvent(event);
    }

    /**
     * Toggle filter visibility
     */
    toggleFilter(show: boolean): void {
        console.log("toggleFilter", show);

        if (show === true) {
            d3.select("#filter-container").classed("hidden", false);
            const transform = `translate(${musigreeManager.svgDimensions[0] / 2},${musigreeManager.svgDimensions[1] / 2})`;
            d3.select("#filter-container").attr("transform", transform);
        } else {
            d3.select("#filter-container").classed("hidden", true);
        }
    }

    /**
     * Toggle network visibility
     */
    toggleNetwork(status: boolean): void {
        if (status) {
            const root = networkManager.layers.root;
            if (root) {
                root.style("transition", "opacity 250ms").style("opacity", 1);
            }
        } else {
            stopForceLayout();
            const root = networkManager.layers.root;
            if (root) {
                root.style("transition", "opacity 250ms").style(
                    "opacity",
                    0.25,
                );
            }
        }
    }

    /**
     * Toggle loading indicator
     */
    toggleLoading(status: boolean): void {
        // Check if the React app is mounted using the existence of the LoadingContext
        const reactAppMounted =
            document.getElementById("react-app-root")?.dataset.mounted ===
            "true";

        if (reactAppMounted) {
            // Create and dispatch custom LoadingToggleEvent for React components to listen to
            const loadingEvent = new CustomEvent("loading:toggle", {
                detail: { status },
            });
            window.dispatchEvent(loadingEvent);
        }
    }

    /**
     * Toggle radial view
     */
    toggleRadial(status: boolean): void {
        //         const entityRelations = document.getElementById("entity-relations");
        //         if (!entityRelations) {
        //             console.warn("entity-relations element not found in DOM");
        //             return;
        //         }

        if (status) {
            //             if (this._showNetworkHandler) {
            //                 entityRelations.removeEventListener(
            //                     "click",
            //                     this._showNetworkHandler,
            //                 );
            //             }

            this._showNetworkHandler = (e: Event): void => {
                this.handle("show-network", null, false, false);
                e.preventDefault();
            };

            //             entityRelations.addEventListener("click", this._showNetworkHandler);
        } else {
            //             if (this._showNetworkHandler) {
            //                 entityRelations.removeEventListener(
            //                     "click",
            //                     this._showNetworkHandler,
            //                 );
            //             }

            this._showNetworkHandler = (e: Event): void => {
                this.handle("show-radial", null, false, false);
                e.preventDefault();
            };

            //             entityRelations.addEventListener("click", this._showNetworkHandler);
        }
    }

    /**
     * Select an entity in the network
     */
    selectEntity(entityKey: NodeKey | undefined, fixed: boolean): void {
        console.log("FSM selectEntity", entityKey, fixed);

        musigreeManager.selectedNodeKey = entityKey;
        let nodeOn: d3.Selection<SVGGElement, SimNode, SVGGElement, unknown>;
        let nodeOff: d3.Selection<SVGGElement, SimNode, SVGGElement, unknown>;
        let linkOn: d3.Selection<SVGGElement, SimLink, SVGGElement, unknown>;
        let linkOff: d3.Selection<SVGGElement, SimLink, SVGGElement, unknown>;

        const nodeLayer = networkManager.layers.node;
        if (!nodeLayer) {
            console.log("Network node layer not found");
            return;
        }

        const linkLayer = networkManager.layers.link;
        if (!linkLayer) {
            console.log("Network link layer not found");
            return;
        }

        if (entityKey !== undefined) {
            nodeOn = nodeLayer.selectAll<SVGGElement, SimNode>(
                "g" + "#node-" + entityKey,
            );
            nodeOff = nodeLayer.selectAll<SVGGElement, SimNode>(
                "g.node:not(#node-" + entityKey + ")",
            );

            if (nodeOn.empty()) {
                console.log("nodeOn not found");
                return;
            }
            if (nodeOff.empty()) {
                console.log("nodeOff not found");
                return;
            }

            const nodeData = nodeOn.datum();
            if (!nodeData) {
                console.log("nodeData not found");
                return;
            }

            //             console.log("nodeData: ", nodeData);
            const linkKeys = nodeData.links.map((l) => l.key);
            const linkSelection = linkLayer.selectAll<SVGGElement, SimLink>(
                "g.link",
            );

            linkOn = linkSelection.filter((d: SimLink) =>
                linkKeys.includes(d.key),
            );
            linkOff = linkSelection.filter(
                (d: SimLink) => !linkKeys.includes(d.key),
            );

            const node = networkManager.data.nodeMap.get(entityKey);
            if (!node) {
                console.log("node not found");
                return;
            }
            //             console.log("new selected node: ", node);

            const [, id] = node.key.split("-");
            const url = `http://discogs.com/${node.type}/${id}`;

            // Dispatch custom event with entity data for React components
            const entitySelectedEvent = new CustomEvent(
                "musigree:entity-selected",
                {
                    detail: {
                        name: node.name,
                        url: url,
                    },
                },
            );
            window.dispatchEvent(entitySelectedEvent);

            // Keep the original D3 code for backward compatibility
            d3.select("#entity-name").text(node.name);
            d3.select("#entity-link").attr("href", url);

            const entityDetails = d3.select("#entity-details");
            entityDetails.classed("hidden", false);
            entityDetails.style("display", "block");

            d3.selectAll(".navbar-title span").text(node.name);

            nodeOn.raise();
            nodeOn.classed("selected", true);
            //             console.log("nodeOn: ", nodeOn);

            if (fixed) {
                //nodeOn.each(function(d) { d.fixed = true; });
                node.fixed = true;
            }
            linkOn.classed("selected", true);
        } else {
            nodeOff = nodeLayer.selectAll<SVGGElement, SimNode>("g.node");
            linkOff = linkLayer.selectAll<SVGGElement, SimLink>("g.link");
        }

        if (nodeOff) {
            //             console.log("nodeOff: ", nodeOff);
            nodeOff.classed("selected", false).each((d) => (d.fixed = false));
        }
        if (linkOff) {
            //             console.log("linkOff: ", linkOff);
            linkOff.classed("selected", false);
        }

        // Request entity details
        this.handle("request-entity", entityKey, false, false);
    }
}
