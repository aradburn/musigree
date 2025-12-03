import { createContext, type Dispatch } from "react";

// Define the state interface
export interface NetworkState {
    nodeStrength: number;
    linkStrength: number;
    gravityStrength: number;
    // eslint-disable-next-line @typescript-eslint/no-redundant-type-constituents
    selectedNode: string | undefined;
}

// Define the actions that can be dispatched
export type NetworkAction =
    | { type: "SET_NODE_STRENGTH"; value: number }
    | { type: "SET_LINK_STRENGTH"; value: number }
    | { type: "SET_GRAVITY_STRENGTH"; value: number }
    // eslint-disable-next-line @typescript-eslint/no-redundant-type-constituents
    | { type: "SELECT_NODE"; nodeId: string | undefined }
    | { type: "SET_FORCES" }
    | { type: "RESET_FORCES" };

// Initial state
export const initialState: NetworkState = {
    nodeStrength: 12,
    linkStrength: 40,
    gravityStrength: 10,
    selectedNode: undefined,
};

// Reducer function
export function networkReducer(
    state: NetworkState,
    action: NetworkAction,
): NetworkState {
    switch (action.type) {
        case "SET_NODE_STRENGTH":
            return { ...state, nodeStrength: action.value };
        case "SET_LINK_STRENGTH":
            return { ...state, linkStrength: action.value };
        case "SET_GRAVITY_STRENGTH":
            return { ...state, gravityStrength: action.value };
        case "SELECT_NODE":
            return { ...state, selectedNode: action.nodeId };
        case "SET_FORCES":
            return { ...state };
        case "RESET_FORCES":
            return { ...initialState };
        default:
            return state;
    }
}

// Context interface
export interface NetworkContextProps {
    state: NetworkState;
    dispatch: Dispatch<NetworkAction>;
    setupChargeForce: (nodeStrength: number) => void;
    setupLinkForce: (linkStrength: number) => void;
    setupGravityForce: (gravityStrength: number) => void;
    setForces: () => void;
    resetForces: () => void;
}

// Create the context
export const NetworkContext = createContext<NetworkContextProps | undefined>(
    undefined,
);
