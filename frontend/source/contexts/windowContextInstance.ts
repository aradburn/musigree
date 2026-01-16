import { createContext } from "react";

// Define the state interface
export interface WindowState {
    width: number;
    height: number;
    dpr: number;
    dimensions: [number, number];
    svgDimensions: [number, number];
    isMobile: boolean;
}

// Context interface
export interface WindowContextProps {
    state: WindowState;
    handleResize: () => void;
}

// Create the context
export const WindowContext = createContext<WindowContextProps | undefined>(
    undefined,
);
