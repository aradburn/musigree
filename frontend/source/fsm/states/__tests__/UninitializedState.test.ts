import { describe, it, expect, vi, beforeEach } from "vitest";
import { UninitializedState } from "../UninitializedState";
import type { StateContext, Actions } from "../../State";
import type {
    NetworkData,
    NodeKey,
    NetworkNode,
    NetworkLink,
} from "../../../network/data";
import type { TransitionFunction } from "../../AbstractFSM";

describe("UninitializedState", () => {
    let state: UninitializedState;
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

        // Create a new state instance
        state = new UninitializedState();
    });

    describe("Instance creation", () => {
        it("should be able to create an instance", () => {
            expect(state).toBeInstanceOf(UninitializedState);
        });
    });

    describe("onEnter method", () => {
        it("should call loadInlineData", () => {
            // Arrange & Act
            state.onEnter(mockContext);

            // Assert
            expect(mockActions.loadInlineData).toHaveBeenCalled();
        });

        it("should log to console", () => {
            // Arrange
            const consoleSpy = vi.spyOn(console, "log");

            // Act
            state.onEnter(mockContext);

            // Assert
            expect(consoleSpy).toHaveBeenCalledWith("UNITIALIZED _onEnter");
        });
    });

    describe("onExit method", () => {
        it("should log to console", () => {
            // Arrange
            const consoleSpy = vi.spyOn(console, "log");

            // Act
            state.onExit(mockContext);

            // Assert
            expect(consoleSpy).toHaveBeenCalledWith("UNITIALIZED _onExit");
        });
    });

    describe("receivedNetwork method", () => {
        let mockNetworkData: NetworkData;

        beforeEach(() => {
            // Create mock NetworkData
            const nodeMap = new Map<NodeKey, NetworkNode>();
            const linkMap = new Map<string, NetworkLink>();
            const center = {
                key: "test-node",
                name: "Test Node",
                type: "artist",
                size: 10,
                x: 0,
                y: 0,
                missing: 0,
                hasMissing: false,
                lastClickTime: 0,
                lastTouchTime: 0,
                distance: 0,
                radius: 5,
                links: [],
                cluster: 0,
                fixed: false,
                isIntermediate: false,
            } as NetworkNode;

            nodeMap.set(center.key, center);

            mockNetworkData = {
                nodeMap,
                center,
                linkMap,
                maxDistance: 1,
            };
        });

        it("should transition to state-viewing-network", () => {
            // Act
            state.receivedNetwork(mockContext, mockNetworkData);

            // Assert
            expect(mockTransition).toHaveBeenCalledWith(
                "state-viewing-network",
            );
        });

        it("should log to console", () => {
            // Arrange
            const consoleSpy = vi.spyOn(console, "log");

            // Act
            state.receivedNetwork(mockContext, mockNetworkData);

            // Assert
            expect(consoleSpy).toHaveBeenCalledWith(
                "UNITIALIZED received-network",
            );
        });
    });

    describe("requestNetwork method", () => {
        it("should transition to state-requesting-network", () => {
            // Arrange
            const entityKey = "test-entity";

            // Act
            state.requestNetwork(mockContext, entityKey);

            // Assert
            expect(mockTransition).toHaveBeenCalledWith(
                "state-requesting-network",
            );
        });

        it("should call requestNetwork with the entity key and true", () => {
            // Arrange
            const entityKey = "test-entity";

            // Act
            state.requestNetwork(mockContext, entityKey);

            // Assert
            expect(mockActions.requestNetwork).toHaveBeenCalledWith(
                entityKey,
                true,
            );
        });

        it("should log to console", () => {
            // Arrange
            const entityKey = "test-entity";
            const consoleSpy = vi.spyOn(console, "log");

            // Act
            state.requestNetwork(mockContext, entityKey);

            // Assert
            expect(consoleSpy).toHaveBeenCalledWith(
                "UNITIALIZED request-network",
            );
        });
    });

    describe("requestRandom method", () => {
        it("should transition to state-requesting-random", () => {
            // Act
            state.requestRandom(mockContext);

            // Assert
            expect(mockTransition).toHaveBeenCalledWith(
                "state-requesting-random",
            );
        });

        it("should call requestRandom", () => {
            // Act
            state.requestRandom(mockContext);

            // Assert
            expect(mockActions.requestRandom).toHaveBeenCalled();
        });

        it("should log to console", () => {
            // Arrange
            const consoleSpy = vi.spyOn(console, "log");

            // Act
            state.requestRandom(mockContext);

            // Assert
            expect(consoleSpy).toHaveBeenCalledWith(
                "UNITIALIZED request-random",
            );
        });
    });
});
