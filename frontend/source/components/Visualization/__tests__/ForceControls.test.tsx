import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { ForceControls } from "../ForceControls";
import * as networkContext from "../../../contexts/useNetwork";
import * as forceLayout from "../../../network/forceLayout";
import { FORCE } from "../../../constants";

// Mock the forceLayout module
vi.mock("../../../network/forceLayout", () => ({
    restartForceLayout: vi.fn(),
    stopForceLayout: vi.fn(),
}));

// Mock the useNetwork context
vi.mock("../../../contexts/useNetwork", () => ({
    useNetwork: vi.fn(),
}));

describe("ForceControls", () => {
    // Mock implementation of useNetwork
    const mockDispatch = vi.fn();
    const mockSetupChargeForce = vi.fn();
    const mockSetupLinkForce = vi.fn();
    const mockSetupGravityForce = vi.fn();

    // Setup default mock values
    const defaultMockState = {
        nodeStrength: 20,
        linkStrength: 30,
        gravityStrength: 40,
        selectedNode: null,
    };

    beforeEach(() => {
        // Reset all mocks
        vi.resetAllMocks();

        // Setup default mock return value for useNetwork
        vi.mocked(networkContext.useNetwork).mockReturnValue({
            state: defaultMockState,
            dispatch: mockDispatch,
            setupChargeForce: mockSetupChargeForce,
            setupLinkForce: mockSetupLinkForce,
            setupGravityForce: mockSetupGravityForce,
            setForces: vi.fn(),
            resetForces: vi.fn(),
        });
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    it("renders with correct initial values", () => {
        render(<ForceControls />);

        // Get all range inputs
        const rangeInputs = screen.getAllByRole("slider");
        expect(rangeInputs).toHaveLength(3);

        // Check each slider has the correct value
        expect(rangeInputs[0]).toHaveValue(
            defaultMockState.nodeStrength.toString(),
        );
        expect(rangeInputs[1]).toHaveValue(
            defaultMockState.linkStrength.toString(),
        );
        expect(rangeInputs[2]).toHaveValue(
            defaultMockState.gravityStrength.toString(),
        );

        // Check labels are present
        expect(screen.getByLabelText(/Node Strength/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Link Strength/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/Gravity Strength/i)).toBeInTheDocument();

        // Check buttons are present - use getAllByText instead of getByText
        const layoutButtons = screen.getAllByText(/LAYOUT/i, {
            selector: "div[role='button'] span",
        });
        expect(layoutButtons).toHaveLength(2);

        // Check for icon elements
        expect(
            screen.getByText("", { selector: "i.bi-lightning" }),
        ).toBeInTheDocument();
        expect(
            screen.getByText("", { selector: "i.bi-sign-stop" }),
        ).toBeInTheDocument();
    });

    it("updates node strength when slider is changed", () => {
        render(<ForceControls />);

        const nodeSlider = screen.getByLabelText(/Node Strength/i);
        fireEvent.change(nodeSlider, { target: { value: "50" } });

        // Verify dispatch was called with correct action
        expect(mockDispatch).toHaveBeenCalledWith({
            type: "SET_NODE_STRENGTH",
            value: 50,
        });

        // Verify setupChargeForce was called with correct value
        expect(mockSetupChargeForce).toHaveBeenCalledWith(50);

        // Verify restartForceLayout was called with correct value
        expect(forceLayout.restartForceLayout).toHaveBeenCalledWith(
            FORCE.SIMULATION.ALPHA / 10.0,
        );
    });

    it("updates link strength when slider is changed", () => {
        render(<ForceControls />);

        const linkSlider = screen.getByLabelText(/Link Strength/i);
        fireEvent.change(linkSlider, { target: { value: "60" } });

        // Verify dispatch was called with correct action
        expect(mockDispatch).toHaveBeenCalledWith({
            type: "SET_LINK_STRENGTH",
            value: 60,
        });

        // Verify setupLinkForce was called with correct value
        expect(mockSetupLinkForce).toHaveBeenCalledWith(60);

        // Verify restartForceLayout was called with correct value
        expect(forceLayout.restartForceLayout).toHaveBeenCalledWith(
            FORCE.SIMULATION.ALPHA / 5.0,
        );
    });

    it("updates gravity strength when slider is changed", () => {
        render(<ForceControls />);

        const gravitySlider = screen.getByLabelText(/Gravity Strength/i);
        fireEvent.change(gravitySlider, { target: { value: "70" } });

        // Verify dispatch was called with correct action
        expect(mockDispatch).toHaveBeenCalledWith({
            type: "SET_GRAVITY_STRENGTH",
            value: 70,
        });

        // Verify setupGravityForce was called with correct value
        expect(mockSetupGravityForce).toHaveBeenCalledWith(70);

        // Verify restartForceLayout was called with correct value
        expect(forceLayout.restartForceLayout).toHaveBeenCalledWith(
            FORCE.SIMULATION.ALPHA / 10.0,
        );
    });

    it("calls restartForceLayout when start layout button is clicked", () => {
        render(<ForceControls />);

        // Find the start layout button
        const startButton = screen.getByText(/LAYOUT/i, {
            selector: "div[role='button']:not(:last-child) span",
        });
        fireEvent.click(startButton.parentElement as HTMLElement);

        // Verify restartForceLayout was called
        expect(forceLayout.restartForceLayout).toHaveBeenCalledWith(
            FORCE.SIMULATION.ALPHA / 10.0,
        );
    });

    it("calls stopForceLayout when stop layout button is clicked", () => {
        render(<ForceControls />);

        // Find the stop layout button
        const stopButton = screen.getByText(/LAYOUT/i, {
            selector: "div[role='button']:last-child span",
        });
        fireEvent.click(stopButton.parentElement as HTMLElement);

        // Verify stopForceLayout was called
        expect(forceLayout.stopForceLayout).toHaveBeenCalled();
    });

    it("renders with custom className when provided", () => {
        const customClassName = "custom-class";
        const { container } = render(
            <ForceControls className={customClassName} />,
        );

        // Check if the container has the custom class
        expect(container.firstChild).toHaveClass(customClassName);
    });
});
