import { useContext } from "react";
import { WindowContext } from "./windowContextInstance";
import type { WindowContextProps } from "./windowContextInstance";

/**
 * Custom hook to use the window context
 * @returns WindowContextProps
 * @throws Error if used outside of WindowProvider
 */
export const useWindow = (): WindowContextProps => {
    const context = useContext(WindowContext);
    if (context === undefined) {
        throw new Error("useWindow must be used within a WindowProvider");
    }
    return context;
};
