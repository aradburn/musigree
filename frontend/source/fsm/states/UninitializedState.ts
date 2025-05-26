/**
 * @fileoverview Implementation of the uninitialized state
 */

import type { NetworkData, NodeKey } from "../../network/data";
import type { StateContext } from "../State";
import { BaseState } from "./BaseState";

/**
 * Initial state before the application is fully loaded
 */
export class UninitializedState extends BaseState {
    /**
     * Called when entering this state
     */
    onEnter(context: StateContext): void {
        console.log("UNITIALIZED _onEnter");
        context.actions.loadInlineData();
    }

    /**
     * Called when exiting this state
     */
    onExit(_context: StateContext): void {
        console.log("UNITIALIZED _onExit");
    }

    /**
     * Handle a network data received event
     */
    receivedNetwork(
        context: StateContext,
        data: NetworkData,
        _pushHistory = false,
    ): void {
        console.log("UNITIALIZED received-network");
        context.transition("state-viewing-network");
    }

    /**
     * Handle a request to get a network for an entity
     */
    requestNetwork(context: StateContext, entityKey: NodeKey): void {
        console.log("UNITIALIZED request-network");
        context.transition("state-requesting-network");
        context.actions.requestNetwork(entityKey, true);
    }

    /**
     * Handle a request to get a random entity
     */
    requestRandom(context: StateContext): void {
        console.log("UNITIALIZED request-random");
        context.transition("state-requesting-random");
        context.actions.requestRandom();
    }
}
