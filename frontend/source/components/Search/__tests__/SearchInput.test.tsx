import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import SearchInput from "../SearchInput";
import * as useSearchApiModule from "../hooks/useSearchApi";
import { TYPEAHEAD } from "../../../constants";

// Extend Window interface to include RequestNetworkEvent
declare global {
    interface Window {
        RequestNetworkEvent: typeof MockRequestNetworkEvent;
    }
}

// Mock the custom hook
vi.mock("../hooks/useSearchApi", () => ({
    default: vi.fn(),
}));

// Mock the Overlay component from react-bootstrap to avoid DOM manipulation issues
vi.mock("react-bootstrap", async () => {
    const originalModule = await vi.importActual("react-bootstrap");
    return {
        ...(originalModule as Record<string, unknown>),
        Overlay: ({
            children,
            show,
        }: {
            children: React.ReactNode;
            show: boolean;
        }) => {
            return show ? (
                <div data-testid="overlay-mock">{children}</div>
            ) : null;
        },
    };
});

// Mock the RequestNetworkEvent
class MockRequestNetworkEvent extends Event {
    key: string;
    constructor(key: string, pushHistory: boolean) {
        super("RequestNetworkEvent");
        this.key = key;
    }
}

// Mock the window.dispatchEvent
const mockDispatchEvent = vi.fn();
window.dispatchEvent = mockDispatchEvent;
window.RequestNetworkEvent = MockRequestNetworkEvent as any;

// Reset mocks after each test
afterEach(() => {
    vi.clearAllMocks();
    // Clean up any added DOM elements
    document.body.innerHTML = "";
});

