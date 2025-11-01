import { describe, it, expect, vi, beforeEach } from "vitest";
import { RequestingRandomState } from "../RequestingRandomState";
import type { StateContext, Actions } from "../../State";
import type {
    NetworkData,
    NodeKey,
    NetworkNode,
    NetworkLink,
} from "../../../network/data";
import type { TransitionFunction } from "../../AbstractFSM";

describe("RequestingRandomState", () => {
    let state: RequestingRandomState;
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
            requestRelations: vi.fn(),
            requestEntity: vi.fn(),
            requestRandom: vi.fn(),
            showNetwork: vi.fn(),
            showRadial: vi.fn(),
            updateEntityDetails: vi.fn(),
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
        state = new RequestingRandomState();
    });

    describe("Instance creation", () => {
        it("should be able to create an instance", () => {
            expect(state).toBeInstanceOf(RequestingRandomState);
        });
    });

    describe("onEnter method", () => {
        it("should toggle loading to true", () => {
            // Arrange & Act
            state.onEnter(mockContext);

            // Assert
            expect(mockActions.toggleLoading).toHaveBeenCalledWith(true);
        });

        it("should log to console", () => {
            // Arrange
            const consoleSpy = vi.spyOn(console, "log");

            // Act
            state.onEnter(mockContext);

            // Assert
            expect(consoleSpy).toHaveBeenCalledWith(
                "REQUESTING-RANDOM _onEnter",
            );
        });
    });

    describe("onExit method", () => {
        it("should toggle loading to false", () => {
            // Arrange & Act
            state.onExit(mockContext);

            // Assert
            expect(mockActions.toggleLoading).toHaveBeenCalledWith(false);
        });

        it("should log to console", () => {
            // Arrange
            const consoleSpy = vi.spyOn(console, "log");

            // Act
            state.onExit(mockContext);

            // Assert
            expect(consoleSpy).toHaveBeenCalledWith(
                "REQUESTING-RANDOM _onExit",
            );
        });
    });

    describe("handleError method", () => {
        it("should delegate to actions.handleError", () => {
            // Arrange
            const error = new Error("Test error");

            // Act
            state.handleError(mockContext, error);

            // Assert
            expect(mockActions.handleError).toHaveBeenCalledWith(error);
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

        it("should call showNetwork with the provided data and default pushHistory", () => {
            // Act
            state.receivedNetwork(mockContext, mockNetworkData);

            // Assert
            expect(mockActions.showNetwork).toHaveBeenCalledWith(
                mockNetworkData,
                false,
            );
        });

        it("should call showNetwork with the provided data and explicit pushHistory", () => {
            // Arrange
            const pushHistory = true;

            // Act
            state.receivedNetwork(mockContext, mockNetworkData, pushHistory);

            // Assert
            expect(mockActions.showNetwork).toHaveBeenCalledWith(
                mockNetworkData,
                pushHistory,
            );
        });

        it("should log to console", () => {
            // Arrange
            const consoleSpy = vi.spyOn(console, "log");

            // Act
            state.receivedNetwork(mockContext, mockNetworkData);

            // Assert
            expect(consoleSpy).toHaveBeenCalledWith(
                "REQUESTING-RANDOM received-network",
            );
        });
    });
});
