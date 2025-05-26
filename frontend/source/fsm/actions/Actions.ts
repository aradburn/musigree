/**
 * @fileoverview Actions interface for FSM
 * Defines all actions that can be triggered by states
 */

import type { NodeKey, NetworkData } from "../../network/data";
import type { RelationsData } from "../../relations";

/**
 * Interface defining all actions that can be performed by the FSM
 */
export interface Actions {
    /**
     * Handle an error that occurred
     */
    handleError(error: unknown): void;

    /**
     * Load data from the inline dgNetwork global variable
     */
    loadInlineData(): void;

    /**
     * Update browser history state
     */
    pushState(entityKey: NodeKey, params?: Record<string, unknown>): void;

    /**
     * Request network data for an entity
     */
    requestNetwork(entityKey: NodeKey, pushHistory: boolean): void;

    /**
     * Request radial data for an entity
     */
    requestRadial(entityKey: NodeKey): void;

    /**
     * Request a random entity
     */
    requestRandom(): void;

    /**
     * Display the network view
     */
    showNetwork(networkData: NetworkData, pushHistory: boolean): void;

    /**
     * Display the radial view
     */
    showRadial(data?: RelationsData): void;

    /**
     * Toggle filter visibility
     */
    toggleFilter(show: boolean): void;

    /**
     * Toggle network visibility
     */
    toggleNetwork(status: boolean): void;

    /**
     * Toggle loading indicator
     */
    toggleLoading(status: boolean): void;

    /**
     * Toggle radial view
     */
    toggleRadial(status: boolean): void;

    /**
     * Select an entity in the network
     */
    selectEntity(entityKey: NodeKey | null, fixed: boolean): void;
}
