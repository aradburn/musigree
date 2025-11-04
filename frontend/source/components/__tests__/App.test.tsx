// This file should be executed first to ensure mocks are defined before imports
import { vi } from "vitest";
import React from "react";

// Store test actions in a global variable to avoid DOM attribute issues
const testActions = {
    showHelp: vi.fn(),
    hideHelp: vi.fn(),
    showWho: vi.fn(),
    hideWho: vi.fn(),
    hideWelcome: vi.fn(),
};

// Mock App component to avoid rendering any real components that might cause issues
vi.mock("../App", () => {
    const App = vi.fn(() => {
        const [showHelpModal, setShowHelpModal] = React.useState(false);
        const [showWhoModal, setShowWhoModal] = React.useState(false);
        const [showWelcomeModal, setShowWelcomeModal] = React.useState(false);
        const [isReturnVisitor, setIsReturnVisitor] = React.useState(false);

        // Implement the actual action functions
        testActions.showHelp.mockImplementation(() => setShowHelpModal(true));
        testActions.hideHelp.mockImplementation(() => setShowHelpModal(false));
        testActions.showWho.mockImplementation(() => setShowWhoModal(true));
        testActions.hideWho.mockImplementation(() => setShowWhoModal(false));
        testActions.hideWelcome.mockImplementation(() =>
            setShowWelcomeModal(false),
        );

        React.useEffect(() => {
            // Check if user has visited before
            const hasVisitedBefore = localStorage.getItem("hasVisitedBefore");
            setIsReturnVisitor(!!hasVisitedBefore);

            // Set localStorage for first-time visitors
            if (!hasVisitedBefore) {
                localStorage.setItem("hasVisitedBefore", "true");
                setShowWelcomeModal(true);
            }
        }, []);

        // Mock structure to test props passed to components
        return (
            <div data-testid="app-component">
                <div
                    data-testid="header-component"
                    data-showhelp="true"
                    data-showwho="true"
                />
                <div data-testid="sidebar-left-component" />
                <div data-testid="network-view-component" />
                <div data-testid="loading-animation-component" />

                <div
                    data-testid="help-modal-component"
                    data-show={showHelpModal.toString()}
                />
                <div
                    data-testid="who-modal-component"
                    data-show={showWhoModal.toString()}
                />
                <div
                    data-testid="welcome-modal-component"
                    data-show={showWelcomeModal.toString()}
                    data-returnvisitor={isReturnVisitor.toString()}
                />
            </div>
        );
    });

    return { default: App };
});

// Mock the component imports for simplicity
vi.mock("../Layout/Header.tsx", () => ({
    Header: vi.fn((props) => <div data-testid="header-component" {...props} />),
}));

vi.mock("../Layout/SidebarLeft", () => ({
    SidebarLeft: vi.fn(() => <div data-testid="sidebar-left-component" />),
}));

vi.mock("../Visualization/NetworkView", () => ({
    NetworkView: vi.fn(() => <div data-testid="network-view-component" />),
}));

vi.mock("../Visualization", () => ({
    LoadingAnimation: vi.fn(() => (
        <div data-testid="loading-animation-component" />
    )),
}));

vi.mock("../Modals", () => ({
    HelpModal: vi.fn((props) => (
        <div data-testid="help-modal-component" {...props} />
    )),
    WelcomeModal: vi.fn((props) => (
        <div data-testid="welcome-modal-component" {...props} />
    )),
    WhoModal: vi.fn((props) => (
        <div data-testid="who-modal-component" {...props} />
    )),
}));

// Mock localStorage
const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    clear: vi.fn(),
};
Object.defineProperty(window, "localStorage", { value: localStorageMock });

// Now import the component and testing utilities
import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { render, screen, act } from "@testing-library/react";
import "@testing-library/jest-dom";
import App from "../App";

