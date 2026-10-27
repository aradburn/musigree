/** @jsxImportSource react */
import React from "react";
import { describe, it, expect, vi } from "vitest";
import { render } from "@testing-library/react";

vi.mock("../Visualization/NetworkView", () => ({
    NetworkView: (): React.ReactElement => <main data-testid="main-view" />,
}));

vi.mock("../Visualization/LoadingAnimation", () => ({
    default: (): null => null,
}));

vi.mock("../Layout/SidebarLeft", () => ({
    SidebarLeft: (): React.ReactElement => <div data-testid="sidebar-left" />,
}));

vi.mock("../Layout/SidebarRight", () => ({
    SidebarRight: (): React.ReactElement => (
        <aside data-testid="sidebar-right" />
    ),
}));

vi.mock("../Layout/Header.tsx", () => ({
    Header: (): React.ReactElement => <header data-testid="header" />,
}));

import App from "../App";

describe("App column order", () => {
    it("stacks main, then the right sidebar, then the left sidebar on mobile", () => {
        const { container } = render(<App />);

        const left = container.querySelector(".sidebar-left-container");
        const main = container.querySelector(".main-container");
        const right = container.querySelector(".sidebar-right-container");

        expect(left).not.toBeNull();
        expect(main).not.toBeNull();
        expect(right).not.toBeNull();
        expect(left?.className).toContain("order-3");
        expect(left?.className).toContain("order-sm-1");
        expect(left?.className).not.toContain("d-none");
        expect(main?.className).toContain("order-1");
        expect(main?.className).toContain("order-sm-2");
        expect(right?.className).toContain("order-2");
        expect(right?.className).toContain("order-sm-3");
    });
});
