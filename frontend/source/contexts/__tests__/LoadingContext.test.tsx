import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import { LoadingProvider } from "../LoadingContext";
import { useLoading } from "../useLoading";

/**
 * Tests for the LoadingContext provider component
 *
 * This test suite verifies that:
 * - The LoadingProvider correctly initializes with isLoading=false
 * - The showLoading, hideLoading, and toggleLoading methods work as expected
 * - The provider responds to custom events
 * - Event listeners are properly cleaned up on unmount
 */

// Test consumer component
const TestComponent = () => {
    const { isLoading, showLoading, hideLoading, toggleLoading } = useLoading();

    return (
        <div>
            <div data-testid="loading-state">
                {isLoading ? "Loading" : "Not Loading"}
            </div>
            <button data-testid="show-loading" onClick={showLoading}>
                Show Loading
            </button>
            <button data-testid="hide-loading" onClick={hideLoading}>
                Hide Loading
            </button>
            <button
                data-testid="toggle-loading-true"
                onClick={() => toggleLoading(true)}
            >
                Toggle Loading True
            </button>
            <button
                data-testid="toggle-loading-false"
                onClick={() => toggleLoading(false)}
            >
                Toggle Loading False
            </button>
        </div>
    );
};

describe("LoadingContext", () => {
    beforeEach(() => {
        vi.resetAllMocks();
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    it("initializes with isLoading set to false", () => {
        render(
            <LoadingProvider>
                <TestComponent />
            </LoadingProvider>,
        );

        expect(screen.getByTestId("loading-state")).toHaveTextContent(
            "Not Loading",
        );
    });

    it("showLoading sets isLoading to true", () => {
        render(
            <LoadingProvider>
                <TestComponent />
            </LoadingProvider>,
        );

        fireEvent.click(screen.getByTestId("show-loading"));
        expect(screen.getByTestId("loading-state")).toHaveTextContent(
            "Loading",
        );
    });

    it("hideLoading sets isLoading to false", () => {
        render(
            <LoadingProvider>
                <TestComponent />
            </LoadingProvider>,
        );

        // First set to true
        fireEvent.click(screen.getByTestId("show-loading"));
        expect(screen.getByTestId("loading-state")).toHaveTextContent(
            "Loading",
        );

        // Then hide
        fireEvent.click(screen.getByTestId("hide-loading"));
        expect(screen.getByTestId("loading-state")).toHaveTextContent(
            "Not Loading",
        );
    });

    it("toggleLoading sets isLoading to the provided value", () => {
        render(
            <LoadingProvider>
                <TestComponent />
            </LoadingProvider>,
        );

        // Toggle to true
        fireEvent.click(screen.getByTestId("toggle-loading-true"));
        expect(screen.getByTestId("loading-state")).toHaveTextContent(
            "Loading",
        );

        // Toggle to false
        fireEvent.click(screen.getByTestId("toggle-loading-false"));
        expect(screen.getByTestId("loading-state")).toHaveTextContent(
            "Not Loading",
        );
    });

    it("responds to loading:toggle custom events", () => {
        render(
            <LoadingProvider>
                <TestComponent />
            </LoadingProvider>,
        );

        // Dispatch custom event with loading true
        act(() => {
            window.dispatchEvent(
                new CustomEvent("loading:toggle", {
                    detail: { status: true },
                }),
            );
        });
        expect(screen.getByTestId("loading-state")).toHaveTextContent(
            "Loading",
        );

        // Dispatch custom event with loading false
        act(() => {
            window.dispatchEvent(
                new CustomEvent("loading:toggle", {
                    detail: { status: false },
                }),
            );
        });
        expect(screen.getByTestId("loading-state")).toHaveTextContent(
            "Not Loading",
        );
    });

    it("removes event listener when unmounted", () => {
        // Spy on window.removeEventListener
        const removeEventListenerSpy = vi.spyOn(window, "removeEventListener");

        const { unmount } = render(
            <LoadingProvider>
                <TestComponent />
            </LoadingProvider>,
        );

        unmount();

        // Verify removeEventListener was called with "loading:toggle"
        expect(removeEventListenerSpy).toHaveBeenCalledWith(
            "loading:toggle",
            expect.any(Function),
        );
    });
});
