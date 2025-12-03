/**
 * @fileoverview Base state implementation that other states can extend
 */

import type { NodeKey, NetworkData } from "../../network/data";
import type { RelationsData } from "../../relations";
import type { EntityData } from "../../entities";
import type { State, StateContext } from "../State";

/**
 * Base state implementation with default no-op methods
 * Concrete states can extend this class and override only the methods they need
 */
export abstract class BaseState implements State {
    /**
     * Called when entering this state
     */
    onEnter(_context: StateContext): void {
        // Default implementation does nothing
    }

    /**
     * Called when exiting this state
     */
    onExit(_context: StateContext): void {
        // Default implementation does nothing
    }

    /**
     * Handle an error that occurred in this state
     */
    handleError(context: StateContext, error: unknown): void {
        // Default implementation delegates to actions
        context.actions.handleError(error);
    }

    /**
     * Handle a network data received event
     */
    receivedNetwork(
        _context: StateContext,
        _data: NetworkData,
        _pushHistory = false,
    ): void {
        // Default implementation does nothing
    }

    /**
     * Handle a relations data received event
     */
    receivedRelations(_context: StateContext, _data: RelationsData): void {
        // Default implementation does nothing
    }

    /**
     * Handle a entity data received event
     */
    receivedEntity(_context: StateContext, _data: EntityData): void {
        // Default implementation does nothing
    }

    /**
     * Handle a random entity received event
     */
    receivedRandom(_context: StateContext, _data: { center: NodeKey }): void {
        // Default implementation does nothing
    }

    /**
     * Handle a request to show the network
     */
    showNetwork(_context: StateContext): void {
        // Default implementation does nothing
    }

    /**
     * Handle a request to show the radial view
     */
    showRadial(_context: StateContext): void {
        // Default implementation does nothing
    }

    /**
     * Handle a request to update the entity details view
     */
    updateEntityDetails(_context: StateContext): void {
        // Default implementation does nothing
    }

    /**
     * Handle a request to get a network for an entity
     */
    requestNetwork(_context: StateContext, _entityKey: NodeKey): void {
        // Default implementation does nothing
    }

    /**
     * Handle a request to get a random entity
     */
    requestRandom(_context: StateContext): void {
        // Default implementation does nothing
    }

    /**
     * Handle a request to select an entity
     */
    selectEntity(
        _context: StateContext,
        // eslint-disable-next-line @typescript-eslint/no-redundant-type-constituents
        _entityKey: NodeKey | undefined,
        _fixed: boolean,
    ): void {
        // Default implementation does nothing
    }
}
