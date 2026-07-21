import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import type { ReactNode } from "react";
import { render, screen, fireEvent, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { Header } from "../Header";
import { FSM } from "../../../constants";
import { WindowProvider } from "../../../contexts/WindowContext";

// Mock SearchInput component (direct import path)
vi.mock("../../Search/SearchInput", () => ({
    default: vi.fn().mockImplementation(({ placeholder, className }) => (
        <div data-testid="mock-search-input" className={className}>
            {placeholder}
        </div>
    )),
}));

// Mock dependencies for WindowProvider
vi.mock("debounce", () => ({
    default: vi.fn((fn) => fn),
}));

vi.mock("../../../core/singletons", () => ({
    musigreeManager: {
        dpr: 1,
        dimensions: [0, 0],
        svgDimensions: [0, 0],
        setIsMobileGetter: vi.fn(),
    },
}));

vi.mock("../../../network/init", () => ({
    resetNetworkTransform: vi.fn(),
}));

vi.mock("@/svg", () => ({
    setSvgSize: vi.fn(),
}));

vi.mock("../../../network/events", () => ({
    ResizeEvent: vi.fn().mockImplementation(function () {
        return {
            type: "musigree:resize",
            bubbles: true,
            detail: {},
        };
    }),
}));

// Mock react-bootstrap subpath imports (direct imports for tree-shaking)
vi.mock("react-bootstrap/Navbar", () => ({
    default: ({
        children,
        className,
    }: {
        children: ReactNode;
        className?: string;
    }) => (
        <nav data-testid="navbar" className={className}>
            {children}
        </nav>
    ),
}));

vi.mock("react-bootstrap/Container", () => ({
    default: ({
        children,
        fluid,
    }: {
        children: ReactNode;
        fluid?: boolean;
    }) => (
        <div
            data-testid="container"
            className={fluid ? "container-fluid" : "container"}
        >
            {children}
        </div>
    ),
}));

vi.mock("react-bootstrap/OverlayTrigger", () => ({
    default: ({
        children,
        overlay,
    }: {
        children: ReactNode;
        overlay: { props: { children: ReactNode } };
    }) => (
        <div data-testid="overlay-trigger">
            {children}
            <div data-testid="tooltip-content">{overlay.props.children}</div>
        </div>
    ),
}));

vi.mock("react-bootstrap/Tooltip", () => ({
    default: ({ id, children }: { id?: string; children: ReactNode }) => (
        <div data-testid={`tooltip-${id}`}>{children}</div>
    ),
}));

describe("Header Component", () => {
    // Setup mocks for window and document
    const originalAddEventListener = window.addEventListener;
    const originalRemoveEventListener = window.removeEventListener;
    const originalDispatchEvent = window.dispatchEvent;
    const originalDevicePixelRatio = window.devicePixelRatio;
    const originalConsoleError = console.error;
    const mockSvgContainer = document.createElement("div");
    mockSvgContainer.id = "svg-container-fluid";
    mockSvgContainer.style.width = "1024px";
    mockSvgContainer.style.height = "768px";

    // Setup and teardown
    beforeEach(() => {
        // Reset mocks
        vi.clearAllMocks();

        // Mock window methods
        window.addEventListener = vi.fn();
        window.removeEventListener = vi.fn();
        window.dispatchEvent = vi.fn();
        Object.defineProperty(window, "devicePixelRatio", {
            value: 2,
            configurable: true,
        });
        Object.defineProperty(window, "innerWidth", {
            value: 1024,
            configurable: true,
        });

        // Mock console.error
        console.error = vi.fn();

        // Mock document.getElementById
        vi.spyOn(document, "getElementById").mockImplementation((id) => {
            if (id === "svg-container-fluid") {
                return mockSvgContainer;
            }
            return null;
        });

        // Mock getBoundingClientRect for SVG container
        mockSvgContainer.getBoundingClientRect = vi.fn().mockReturnValue({
            width: 1024,
            height: 768,
        });

        // Mock clientWidth and clientHeight with configurable: true
        Object.defineProperty(mockSvgContainer, "clientWidth", {
            value: 1024,
            configurable: true,
        });
        Object.defineProperty(mockSvgContainer, "clientHeight", {
            value: 768,
            configurable: true,
        });

        // Mock document.dispatchEvent
        vi.spyOn(document, "dispatchEvent").mockImplementation(vi.fn());
    });

    afterEach(() => {
        // Restore original methods
        window.addEventListener = originalAddEventListener;
        window.removeEventListener = originalRemoveEventListener;
        window.dispatchEvent = originalDispatchEvent;
        Object.defineProperty(window, "devicePixelRatio", {
            value: originalDevicePixelRatio,
            configurable: true,
        });
        console.error = originalConsoleError;

        vi.restoreAllMocks();
    });

    it("renders correctly with all elements", () => {
        const { container } = render(
            <WindowProvider>
                <Header />
            </WindowProvider>,
        );

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
        render(
            <WindowProvider>
                <Header onShowHelp={mockOnShowHelp} />
            </WindowProvider>,
        );

        // Find the help button by its text and closest div with role="button"
        const helpText = screen.getByText("HELP");
        const helpButton = helpText.closest('div[role="button"]');

        expect(helpButton).not.toBeNull();
        await user.click(helpButton);

        expect(mockOnShowHelp).toHaveBeenCalledTimes(1);
    });

    it("dispatches REQUEST_RANDOM event when random button is clicked", async () => {
        const user = userEvent.setup();
        render(
            <WindowProvider>
                <Header />
            </WindowProvider>,
        );

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
        render(
            <WindowProvider>
                <Header />
            </WindowProvider>,
        );

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
