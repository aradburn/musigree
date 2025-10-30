import { useContext } from "react";
import { EntityContext } from "./entityContextInstance";
import type { EntityContextProps } from "./entityContextInstance";

export const useEntity = (): EntityContextProps => {
    const context = useContext(EntityContext);
    if (context === undefined) {
        throw new Error("useEntity must be used within an EntityProvider");
    }
    return context;
};
