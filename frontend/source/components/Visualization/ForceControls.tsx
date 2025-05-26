/** @jsxImportSource react */
import React, { useCallback } from "react";
import { Form } from "react-bootstrap";
import { FORCE } from "../../constants";
import { useNetwork } from "../../contexts/useNetwork";
import { restartForceLayout, stopForceLayout } from "../../network/forceLayout";

interface ForceControlsProps {
    className?: string;
}

/**
 * Component for force layout controls (sliders).
 * Used in Sidebar.
 */
export const ForceControls: React.FC<ForceControlsProps> = ({
    className = "",
}) => {
    const {
        state,
        dispatch,
        setupChargeForce,
        setupLinkForce,
        setupGravityForce,
    } = useNetwork();

    // Memoize event handlers to prevent unnecessary re-renders
    const handleNodeStrengthChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>): void => {
            const value = parseInt(e.target.value, 10);
            dispatch({ type: "SET_NODE_STRENGTH", value });

            // Update the node strength in the force layout
            setupChargeForce(value);
            // Restart the force layout with a reduced alpha
            restartForceLayout(FORCE.SIMULATION.ALPHA / 10.0);
        },
        [dispatch, setupChargeForce],
    );

    const handleLinkStrengthChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>): void => {
            const value = parseInt(e.target.value, 10);
            dispatch({ type: "SET_LINK_STRENGTH", value });

            // Update the link strength in the force layout
            setupLinkForce(value);
            // Restart the force layout with a reduced alpha
            restartForceLayout(FORCE.SIMULATION.ALPHA / 5.0);
        },
        [dispatch, setupLinkForce],
    );

    const handleGravityStrengthChange = useCallback(
        (e: React.ChangeEvent<HTMLInputElement>): void => {
            const value = parseInt(e.target.value, 10);
            dispatch({ type: "SET_GRAVITY_STRENGTH", value });

            // Update the gravity strength in the force layout
            setupGravityForce(value);
            // Restart the force layout with a reduced alpha
            restartForceLayout(FORCE.SIMULATION.ALPHA / 10.0);
        },
        [dispatch, setupGravityForce],
    );

    // Create new handlers to directly use startForceLayout and stopForceLayout
    const handleStartLayout = useCallback((): void => {
        restartForceLayout(FORCE.SIMULATION.ALPHA / 10.0);
    }, []);

    const handleStopLayout = useCallback((): void => {
        stopForceLayout();
    }, []);

    return (
        <div className={`force-controls ${className}`}>
            {/* Node strength slider */}
            <Form.Label htmlFor="nodeRange">Node Strength</Form.Label>
            <Form.Range
                id="nodeRange"
                value={state.nodeStrength}
                onChange={handleNodeStrengthChange}
                min={0}
                max={100}
            />

            {/* Link strength slider */}
            <Form.Label htmlFor="linkRange">Link Strength</Form.Label>
            <Form.Range
                id="linkRange"
                value={state.linkStrength}
                onChange={handleLinkStrengthChange}
                min={0}
                max={100}
            />

            {/* Gravity strength slider */}
            <Form.Label htmlFor="gravRange">Gravity Strength</Form.Label>
            <Form.Range
                id="gravRange"
                value={state.gravityStrength}
                onChange={handleGravityStrengthChange}
                min={0}
                max={100}
            />

            {/* Layout buttons */}
            <div className="d-flex flex-column w-100">
                <div
                    className="navbar-text px-sm-0 px-2 justify-content-end"
                    role="button"
                    onClick={handleStartLayout}
                >
                    <i className="fs-5 bi-lightning"></i>
                    <span className="ms-1 d-none d-sm-inline">LAYOUT</span>
                </div>

                <div
                    className="navbar-text px-sm-0 px-2 justify-content-end"
                    role="button"
                    onClick={handleStopLayout}
                >
                    <i className="fs-5 bi-sign-stop"></i>
                    <span className="ms-1 d-none d-sm-inline">LAYOUT</span>
                </div>
            </div>
        </div>
    );
};

export default ForceControls;
