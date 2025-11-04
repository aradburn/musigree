/**
 * @fileoverview Implementation of the requesting-relations state
 */

import type { RelationsData } from "../../relations";
import type { StateContext } from "../State";
import { BaseState } from "./BaseState";

/**
 * State when requesting relations data for an entity
 */
export class RequestingRelationsState extends BaseState {
    /**
     * Called when entering this state
     */
    onEnter(context: StateContext): void {
        console.log("REQUESTING-RELATIONS _onEnter");
        context.actions.toggleLoading(true);
    }

    /**
     * Called when exiting this state
     */
    onExit(context: StateContext): void {
        console.log("REQUESTING-RELATIONS _onExit");
        context.actions.toggleLoading(false);
    }

    /**
     * Handle an error that occurred in this state
     */
    handleError(context: StateContext, error: unknown): void {
        context.actions.handleError(error);
    }

    /**
     * Handle a relations data received event
     */
    receivedRelations(context: StateContext, data: RelationsData): void {
        console.log("REQUESTING-RELATIONS received-relations");
        context.actions.showRadial(data);
    }
}
