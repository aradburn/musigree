/**
 * @fileoverview Implementation of the requesting-radial state
 */

import type { RelationsData } from "../../relations";
import type { StateContext } from "../State";
import { BaseState } from "./BaseState";

/**
 * State when requesting radial data for an entity
 */
export class RequestingRadialState extends BaseState {
    /**
     * Called when entering this state
     */
    onEnter(context: StateContext): void {
        console.log("REQUESTING-RADIAL _onEnter");
        context.actions.toggleLoading(true);
    }

    /**
     * Called when exiting this state
     */
    onExit(context: StateContext): void {
        console.log("REQUESTING-RADIAL _onExit");
        context.actions.toggleLoading(false);
    }

    /**
     * Handle an error that occurred in this state
     */
    handleError(context: StateContext, error: unknown): void {
        context.actions.handleError(error);
    }

    /**
     * Handle a radial data received event
     */
    receivedRadial(context: StateContext, data: RelationsData): void {
        console.log("REQUESTING-RADIAL received-radial");
        context.actions.showRadial(data);
    }
}
