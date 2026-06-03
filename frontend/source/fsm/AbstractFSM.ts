/**
 * @fileoverview Abstract Finite State Machine implementation using the state pattern
 */

import type { State, StateContext } from "./State";
import type { FSMStateType } from "./types";
import type { Actions } from "./actions/Actions";

/**
 * Type for event data that can be passed to handlers
 */
export type EventData = unknown;

/**
 * Type for the transition function passed to states
 */
export type TransitionFunction = (state: FSMStateType) => void;

/**
 * Abstract FSM implementation using the state pattern
 */
export abstract class AbstractFSM {
    /**
     * The current state of the FSM
     */
    protected _state: State;

    /**
     * Map of all available states
     */
    protected _states: Map<FSMStateType, State>;

    /**
     * The current state type
     */
    protected _currentStateType: FSMStateType;

    /**
     * Event handlers for FSM events
     */
    protected _eventHandlers: Map<
        string,
        Set<(event: string, data: EventData) => void>
    >;

    /**
     * Create a new FSM instance
     */
    constructor(initialState: FSMStateType) {
        this._states = new Map();
        this._eventHandlers = new Map();
        this._currentStateType = initialState;
        this._state = this.createFallbackState();
    }

    /**
     * Get the current state type
     */
    get state(): FSMStateType {
        return this._currentStateType;
    }

    /**
     * Register a state with the FSM
     */
    protected registerState(stateType: FSMStateType, state: State): void {
        this._states.set(stateType, state);
    }

    /**
     * Get a state by type, creating a default one if it doesn't exist
     */
    protected getOrCreateState(stateType: FSMStateType): State {
        const state = this._states.get(stateType);
        if (!state) {
            console.warn(`State ${stateType} not found, using fallback state`);
            // Get fallback state
            const fallbackState = this.getFallbackState();
            if (!fallbackState) {
                throw new Error(
                    "Fallback state not found, FSM is in an invalid state",
                );
            }
            return fallbackState;
        }
        return state;
    }

    /**
     * Create the fallback state for the FSM
     * Must be implemented by subclasses
     */
    protected abstract createFallbackState(): State;

    /**
     * Get the fallback state for the FSM
     * Must be implemented by subclasses
     */
    protected abstract getFallbackState(): State;

    /**
     * Initialize the FSM with event listeners
     * Must be implemented by subclasses
     */
    protected abstract initialize(): void;

    /**
     * Transition to a new state
     */
    transition(newStateType: FSMStateType): void {
        console.log(
            `Transitioning from ${this._currentStateType} to ${newStateType}`,
        );

        const context: StateContext = {
            actions: this as unknown as Actions,
            transition: this.transition.bind(this) as TransitionFunction,
        };

        // Exit the current state
        this._state.onExit(context);

        // Update state
        this._currentStateType = newStateType;
        this._state = this.getOrCreateState(newStateType);

        // Enter the new state
        this._state.onEnter(context);

        // Emit state change event
        this.emit("*", this._currentStateType);
    }

    /**
     * Handle an event with optional data
     */
    handle(event: string, data: EventData, ...args: unknown[]): void {
        console.log(
            `Handling event ${event} in state ${this._currentStateType}`,
            data,
        );

        const context: StateContext = {
            actions: this as unknown as Actions,
            transition: this.transition.bind(this) as TransitionFunction,
        };

        // Call the corresponding method on the current state if it exists
        const methodKey = event.replace(/-([a-z])/g, (_, letter: string) =>
            letter.toUpperCase(),
        );
        const stateMethod = this._state[methodKey as keyof State];

        if (typeof stateMethod === "function") {
            stateMethod.call(this._state, context, data, ...args);
        } else {
            console.warn(`Unhandled event: ${event}`);
        }

        // Emit the event
        this.emit(event, data);
    }

    /**
     * Register an event handler
     */
    on(event: string, handler: (event: string, data: EventData) => void): void {
        if (!this._eventHandlers.has(event)) {
            this._eventHandlers.set(event, new Set());
        }

        this._eventHandlers.get(event)?.add(handler);
    }

    /**
     * Emit an event to registered handlers
     */
    protected emit(event: string, data: EventData): void {
        // Call handlers for the specific event
        this._eventHandlers.get(event)?.forEach((handler) => {
            handler(event, data);
        });

        // Call handlers for the wildcard event
        if (event !== "*") {
            this._eventHandlers.get("*")?.forEach((handler) => {
                handler(event, data);
            });
        }
    }
}
