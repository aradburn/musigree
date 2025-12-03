import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { Header } from "../Header";
import { FSM } from "../../../constants";

// Mock SearchInput component
vi.mock("../../Search", () => ({
    SearchInput: vi.fn().mockImplementation(({ placeholder, className }) => (
        <div data-testid="mock-search-input" className={className}>
            {placeholder}
        </div>
    )),
}));

// We need to mock react-bootstrap to handle OverlayTrigger and Tooltip
vi.mock("react-bootstrap", () => {
    return {
        Navbar: ({ children, className }) => (
            <nav data-testid="navbar" className={className}>
                {children}
            </nav>
        ),
        Container: ({ children, fluid }) => (
            <div
                data-testid="container"
                className={fluid ? "container-fluid" : "container"}
            >
                {children}
            </div>
        ),
        OverlayTrigger: ({ children, overlay }) => (
            <div data-testid="overlay-trigger">
                {children}
                <div data-testid="tooltip-content">
                    {overlay.props.children}
                </div>
            </div>
        ),
        Tooltip: ({ id, children }) => (
            <div data-testid={`tooltip-${id}`}>{children}</div>
        ),
    };
});

describe("Header Component", () => {
    // Setup and teardown
    beforeEach(() => {
        // Mock document.dispatchEvent
        vi.spyOn(document, "dispatchEvent").mockImplementation(vi.fn());
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("renders correctly with all elements", () => {
        const { container } = render(<Header />);

        // Debug output to see what's rendered
        // console.log(container.innerHTML);

        // Check brand section
        expect(screen.getByText("MUSIGREE")).toBeInTheDocument();

        // Check search section
        expect(screen.getByTestId("mock-search-input")).toBeInTheDocument();
        expect(screen.getByTestId("mock-search-input")).toHaveTextContent(
            "Search for artists, labels, etc.",
        );

        // Check random button
        expect(screen.getByText("RANDOM")).toBeInTheDocument();

        // Check help button
        expect(screen.getByText("HELP")).toBeInTheDocument();
    });

    it("calls onShowHelp callback when help button is clicked", async () => {
        const mockOnShowHelp = vi.fn();
        const user = userEvent.setup();
        render(<Header onShowHelp={mockOnShowHelp} />);

        // Find the help button by its text and closest div with role="button"
        const helpText = screen.getByText("HELP");
        const helpButton = helpText.closest('div[role="button"]');

        expect(helpButton).not.toBeNull();
        await user.click(helpButton);

        expect(mockOnShowHelp).toHaveBeenCalledTimes(1);
    });

    it("dispatches REQUEST_RANDOM event when random button is clicked", async () => {
        const user = userEvent.setup();
        render(<Header />);

        // Find the random button by its text and closest div with role="button"
        const randomText = screen.getByText("RANDOM");
        const randomButton = randomText.closest('div[role="button"]');

        expect(randomButton).not.toBeNull();
        await user.click(randomButton);

        // Check that the correct custom event was dispatched
        expect(document.dispatchEvent).toHaveBeenCalledTimes(1);

        // Check that the event was created with the correct type and options
        const mockCalls = vi.mocked(document.dispatchEvent).mock.calls;
        expect(mockCalls[0][0].type).toBe(FSM.EVENTS.REQUEST_RANDOM);
        expect(mockCalls[0][0].bubbles).toBe(true);
    });

    it("renders tooltips correctly", () => {
        render(<Header />);

        // Check tooltip contents
        const tooltipContents = screen.getAllByTestId("tooltip-content");
        expect(tooltipContents.length).toBeGreaterThan(0);

        // Extract all tooltip texts
        const tooltipTexts = tooltipContents.map((el) => el.textContent);

        // Check for expected tooltip texts
        expect(tooltipTexts).toContain("Choose a random artist");
        expect(tooltipTexts).toContain("Help");
    });
});
