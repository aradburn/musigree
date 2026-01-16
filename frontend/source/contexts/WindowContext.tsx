/** @jsxImportSource react */
import React, { useState, useEffect, useRef } from "react";
import type { ReactNode } from "react";
import debounce from "debounce";
import { DOM_IDS, INIT, SVG } from "../constants";
import { musigreeManager } from "../core";
import { ResizeEvent } from "../network/events";
import { resetNetworkTransform } from "../network/init";
import { setSvgSize } from "@/svg";
import { WindowContext } from "./windowContextInstance";
import type { WindowState, WindowContextProps } from "./windowContextInstance";

// Initial state (with placeholder values that will be updated in useEffect)
const initialState: WindowState = {
    width: 0,
    height: 0,
    dpr: 1,
    dimensions: [0, 0],
    svgDimensions: [0, 0],
    isMobile: false,
};

// WindowContext is imported from windowContextInstance.ts

// Provider component
interface WindowProviderProps {
    children: ReactNode;
}

export const WindowProvider: React.FC<WindowProviderProps> = ({ children }) => {
    const [state, setState] = useState<WindowState>(initialState);
    const stateRef = useRef<WindowState>(state);

    // Calculate window and SVG dimensions
    const calculateDimensions = (): WindowState => {
        const dpr = window.devicePixelRatio || 1;
        const svgContainer = document.getElementById("svg-container-fluid");

        if (!svgContainer) {
            return {
                ...state,
                dpr,
            };
        }

        const width = svgContainer.clientWidth;
        const height = svgContainer.clientHeight;
        const dimensions: [number, number] = [width, height];
        const svgDimensions: [number, number] = [
            dimensions[0] * SVG.VIEWPORT_SIZE_MULTIPLIER * dpr,
            dimensions[1] * SVG.VIEWPORT_SIZE_MULTIPLIER * dpr,
        ];
        const isMobile = window.innerWidth < 768;

        // Update the musigreeManager with the new dimensions
        musigreeManager.dpr = dpr;
        musigreeManager.dimensions = dimensions;
        musigreeManager.svgDimensions = svgDimensions;
        // Note: isMobile is now retrieved from WindowContext via getter function

        return {
            width,
            height,
            dpr,
            dimensions,
            svgDimensions,
            isMobile,
        };
    };

    // Handle window resize
    const handleResize = debounce((): void => {
        console.log("WindowContext handleResize()");
        try {
            // Update dimensions state
            const newState = calculateDimensions();
            setState(newState);
            stateRef.current = newState;

            // Setup window dimensions on SVG element
            setSvgSize(DOM_IDS.SVG_ID);
            // Reset network visualization
            resetNetworkTransform();

            // Dispatch resize event
            window.dispatchEvent(new ResizeEvent());
        } catch (error: unknown) {
            const errorMessage =
                error instanceof Error
                    ? error.message
                    : typeof error === "string"
                      ? error
                      : JSON.stringify(error);
            console.error("Error during window resize:", errorMessage);
        }
    }, INIT.DEBOUNCE_DELAY);

    // Initialize dimensions on mount and set up resize listener
    useEffect(() => {
        // Calculate initial dimensions
        const initialState = calculateDimensions();
        setState(initialState);
        stateRef.current = initialState;

        // Register getter function to retrieve isMobile from WindowContext state
        musigreeManager.setIsMobileGetter(() => stateRef.current.isMobile);

        // Add resize event listener
        window.addEventListener("resize", handleResize as () => void);

        // Clean up event listener on unmount
        return (): void => {
            window.removeEventListener("resize", handleResize as () => void);
        };
    }, []);

    // Update state ref whenever state changes
    useEffect(() => {
        stateRef.current = state;
    }, [state]);

    return (
        <WindowContext.Provider value={{ state, handleResize }}>
            {children}
        </WindowContext.Provider>
    );
};

// WindowContext is already exported from windowContextInstance.ts
