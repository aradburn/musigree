/** @jsxImportSource react */
import { useState, useEffect } from "react";
import { TYPEAHEAD, TIMING } from "../../../constants";

/**
 * Search result interface matching the API response format
 */
export interface SearchResult {
    name: string;
    key: string;
}

/**
 * API response interface
 */
interface SearchApiResponse {
    results: SearchResult[];
}

/**
 * Result object returned by the hook
 */
interface SearchApiResult {
    results: SearchResult[];
    loading: boolean;
    error: string | null;
}

const isAbortError = (err: unknown): boolean =>
    (err instanceof DOMException || err instanceof Error) &&
    err.name === "AbortError";

/**
 * Custom hook for fetching search results from the API with debouncing
 * @param query - The search query string
 * @param debounceTime - Time in milliseconds to wait before making the API call (default: from constants)
 * @returns An object containing loading state, search results, and any error
 */
export const useSearchApi = (
    query: string,
    debounceTime: number = TIMING.TYPEAHEAD_DEBOUNCE,
): SearchApiResult => {
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        // Don't search if query is too short
        if (!query || query.length < TYPEAHEAD.MIN_QUERY_LENGTH) {
            setResults([]);
            setLoading(false);
            setError(null);
            return;
        }

        // Set loading state immediately
        setLoading(true);

        const abortController = new AbortController();

        // Setup debounce timer
        const timerId = setTimeout(() => {
            const fetchData = async (): Promise<void> => {
                try {
                    // Replace wildcard with actual query
                    const url = TYPEAHEAD.API_ENDPOINT.replace(
                        TYPEAHEAD.QUERY_WILDCARD,
                        encodeURIComponent(query),
                    );

                    const response = await fetch(url, {
                        signal: abortController.signal,
                    });

                    if (abortController.signal.aborted) {
                        return;
                    }

                    if (!response.ok) {
                        throw new Error(`API error: ${response.status}`);
                    }

                    const data = (await response.json()) as SearchApiResponse;
                    if (abortController.signal.aborted) {
                        return;
                    }
                    setResults(data.results || []);
                    setError(null);
                } catch (err) {
                    // Ignore aborted requests (stale query or unmount)
                    if (isAbortError(err)) {
                        return;
                    }
                    console.error("Search API error:", err);
                    setResults([]);
                    setError(
                        err instanceof Error ? err.message : "Unknown error",
                    );
                } finally {
                    if (!abortController.signal.aborted) {
                        setLoading(false);
                    }
                }
            };

            void fetchData();
        }, debounceTime);

        // Cleanup: cancel debounce timer and in-flight fetch on query change/unmount
        return (): void => {
            clearTimeout(timerId);
            abortController.abort();
        };
    }, [query, debounceTime]); // Re-run effect when query or debounceTime changes

    return { results, loading, error };
};

export default useSearchApi;
