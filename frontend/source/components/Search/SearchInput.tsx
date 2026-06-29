/** @jsxImportSource react */
import React, {useCallback, useEffect, useRef, useState} from "react";
import {Form, Overlay, Popover, Spinner} from "react-bootstrap";
import {TYPEAHEAD} from "@/constants.ts";
import type {SearchResult as SearchResultType} from "./hooks/useSearchApi";
import useSearchApi from "./hooks/useSearchApi";
import SearchResult from "./SearchResult";
import {RequestNetworkEvent} from "@/network/events.ts";

interface SearchInputProps {
    placeholder?: string;
    className?: string;
}

/**
 * SearchInput component with typeahead functionality
 * This replaces the jQuery-based typeahead implementation
 */
const SearchInput: React.FC<SearchInputProps> = ({
                                                     placeholder = "Search",
                                                     className = "",
                                                 }): React.ReactElement => {
    const [query, setQuery] = useState<string>("");
    const [showResults, setShowResults] = useState<boolean>(false);
    const [selectedIndex, setSelectedIndex] = useState<number>(-1);

    const inputRef = useRef<HTMLInputElement>(null);
    const popoverRef = useRef<HTMLDivElement>(null);
    const pendingEnterRef = useRef(false);

    // Use our custom hook to fetch search results
    const {results, loading, error} = useSearchApi(query);

    const selectResult = useCallback((result: SearchResultType): void => {
        setQuery(result.name);
        setShowResults(false);
        setSelectedIndex(-1);
        pendingEnterRef.current = false;

        // Trigger network event similar to jQuery implementation
        if (result.key) {
            const pushHistory = true;
            window.dispatchEvent(
                new RequestNetworkEvent(result.key, pushHistory),
            );
        }
    }, []);

    const actionTopResult = useCallback((): void => {
        if (results.length === 0) return;
        setSelectedIndex(0);
        selectResult(results[0]);
    }, [results, selectResult]);

    // Complete a deferred Enter once the in-flight search finishes
    useEffect(() => {
        if (!pendingEnterRef.current || loading) return;

        pendingEnterRef.current = false;
        if (results.length > 0) {
            setSelectedIndex(0);
            selectResult(results[0]);
        }
    }, [loading, results, selectResult]);

    // Close the results dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent): void => {
            if (
                popoverRef.current &&
                !popoverRef.current.contains(event.target as Node) &&
                inputRef.current &&
                !inputRef.current.contains(event.target as Node)
            ) {
                setShowResults(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return (): void => {
            document.removeEventListener("mousedown", handleClickOutside);
        };
    }, []);

    // Handle input changes
    const handleInputChange = (
        event: React.ChangeEvent<HTMLInputElement>,
    ): void => {
        const value = event.target.value;
        setQuery(value);
        setSelectedIndex(-1); // Reset selection on input change
        pendingEnterRef.current = false;

        if (value.length >= TYPEAHEAD.MIN_QUERY_LENGTH) {
            setShowResults(true);
        } else {
            setShowResults(false);
        }
    };

    // Handle keyboard navigation
    const handleKeyDown = (
        event: React.KeyboardEvent<HTMLInputElement>,
    ): void => {
        if (event.key === "Enter") {
            if (query.length < TYPEAHEAD.MIN_QUERY_LENGTH) return;

            event.preventDefault();
            setShowResults(true);

            if (loading) {
                pendingEnterRef.current = true;
                return;
            }

            actionTopResult();
            return;
        }

        if (!showResults || results.length === 0) return;

        // Arrow down
        if (event.key === "ArrowDown") {
            event.preventDefault();
            setSelectedIndex((prev) =>
                prev < results.length - 1 ? prev + 1 : prev,
            );
        }

        // Arrow up
        else if (event.key === "ArrowUp") {
            event.preventDefault();
            setSelectedIndex((prev) => (prev > 0 ? prev - 1 : 0));
        }

        // Escape key
        else if (event.key === "Escape") {
            event.preventDefault();
            pendingEnterRef.current = false;
            setShowResults(false);
        }
    };

    // Handle clear button click
    const handleClearClick = (): void => {
        setQuery("");
        setShowResults(false);
        setSelectedIndex(-1);
        pendingEnterRef.current = false;

        if (inputRef.current) {
            inputRef.current.focus();
        }
    };

    return (
        <div className={`${className}`}>
            <Form className="container-fluid">
                <div
                    className="input-group flex-nowrap border border-secondary">
                    <span
                        className="bg-light-subtle opacity-50 input-group-text px-2 py-0">
                        {loading ? (
                            <Spinner
                                as="span"
                                animation="border"
                                size="sm"
                                role="status"
                                aria-hidden="true"
                            />
                        ) : (
                            <i className="bi bi-search"></i>
                        )}
                    </span>

                    <Form.Control
                        id="musigree-search"
                        className="rounded-0 px-2 py-1"
                        ref={inputRef}
                        type="search"
                        placeholder={placeholder}
                        value={query}
                        onChange={handleInputChange}
                        onKeyDown={handleKeyDown}
                        onFocus={() => {
                            if (query.length >= TYPEAHEAD.MIN_QUERY_LENGTH) {
                                setShowResults(true);
                            }
                        }}
                        autoComplete="off"
                        aria-autocomplete="list"
                        aria-controls="search-results"
                        aria-expanded={showResults}
                    />

                    {query ? (
                        <span
                            className="clear bg-light-subtle opacity-50 input-group-text px-2 py-0"
                            role="button"
                            onClick={handleClearClick}
                            aria-label="Clear search"
                        >
                            <i className="bi bi-backspace"></i>
                        </span>
                    ) : null}
                </div>
            </Form>

            <Overlay
                show={showResults}
                target={inputRef.current}
                placement="bottom"
                container={document.body}
                rootClose
                //                 onHide={() => setShowResults(false)}
            >
                <Popover
                    id="search-results"
                    style={{minWidth: inputRef.current?.offsetWidth}}
                    ref={popoverRef}
                >
                    <Popover.Body className="search-results-body p-0">
                        {loading ? (
                            <div className="d-flex justify-content-center p-3">
                                <Spinner
                                    animation="border"
                                    role="status"
                                    size="sm"
                                >
                                    <span className="visually-hidden">
                                        Loading...
                                    </span>
                                </Spinner>
                                <span className="ms-2">Loading...</span>
                            </div>
                        ) : null}

                        {error ? (
                            <div className="text-danger p-3">
                                Error: {error}
                            </div>
                        ) : null}

                        {!loading &&
                        !error &&
                        results.length === 0 &&
                        query.length >= TYPEAHEAD.MIN_QUERY_LENGTH ? (
                            <div className="p-3">
                                No results found for "{query}"
                            </div>
                        ) : null}

                        {!loading && !error && results.length > 0 ? (
                            <div
                                role="listbox"
                                className="list-group list-group-flush"
                            >
                                {results.map((result, index) => (
                                    <SearchResult
                                        key={result.key}
                                        result={result}
                                        onClick={selectResult}
                                        active={index === selectedIndex}
                                    />
                                ))}
                            </div>
                        ) : null}
                    </Popover.Body>
                </Popover>
            </Overlay>
        </div>
    );
};

export default SearchInput;
