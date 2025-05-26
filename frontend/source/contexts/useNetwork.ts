import { useContext } from "react";
import { NetworkContext } from "./networkContextInstance";
import type { NetworkContextProps } from "./networkContextInstance";

/**
 * Custom hook to use the network context
 * @returns NetworkContextProps
 * @throws Error if used outside of NetworkProvider
 */
export const useNetwork = (): NetworkContextProps => {
    const context = useContext(NetworkContext);
    if (context === undefined) {
        throw new Error("useNetwork must be used within a NetworkProvider");
    }
    return context;
};
