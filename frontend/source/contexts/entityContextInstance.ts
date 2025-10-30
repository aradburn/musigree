import { createContext, type Dispatch } from "react";
import type { EntityData } from "../entities";

export interface EntityState {
    entity: EntityData | null;
}

export type EntityAction = { type: "SET_ENTITY"; entity: EntityData | null };

export const initialEntityState: EntityState = {
    entity: null,
};

export function entityReducer(
    state: EntityState,
    action: EntityAction,
): EntityState {
    switch (action.type) {
        case "SET_ENTITY":
            return { ...state, entity: action.entity };
        default:
            return state;
    }
}

export interface EntityContextProps {
    state: EntityState;
    dispatch: Dispatch<EntityAction>;
}

export const EntityContext = createContext<EntityContextProps | undefined>(
    undefined,
);
