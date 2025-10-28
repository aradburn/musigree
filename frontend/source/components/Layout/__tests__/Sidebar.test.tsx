import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { SidebarLeft } from "../SidebarLeft";

// Mock dependencies
vi.mock("../../../print", () => ({
    printSvg: vi.fn(),
}));

vi.mock("../../../core", () => ({
    musigreeManager: {
        svgDimensions: [800, 600],
    },
}));

// Mock ForceControls component
vi.mock("../../Visualization/ForceControls", () => ({
    default: vi
        .fn()
        .mockImplementation(() => (
            <div data-testid="mock-force-controls">ForceControls Mock</div>
        )),
}));

// Import after mocking
import { printSvg } from "../../../print";
import { musigreeManager } from "../../../core";

describe("SidebarLeft Component", () => {
    beforeEach(() => {
        // Clear all mocks before each test
        vi.clearAllMocks();

        // Mock window.dispatchEvent
        vi.spyOn(window, "dispatchEvent").mockImplementation(vi.fn());
    });

    afterEach(() => {
        // Restore mocks after each test
        vi.restoreAllMocks();
    });

    it("renders correctly with all expected elements", () => {
        render(<SidebarLeft />);

        // Check if the sidebar container is rendered
        const sidebarLeft = screen
            .getByRole("button", { name: /details/i })
            .closest(".sidebar");
        expect(sidebarLeft).toBeInTheDocument();

        // Check if all buttons are rendered with correct text
        expect(
            screen.getByRole("button", { name: /details/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /roles/i }),
        ).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: /print/i }),
        ).toBeInTheDocument();

        // Check if ForceControls component is rendered
        expect(screen.getByTestId("mock-force-controls")).toBeInTheDocument();
    });

    it("dispatches custom event when Details button is clicked", async () => {
        const user = userEvent.setup();
        render(<SidebarLeft />);

        // Click the Details button
        await user.click(screen.getByRole("button", { name: /details/i }));

        // Check if the correct custom event was dispatched
        expect(window.dispatchEvent).toHaveBeenCalledTimes(1);

        // Get the first call argument (the event)
        const dispatchedEvent = vi.mocked(window.dispatchEvent).mock
            .calls[0][0];
        expect(dispatchedEvent).toBeInstanceOf(CustomEvent);
        expect(dispatchedEvent.type).toBe(
            "musigree:show-entity-details-overlay",
        );
    });

    it("dispatches custom event when Roles button is clicked", async () => {
        const user = userEvent.setup();
        render(<SidebarLeft />);

        // Click the Roles button
        await user.click(screen.getByRole("button", { name: /roles/i }));

        // Check if the correct custom event was dispatched
        expect(window.dispatchEvent).toHaveBeenCalledTimes(1);

        // Get the first call argument (the event)
        const dispatchedEvent = vi.mocked(window.dispatchEvent).mock
            .calls[0][0];
        expect(dispatchedEvent).toBeInstanceOf(CustomEvent);
        expect(dispatchedEvent.type).toBe("musigree:show-roles-overlay");
    });

    it("calls printSvg function when Print button is clicked", async () => {
        const user = userEvent.setup();
        render(<SidebarLeft />);

        // Click the Print button
        await user.click(screen.getByRole("button", { name: /print/i }));

        // Check if printSvg was called with the correct arguments
        expect(printSvg).toHaveBeenCalledTimes(1);
        expect(printSvg).toHaveBeenCalledWith(
            musigreeManager.svgDimensions[0],
            musigreeManager.svgDimensions[1],
        );
    });

    it("renders with appropriate Bootstrap classes for responsive layout", () => {
        render(<SidebarLeft />);

        // Check if the sidebar has the expected Bootstrap classes
        const sidebarLeft = screen
            .getByRole("button", { name: /details/i })
            .closest(".sidebar");
        expect(sidebarLeft).toHaveClass("d-flex");
        expect(sidebarLeft).toHaveClass("h-100");
        expect(sidebarLeft).toHaveClass("flex-sm-column");
        expect(sidebarLeft).toHaveClass("bg-secondary-subtle");

        // Check if the buttons have responsive text classes
        const detailsButton = screen.getByRole("button", { name: /details/i });
        const detailsText = detailsButton.querySelector("span");
        expect(detailsText).toHaveClass("d-none");
        expect(detailsText).toHaveClass("d-sm-inline");
    });
});
