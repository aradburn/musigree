import { useContext } from "react";
import { LoadingContext } from "./loadingContextInstance";
import type { LoadingContextProps } from "./loadingContextInstance";

/**
 * Custom hook to use the loading context
 * @returns LoadingContextProps
 * @throws Error if used outside of LoadingProvider
 */
export const useLoading = (): LoadingContextProps => {
    const context = useContext(LoadingContext);
    if (context === undefined) {
        throw new Error("useLoading must be used within a LoadingProvider");
    }
    return context;
};
