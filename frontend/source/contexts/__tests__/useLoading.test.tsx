/** @jsxImportSource react */
import { describe, it, expect, vi } from "vitest";
import type { ReactNode } from "react";
import { render, renderHook } from "@testing-library/react";
import "@testing-library/jest-dom";
import { useLoading } from "../useLoading";
import {
    LoadingContext,
    type LoadingContextProps,
} from "../loadingContextInstance";

/**
 * Tests for the useLoading hook
 *
 * This test suite verifies that:
 * - The hook throws an error when used outside of a LoadingProvider
 * - The hook returns the context value when used within a LoadingProvider
 */

describe("useLoading", () => {
    // Test error case: hook used outside of LoadingProvider
    it("should throw an error when used outside of LoadingProvider", () => {
        // Silence the console.error for this test since we expect an error
        const consoleSpy = vi.spyOn(console, "error");
        consoleSpy.mockImplementation(() => {});

        // Expect the hook to throw when rendered outside a provider
        expect(() => {
            renderHook(() => useLoading());
        }).toThrow("useLoading must be used within a LoadingProvider");

        // Restore console.error
        consoleSpy.mockRestore();
    });

    // Test success case: hook used within a LoadingProvider
    it("should return the context value when used within a LoadingProvider", () => {
        // Mock the context value
        const mockContextValue: LoadingContextProps = {
            isLoading: false,
            showLoading: vi.fn(),
            hideLoading: vi.fn(),
            toggleLoading: vi.fn(),
        };

        // Create a wrapper with the LoadingContext.Provider
        const wrapper = ({ children }: { children: ReactNode }) => (
            <LoadingContext.Provider value={mockContextValue}>
                {children}
            </LoadingContext.Provider>
        );

        // Render the hook within the provider
        const { result } = renderHook(() => useLoading(), { wrapper });

        // Expect the hook to return the context value
        expect(result.current).toBe(mockContextValue);
        expect(result.current.isLoading).toBe(false);
        expect(result.current.showLoading).toBe(mockContextValue.showLoading);
        expect(result.current.hideLoading).toBe(mockContextValue.hideLoading);
        expect(result.current.toggleLoading).toBe(
            mockContextValue.toggleLoading,
        );
    });
});
