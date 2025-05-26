/** @jsxImportSource react */
import React, { useState, useCallback, useEffect } from "react";
import type { ReactNode } from "react";
import { LoadingContext } from "./loadingContextInstance";

// Provider component
interface LoadingProviderProps {
    children: ReactNode;
}

/**
 * Provider component for loading state
 * Manages global loading state for the application
 */
export const LoadingProvider: React.FC<LoadingProviderProps> = ({
    children,
}) => {
    const [isLoading, setIsLoading] = useState<boolean>(false);

    // Show loading animation
    const showLoading = useCallback((): void => {
        setIsLoading(true);
    }, []);

    // Hide loading animation
    const hideLoading = useCallback((): void => {
        setIsLoading(false);
    }, []);

    // Toggle loading animation
    const toggleLoading = useCallback((status: boolean): void => {
        setIsLoading(status);
    }, []);

    // Listen for custom loading:toggle events from the FSM
    useEffect(() => {
        const handleLoadingToggle = (event: Event): void => {
            const customEvent = event as CustomEvent<{ status: boolean }>;
            toggleLoading(customEvent.detail.status);
        };

        window.addEventListener("loading:toggle", handleLoadingToggle);

        return (): void => {
            window.removeEventListener("loading:toggle", handleLoadingToggle);
        };
    }, [toggleLoading]);

    const value = {
        isLoading,
        showLoading,
        hideLoading,
        toggleLoading,
    };

    return (
        <LoadingContext.Provider value={value}>
            {children}
        </LoadingContext.Provider>
    );
};
