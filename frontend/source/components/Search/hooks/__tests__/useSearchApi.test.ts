import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { act, renderHook, waitFor } from "@testing-library/react";
import { useSearchApi, type SearchResult } from "../useSearchApi";

// Mock constants used by the hook
const MOCK_CONSTANTS = {
    TYPEAHEAD: {
        MIN_QUERY_LENGTH: 4,
        API_ENDPOINT: "/api/search/%QUERY",
        QUERY_WILDCARD: "%QUERY",
    },
    TIMING: {
        TYPEAHEAD_DEBOUNCE: 300, // Use a shorter time for tests
    },
};

// Mock the constants import
vi.mock("../../../constants", () => {
    return MOCK_CONSTANTS;
});

// Create a proper mock implementation for global.fetch
const createFetchResponse = (
    data: unknown,
    options: ResponseInit = { status: 200 },
) => {
    return {
        json: () => Promise.resolve(data),
        ok: options.status >= 200 && options.status < 300,
        status: options.status,
    } as Response;
};

describe("useSearchApi", () => {
    // Setup and teardown
    beforeEach(() => {
        vi.useFakeTimers({ shouldAdvanceTime: true });
        // Suppress console.error for expected error tests
        vi.spyOn(console, "error").mockImplementation(() => {});
    });

    afterEach(() => {
        vi.restoreAllMocks();
        vi.clearAllTimers();
    });

    // Test for short query
    it("should return empty results when query is too short", () => {
        const { result } = renderHook(() => useSearchApi("abc"));

        expect(result.current.results).toEqual([]);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeNull();
    });

    // Test for empty query
    it("should return empty results when query is empty", () => {
        const { result } = renderHook(() => useSearchApi(""));

        expect(result.current.results).toEqual([]);
        expect(result.current.loading).toBe(false);
        expect(result.current.error).toBeNull();
    });

    // Test for successful API response
    it("should fetch and return results for valid query", async () => {
        const mockResults: SearchResult[] = [
            { name: "Result 1", key: "r1" },
            { name: "Result 2", key: "r2" },
        ];

        const fetchSpy = vi
            .spyOn(global, "fetch")
            .mockResolvedValueOnce(
                createFetchResponse({ results: mockResults }),
            );

        const { result } = renderHook(() => useSearchApi("test query"));

        // Initial state should show loading
        expect(result.current.loading).toBe(true);

        // Fast-forward timers to trigger the debounced function
        await act(async () => {
            vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
            await Promise.resolve();
            await Promise.resolve();
        });

        // Wait for the hook to update with the fetched results
        await waitFor(() => {
            expect(fetchSpy).toHaveBeenCalledWith("/api/search/test%20query");
            expect(result.current.results).toEqual(mockResults);
            expect(result.current.loading).toBe(false);
            expect(result.current.error).toBeNull();
        });
    });

    // Test for API error
    it("should handle API errors", async () => {
        vi.spyOn(global, "fetch").mockResolvedValueOnce(
            createFetchResponse({}, { status: 500 }),
        );

        const { result } = renderHook(() => useSearchApi("error test"));

        await act(async () => {
            vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
            await Promise.resolve();
            await Promise.resolve();
        });

        await waitFor(() => {
            expect(result.current.results).toEqual([]);
            expect(result.current.loading).toBe(false);
            expect(result.current.error).toBe("API error: 500");
        });
    });

    // Test for network error
    it("should handle network errors", async () => {
        const networkError = new Error("Network error");

        vi.spyOn(global, "fetch").mockRejectedValueOnce(networkError);

        const { result } = renderHook(() => useSearchApi("network test"));

        await act(async () => {
            vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
            await Promise.resolve();
            await Promise.resolve();
        });

        await waitFor(() => {
            expect(result.current.results).toEqual([]);
            expect(result.current.loading).toBe(false);
            expect(result.current.error).toBe("Network error");
        });
    });

    // Test for debouncing
    it("should debounce API calls", async () => {
        const fetchSpy = vi
            .spyOn(global, "fetch")
            .mockResolvedValue(createFetchResponse({ results: [] }));

        const { rerender } = renderHook((props) => useSearchApi(props.query), {
            initialProps: { query: "test" },
        });

        // Change the query multiple times in quick succession
        act(() => {
            rerender({ query: "test1" });
            rerender({ query: "test2" });
            rerender({ query: "test3" });
        });

        // Advance time by less than debounce time - no fetch should happen yet
        act(() => {
            vi.advanceTimersByTime(
                MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE - 50,
            );
        });
        expect(fetchSpy).not.toHaveBeenCalled();

        // Advance time to trigger the debounced function
        await act(async () => {
            vi.advanceTimersByTime(100); // This should exceed the debounce time
            await Promise.resolve();
            await Promise.resolve();
        });

        // Should only be called once with the latest query
        await waitFor(() => {
            expect(fetchSpy).toHaveBeenCalledTimes(1);
            expect(fetchSpy).toHaveBeenCalledWith("/api/search/test3");
        });
    });

    // Test custom debounce time
    it("should respect custom debounce time", async () => {
        const fetchSpy = vi
            .spyOn(global, "fetch")
            .mockResolvedValue(createFetchResponse({ results: [] }));

        const customDebounceTime = 500;
        renderHook(() => useSearchApi("custom", customDebounceTime));

        // Advance time by the default debounce time - fetch should not occur yet
        act(() => {
            vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
        });

        expect(fetchSpy).not.toHaveBeenCalled();

        // Advance time to hit the custom debounce time
        await act(async () => {
            vi.advanceTimersByTime(
                customDebounceTime - MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE,
            );
            // Make sure the fetch promise resolves
            await Promise.resolve();
        });

        expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    // Test for query exactly at minimum length
    it("should search when query is exactly minimum length", async () => {
        const mockResults: SearchResult[] = [{ name: "Result 1", key: "r1" }];

        const fetchSpy = vi
            .spyOn(global, "fetch")
            .mockResolvedValueOnce(
                createFetchResponse({ results: mockResults }),
            );

        const { result } = renderHook(() => useSearchApi("test")); // 4 characters

        expect(result.current.loading).toBe(true);

        await act(async () => {
            vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
            await Promise.resolve();
            await Promise.resolve();
        });

        await waitFor(() => {
            expect(fetchSpy).toHaveBeenCalledWith("/api/search/test");
            expect(result.current.results).toEqual(mockResults);
            expect(result.current.loading).toBe(false);
            expect(result.current.error).toBeNull();
        });
    });

    // Test for query with special characters
    it("should properly encode query with special characters", async () => {
        const fetchSpy = vi
            .spyOn(global, "fetch")
            .mockResolvedValue(createFetchResponse({ results: [] }));

        const { result } = renderHook(() =>
            useSearchApi("test & query + special"),
        );

        await act(async () => {
            vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
            await Promise.resolve();
            await Promise.resolve();
        });

        await waitFor(() => {
            expect(fetchSpy).toHaveBeenCalledWith(
                "/api/search/test%20%26%20query%20%2B%20special",
            );
            expect(result.current.loading).toBe(false);
        });
    });

    // Test for API response with no results property
    it("should handle API response with missing results property", async () => {
        const fetchSpy = vi
            .spyOn(global, "fetch")
            .mockResolvedValueOnce(createFetchResponse({})); // No results property

        const { result } = renderHook(() => useSearchApi("test"));

        await act(async () => {
            vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
            await Promise.resolve();
            await Promise.resolve();
        });

        await waitFor(() => {
            expect(fetchSpy).toHaveBeenCalledWith("/api/search/test");
            expect(result.current.results).toEqual([]);
            expect(result.current.loading).toBe(false);
            expect(result.current.error).toBeNull();
        });
    });

    // Test for non-Error exception
    it("should handle non-Error exceptions", async () => {
        vi.spyOn(global, "fetch").mockRejectedValueOnce("String error");

        const { result } = renderHook(() => useSearchApi("test"));

        await act(async () => {
            vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
            await Promise.resolve();
            await Promise.resolve();
        });

        await waitFor(() => {
            expect(result.current.results).toEqual([]);
            expect(result.current.loading).toBe(false);
            expect(result.current.error).toBe("Unknown error");
        });
    });

    // Test for cleanup on unmount
    it("should cleanup timer on unmount", () => {
        const fetchSpy = vi
            .spyOn(global, "fetch")
            .mockResolvedValue(createFetchResponse({ results: [] }));

        const { unmount } = renderHook(() => useSearchApi("test"));

        // Unmount before debounce time
        unmount();

        // Advance time past debounce - should not call fetch
        act(() => {
            vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
        });

        expect(fetchSpy).not.toHaveBeenCalled();
    });

    // Test for query change resets debounce timer
    it("should reset debounce timer when query changes", async () => {
        const fetchSpy = vi
            .spyOn(global, "fetch")
            .mockResolvedValue(createFetchResponse({ results: [] }));

        const { rerender } = renderHook((props) => useSearchApi(props.query), {
            initialProps: { query: "first" },
        });

        // Advance time by less than debounce time
        act(() => {
            vi.advanceTimersByTime(
                MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE - 100,
            );
        });

        // Change query - this should reset the timer
        act(() => {
            rerender({ query: "second" });
        });

        // Advance time by less than full debounce time again
        act(() => {
            vi.advanceTimersByTime(
                MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE - 100,
            );
        });

        // Should not have been called yet
        expect(fetchSpy).not.toHaveBeenCalled();

        // Now advance the remaining time to trigger the request
        await act(async () => {
            vi.advanceTimersByTime(100);
            await Promise.resolve();
            await Promise.resolve();
        });

        // Should have been called once with the latest query
        await waitFor(() => {
            expect(fetchSpy).toHaveBeenCalledTimes(1);
            expect(fetchSpy).toHaveBeenCalledWith("/api/search/second");
        });
    });
});
