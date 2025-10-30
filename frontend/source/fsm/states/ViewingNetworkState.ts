/**
 * @fileoverview Implementation of the viewing-network state
 */

import type { NodeKey } from "../../network/data";
import type { StateContext } from "../State";
import { BaseState } from "./BaseState";

/**
 * State when the user is viewing the network diagram
 */
export class ViewingNetworkState extends BaseState {
    /**
     * Called when entering this state
     */
    onEnter(context: StateContext): void {
        console.log("VIEWING-NETWORK _onEnter");
        context.actions.toggleNetwork(true);
        context.actions.toggleRadial(false);
        context.actions.toggleFilter(true);
    }

    /**
     * Called when exiting this state
     */
    onExit(context: StateContext): void {
        console.log("VIEWING-NETWORK _onExit");
        context.actions.toggleNetwork(false);
        context.actions.toggleFilter(false);
    }

    /**
     * Handle a request to get a network for an entity
     */
    requestNetwork(context: StateContext, entityKey: NodeKey): void {
        console.log("VIEWING-NETWORK request-network");
        context.actions.requestNetwork(entityKey, true);
    }

    /**
     * Handle a request to get entity data
     */
    requestEntity(context: StateContext, entityKey: NodeKey): void {
        console.log("VIEWING-NETWORK request-entity");
        context.actions.requestEntity(entityKey);
    }

    /**
     * Handle a request to get a random entity
     */
    requestRandom(context: StateContext): void {
        console.log("VIEWING-NETWORK request-random");
        context.actions.requestRandom();
    }

    /**
     * Handle a request to show the radial view
     */
    showRadial(context: StateContext): void {
        console.log("VIEWING-NETWORK show-radial");
        context.actions.showRadial();
    }

    /**
     * Handle a request to select an entity
     */
    selectEntity(
        context: StateContext,
        entityKey: NodeKey | null,
        fixed: boolean,
    ): void {
        console.log("VIEWING-NETWORK select-entity:", entityKey);
        if (entityKey) {
            context.actions.selectEntity(entityKey, fixed);
        }
    }
}
