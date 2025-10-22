import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import SearchResult from "../SearchResult";
import type { SearchResult as SearchResultType } from "../hooks/useSearchApi";

describe("SearchResult", () => {
    // Mock data for tests
    const mockResult: SearchResultType = {
        name: "Test Artist",
        key: "a-12345",
    };

    it("renders correctly with result name", () => {
        const mockOnClick = vi.fn();

        render(<SearchResult result={mockResult} onClick={mockOnClick} />);

        // Check if the result name is displayed
        expect(screen.getByText("Test Artist")).toBeInTheDocument();
    });

    it("displays the correct entity type extracted from key", () => {
        const mockOnClick = vi.fn();

        render(<SearchResult result={mockResult} onClick={mockOnClick} />);

        // Key "a-12345" should extract entity type "a"
        expect(screen.getByText("(a)")).toBeInTheDocument();
    });

    it("applies active styling when active prop is true", () => {
        const mockOnClick = vi.fn();

        const { container } = render(
            <SearchResult
                result={mockResult}
                onClick={mockOnClick}
                active={true}
            />,
        );

        // Check if the bg-success-subtle class is applied when active=true
        const resultDiv = container.firstChild as HTMLElement;
        expect(resultDiv).toHaveClass("bg-success-subtle");
    });

    it("does not apply active styling when active prop is false", () => {
        const mockOnClick = vi.fn();

        const { container } = render(
            <SearchResult
                result={mockResult}
                onClick={mockOnClick}
                active={false}
            />,
        );

        // Check if the bg-light class is applied when active=false
        const resultDiv = container.firstChild as HTMLElement;
        expect(resultDiv).toHaveClass("bg-light");
    });

    it("calls onClick handler when clicked", () => {
        const mockOnClick = vi.fn();

        render(<SearchResult result={mockResult} onClick={mockOnClick} />);

        // Click on the result div
        fireEvent.click(screen.getByText("Test Artist"));

        // Verify that onClick was called with the result
        expect(mockOnClick).toHaveBeenCalledTimes(1);
        expect(mockOnClick).toHaveBeenCalledWith(mockResult);
    });

    it("has correct accessibility attributes", () => {
        const mockOnClick = vi.fn();

        const { container } = render(
            <SearchResult
                result={mockResult}
                onClick={mockOnClick}
                active={true}
            />,
        );

        // Check correct accessibility attributes
        const resultDiv = container.firstChild as HTMLElement;
        expect(resultDiv).toHaveAttribute("role", "option");
        expect(resultDiv).toHaveAttribute("aria-selected", "true");
    });

    it("has correct accessibility attributes when not active", () => {
        const mockOnClick = vi.fn();

        const { container } = render(
            <SearchResult
                result={mockResult}
                onClick={mockOnClick}
                active={false}
            />,
        );

        // Check correct accessibility attributes
        const resultDiv = container.firstChild as HTMLElement;
        expect(resultDiv).toHaveAttribute("role", "option");
        expect(resultDiv).toHaveAttribute("aria-selected", "false");
    });
});
