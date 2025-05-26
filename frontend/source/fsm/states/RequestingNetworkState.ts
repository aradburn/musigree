/**
 * @fileoverview Implementation of the requesting-network state
 */

import type { NetworkData, NetworkCenter } from "../../network/data";
import type { RelationsData } from "../../relations";
import type { StateContext } from "../State";
import { BaseState } from "./BaseState";

/**
 * State when requesting network data for an entity
 */
export class RequestingNetworkState extends BaseState {
    /**
     * Called when entering this state
     */
    onEnter(context: StateContext): void {
        console.log("REQUESTING-NETWORK _onEnter");
        context.actions.toggleLoading(true);
    }

    /**
     * Called when exiting this state
     */
    onExit(context: StateContext): void {
        console.log("REQUESTING-NETWORK _onExit");
        context.actions.toggleLoading(false);
    }

    /**
     * Handle an error that occurred in this state
     */
    handleError(context: StateContext, error: unknown): void {
        context.actions.handleError(error);
    }

    /**
     * Handle a network data received event
     */
    receivedNetwork(
        context: StateContext,
        data: NetworkData,
        pushHistory = false,
    ): void {
        console.log("REQUESTING-NETWORK received-network data: ", data);
        context.actions.showNetwork(data, pushHistory);
    }

    /**
     * Handle a random entity received event
     */
    receivedRandom(context: StateContext, data: NetworkCenter): void {
        console.log("REQUESTING-NETWORK received-random data: ", data);
        context.actions.requestNetwork(data.center, true);
    }

    /**
     * Handle a radial data received event
     */
    receivedRadial(context: StateContext, data: RelationsData): void {
        console.log("REQUESTING-NETWORK received-radial");
        context.actions.showRadial(data);
    }
}
