import { describe, it, expect, vi } from "vitest";
import React, { useContext } from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { NetworkProvider } from "../NetworkContext";
import {
    NetworkContext,
    networkReducer,
    initialState,
    type NetworkAction,
} from "../networkContextInstance";

describe("NetworkContext", () => {
    it("renders without crashing", () => {
        // Just test that the provider renders without errors
        render(
            <NetworkProvider>
                <div>Test</div>
            </NetworkProvider>,
        );
        expect(true).toBe(true);
    });
});

describe("networkReducer", () => {
    it("SET_NODE_STRENGTH: should update node strength", () => {
        const action: NetworkAction = { type: "SET_NODE_STRENGTH", value: 20 };
        const newState = networkReducer(initialState, action);
        expect(newState.nodeStrength).toBe(20);
    });

    it("SET_LINK_STRENGTH: should update link strength", () => {
        const action: NetworkAction = { type: "SET_LINK_STRENGTH", value: 50 };
        const newState = networkReducer(initialState, action);
        expect(newState.linkStrength).toBe(50);
    });

    it("SET_GRAVITY_STRENGTH: should update gravity strength", () => {
        const action: NetworkAction = {
            type: "SET_GRAVITY_STRENGTH",
            value: 15,
        };
        const newState = networkReducer(initialState, action);
        expect(newState.gravityStrength).toBe(15);
    });

    it("SELECT_NODE: should set the selected node", () => {
        const action: NetworkAction = {
            type: "SELECT_NODE",
            nodeId: "test-node",
        };
        const newState = networkReducer(initialState, action);
        expect(newState.selectedNode).toBe("test-node");
    });

    it("SET_FORCES: should return the current state", () => {
        const currentState = { ...initialState, nodeStrength: 20 };
        const action: NetworkAction = { type: "SET_FORCES" };
        const newState = networkReducer(currentState, action);
        expect(newState).toEqual(currentState);
    });

    it("RESET_FORCES: should reset to initial state", () => {
        const currentState = {
            nodeStrength: 20,
            linkStrength: 50,
            gravityStrength: 15,
            selectedNode: "test-node",
        };
        const action: NetworkAction = { type: "RESET_FORCES" };
        const newState = networkReducer(currentState, action);
        expect(newState).toEqual(initialState);
    });

    it("unknown action: should return current state", () => {
        // Using type assertion to test an invalid action type
        const action = { type: "UNKNOWN_ACTION" } as unknown as NetworkAction;
        const newState = networkReducer(initialState, action);
        expect(newState).toEqual(initialState);
    });
});
