import { describe, it, expect, vi } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { HelpModal } from "../HelpModal";

describe("HelpModal Component", () => {
    it("renders correctly when show is true", () => {
        const handleHide = vi.fn();
        render(<HelpModal show={true} onHide={handleHide} />);

        // Check for modal title specifically in the modal header
        const modalTitle = screen.getByText("Musigree v2", {
            selector: ".modal-title",
        });
        expect(modalTitle).toBeInTheDocument();

        // Check for some content
        expect(
            screen.getByText(/is an interactive visualization/i),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/What do all of these symbols mean\?/i),
        ).toBeInTheDocument();

        // Check for close button
        expect(screen.getByText("Close")).toBeInTheDocument();
    });

    it("does not render modal content when show is false", () => {
        render(<HelpModal show={false} />);

        // Modal content should not be visible
        expect(
            screen.queryByText(/is an interactive visualization/i),
        ).not.toBeInTheDocument();
    });

    it("calls onHide when close button is clicked", async () => {
        const handleHide = vi.fn();
        const user = userEvent.setup();

        render(<HelpModal show={true} onHide={handleHide} />);

        // Click the footer close button specifically (the one with text "Close", not aria-label="Close")
        const footerCloseButton = screen.getByText("Close", {
            selector: "button.btn-secondary",
        });
        await user.click(footerCloseButton);

        // Check if onHide was called
        expect(handleHide).toHaveBeenCalledTimes(1);
    });

    it("has correct content about symbols", () => {
        render(<HelpModal show={true} />);

        // Check for specific content about symbols
        expect(
            screen.getByText(/Small circles represent artists./i),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Large circles represent bands./i),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Squares represent labels and other companies./i),
        ).toBeInTheDocument();
    });

    it("has links to external resources", () => {
        render(<HelpModal show={true} />);

        // Check for links to Discogs.com
        const discogsLinks = screen.getAllByText("Discogs.com");
        expect(discogsLinks.length).toBeGreaterThan(0);

        // Check for GitHub links (case-insensitive)
        const githubLinks = screen.getAllByText(/github/i);
        expect(githubLinks.length).toBeGreaterThan(0);
    });
});
