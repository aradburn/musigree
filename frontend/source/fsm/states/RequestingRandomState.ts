/**
 * @fileoverview Implementation of the requesting-random state
 */

import type { NetworkData } from "../../network/data";
import type { StateContext } from "../State";
import { BaseState } from "./BaseState";

/**
 * State when requesting a random entity
 */
export class RequestingRandomState extends BaseState {
    /**
     * Called when entering this state
     */
    onEnter(context: StateContext): void {
        console.log("REQUESTING-RANDOM _onEnter");
        context.actions.toggleLoading(true);
    }

    /**
     * Called when exiting this state
     */
    onExit(context: StateContext): void {
        console.log("REQUESTING-RANDOM _onExit");
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
        console.log("REQUESTING-RANDOM received-network");
        context.actions.showNetwork(data, pushHistory);
    }
}
