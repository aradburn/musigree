/** @jsxImportSource react */
import React from "react";
import type { SearchResult as SearchResultType } from "./hooks/useSearchApi";

interface SearchResultProps {
    result: SearchResultType;
    onClick: (result: SearchResultType) => void;
    active?: boolean;
}

/**
 * Component for rendering an individual search result
 */
const SearchResult: React.FC<SearchResultProps> = ({
    result,
    onClick,
    active = false,
}): React.ReactElement => {
    const entityType = result.key.split("-")[0];

    const handleClick = (): void => {
        onClick(result);
    };

    return (
        <div
            className={`search-result d-flex justify-content-between align-items-center px-3 py-2 cursor-pointer ${active ? "bg-success-subtle" : "bg-light"}`}
            onClick={handleClick}
            role="option"
            aria-selected={active}
        >
            <span className="text-truncate">{result.name}</span>
            <span className="text-muted small ms-2">({entityType})</span>
        </div>
    );
};

export default SearchResult;
