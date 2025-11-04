/** @jsxImportSource react */
import React, { useEffect, useMemo, useReducer } from "react";
import type { ReactNode } from "react";
import type { EntityData } from "../entities";
import {
    EntityContext,
    initialEntityState,
    entityReducer,
} from "./entityContextInstance";

interface EntityProviderProps {
    children: ReactNode;
}

export const EntityProvider = ({
    children,
}: EntityProviderProps): React.ReactElement => {
    const [state, dispatch] = useReducer(entityReducer, initialEntityState);

    useEffect(() => {
        const handleDetailsUpdated = (event: Event): void => {
            const custom = event as CustomEvent<EntityData>;
            dispatch({ type: "SET_ENTITY", entity: custom.detail ?? null });
        };

        window.addEventListener(
            "musigree:entity-details-updated",
            handleDetailsUpdated,
        );
        return (): void => {
            window.removeEventListener(
                "musigree:entity-details-updated",
                handleDetailsUpdated,
            );
        };
    }, []);

    const value = useMemo(() => ({ state, dispatch }), [state, dispatch]);

    return (
        <EntityContext.Provider value={value}>
            {children}
        </EntityContext.Provider>
    );
};
