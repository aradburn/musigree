/** @jsxImportSource react */
import { describe, it, expect, vi } from "vitest";
import React from "react";
import { render, screen, renderHook } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useNetwork } from "../useNetwork";
import { NetworkProvider } from "../NetworkContext";
import {
    NetworkContext,
    type NetworkContextProps,
    initialState,
} from "../networkContextInstance";

// Test component that uses the hook within a component
const TestComponent = () => {
    const network = useNetwork();
    return (
        <div data-testid="network-state">{JSON.stringify(network.state)}</div>
    );
};

// Component that will throw because it's used outside a provider
const ErrorComponent = () => {
    try {
        useNetwork();
        return <div>Should not render</div>;
    } catch (error) {
        return (
            <div data-testid="error-message">{(error as Error).message}</div>
        );
    }
};

describe("useNetwork", () => {
    it("should return the network context when used within NetworkProvider", () => {
        render(
            <NetworkProvider>
                <TestComponent />
            </NetworkProvider>,
        );

        // Check that the component rendered with state from the context
        const stateElement = screen.getByTestId("network-state");
        // Convert both to objects for deep comparison
        const renderedState = JSON.parse(stateElement.textContent || "{}");
        expect(renderedState).toEqual(initialState);
    });

    it("should throw an error when used outside of NetworkProvider", () => {
        render(<ErrorComponent />);
        expect(screen.getByTestId("error-message")).toHaveTextContent(
            "useNetwork must be used within a NetworkProvider",
        );
    });

    it("should provide all expected properties in the context", () => {
        // Use renderHook to test the hook directly
        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <NetworkProvider>{children}</NetworkProvider>
        );

        const { result } = renderHook(() => useNetwork(), { wrapper });

        // Check that all expected properties exist
        expect(result.current).toHaveProperty("state");
        expect(result.current).toHaveProperty("dispatch");
        expect(result.current).toHaveProperty("setupChargeForce");
        expect(result.current).toHaveProperty("setupLinkForce");
        expect(result.current).toHaveProperty("setupGravityForce");
        expect(result.current).toHaveProperty("setForces");
        expect(result.current).toHaveProperty("resetForces");

        // Check state structure
        expect(result.current.state).toHaveProperty("nodeStrength");
        expect(result.current.state).toHaveProperty("linkStrength");
        expect(result.current.state).toHaveProperty("gravityStrength");
        expect(result.current.state).toHaveProperty("selectedNode");
    });

    it("should throw the expected error message", () => {
        // Test directly with renderHook to verify the exact error message
        expect(() => {
            renderHook(() => useNetwork());
        }).toThrow("useNetwork must be used within a NetworkProvider");
    });
});
