# Musigree FSM Architecture

This directory contains the implementation of the Musigree Finite State Machine (FSM) using the state pattern.

## Overview

The FSM is designed around the following principles:

1. **States**: Each application state is represented by its own class
2. **Actions**: Common actions that can be performed are gathered in a central interface
3. **Events**: The FSM processes events and delegates them to the current state

## Directory Structure

- `fsm/`
    - `states/` - All state implementations
        - `BaseState.ts` - Base class for all states
        - `ViewingNetworkState.ts` - State for viewing the network graph
        - `ViewingRadialState.ts` - State for viewing the radial visualization
        - `RequestingNetworkState.ts` - State when requesting network data
        - `RequestingRadialState.ts` - State when requesting radial data
        - `RequestingRandomState.ts` - State when requesting a random entity
        - `UninitializedState.ts` - Initial state
    - `actions/` - Action interfaces
        - `Actions.ts` - Interface for all actions
    - `MusigreeFSM.ts` - Main FSM implementation
    - `State.ts` - Interface for states
    - `index.ts` - Entry point

## Adding a New State

To add a new state to the FSM:

1. Create a new state class in `states/` that extends `BaseState`
2. Implement the required methods for that state
3. Register the state in the `MusigreeFSM` constructor

Example of a new state implementation:

```typescript
import type { StateContext } from "../State";
import { BaseState } from "./BaseState";

export class NewState extends BaseState {
    onEnter(context: StateContext): void {
        console.log("NEW-STATE _onEnter");
        // Perform actions when entering this state
    }

    onExit(context: StateContext): void {
        console.log("NEW-STATE _onExit");
        // Perform actions when exiting this state
    }

    // Override any event handlers needed for this state
    showNetwork(context: StateContext): void {
        console.log("NEW-STATE show-network");
        context.actions.showNetwork(null, false);
    }
}
```

Then register it in the FSM:

```typescript
// In MusigreeFSM.ts constructor
this.registerState("state-new-state", new NewState());
```

## Handling Events

Events are dispatched to the current state through the `handle` method. To add a new event type:

1. Update the event handling in `MusigreeFSM.handle`
2. Add a corresponding method to the `State` interface
3. Implement the method in states that need to handle the event

## Architecture Benefits

This architecture provides several advantages:

1. **Separation of concerns**: Each state's behavior is isolated
2. **Maintainability**: Easy to add/modify states without affecting others
3. **Testability**: States can be tested independently
4. **Readability**: Clear organization of state-specific logic
