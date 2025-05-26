import { describe, it, expect, vi, beforeEach } from "vitest";
import { RequestingRadialState } from "../RequestingRadialState";
import type { StateContext, Actions } from "../../State";
import type { RelationsData } from "../../../relations";
import type { TransitionFunction } from "../../AbstractFSM";

describe("RequestingRadialState", () => {
    let state: RequestingRadialState;
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
        state = new RequestingRadialState();
    });

    describe("Instance creation", () => {
        it("should be able to create an instance", () => {
            expect(state).toBeInstanceOf(RequestingRadialState);
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
                "REQUESTING-RADIAL _onEnter",
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
                "REQUESTING-RADIAL _onExit",
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

    describe("receivedRadial method", () => {
        it("should call showRadial with the provided data", () => {
            // Arrange
            const mockData: RelationsData = {
                results: [],
            };

            // Act
            state.receivedRadial(mockContext, mockData);

            // Assert
            expect(mockActions.showRadial).toHaveBeenCalledWith(mockData);
        });

        it("should log to console", () => {
            // Arrange
            const consoleSpy = vi.spyOn(console, "log");
            const mockData: RelationsData = {
                results: [],
            };

            // Act
            state.receivedRadial(mockContext, mockData);

            // Assert
            expect(consoleSpy).toHaveBeenCalledWith(
                "REQUESTING-RADIAL received-radial",
            );
        });
    });
});
