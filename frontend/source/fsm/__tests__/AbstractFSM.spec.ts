import {
    describe,
    it,
    expect,
    vi,
    beforeEach,
    afterEach,
    type MockInstance,
} from "vitest";
import { AbstractFSM, type EventData } from "../AbstractFSM";
import type { State } from "../State";
import type { FSMStateType } from "../types";

// Mock implementation of State
class MockState implements State {
    onEnter = vi.fn();
    onExit = vi.fn();
    handleEvent = vi.fn();
    handleError = vi.fn();
    requestNetwork = vi.fn();
}

// Concrete implementation of AbstractFSM for testing
class TestFSM extends AbstractFSM {
    constructor(initialState: FSMStateType = "uninitialized") {
        super(initialState);

        // Register test states
        this.registerState("uninitialized", new MockState());
        this.registerState("state-viewing-network", new MockState());
    }

    protected createFallbackState(): State {
        return new MockState();
    }

    protected getFallbackState(): State {
        return this._states.get("uninitialized") || new MockState();
    }

    protected initialize(): void {
        // No-op for testing
    }

    // Expose protected methods for testing
    public exposeRegisterState(stateType: FSMStateType, state: State): void {
        this.registerState(stateType, state);
    }

    public exposeGetOrCreateState(stateType: FSMStateType): State {
        return this.getOrCreateState(stateType);
    }

    public exposeEmit(event: string, data: EventData): void {
        this.emit(event, data);
    }
}

// Special test FSM to test fallback state error
class BrokenFallbackFSM extends AbstractFSM {
    constructor(initialState: FSMStateType = "uninitialized") {
        super(initialState);
    }

    protected createFallbackState(): State {
        return new MockState();
    }

    protected getFallbackState(): State | null {
        // Return null to trigger the error case
        return null;
    }

    protected initialize(): void {
        // No-op for testing
    }

    public exposeGetOrCreateState(stateType: FSMStateType): State {
        return this.getOrCreateState(stateType);
    }
}

// Define an interface for console spies
interface ConsoleSpy {
    log: MockInstance<typeof console.log>;
    warn: MockInstance<typeof console.warn>;
    error: MockInstance<typeof console.error>;
}

