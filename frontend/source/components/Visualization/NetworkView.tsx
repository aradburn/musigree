/** @jsxImportSource react */
import React, { useRef, useEffect, memo } from "react";
import { initNetwork } from "../../network/init";
import { initSvg } from "../../svg";
import { networkManager } from "../../core/singletons";
import { useNetwork } from "../../contexts/useNetwork";
import { DOM_IDS } from "../../constants";

/**
 * NetworkView component that serves as a wrapper for the D3.js visualization.
 * This component initializes and integrates with the existing D3.js visualization.
 * It uses NetworkContext to manage the visualization state.
 */
const NetworkView: React.FC = () => {
    const containerRef = useRef<HTMLDivElement>(null);
    const { dispatch } = useNetwork();
    const initializedRef = useRef<boolean>(false);

    useEffect(() => {
        // Initialize the D3.js visualization when the component mounts
        if (containerRef.current && !initializedRef.current) {
            console.log("Initializing D3.js network visualization");

            // Clear any existing network elements first
            if (networkManager.layers.root) {
                networkManager.layers.root.remove();
            }

            // Make sure the SVG container has its required id for backward compatibility
            if (containerRef.current.id !== DOM_IDS.SVG_CONTAINER) {
                containerRef.current.id = DOM_IDS.SVG_CONTAINER;
            }

            initSvg();

            // Initialize the network with our SVG element
            initNetwork(`${DOM_IDS.SVG_ID}`);

            // Mark the network as initialized
            initializedRef.current = true;
            // dispatch({ type: "SET_INITIALIZED", value: true });
        }

        // Cleanup function to handle component unmount
        return (): void => {
            console.log("Cleaning up D3.js network visualization");
            // Stop the force simulation if it's running
            if (networkManager.forceLayout) {
                networkManager.forceLayout.stop();
            }

            // Remove the visualization layers
            if (networkManager.layers.root) {
                networkManager.layers.root.remove();
            }

            // Mark the network as uninitialized
            initializedRef.current = false;
            // dispatch({ type: "SET_INITIALIZED", value: false });
        };
    }, [dispatch]);

    return <main id={DOM_IDS.SVG_CONTAINER} ref={containerRef}></main>;
};

// Wrap with memo to prevent unnecessary re-renders as this component rarely changes
export default memo(NetworkView);

// Also export the non-memoized version for cases where that might be needed
export { NetworkView };
