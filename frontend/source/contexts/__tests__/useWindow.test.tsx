/** @jsxImportSource react */
import { describe, it, expect, vi } from "vitest";
import type { ReactNode } from "react";
import { renderHook } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useWindow } from "../useWindow";
import {
    WindowContext,
    type WindowContextProps,
} from "../windowContextInstance";

/**
 * Tests for the useWindow hook
 *
 * This test suite verifies that:
 * - The hook throws an error when used outside of a WindowProvider
 * - The hook returns the context value when used within a WindowProvider
 */
describe("useWindow", () => {
    // Test error case: hook used outside of WindowProvider
    it("should throw an error when used outside of WindowProvider", () => {
        // Silence the console.error for this test since we expect an error
        const consoleSpy = vi.spyOn(console, "error");
        consoleSpy.mockImplementation(() => {});

        // Expect the hook to throw when rendered outside a provider
        expect(() => {
            renderHook(() => useWindow());
        }).toThrow("useWindow must be used within a WindowProvider");

        // Restore console.error
        consoleSpy.mockRestore();
    });

    // Test success case: hook used within a WindowProvider
    it("should return the context value when used within a WindowProvider", () => {
        // Mock the context value
        const mockContextValue: WindowContextProps = {
            state: {
                width: 1024,
                height: 768,
                dpr: 2,
                dimensions: [1024, 768],
                svgDimensions: [2048, 1536],
                isMobile: false,
            },
            handleResize: vi.fn(),
        };

        // Create a wrapper with the WindowContext.Provider
        const wrapper = ({ children }: { children: ReactNode }) => (
            <WindowContext.Provider value={mockContextValue}>
                {children}
            </WindowContext.Provider>
        );

        // Render the hook within the provider
        const { result } = renderHook(() => useWindow(), { wrapper });

        // Expect the hook to return the context value
        expect(result.current).toBe(mockContextValue);
        expect(result.current.state.width).toBe(1024);
        expect(result.current.state.height).toBe(768);
        expect(result.current.state.dpr).toBe(2);
        expect(result.current.state.dimensions).toEqual([1024, 768]);
        expect(result.current.state.svgDimensions).toEqual([2048, 1536]);
        expect(result.current.handleResize).toBe(mockContextValue.handleResize);
    });
});
