/**
 * @fileoverview Base interfaces for the FSM states
 */

import type { NodeKey, NetworkData } from "../network/data";
import type { RelationsData } from "../relations";
import type { TransitionFunction } from "./AbstractFSM";

/**
 * Forward declaration of Actions interface to avoid circular imports
 */
export interface Actions {
    handleError(error: unknown): void;
    loadInlineData(): void;
    pushState(entityKey: NodeKey, params?: Record<string, unknown>): void;
    requestNetwork(entityKey: NodeKey, pushHistory: boolean): void;
    requestRadial(entityKey: NodeKey): void;
    requestRandom(): void;
    showNetwork(networkData: NetworkData, pushHistory: boolean): void;
    showRadial(data?: RelationsData): void;
    toggleFilter(show: boolean): void;
    toggleNetwork(status: boolean): void;
    toggleLoading(status: boolean): void;
    toggleRadial(status: boolean): void;
    selectEntity(entityKey: NodeKey | null, fixed: boolean): void;
}

/**
 * Interface for the state context that's passed to state methods
 */
export interface StateContext {
    actions: Actions;
    transition: TransitionFunction;
}

/**
 * Base interface for all FSM states
 */
export interface State {
    /**
     * Called when entering this state
     */
    onEnter(context: StateContext): void;

    /**
     * Called when exiting this state
     */
    onExit(context: StateContext): void;

    /**
     * Handle an error that occurred in this state
     */
    handleError?(context: StateContext, error: unknown): void;

    /**
     * Handle a network data received event
     */
    receivedNetwork?(
        context: StateContext,
        data: NetworkData,
        pushHistory?: boolean,
    ): void;

    /**
     * Handle a radial data received event
     */
    receivedRadial?(context: StateContext, data: RelationsData): void;

    /**
     * Handle a random entity received event
     */
    receivedRandom?(context: StateContext, data: { center: NodeKey }): void;

    /**
     * Handle a request to show the network
     */
    showNetwork?(context: StateContext): void;

    /**
     * Handle a request to show the radial view
     */
    showRadial?(context: StateContext): void;

    /**
     * Handle a request to get a network for an entity
     */
    requestNetwork?(context: StateContext, entityKey: NodeKey): void;

    /**
     * Handle a request to get a random entity
     */
    requestRandom?(context: StateContext): void;

    /**
     * Handle a request to select an entity
     */
    selectEntity?(
        context: StateContext,
        entityKey: NodeKey | null,
        fixed: boolean,
    ): void;
}
