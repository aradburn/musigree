/** @jsxImportSource react */
import { describe, it, expect } from "vitest";
import React, { useContext } from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { NetworkContext } from "../networkContextInstance";

// Test consumer component to verify context behavior
const TestConsumer = () => {
    const context = useContext(NetworkContext);
    return (
        <div data-testid="context-value">
            {context === undefined ? "undefined" : "defined"}
        </div>
    );
};

describe("networkContextInstance", () => {
    it("should export NetworkContext", () => {
        expect(NetworkContext).toBeDefined();
        expect(NetworkContext.Provider).toBeDefined();
        expect(NetworkContext.Consumer).toBeDefined();
    });

    it("should initialize NetworkContext with undefined value", () => {
        render(<TestConsumer />);
        expect(screen.getByTestId("context-value")).toHaveTextContent(
            "undefined",
        );
    });
});
