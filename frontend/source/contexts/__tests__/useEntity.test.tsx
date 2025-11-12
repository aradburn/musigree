/** @jsxImportSource react */
import { describe, it, expect, vi } from "vitest";
import { renderHook } from "@testing-library/react";
import { useEntity } from "../useEntity";
import {
    EntityContext,
    type EntityContextProps,
} from "../entityContextInstance";

/**
 * Tests for the useEntity hook
 *
 * This test suite verifies that:
 * - The hook throws an error when used outside of an EntityProvider
 * - The hook returns the context value when used within an EntityProvider
 */

describe("useEntity", () => {
    // Test error case: hook used outside of EntityProvider
    it("should throw an error when used outside of EntityProvider", () => {
        // Silence the console.error for this test since we expect an error
        const consoleSpy = vi.spyOn(console, "error");
        consoleSpy.mockImplementation(() => {});

        // Expect the hook to throw when rendered outside a provider
        expect(() => {
            renderHook(() => useEntity());
        }).toThrow("useEntity must be used within an EntityProvider");

        // Restore console.error
        consoleSpy.mockRestore();
    });

    // Test success case: hook used within an EntityProvider
    it("should return the context value when used within an EntityProvider", () => {
        // Mock the context value
        const mockContextValue: EntityContextProps = {
            state: {
                entity: null,
            },
            dispatch: vi.fn(),
        };

        // Create a wrapper with the EntityContext.Provider
        const wrapper = ({ children }: { children: React.ReactNode }) => (
            <EntityContext.Provider value={mockContextValue}>
                {children}
            </EntityContext.Provider>
        );

        // Render the hook within the provider
        const { result } = renderHook(() => useEntity(), { wrapper });

        // Expect the hook to return the context value
        expect(result.current).toBe(mockContextValue);
        expect(result.current.state).toBe(mockContextValue.state);
        expect(result.current.dispatch).toBe(mockContextValue.dispatch);
    });
});
