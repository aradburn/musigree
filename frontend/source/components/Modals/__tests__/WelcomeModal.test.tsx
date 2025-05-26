import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { WelcomeModal } from "../WelcomeModal";

describe("WelcomeModal Component", () => {
    it("should not render when isReturnVisitor is true", () => {
        // Render component with isReturnVisitor set to true
        render(<WelcomeModal show={true} isReturnVisitor={true} />);

        // Modal content should not be visible
        expect(
            screen.queryByText("Hello music lovers!"),
        ).not.toBeInTheDocument();
    });

    it("should not display content when show is false", () => {
        render(<WelcomeModal show={false} />);

        // Modal content should not be visible
        expect(
            screen.queryByText("Hello music lovers!"),
        ).not.toBeInTheDocument();
    });

    it("should render correctly when show is true", () => {
        render(<WelcomeModal show={true} />);

        // Check for modal title
        const modalTitle = screen.getByText("Hello music lovers!", {
            selector: ".modal-title",
        });
        expect(modalTitle).toBeInTheDocument();

        // Check for key content
        expect(screen.getByText(/Welcome to/i)).toBeInTheDocument();
        // Use getAllByText since "Musigree" appears multiple times
        const musigreeElements = screen.getAllByText(/Musigree/i);
        expect(musigreeElements.length).toBeGreaterThan(0);
        expect(screen.getByText(/based on data from the/i)).toBeInTheDocument();

        // Check for Start button
        expect(screen.getByText("Start")).toBeInTheDocument();
    });

    it("should display correct information about usage", () => {
        render(<WelcomeModal show={true} />);

        // Check for specific usage instructions
        expect(
            screen.getByText(/Use the search box in the right corner/i),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/click and drag the nodes around/i),
        ).toBeInTheDocument();
        expect(
            screen.getByText(/Double-click on any node/i),
        ).toBeInTheDocument();
    });

    it("should have links to external resources", () => {
        render(<WelcomeModal show={true} />);

        // Check for links to Discogs.com
        const discogsLinks = screen.getAllByText("Discogs.com");
        expect(discogsLinks.length).toBeGreaterThan(0);

        // Check attribution links
        expect(screen.getByText("Josiah Wolf Oberholtzer")).toBeInTheDocument();
        expect(screen.getByText("Andy Radburn")).toBeInTheDocument();

        // Check tool links
        expect(screen.getByText("Python 3")).toBeInTheDocument();
        expect(screen.getByText("D3")).toBeInTheDocument();
    });

    it("should call onHide when close button is clicked", async () => {
        const handleHide = vi.fn();
        const user = userEvent.setup();

        render(<WelcomeModal show={true} onHide={handleHide} />);

        // Find and click the close button in the header
        const closeButton = screen.getByLabelText("Close");
        await user.click(closeButton);

        // Check if onHide was called
        expect(handleHide).toHaveBeenCalledTimes(1);
    });

    it("should call onHide when Start button is clicked", async () => {
        const handleHide = vi.fn();
        const user = userEvent.setup();

        render(<WelcomeModal show={true} onHide={handleHide} />);

        // Find and click the Start button
        const startButton = screen.getByText("Start");
        await user.click(startButton);

        // Check if onHide was called
        expect(handleHide).toHaveBeenCalledTimes(1);
    });
});