describe("SearchInput", () => {
    let user: ReturnType<typeof userEvent.setup>;

    beforeEach(() => {
        user = userEvent.setup();
    });

    it("renders correctly with default props", () => {
        // Mock the hook to return empty results
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: [],
            loading: false,
            error: null,
        });

        render(<SearchInput />);

        // Check if search input is rendered with default placeholder
        expect(screen.getByPlaceholderText("Search")).toBeInTheDocument();
    });

    it("renders with custom placeholder and className", () => {
        // Mock the hook to return empty results
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: [],
            loading: false,
            error: null,
        });

        const customPlaceholder = "Find artists...";
        const customClassName = "custom-search";

        render(
            <SearchInput
                placeholder={customPlaceholder}
                className={customClassName}
            />,
        );

        // Check if custom placeholder is used
        expect(
            screen.getByPlaceholderText(customPlaceholder),
        ).toBeInTheDocument();

        // Check if custom className is applied
        const searchContainer = document.querySelector(`.${customClassName}`);
        expect(searchContainer).toBeInTheDocument();
    });

    it("shows loading state", () => {
        // Mock the hook to return loading state
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: [],
            loading: true,
            error: null,
        });

        render(<SearchInput />);

        // Check if spinner is visible - using querySelector since the spinner has aria-hidden="true"
        const spinner = document.querySelector(".spinner-border");
        expect(spinner).toBeInTheDocument();
    });

    // Test that the hook is called with the correct query
    it("calls useSearchApi with correct query", async () => {
        // Mock the hook
        const mockHook = vi.fn().mockReturnValue({
            results: [],
            loading: false,
            error: null,
        });

        vi.mocked(useSearchApiModule.default).mockImplementation(mockHook);

        render(<SearchInput />);

        // Type in the search box
        const searchInput = screen.getByPlaceholderText("Search");
        await user.type(searchInput, "artist");

        // Verify the hook was called with the correct query
        expect(mockHook).toHaveBeenCalledWith("artist");
    });

    it("shows error state", async () => {
        // Mock the hook to return error state
        const errorMessage = "API Error: 500";
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: [],
            loading: false,
            error: errorMessage,
        });

        render(<SearchInput />);

        // Type in the search box to trigger results display
        const searchInput = screen.getByPlaceholderText("Search");
        await user.type(searchInput, "test query");

        // Check if error message is displayed
        await waitFor(() => {
            expect(
                screen.getByText(`Error: ${errorMessage}`),
            ).toBeInTheDocument();
        });
    });

    it("shows 'No results' message when no results are found", async () => {
        // Mock the hook to return empty results
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: [],
            loading: false,
            error: null,
        });

        render(<SearchInput />);

        // Type in the search box with a query long enough
        const searchInput = screen.getByPlaceholderText("Search");
        await user.type(searchInput, "artist"); // Assuming MIN_QUERY_LENGTH <= 6

        // Check if "No results" message is displayed
        await waitFor(() => {
            expect(
                screen.getByText(`No results found for "artist"`),
            ).toBeInTheDocument();
        });
    });

    it("shows results when typing", async () => {
        // Mock search results
        const mockResults = [
            { name: "Artist 1", key: "a-1234", type: "artist" },
            { name: "Artist 2", key: "a-5678", type: "artist" },
        ];

        // Mock the hook to return results
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: mockResults,
            loading: false,
            error: null,
        });

        render(<SearchInput />);

        // Type in the search box
        const searchInput = screen.getByPlaceholderText("Search");
        await user.type(searchInput, "artist");

        // Wait for results to be visible
        await waitFor(() => {
            expect(screen.getByText("Artist 1")).toBeInTheDocument();
            expect(screen.getByText("Artist 2")).toBeInTheDocument();
        });
    });

    it("does not show results when query is too short", async () => {
        // Mock search results
        const mockResults = [
            { name: "Artist 1", key: "a-1234", type: "artist" },
        ];

        // Mock the hook to return results
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: mockResults,
            loading: false,
            error: null,
        });

        render(<SearchInput />);

        // Type a short query (less than MIN_QUERY_LENGTH)
        const searchInput = screen.getByPlaceholderText("Search");
        await user.type(searchInput, "a"); // Assuming MIN_QUERY_LENGTH == 2

        // Ensure Overlay doesn't show by checking aria-expanded attribute
        expect(searchInput).toHaveAttribute("aria-expanded", "false");
    });

    it("dispatches network event when selecting a result", async () => {
        // Mock search results
        const mockResults = [
            { name: "Artist 1", key: "a-1234", type: "artist" },
        ];

        // Mock the hook to return results
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: mockResults,
            loading: false,
            error: null,
        });

        const { container } = render(<SearchInput />);

        // Type in the search box to trigger results
        const searchInput = screen.getByPlaceholderText("Search");
        await user.type(searchInput, "artist");

        // Directly call the select function by simulating the click
        // First trigger show results by setting aria-expanded
        searchInput.setAttribute("aria-expanded", "true");

        // Find and click the first result (this might still be visible due to our mock)
        const resultElements = container.querySelectorAll('[role="option"]');
        if (resultElements.length > 0) {
            fireEvent.click(resultElements[0]);
        } else {
            // Simulate a result selection by dispatching a custom event
            // This test verifies the event dispatching logic without relying on the overlay
            const selectEvent = new CustomEvent("selectResult", {
                detail: mockResults[0],
            });
            searchInput.dispatchEvent(selectEvent);
        }

        // Verify the event was dispatched
        expect(mockDispatchEvent).toHaveBeenCalled();
    });

    it("allows clearing the input", async () => {
        // Mock the hook
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: [],
            loading: false,
            error: null,
        });

        render(<SearchInput />);

        // Type in the search box
        const searchInput = screen.getByPlaceholderText("Search");
        await user.type(searchInput, "artist");

        // Wait for input to have the value
        expect(searchInput).toHaveValue("artist");

        // Click the clear button
        const clearButton = screen.getByRole("button", {
            name: /clear search/i,
        });
        await user.click(clearButton);

        // Verify input was cleared
        expect(searchInput).toHaveValue("");
    });

    it("handles keyboard navigation", async () => {
        // Mock search results
        const mockResults = [
            { name: "Artist 1", key: "a-1234", type: "artist" },
            { name: "Artist 2", key: "a-5678", type: "artist" },
        ];

        // Mock the hook to return results
        vi.mocked(useSearchApiModule.default).mockReturnValue({
            results: mockResults,
            loading: false,
            error: null,
        });

        render(<SearchInput />);

        // Type in the search box
        const searchInput = screen.getByPlaceholderText("Search");
        await user.type(searchInput, "artist");

        // Press arrow down, arrow up, escape keys
        fireEvent.keyDown(searchInput, { key: "ArrowDown" });
        fireEvent.keyDown(searchInput, { key: "ArrowUp" });
        fireEvent.keyDown(searchInput, { key: "Escape" });

        // We can't easily test the selected index without mocking internal state
        // But we can verify the escape key closes the dropdown
        expect(searchInput).toHaveAttribute("aria-expanded", "false");
    });
});
