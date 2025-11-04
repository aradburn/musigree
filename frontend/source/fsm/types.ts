/**
 * @fileoverview Type definitions for the Musigree Finite State Machine
 */

import type { NodeKey, NetworkCenter, NetworkData } from "../network/data";
import type { RelationsData } from "../relations";
import type { EntityData } from "../entities";

/**
 * The possible states of the FSM
 */
export type FSMStateType =
    | "state-viewing-network"
    | "state-viewing-radial"
    | "state-requesting-network"
    | "state-requesting-relations"
    | "state-requesting-random"
    | "uninitialized";

/**
 * The FSM instance interface
 */
export interface FSMInstance {
    state: FSMStateType;
    handle(
        event: string,
        data:
            | NetworkData
            | RelationsData
            | EntityData
            | NetworkCenter
            | NodeKey
            | null,
        pushHistory: boolean,
        fixed: boolean,
    ): void;
    handleError(error: unknown): void;
    showNetwork(data: NetworkData, pushHistory: boolean): void;
    showRadial(data?: RelationsData): void;
    transition(state: FSMStateType): void;
    requestNetwork(entityKey: NodeKey, pushHistory: boolean): void;
    requestRandom(): void;
    requestRelations(entityKey: NodeKey): void;
    requestEntity(entityKey: NodeKey): void;
    selectEntity(entityKey: NodeKey | null, fixed: boolean): void;
    loadInlineData(): void;
    toggleRadial(show: boolean): void;
    toggleNetwork(show: boolean): void;
    toggleLoading(show: boolean): void;
    toggleFilter(show: boolean): void;
    pushState(entityKey: string, params?: Record<string, unknown>): void;
    on(
        event: string,
        handler: (
            event: string,
            data:
                | NetworkData
                | RelationsData
                | EntityData
                | NetworkCenter
                | NodeKey
                | null,
        ) => void,
    ): void;
    _showNetworkHandler?: (event: Event) => void;
}

/**
 * Individual state handlers
 */
export interface FSMState {
    _onEnter?: (this: FSMInstance) => void;
    _onExit?: (this: FSMInstance) => void;
    "received-network"?: (
        this: FSMInstance,
        data: NetworkData,
        pushHistory?: boolean,
    ) => void;
    "received-relations"?: (this: FSMInstance, data: RelationsData) => void;
    "received-entity"?: (this: FSMInstance, data: EntityData) => void;
    "request-network"?: (this: FSMInstance, entityKey: string) => void;
    "request-random"?: (this: FSMInstance) => void;
    "show-radial"?: (this: FSMInstance) => void;
    "show-network"?: (this: FSMInstance) => void;
    "select-entity"?: (
        this: FSMInstance,
        entityKey: string | null,
        fixed: boolean,
    ) => void;
    errored?: (this: FSMInstance, error: unknown) => void;
    handleError?: (this: FSMInstance, error: unknown) => void;
}

/**
 * Map of all FSM states
 */
export interface FSMStates {
    "state-viewing-network": FSMState;
    "state-viewing-radial": FSMState;
    "state-requesting-network": FSMState;
    "state-requesting-relations": FSMState;
    "state-requesting-random": FSMState;
    uninitialized: FSMState;
}

/**
 * FSM configuration interface
 */
export interface FSMConfig extends FSMState {
    initialize?: (this: FSMInstance) => void;
    namespace?: string;
    initialState?: FSMStateType;
    states?: FSMStates;
    handleError?: (this: FSMInstance, error: unknown) => void;
    loadInlineData?: (this: FSMInstance) => void;
    toggleRadial?: (this: FSMInstance, show: boolean) => void;
    toggleNetwork?: (this: FSMInstance, show: boolean) => void;
    toggleLoading?: (this: FSMInstance, show: boolean) => void;
    toggleFilter?: (this: FSMInstance, show: boolean) => void;
    pushState?: (this: FSMInstance, entityKey: string) => void;
    requestNetwork?: (
        this: FSMInstance,
        entityKey: NodeKey,
        pushHistory?: boolean,
    ) => void;
    requestRandom?: (this: FSMInstance) => void;
    requestRelations?: (this: FSMInstance, entityKey: NodeKey) => void;
    requestEntity?: (this: FSMInstance, entityKey: NodeKey) => void;
    selectEntity?: (
        this: FSMInstance,
        entityKey: string | null,
        fixed: boolean,
    ) => void;
    showNetwork?: (
        this: FSMInstance,
        data?: NetworkData,
        pushHistory?: boolean,
    ) => void;
    showRadial?: (this: FSMInstance, data?: RelationsData) => void;
    updateEntityDetails?: (this: FSMInstance, data?: EntityData) => void;
    handle?: (
        this: FSMInstance,
        event: string,
        data: NetworkData | RelationsData | EntityData | NodeKey | null,
        pushHistory: boolean,
        fixed: boolean,
    ) => void;
    transition?: (this: FSMInstance, state: FSMStateType) => void;
}
