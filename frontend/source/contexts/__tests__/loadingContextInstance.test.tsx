/** @jsxImportSource react */
import { describe, it, expect } from "vitest";
import React, { useContext } from "react";
import { render, screen } from "@testing-library/react";
import "@testing-library/jest-dom";
import { LoadingContext } from "../loadingContextInstance";

// Test consumer component to verify context behavior
const TestConsumer = () => {
    const context = useContext(LoadingContext);
    return (
        <div data-testid="context-value">
            {context === undefined ? "undefined" : "defined"}
        </div>
    );
};

describe("loadingContextInstance", () => {
    it("should export LoadingContext", () => {
        expect(LoadingContext).toBeDefined();
        expect(LoadingContext.Provider).toBeDefined();
        expect(LoadingContext.Consumer).toBeDefined();
    });

    it("should initialize LoadingContext with undefined value", () => {
        render(<TestConsumer />);
        expect(screen.getByTestId("context-value")).toHaveTextContent(
            "undefined",
        );
    });
});
