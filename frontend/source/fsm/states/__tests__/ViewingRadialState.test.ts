import { describe, it, expect, vi, beforeEach } from "vitest";
import { ViewingRadialState } from "../ViewingRadialState";
import type { StateContext, Actions } from "../../State";
import type { NodeKey } from "../../../network/data";
import type { TransitionFunction } from "../../AbstractFSM";

describe("ViewingRadialState", () => {
    let viewingRadialState: ViewingRadialState;
    let mockActions: Actions;
    let mockTransition: TransitionFunction;
    let mockContext: StateContext;

    beforeEach(() => {
        // Setup mocks
        mockActions = {
            handleError: vi.fn(),
            loadInlineData: vi.fn(),
            pushState: vi.fn(),
            requestNetwork: vi.fn(),
            requestRadial: vi.fn(),
            requestRandom: vi.fn(),
            showNetwork: vi.fn(),
            showRadial: vi.fn(),
            toggleFilter: vi.fn(),
            toggleNetwork: vi.fn(),
            toggleLoading: vi.fn(),
            toggleRadial: vi.fn(),
            selectEntity: vi.fn(),
        };

        mockTransition = vi.fn();

        mockContext = {
            actions: mockActions,
            transition: mockTransition,
        };

        // Create a new instance of ViewingRadialState
        viewingRadialState = new ViewingRadialState();
    });

    describe("onEnter", () => {
        it("should call the correct actions when entering the state", () => {
            // Act
            viewingRadialState.onEnter(mockContext);

            // Assert
            expect(mockActions.toggleNetwork).toHaveBeenCalledWith(false);
            expect(mockActions.toggleRadial).toHaveBeenCalledWith(true);
            expect(mockActions.toggleFilter).toHaveBeenCalledWith(false);
        });
    });

    describe("onExit", () => {
        it("should call the correct actions when exiting the state", () => {
            // Act
            viewingRadialState.onExit(mockContext);

            // Assert
            expect(mockActions.toggleRadial).toHaveBeenCalledWith(false);
        });
    });

    describe("requestNetwork", () => {
        it("should call actions.requestNetwork with the entity key and false", () => {
            // Arrange
            const entityKey: NodeKey = "testEntity" as NodeKey;

            // Act
            viewingRadialState.requestNetwork(mockContext, entityKey);

            // Assert
            expect(mockActions.requestNetwork).toHaveBeenCalledWith(
                entityKey,
                false,
            );
        });
    });

    describe("requestRandom", () => {
        it("should call actions.requestRandom", () => {
            // Act
            viewingRadialState.requestRandom(mockContext);

            // Assert
            expect(mockActions.requestRandom).toHaveBeenCalled();
        });
    });
});
