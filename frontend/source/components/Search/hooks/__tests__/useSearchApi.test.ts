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
        vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
        await Promise.resolve();
        await Promise.resolve();

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

        vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
        await Promise.resolve();
        await Promise.resolve();

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

        vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);
        await Promise.resolve();
        await Promise.resolve();

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
        rerender({ query: "test1" });
        rerender({ query: "test2" });
        rerender({ query: "test3" });

        // Advance time by less than debounce time - no fetch should happen yet
        vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE - 50);
        expect(fetchSpy).not.toHaveBeenCalled();

        // Advance time to trigger the debounced function
        vi.advanceTimersByTime(100); // This should exceed the debounce time
        await Promise.resolve();
        await Promise.resolve();

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
        vi.advanceTimersByTime(MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE);

        expect(fetchSpy).not.toHaveBeenCalled();

        // Advance time to hit the custom debounce time
        vi.advanceTimersByTime(
            customDebounceTime - MOCK_CONSTANTS.TIMING.TYPEAHEAD_DEBOUNCE,
        );

        // Make sure the fetch promise resolves
        await Promise.resolve();

        expect(fetchSpy).toHaveBeenCalledTimes(1);
    });

    /**
     * Note: Several tests in this file are skipped because they require complex setup with async
     * React state updates that are difficult to test reliably. In a real-world scenario, these tests
     * would benefit from using a tool like MSW (Mock Service Worker) to intercept and mock fetch requests
     * more effectively, or from integration tests that test the hook in the context of a real component.
     *
     * The remaining tests still provide good coverage of the basic functionality, ensuring:
     * 1. Queries below the minimum length return empty results
     * 2. Empty queries return empty results
     * 3. Custom debounce timing is respected
     */
});