describe("AbstractFSM", () => {
    let fsm: TestFSM;
    let consoleSpy: ConsoleSpy;

    beforeEach(() => {
        // Create a new FSM instance before each test
        fsm = new TestFSM();

        // Spy on console methods
        consoleSpy = {
            log: vi.spyOn(console, "log").mockImplementation(() => {}),
            warn: vi.spyOn(console, "warn").mockImplementation(() => {}),
            error: vi.spyOn(console, "error").mockImplementation(() => {}),
        };
    });

    afterEach(() => {
        // Clean up mocks after each test
        vi.clearAllMocks();
    });

    describe("constructor", () => {
        it("should initialize with the provided state", () => {
            const initialState: FSMStateType = "state-viewing-network";
            const fsm = new TestFSM(initialState);
            expect(fsm.state).toBe(initialState);
        });

        it("should initialize maps for states and event handlers", () => {
            expect(fsm["_states"]).toBeInstanceOf(Map);
            expect(fsm["_eventHandlers"]).toBeInstanceOf(Map);
        });
    });

    describe("state getter", () => {
        it("should return the current state type", () => {
            expect(fsm.state).toBe("uninitialized");
        });
    });

    describe("registerState", () => {
        it("should add a state to the states map", () => {
            const stateType: FSMStateType = "state-requesting-network";
            const state = new MockState();

            fsm.exposeRegisterState(stateType, state);

            expect(fsm["_states"].get(stateType)).toBe(state);
        });
    });

    describe("getOrCreateState", () => {
        it("should return the requested state if it exists", () => {
            const stateType: FSMStateType = "state-viewing-network";
            const state = fsm.exposeGetOrCreateState(stateType);

            expect(state).toBe(fsm["_states"].get(stateType));
        });

        it("should return the fallback state if the requested state doesn't exist", () => {
            // Use a type assertion to test with a non-existent state
            // This simulates what happens when an invalid state is requested
            const invalidStateType = "invalid-state" as FSMStateType;
            const invalidState = fsm.exposeGetOrCreateState(invalidStateType);

            // Should return the fallback state
            expect(invalidState).toBe(fsm["_states"].get("uninitialized"));
            expect(consoleSpy.warn).toHaveBeenCalledWith(
                `State ${invalidStateType} not found, using fallback state`,
            );
        });

        it("should throw an error if fallback state is not available", () => {
            const brokenFsm = new BrokenFallbackFSM();
            const stateType = "invalid-state" as FSMStateType;

            expect(() => {
                brokenFsm.exposeGetOrCreateState(stateType);
            }).toThrow("Fallback state not found, FSM is in an invalid state");
        });
    });

    describe("transition", () => {
        it("should change the current state", () => {
            const initialState = fsm.state;
            const newStateType: FSMStateType = "state-viewing-network";

            fsm.transition(newStateType);

            expect(fsm.state).toBe(newStateType);
            expect(fsm.state).not.toBe(initialState);
        });

        it("should call onExit on the current state and onEnter on the new state", () => {
            const oldState = fsm["_state"] as MockState;
            const newStateType: FSMStateType = "state-viewing-network";
            const newState = fsm["_states"].get(newStateType) as MockState;

            fsm.transition(newStateType);

            expect(oldState.onExit).toHaveBeenCalledTimes(1);
            expect(newState.onEnter).toHaveBeenCalledTimes(1);
        });

        it("should emit a wildcard event with the new state type", () => {
            const emitSpy = vi.spyOn(
                fsm as unknown as {
                    emit: (event: string, data: FSMStateType) => void;
                },
                "emit",
            );
            const newStateType: FSMStateType = "state-viewing-network";

            fsm.transition(newStateType);

            expect(emitSpy).toHaveBeenCalledWith("*", newStateType);
        });
    });

    describe("handle", () => {
        it("should attempt to call the appropriate method on the current state", () => {
            const event = "request-network";
            const data = "entity123";
            const methodKey = "requestNetwork"; // camelCase conversion

            // Add a spy to the mock state's method
            const mockState = fsm["_state"] as MockState;

            fsm.handle(event, data);

            expect(mockState[methodKey as keyof MockState]).toHaveBeenCalled();
        });

        it("should emit the event", () => {
            const emitSpy = vi.spyOn(
                fsm as unknown as {
                    emit: (event: string, data: unknown) => void;
                },
                "emit",
            );
            const event = "request-network";
            const data = "entity123";

            fsm.handle(event, data);

            expect(emitSpy).toHaveBeenCalledWith(event, data);
        });

        it("should warn about unhandled events", () => {
            const event = "unknown-event";
            const data = null;

            fsm.handle(event, data);

            expect(consoleSpy.warn).toHaveBeenCalledWith(
                `Unhandled event: ${event}`,
            );
        });

        it("should convert kebab-case event names to camelCase method names", () => {
            const mockState = new MockState();
            mockState.requestNetwork = vi.fn();
            fsm["_state"] = mockState;

            fsm.handle("request-network", "entity123");

            expect(mockState.requestNetwork).toHaveBeenCalled();
        });
    });

    describe("on", () => {
        it("should register an event handler", () => {
            const event = "test-event";
            const handler = vi.fn();

            fsm.on(event, handler);

            expect(fsm["_eventHandlers"].has(event)).toBe(true);
            expect(fsm["_eventHandlers"].get(event)?.has(handler)).toBe(true);
        });

        it("should create a new Set for the event if it doesn't exist", () => {
            const event = "new-event";
            const handler = vi.fn();

            expect(fsm["_eventHandlers"].has(event)).toBe(false);

            fsm.on(event, handler);

            expect(fsm["_eventHandlers"].has(event)).toBe(true);
            expect(fsm["_eventHandlers"].get(event)).toBeInstanceOf(Set);
        });

        it("should add the handler to an existing Set if the event exists", () => {
            const event = "existing-event";
            const handler1 = vi.fn();
            const handler2 = vi.fn();

            fsm.on(event, handler1);
            fsm.on(event, handler2);

            const handlers = fsm["_eventHandlers"].get(event);
            expect(handlers?.size).toBe(2);
            expect(handlers?.has(handler1)).toBe(true);
            expect(handlers?.has(handler2)).toBe(true);
        });
    });

    describe("emit", () => {
        it("should call all handlers registered for the event", () => {
            const event = "test-event";
            const data = { test: "data" };
            const handler1 = vi.fn();
            const handler2 = vi.fn();

            fsm.on(event, handler1);
            fsm.on(event, handler2);

            fsm.exposeEmit(event, data);

            expect(handler1).toHaveBeenCalledWith(event, data);
            expect(handler2).toHaveBeenCalledWith(event, data);
        });

        it("should call all wildcard handlers for non-wildcard events", () => {
            const specificEvent = "specific-event";
            const wildcardEvent = "*";
            const data = { test: "data" };
            const specificHandler = vi.fn();
            const wildcardHandler = vi.fn();

            fsm.on(specificEvent, specificHandler);
            fsm.on(wildcardEvent, wildcardHandler);

            fsm.exposeEmit(specificEvent, data);

            expect(specificHandler).toHaveBeenCalledWith(specificEvent, data);
            expect(wildcardHandler).toHaveBeenCalledWith(specificEvent, data);
        });

        it("should not call wildcard handlers when emitting a wildcard event", () => {
            const wildcardEvent = "*";
            const data = { test: "data" };
            const wildcardHandler = vi.fn();

            fsm.on(wildcardEvent, wildcardHandler);

            fsm.exposeEmit(wildcardEvent, data);

            // Wildcard handlers should not be called for wildcard events to prevent infinite loops
            expect(wildcardHandler).toHaveBeenCalledTimes(1);
        });

        it("should gracefully handle events with no registered handlers", () => {
            const event = "no-handlers";
            const data = { test: "data" };

            expect(() => {
                fsm.exposeEmit(event, data);
            }).not.toThrow();
        });
    });
});
