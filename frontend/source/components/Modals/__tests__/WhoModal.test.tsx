import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { WhoModal } from "../WhoModal";

describe("WhoModal Component", () => {
    it("should not display content when show is false (default)", () => {
        render(<WhoModal />);

        // Modal content should not be visible
        expect(screen.queryByText("Who made this?")).not.toBeInTheDocument();
    });

    it("should render correctly when show is true", () => {
        render(<WhoModal show={true} />);

        // Check for modal title
        const modalTitle = screen.getByText("Who made this?", {
            selector: ".modal-title",
        });
        expect(modalTitle).toBeInTheDocument();

        // Check for some key content
        expect(
            screen.getByText(/Originally made in 2015 by/i),
        ).toBeInTheDocument();
        expect(screen.getByText(/Updated 2023 by/i)).toBeInTheDocument();
    });

    it("should display correct information about creators", () => {
        render(<WhoModal show={true} />);

        // Check for creator information
        expect(screen.getByText("Josiah Wolf Oberholtzer")).toBeInTheDocument();
        expect(screen.getByText("Andy Radburn")).toBeInTheDocument();
    });

    it("should have links to tools and resources", () => {
        render(<WhoModal show={true} />);

        // Check for links to tools
        expect(screen.getByText("Python 3")).toBeInTheDocument();
        expect(screen.getByText("D3")).toBeInTheDocument();
        expect(screen.getByText("Bootstrap CSS")).toBeInTheDocument();

        // Check for Discogs link - using getAllByText since it appears multiple times
        const discogsLinks = screen.getAllByText("Discogs.com");
        expect(discogsLinks.length).toBeGreaterThan(0);
    });

    it("should call onHide when close button in header is clicked", async () => {
        const handleHide = vi.fn();
        const user = userEvent.setup();

        render(<WhoModal show={true} onHide={handleHide} />);

        // Find and click the close button in the header
        const closeButton = screen.getByLabelText("Close");
        await user.click(closeButton);

        // Check if onHide was called
        expect(handleHide).toHaveBeenCalledTimes(1);
    });

    it("should call onHide when Close button in footer is clicked", async () => {
        const handleHide = vi.fn();
        const user = userEvent.setup();

        render(<WhoModal show={true} onHide={handleHide} />);

        // Find and click the Close button in the footer
        const closeButton = screen.getByText("Close", { selector: "button" });
        await user.click(closeButton);

        // Check if onHide was called
        expect(handleHide).toHaveBeenCalledTimes(1);
    });
});
