import { describe, it, expect, vi, beforeEach } from "vitest";
import { BaseState } from "../BaseState";
import type { StateContext, Actions } from "../../State";
import { NodeType } from "../../../network/data";
import type { NodeKey, NetworkData } from "../../../network/data";
import type { RelationsData } from "../../../relations";
import type { TransitionFunction } from "../../AbstractFSM";

// Create a concrete implementation of BaseState for testing
class TestState extends BaseState {
    // Optional overrides to test method overriding
    receivedNetworkCalled = false;

    override receivedNetwork(
        context: StateContext,
        data: NetworkData,
        pushHistory = false,
    ): void {
        this.receivedNetworkCalled = true;
        // Call super to test super implementation
        super.receivedNetwork(context, data, pushHistory);
    }
}

describe("BaseState", () => {
    let testState: TestState;
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

        // Create a new test state instance
        testState = new TestState();
    });

    describe("Instance creation", () => {
        it("should be able to create a concrete instance", () => {
            expect(testState).toBeInstanceOf(BaseState);
            expect(testState).toBeInstanceOf(TestState);
        });
    });

    describe("No-op methods", () => {
        it("should have onEnter method that does nothing", () => {
            // Arrange & Act
            testState.onEnter(mockContext);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have onExit method that does nothing", () => {
            // Arrange & Act
            testState.onExit(mockContext);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have receivedNetwork method that does nothing", () => {
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
            testState.receivedNetwork(mockContext, mockData);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have receivedRadial method that does nothing", () => {
            // Arrange
            const mockData: RelationsData = {
                results: [],
            };

            // Act
            testState.receivedRelations(mockContext, mockData);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have receivedRandom method that does nothing", () => {
            // Arrange
            const mockData = { center: "entity1" as NodeKey };

            // Act
            testState.receivedRandom(mockContext, mockData);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have showNetwork method that does nothing", () => {
            // Act
            testState.showNetwork(mockContext);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have showRadial method that does nothing", () => {
            // Act
            testState.showRadial(mockContext);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have requestNetwork method that does nothing", () => {
            // Arrange
            const entityKey = "entity1" as NodeKey;

            // Act
            testState.requestNetwork(mockContext, entityKey);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have requestRandom method that does nothing", () => {
            // Act
            testState.requestRandom(mockContext);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have selectEntity method that does nothing", () => {
            // Arrange
            const entityKey = "entity1" as NodeKey;

            // Act
            testState.selectEntity(mockContext, entityKey, true);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have receivedEntity method that does nothing", () => {
            // Arrange
            const mockEntityData = {
                key: "entity1" as NodeKey,
                name: "Test Entity",
            };

            // Act
            testState.receivedEntity(mockContext, mockEntityData);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should have updateEntityDetails method that does nothing", () => {
            // Act
            testState.updateEntityDetails(mockContext);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should handle selectEntity with null entityKey", () => {
            // Act
            testState.selectEntity(mockContext, null, false);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });

        it("should handle receivedNetwork with pushHistory true", () => {
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
            testState.receivedNetwork(mockContext, mockData, true);

            // Assert - should not throw and not call any actions
            expect(mockActions.handleError).not.toHaveBeenCalled();
            expect(mockTransition).not.toHaveBeenCalled();
        });
    });

    describe("handleError method", () => {
        it("should delegate to actions.handleError", () => {
            // Arrange
            const error = new Error("Test error");

            // Act
            testState.handleError(mockContext, error);

            // Assert
            expect(mockActions.handleError).toHaveBeenCalledWith(error);
            expect(mockTransition).not.toHaveBeenCalled();
        });
    });

    describe("Method overriding", () => {
        it("should allow methods to be overridden", () => {
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
            testState.receivedNetwork(mockContext, mockData);

            // Assert
            expect(testState.receivedNetworkCalled).toBe(true);
        });
    });
});
