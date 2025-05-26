/**
 * @fileoverview Implementation of the viewing-radial state
 */

import type { NodeKey } from "../../network/data";
import type { StateContext } from "../State";
import { BaseState } from "./BaseState";

/**
 * State when the user is viewing the radial visualization
 */
export class ViewingRadialState extends BaseState {
    /**
     * Called when entering this state
     */
    onEnter(context: StateContext): void {
        console.log("VIEWING-RADIAL _onEnter");
        context.actions.toggleNetwork(false);
        context.actions.toggleRadial(true);
        context.actions.toggleFilter(false);
    }

    /**
     * Called when exiting this state
     */
    onExit(context: StateContext): void {
        console.log("VIEWING-RADIAL _onExit");
        context.actions.toggleRadial(false);
    }

    /**
     * Handle a request to get a network for an entity
     */
    requestNetwork(context: StateContext, entityKey: NodeKey): void {
        console.log("VIEWING-RADIAL request-network");
        context.actions.requestNetwork(entityKey, false);
    }

    /**
     * Handle a request to get a random entity
     */
    requestRandom(context: StateContext): void {
        console.log("VIEWING-RADIAL request-random");
        context.actions.requestRandom();
    }
}
