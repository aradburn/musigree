/** @jsxImportSource react */
import { describe, it, expect, vi } from "vitest";
import {
    WindowContext,
    type WindowContextProps,
    type WindowState,
} from "../windowContextInstance";
import { useContext, FC, ReactNode } from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";

// Create a test provider that uses the WindowContext
const TestWindowProvider: FC<{
    value: WindowContextProps;
    children: ReactNode;
}> = ({ value, children }) => {
    return (
        <WindowContext.Provider value={value}>
            {children}
        </WindowContext.Provider>
    );
};

// Create a test consumer with resize button for testing handleResize
const TestWindowConsumer: FC = () => {
    const context = useContext(WindowContext);

    if (!context) {
        return <div data-testid="no-context">No context</div>;
    }

    return (
        <div>
            <div data-testid="window-width">{context.state.width}</div>
            <div data-testid="window-height">{context.state.height}</div>
            <div data-testid="window-dpr">{context.state.dpr}</div>
            <div data-testid="window-dimensions-0">
                {context.state.dimensions[0]}
            </div>
            <div data-testid="window-dimensions-1">
                {context.state.dimensions[1]}
            </div>
            <div data-testid="window-svg-dimensions-0">
                {context.state.svgDimensions[0]}
            </div>
            <div data-testid="window-svg-dimensions-1">
                {context.state.svgDimensions[1]}
            </div>
            <button
                data-testid="resize-button"
                onClick={() => context.handleResize()}
            >
                Resize
            </button>
        </div>
    );
};

describe("windowContextInstance", () => {
    it("should export WindowContext", () => {
        expect(WindowContext).toBeDefined();
    });

    it("should have undefined as default value", () => {
        render(<TestWindowConsumer />);
        expect(screen.getByTestId("no-context")).toBeInTheDocument();
    });

    it("should provide context value when used with provider", () => {
        const mockValue: WindowContextProps = {
            state: {
                width: 1024,
                height: 768,
                dpr: 2,
                dimensions: [1024, 768],
                svgDimensions: [2048, 1536],
                isMobile: false,
            },
            handleResize: vi.fn(),
        };

        render(
            <TestWindowProvider value={mockValue}>
                <TestWindowConsumer />
            </TestWindowProvider>,
        );

        expect(screen.getByTestId("window-width")).toHaveTextContent("1024");
        expect(screen.getByTestId("window-height")).toHaveTextContent("768");
        expect(screen.getByTestId("window-dpr")).toHaveTextContent("2");
        expect(screen.getByTestId("window-dimensions-0")).toHaveTextContent(
            "1024",
        );
        expect(screen.getByTestId("window-dimensions-1")).toHaveTextContent(
            "768",
        );
        expect(screen.getByTestId("window-svg-dimensions-0")).toHaveTextContent(
            "2048",
        );
        expect(screen.getByTestId("window-svg-dimensions-1")).toHaveTextContent(
            "1536",
        );
    });

    it("should call handleResize when resize button is clicked", () => {
        const handleResize = vi.fn();
        const mockValue: WindowContextProps = {
            state: {
                width: 1024,
                height: 768,
                dpr: 2,
                dimensions: [1024, 768],
                svgDimensions: [2048, 1536],
                isMobile: false,
            },
            handleResize,
        };

        render(
            <TestWindowProvider value={mockValue}>
                <TestWindowConsumer />
            </TestWindowProvider>,
        );

        fireEvent.click(screen.getByTestId("resize-button"));
        expect(handleResize).toHaveBeenCalledTimes(1);
    });

    it("should accept different context values", () => {
        const mockValue: WindowContextProps = {
            state: {
                width: 800,
                height: 600,
                dpr: 1,
                dimensions: [800, 600],
                svgDimensions: [1600, 1200],
                isMobile: false,
            },
            handleResize: vi.fn(),
        };

        render(
            <TestWindowProvider value={mockValue}>
                <TestWindowConsumer />
            </TestWindowProvider>,
        );

        expect(screen.getByTestId("window-width")).toHaveTextContent("800");
        expect(screen.getByTestId("window-height")).toHaveTextContent("600");
        expect(screen.getByTestId("window-dpr")).toHaveTextContent("1");
        expect(screen.getByTestId("window-dimensions-0")).toHaveTextContent(
            "800",
        );
        expect(screen.getByTestId("window-dimensions-1")).toHaveTextContent(
            "600",
        );
        expect(screen.getByTestId("window-svg-dimensions-0")).toHaveTextContent(
            "1600",
        );
        expect(screen.getByTestId("window-svg-dimensions-1")).toHaveTextContent(
            "1200",
        );
    });
});