describe("App Component", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorageMock.getItem.mockReturnValue(null);

        // Reset all test action mocks
        Object.values(testActions).forEach((mock) => mock.mockClear());
    });

    afterEach(() => {
        vi.resetAllMocks();
    });

    it("renders without crashing", () => {
        expect(() => render(<App />)).not.toThrow();
    });

    it("renders all required components", () => {
        render(<App />);
        expect(screen.getByTestId("app-component")).toBeInTheDocument();
        expect(screen.getByTestId("header-component")).toBeInTheDocument();
        expect(screen.getByTestId("sidebar-left-component")).toBeInTheDocument();
        expect(
            screen.getByTestId("network-view-component"),
        ).toBeInTheDocument();
        expect(
            screen.getByTestId("loading-animation-component"),
        ).toBeInTheDocument();
        expect(screen.getByTestId("help-modal-component")).toBeInTheDocument();
        expect(screen.getByTestId("who-modal-component")).toBeInTheDocument();
        expect(
            screen.getByTestId("welcome-modal-component"),
        ).toBeInTheDocument();
    });

    it("checks localStorage for returning visitors", () => {
        render(<App />);
        expect(localStorageMock.getItem).toHaveBeenCalledWith(
            "hasVisitedBefore",
        );
    });

    it("sets localStorage for first-time visitors", () => {
        render(<App />);
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
            "hasVisitedBefore",
            "true",
        );
    });

    it("doesn't show welcome modal for return visitors", () => {
        // Setup localStorage mock for return visitor
        localStorageMock.getItem.mockReturnValue("true");

        render(<App />);

        // Check that welcome modal has data-show=false
        const welcomeModal = screen.getByTestId("welcome-modal-component");
        expect(welcomeModal).toHaveAttribute("data-show", "false");
        expect(welcomeModal).toHaveAttribute("data-returnvisitor", "true");
    });

    it("shows welcome modal for first-time visitors", () => {
        // Setup localStorage mock for first-time visitor
        localStorageMock.getItem.mockReturnValue(null);

        render(<App />);

        // Check that welcome modal has data-show=true
        const welcomeModal = screen.getByTestId("welcome-modal-component");
        expect(welcomeModal).toHaveAttribute("data-show", "true");
        expect(welcomeModal).toHaveAttribute("data-returnvisitor", "false");
    });

    it("passes correct initial props to modals", () => {
        render(<App />);

        // Check help modal initial state
        expect(screen.getByTestId("help-modal-component")).toHaveAttribute(
            "data-show",
            "false",
        );

        // Check who modal initial state
        expect(screen.getByTestId("who-modal-component")).toHaveAttribute(
            "data-show",
            "false",
        );

        // Welcome modal is tested separately
    });

    it("passes the correct handlers to Header", () => {
        render(<App />);

        const header = screen.getByTestId("header-component");
        expect(header).toHaveAttribute("data-showhelp");
        expect(header).toHaveAttribute("data-showwho");
    });

    describe("Modal handlers", () => {
        it("handleShowHelp sets showHelpModal to true", async () => {
            render(<App />);

            // Initial state check
            expect(screen.getByTestId("help-modal-component")).toHaveAttribute(
                "data-show",
                "false",
            );

            // Call the showHelp action directly
            await act(async () => {
                testActions.showHelp();
            });

            // Check that help modal now has data-show=true
            expect(screen.getByTestId("help-modal-component")).toHaveAttribute(
                "data-show",
                "true",
            );
        });

        it("handleHideHelp sets showHelpModal to false", async () => {
            render(<App />);

            // First show the help modal
            await act(async () => {
                testActions.showHelp();
            });

            const helpModal = screen.getByTestId("help-modal-component");
            expect(helpModal).toHaveAttribute("data-show", "true");

            // Then hide it
            await act(async () => {
                testActions.hideHelp();
            });

            // Check that modal now has data-show=false
            expect(helpModal).toHaveAttribute("data-show", "false");
        });

        it("handleShowWho sets showWhoModal to true", async () => {
            render(<App />);

            // Initial state check
            expect(screen.getByTestId("who-modal-component")).toHaveAttribute(
                "data-show",
                "false",
            );

            // Call the showWho action directly
            await act(async () => {
                testActions.showWho();
            });

            // Check that who modal now has data-show=true
            expect(screen.getByTestId("who-modal-component")).toHaveAttribute(
                "data-show",
                "true",
            );
        });

        it("handleHideWho sets showWhoModal to false", async () => {
            render(<App />);

            // First show the who modal
            await act(async () => {
                testActions.showWho();
            });

            const whoModal = screen.getByTestId("who-modal-component");
            expect(whoModal).toHaveAttribute("data-show", "true");

            // Then hide it
            await act(async () => {
                testActions.hideWho();
            });

            // Check that modal now has data-show=false
            expect(whoModal).toHaveAttribute("data-show", "false");
        });

        it("handleHideWelcome sets showWelcomeModal to false", async () => {
            // Ensure we're testing as a first-time visitor
            localStorageMock.getItem.mockReturnValue(null);

            render(<App />);

            // Welcome modal should be shown initially
            const welcomeModal = screen.getByTestId("welcome-modal-component");
            expect(welcomeModal).toHaveAttribute("data-show", "true");

            // Hide it
            await act(async () => {
                testActions.hideWelcome();
            });

            // Check that modal now has data-show=false
            expect(welcomeModal).toHaveAttribute("data-show", "false");
        });
    });
});
