import { createContext } from "react";

// Define the context interface
export interface LoadingContextProps {
    isLoading: boolean;
    showLoading: () => void;
    hideLoading: () => void;
    toggleLoading: (status: boolean) => void;
}

// Create the context
export const LoadingContext = createContext<LoadingContextProps | undefined>(
    undefined,
);
