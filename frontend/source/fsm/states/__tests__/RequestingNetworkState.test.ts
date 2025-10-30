import { describe, it, expect, vi, beforeEach } from "vitest";
import { RequestingNetworkState } from "../RequestingNetworkState";
import type { StateContext, Actions } from "../../State";
import { NodeType } from "../../../network/data";
import type {
    NodeKey,
    NetworkData,
    NetworkCenter,
} from "../../../network/data";
import type { RelationsData } from "../../../relations";
import type { TransitionFunction } from "../../AbstractFSM";

describe("RequestingNetworkState", () => {
    let state: RequestingNetworkState;
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
        state = new RequestingNetworkState();
    });

    describe("Instance creation", () => {
        it("should be able to create an instance", () => {
            expect(state).toBeInstanceOf(RequestingNetworkState);
        });
    });

    describe("onEnter method", () => {
        it("should toggle loading to true", () => {
            // Arrange & Act
            state.onEnter(mockContext);

            // Assert
            expect(mockActions.toggleLoading).toHaveBeenCalledWith(true);
        });
    });

    describe("onExit method", () => {
        it("should toggle loading to false", () => {
            // Arrange & Act
            state.onExit(mockContext);

            // Assert
            expect(mockActions.toggleLoading).toHaveBeenCalledWith(false);
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
        it("should call showNetwork with the provided data", () => {
            // Arrange
            const mockNode = {
                key: "entity1" as NodeKey,
                name: "Test Entity",
                type: NodeType.Artist,
                size: 10,
                x: 0,
                y: 0,
                missing: 0,
                hasMissing: false,
                lastClickTime: 0,
                lastTouchTime: 0,
                distance: 0,
                radius: 0,
                links: [],
                cluster: 0,
                fixed: false,
                isIntermediate: false,
            };

            const mockData: NetworkData = {
                nodeMap: new Map([[mockNode.key, mockNode]]),
                center: mockNode,
                linkMap: new Map(),
                maxDistance: 0,
            };

            // Act
            state.receivedNetwork(mockContext, mockData);

            // Assert
            expect(mockActions.showNetwork).toHaveBeenCalledWith(
                mockData,
                false,
            );
        });

        it("should call showNetwork with pushHistory=true when specified", () => {
            // Arrange
            const mockNode = {
                key: "entity1" as NodeKey,
                name: "Test Entity",
                type: NodeType.Artist,
                size: 10,
                x: 0,
                y: 0,
                missing: 0,
                hasMissing: false,
                lastClickTime: 0,
                lastTouchTime: 0,
                distance: 0,
                radius: 0,
                links: [],
                cluster: 0,
                fixed: false,
                isIntermediate: false,
            };

            const mockData: NetworkData = {
                nodeMap: new Map([[mockNode.key, mockNode]]),
                center: mockNode,
                linkMap: new Map(),
                maxDistance: 0,
            };

            const pushHistory = true;

            // Act
            state.receivedNetwork(mockContext, mockData, pushHistory);

            // Assert
            expect(mockActions.showNetwork).toHaveBeenCalledWith(
                mockData,
                pushHistory,
            );
        });
    });

    describe("receivedRandom method", () => {
        it("should call requestNetwork with the center and pushHistory=true", () => {
            // Arrange
            const mockData: NetworkCenter = {
                center: "entity1" as NodeKey,
            };

            // Act
            state.receivedRandom(mockContext, mockData);

            // Assert
            expect(mockActions.requestNetwork).toHaveBeenCalledWith(
                mockData.center,
                true,
            );
        });
    });

    describe("receivedRelations method", () => {
        it("should call showRadial with the provided data", () => {
            // Arrange
            const mockData: RelationsData = {
                results: [],
            };

            // Act
            state.receivedRelations(mockContext, mockData);

            // Assert
            expect(mockActions.showRadial).toHaveBeenCalledWith(mockData);
        });
    });
});
