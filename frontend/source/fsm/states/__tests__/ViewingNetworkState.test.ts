import { describe, it, expect, vi, beforeEach } from "vitest";
import { ViewingNetworkState } from "../ViewingNetworkState";
import type { StateContext, Actions } from "../../State";
import type { NodeKey } from "../../../network/data";
import type { TransitionFunction } from "../../AbstractFSM";

describe("ViewingNetworkState", () => {
    let viewingNetworkState: ViewingNetworkState;
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

        // Create a new instance of ViewingNetworkState
        viewingNetworkState = new ViewingNetworkState();
    });

    describe("onEnter", () => {
        it("should call the correct actions when entering the state", () => {
            // Act
            viewingNetworkState.onEnter(mockContext);

            // Assert
            expect(mockActions.toggleNetwork).toHaveBeenCalledWith(true);
            expect(mockActions.toggleRadial).toHaveBeenCalledWith(false);
            expect(mockActions.toggleFilter).toHaveBeenCalledWith(true);
        });
    });

    describe("onExit", () => {
        it("should call the correct actions when exiting the state", () => {
            // Act
            viewingNetworkState.onExit(mockContext);

            // Assert
            expect(mockActions.toggleNetwork).toHaveBeenCalledWith(false);
            expect(mockActions.toggleFilter).toHaveBeenCalledWith(false);
        });
    });

    describe("requestNetwork", () => {
        it("should call actions.requestNetwork with the entity key and true", () => {
            // Arrange
            const entityKey: NodeKey = "testEntity" as NodeKey;

            // Act
            viewingNetworkState.requestNetwork(mockContext, entityKey);

            // Assert
            expect(mockActions.requestNetwork).toHaveBeenCalledWith(
                entityKey,
                true,
            );
        });
    });

    describe("requestRandom", () => {
        it("should call actions.requestRandom", () => {
            // Act
            viewingNetworkState.requestRandom(mockContext);

            // Assert
            expect(mockActions.requestRandom).toHaveBeenCalled();
        });
    });

    describe("showRadial", () => {
        it("should call actions.showRadial", () => {
            // Act
            viewingNetworkState.showRadial(mockContext);

            // Assert
            expect(mockActions.showRadial).toHaveBeenCalled();
        });
    });

    describe("selectEntity", () => {
        it("should call actions.selectEntity with the entity key and fixed flag when entity key is provided", () => {
            // Arrange
            const entityKey: NodeKey = "testEntity" as NodeKey;
            const fixed = true;

            // Act
            viewingNetworkState.selectEntity(mockContext, entityKey, fixed);

            // Assert
            expect(mockActions.selectEntity).toHaveBeenCalledWith(
                entityKey,
                fixed,
            );
        });

        it("should not call actions.selectEntity when entity key is null", () => {
            // Arrange
            const entityKey: NodeKey | null = null;
            const fixed = true;

            // Act
            viewingNetworkState.selectEntity(mockContext, entityKey, fixed);

            // Assert
            expect(mockActions.selectEntity).not.toHaveBeenCalled();
        });
    });
});
