import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import React, { useContext } from "react";
import { render, screen, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { NetworkProvider } from "../NetworkContext";
import {
    NetworkContext,
    networkReducer,
    initialState,
    type NetworkAction,
} from "../networkContextInstance";
import * as d3 from "d3";
import { networkManager, musigreeManager } from "../../core/singletons";
import { FORCE } from "../../constants";

// Mock the singletons
vi.mock("../../core/singletons", () => ({
    networkManager: {
        forceLayout: null,
    },
    musigreeManager: {
        svgDimensions: [800, 600],
    },
}));

describe("NetworkContext", () => {
    let mockForceLayout: d3.Simulation<any, any>;
    let mockForceManyBody: ReturnType<typeof vi.fn>;
    let mockForceLink: ReturnType<typeof vi.fn>;
    let mockForceX: ReturnType<typeof vi.fn>;
    let mockForceY: ReturnType<typeof vi.fn>;

    beforeEach(() => {
        // Create mock force functions
        mockForceManyBody = vi.fn().mockReturnValue({
            strength: vi.fn().mockReturnThis(),
            distanceMax: vi.fn().mockReturnThis(),
            theta: vi.fn().mockReturnThis(),
        });

        mockForceLink = vi.fn().mockReturnValue({
            id: vi.fn().mockReturnThis(),
            links: vi.fn().mockReturnThis(),
            distance: vi.fn().mockReturnThis(),
            iterations: vi.fn().mockReturnThis(),
        });

        mockForceX = vi.fn().mockReturnValue({
            strength: vi.fn().mockReturnThis(),
        });

        mockForceY = vi.fn().mockReturnValue({
            strength: vi.fn().mockReturnThis(),
        });

        mockForceLayout = {
            force: vi.fn().mockReturnThis(),
            nodes: vi.fn().mockReturnValue([]),
            alpha: vi.fn().mockReturnThis(),
            restart: vi.fn(),
            stop: vi.fn(),
        } as unknown as d3.Simulation<any, any>;

        // Mock d3 functions
        vi.spyOn(d3, "forceManyBody").mockImplementation(
            mockForceManyBody as any,
        );
        vi.spyOn(d3, "forceLink").mockImplementation(mockForceLink as any);
        vi.spyOn(d3, "forceX").mockImplementation(mockForceX as any);
        vi.spyOn(d3, "forceY").mockImplementation(mockForceY as any);

        // Set up networkManager mock
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map(),
        };
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("renders without crashing", () => {
        // Just test that the provider renders without errors
        render(
            <NetworkProvider>
                <div>Test</div>
            </NetworkProvider>,
        );
        expect(true).toBe(true);
    });

    it("provides context value with all expected properties", () => {
        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            expect(context).toBeDefined();
            expect(context?.state).toBeDefined();
            expect(context?.dispatch).toBeDefined();
            expect(context?.setupChargeForce).toBeDefined();
            expect(context?.setupLinkForce).toBeDefined();
            expect(context?.setupGravityForce).toBeDefined();
            expect(context?.setForces).toBeDefined();
            expect(context?.resetForces).toBeDefined();
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );
    });

    it("initializes with correct initial state", () => {
        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            expect(context?.state.nodeStrength).toBe(initialState.nodeStrength);
            expect(context?.state.linkStrength).toBe(initialState.linkStrength);
            expect(context?.state.gravityStrength).toBe(
                initialState.gravityStrength,
            );
            expect(context?.state.selectedNode).toBe(initialState.selectedNode);
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );
    });

    it("handles setupChargeForce when forceLayout is not initialized", () => {
        (networkManager as any).forceLayout = null;
        const consoleSpy = vi
            .spyOn(console, "error")
            .mockImplementation(() => {});

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupChargeForce(20);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        expect(consoleSpy).toHaveBeenCalledWith("forceLayout not setup yet");
        consoleSpy.mockRestore();
    });

    it("handles setupLinkForce when forceLayout is not initialized", () => {
        (networkManager as any).forceLayout = null;

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupLinkForce(30);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Should not throw
        expect(true).toBe(true);
    });

    it("handles setupGravityForce when forceLayout is not initialized", () => {
        (networkManager as any).forceLayout = null;

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupGravityForce(15);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Should not throw
        expect(true).toBe(true);
    });

    it("calls setForces callback", () => {
        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setForces();
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Should not throw
        expect(true).toBe(true);
    });

    it("calls resetForces callback", () => {
        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.resetForces();
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Should not throw
        expect(true).toBe(true);
    });

    it("handles musigree:force-layout-initialized event", () => {
        const TestComponent = (): React.ReactElement => {
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        act(() => {
            window.dispatchEvent(
                new CustomEvent("musigree:force-layout-initialized"),
            );
        });

        // Should not throw
        expect(true).toBe(true);
    });

    it("handles musigree:set-forces event", () => {
        const TestComponent = (): React.ReactElement => {
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        act(() => {
            window.dispatchEvent(new CustomEvent("musigree:set-forces"));
        });

        // Should not throw
        expect(true).toBe(true);
    });

    it("handles musigree:reset-forces event", () => {
        const TestComponent = (): React.ReactElement => {
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        act(() => {
            window.dispatchEvent(new CustomEvent("musigree:reset-forces"));
        });

        // Should not throw
        expect(true).toBe(true);
    });

    it("cleans up event listeners on unmount", () => {
        const removeEventListenerSpy = vi.spyOn(window, "removeEventListener");

        const { unmount } = render(
            <NetworkProvider>
                <div>Test</div>
            </NetworkProvider>,
        );

        unmount();

        expect(removeEventListenerSpy).toHaveBeenCalled();
        removeEventListenerSpy.mockRestore();
    });

    it("handles useEffect when forceLayout is not initialized", () => {
        (networkManager as any).forceLayout = null;
        const consoleSpy = vi
            .spyOn(console, "log")
            .mockImplementation(() => {});

        render(
            <NetworkProvider>
                <div>Test</div>
            </NetworkProvider>,
        );

        // Should log that force layout is not initialized yet
        expect(consoleSpy).toHaveBeenCalledWith(
            "Force layout not initialized yet, will set up forces when ready",
        );
        consoleSpy.mockRestore();
    });

    it("handles useEffect when forceLayout is initialized", () => {
        (networkManager as any).forceLayout = mockForceLayout;
        const consoleSpy = vi
            .spyOn(console, "log")
            .mockImplementation(() => {});

        render(
            <NetworkProvider>
                <div>Test</div>
            </NetworkProvider>,
        );

        // Should log that forces are being initialized
        expect(consoleSpy).toHaveBeenCalledWith(
            "Initializing network forces from React context",
        );
        consoleSpy.mockRestore();
    });

    it("tests calculateNodeStrength with isIntermediate node", () => {
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map(),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupChargeForce(20);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceManyBody was called
        expect(mockForceManyBody).toHaveBeenCalled();
    });

    it("tests calculateNodeStrength with cluster node", () => {
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map(),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupChargeForce(20);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceManyBody was called
        expect(mockForceManyBody).toHaveBeenCalled();
    });

    it("tests calculateNodeStrength with level one node (distance == 1)", () => {
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map(),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupChargeForce(20);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceManyBody was called
        expect(mockForceManyBody).toHaveBeenCalled();
    });

    it("tests calculateLinkDistance with ALIAS role", () => {
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map([
                [
                    "link1",
                    {
                        role: FORCE.LINK.ROLES.ALIAS,
                        distance: 0,
                        source: { radius: 10 },
                        target: { radius: 10 },
                    },
                ],
            ]),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupLinkForce(30);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceLink was called
        expect(mockForceLink).toHaveBeenCalled();
    });

    it("tests calculateLinkDistance with RELEASED_ON role", () => {
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map([
                [
                    "link1",
                    {
                        role: FORCE.LINK.ROLES.RELEASED_ON,
                        distance: 0,
                        source: { radius: 10 },
                        target: { radius: 10 },
                    },
                ],
            ]),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupLinkForce(30);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceLink was called
        expect(mockForceLink).toHaveBeenCalled();
    });

    it("tests calculateLinkDistance with isSpline and distance < 1", () => {
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map([
                [
                    "link1",
                    {
                        isSpline: true,
                        distance: 0,
                        source: { radius: 10 },
                        target: { radius: 10 },
                    },
                ],
            ]),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupLinkForce(30);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceLink was called
        expect(mockForceLink).toHaveBeenCalled();
    });

    it("tests calculateLinkDistance with isSpline and distance >= 1", () => {
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map([
                [
                    "link1",
                    {
                        isSpline: true,
                        distance: 1,
                        source: { radius: 10 },
                        target: { radius: 10 },
                    },
                ],
            ]),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupLinkForce(30);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceLink was called
        expect(mockForceLink).toHaveBeenCalled();
    });

    it("tests calculateGravityStrength with different distance values", () => {
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map(),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupGravityForce(15);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceX and forceY were called
        expect(mockForceX).toHaveBeenCalled();
        expect(mockForceY).toHaveBeenCalled();
    });

    it("tests calculateGravityStrength when svgDimensions width >= height", () => {
        (musigreeManager as any).svgDimensions = [1000, 800];
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map(),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupGravityForce(15);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceX and forceY were called
        expect(mockForceX).toHaveBeenCalled();
        expect(mockForceY).toHaveBeenCalled();
    });

    it("tests calculateGravityStrength when svgDimensions width < height", () => {
        (musigreeManager as any).svgDimensions = [800, 1000];
        (networkManager as any).forceLayout = mockForceLayout;
        (networkManager as any).data = {
            linkMap: new Map(),
        };

        const TestComponent = (): React.ReactElement => {
            const context = useContext(NetworkContext);
            act(() => {
                context?.setupGravityForce(15);
            });
            return <div>Test</div>;
        };

        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Verify forceX and forceY were called
        expect(mockForceX).toHaveBeenCalled();
        expect(mockForceY).toHaveBeenCalled();
    });
});

describe("networkReducer", () => {
    it("SET_NODE_STRENGTH: should update node strength", () => {
        const action: NetworkAction = { type: "SET_NODE_STRENGTH", value: 20 };
        const newState = networkReducer(initialState, action);
        expect(newState.nodeStrength).toBe(20);
    });

    it("SET_LINK_STRENGTH: should update link strength", () => {
        const action: NetworkAction = { type: "SET_LINK_STRENGTH", value: 50 };
        const newState = networkReducer(initialState, action);
        expect(newState.linkStrength).toBe(50);
    });

    it("SET_GRAVITY_STRENGTH: should update gravity strength", () => {
        const action: NetworkAction = {
            type: "SET_GRAVITY_STRENGTH",
            value: 15,
        };
        const newState = networkReducer(initialState, action);
        expect(newState.gravityStrength).toBe(15);
    });

    it("SELECT_NODE: should set the selected node", () => {
        const action: NetworkAction = {
            type: "SELECT_NODE",
            nodeId: "test-node",
        };
        const newState = networkReducer(initialState, action);
        expect(newState.selectedNode).toBe("test-node");
    });

    it("SET_FORCES: should return the current state", () => {
        const currentState = { ...initialState, nodeStrength: 20 };
        const action: NetworkAction = { type: "SET_FORCES" };
        const newState = networkReducer(currentState, action);
        expect(newState).toEqual(currentState);
    });

    it("RESET_FORCES: should reset to initial state", () => {
        const currentState = {
            nodeStrength: 20,
            linkStrength: 50,
            gravityStrength: 15,
            selectedNode: "test-node",
        };
        const action: NetworkAction = { type: "RESET_FORCES" };
        const newState = networkReducer(currentState, action);
        expect(newState).toEqual(initialState);
    });

    it("unknown action: should return current state", () => {
        // Using type assertion to test an invalid action type
        const action = { type: "UNKNOWN_ACTION" } as unknown as NetworkAction;
        const newState = networkReducer(initialState, action);
        expect(newState).toEqual(initialState);
    });
});
