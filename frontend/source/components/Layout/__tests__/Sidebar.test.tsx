import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { render, screen, fireEvent, within } from "@testing-library/react";
import "@testing-library/jest-dom";
import { SidebarLeft } from "../SidebarLeft";
import { FORCE, INIT } from "../../../constants";
import { RequestNetworkEvent } from "../../../network/events";
import {
    YEAR_TRACK_MAX,
    YEAR_TRACK_MIN,
    updateSelectedYearBounds,
} from "../../../yearBounds";
import { updateSelectedRoleIds } from "../../../roles";

vi.mock("../../../print", () => ({
    printSvg: vi.fn(),
}));

vi.mock("../../../core", () => ({
    musigreeManager: {
        svgDimensions: [800, 600],
    },
}));

vi.mock("../../../core/singletons", () => ({
    musigreeManager: {
        svgDimensions: [800, 600],
    },
}));

vi.mock("../../../network/forceLayout", () => ({
    restartForceLayout: vi.fn(),
    stopForceLayout: vi.fn(),
}));

vi.mock("../../Visualization/ForceControls", () => ({
    default: vi
        .fn()
        .mockImplementation(() => (
            <div data-testid="mock-force-controls">ForceControls Mock</div>
        )),
}));

import { printSvg } from "../../../print";
import { musigreeManager } from "../../../core/singletons";
import {
    restartForceLayout,
    stopForceLayout,
} from "../../../network/forceLayout";

describe("SidebarLeft Component", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.useFakeTimers();
        updateSelectedYearBounds({
            minYear: YEAR_TRACK_MIN,
            maxYear: YEAR_TRACK_MAX,
        });
        vi.spyOn(window, "dispatchEvent").mockImplementation(() => true);
    });

    afterEach(() => {
        vi.useRealTimers();
        vi.restoreAllMocks();
        updateSelectedYearBounds({
            minYear: YEAR_TRACK_MIN,
            maxYear: YEAR_TRACK_MAX,
        });
        updateSelectedRoleIds([]);
        delete window.dgRoles;
    });

    it("keeps filter and layout closed until their headings are opened", () => {
        render(<SidebarLeft />);

        const filterToggle = screen.getByRole("button", { name: "Filter" });
        const layoutToggle = screen.getByRole("button", { name: "Layout" });
        const printToggle = screen.getByRole("button", { name: "Print" });

        expect(filterToggle.querySelector("i.bi-funnel")).toBeInTheDocument();
        expect(layoutToggle.querySelector("i.bi-sliders")).toBeInTheDocument();
        expect(printToggle.querySelector("i.bi-printer")).toBeInTheDocument();
        expect(filterToggle).toHaveAttribute("aria-expanded", "false");
        expect(layoutToggle).toHaveAttribute("aria-expanded", "false");
        expect(printToggle).toHaveAttribute("aria-expanded", "false");
        expect(
            document.getElementById("sidebar-print-panel"),
        ).not.toBeVisible();
        expect(
            screen.queryByRole("group", { name: "Relationships" }),
        ).not.toBeInTheDocument();
        expect(
            screen.queryByRole("button", { name: "Start layout" }),
        ).not.toBeInTheDocument();

        fireEvent.click(filterToggle);
        fireEvent.click(layoutToggle);

        expect(filterToggle).toHaveAttribute("aria-expanded", "true");
        expect(layoutToggle).toHaveAttribute("aria-expanded", "true");
        expect(
            screen.getByRole("group", { name: "Relationships" }),
        ).toBeVisible();
        expect(
            screen.getByRole("button", { name: "Start layout" }),
        ).toBeVisible();
    });

    it("renders filters, then layout controls, with print last", () => {
        render(<SidebarLeft />);

        fireEvent.click(screen.getByRole("button", { name: "Filter" }));
        fireEvent.click(screen.getByRole("button", { name: "Layout" }));
        fireEvent.click(screen.getByRole("button", { name: "Print" }));

        const filtersHeading = screen.getByRole("heading", {
            level: 4,
            name: "Filter",
        });
        const layoutHeading = screen.getByRole("heading", {
            level: 4,
            name: "Layout",
        });
        const forceControls = screen.getByTestId("mock-force-controls");
        const printPanel = document.getElementById("sidebar-print-panel");
        const printButton = within(printPanel as HTMLElement).getByRole(
            "button",
            { name: "Print" },
        );

        expect(filtersHeading).toBeInTheDocument();
        const relationships = screen.getByText("Relationships");
        const roles = screen.getByText("Roles");

        expect(screen.getByText("Years")).toHaveClass("h6");
        expect(relationships).toHaveClass("h6");
        expect(roles).toHaveClass("h6");
        expect(
            relationships.compareDocumentPosition(roles) &
                Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();
        expect(
            filtersHeading.compareDocumentPosition(relationships) &
                Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();
        expect(screen.getByLabelText("Minimum year")).toHaveValue(
            String(YEAR_TRACK_MIN),
        );
        expect(screen.getByLabelText("Maximum year")).toHaveValue(
            String(YEAR_TRACK_MAX),
        );
        const startLayout = screen.getByRole("button", {
            name: "Start layout",
        });
        const stopLayout = screen.getByRole("button", { name: "Stop layout" });
        const layoutPanel = document.getElementById("sidebar-layout-panel");

        expect(layoutHeading).toBeInTheDocument();
        expect(startLayout.querySelector("i.bi-lightning")).toBeInTheDocument();
        expect(stopLayout.querySelector("i.bi-sign-stop")).toBeInTheDocument();
        expect(startLayout).not.toHaveTextContent(/\S/);
        expect(stopLayout).not.toHaveTextContent(/\S/);
        expect(layoutPanel).toContainElement(startLayout);
        expect(layoutPanel).toContainElement(stopLayout);
        expect(forceControls).toBeInTheDocument();
        expect(printButton).toBeInTheDocument();
        expect(printButton).toHaveClass("btn");
        expect(printPanel).toContainElement(printButton);
        expect(
            filtersHeading.compareDocumentPosition(layoutHeading) &
                Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();
        expect(
            layoutHeading.compareDocumentPosition(startLayout) &
                Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();
        expect(
            startLayout.compareDocumentPosition(stopLayout) &
                Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();
        expect(
            stopLayout.compareDocumentPosition(forceControls) &
                Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();
        expect(
            forceControls.compareDocumentPosition(printButton) &
                Node.DOCUMENT_POSITION_FOLLOWING,
        ).toBeTruthy();
    });

    it("splits structural links between the checkbox group and the roles tree", () => {
        window.dgRoles = {
            core: {
                data: [
                    { id: "Production", text: "Production", parent: "#" },
                    {
                        id: "Structural Relationships",
                        text: "Structural Relationships",
                        parent: "#",
                    },
                    {
                        id: "alias",
                        text: "Alias",
                        parent: "Structural Relationships",
                    },
                    {
                        id: "member",
                        text: "Member Of",
                        parent: "Structural Relationships",
                    },
                    {
                        id: "released",
                        text: "Released On",
                        parent: "Structural Relationships",
                    },
                    {
                        id: "sublabel",
                        text: "Sublabel Of",
                        parent: "Structural Relationships",
                    },
                    {
                        id: "collaborated",
                        text: "Collaborated With",
                        parent: "Structural Relationships",
                    },
                    {
                        id: "compiled",
                        text: "Compiled On",
                        parent: "Structural Relationships",
                    },
                    {
                        id: "split",
                        text: "Split With",
                        parent: "Structural Relationships",
                    },
                    {
                        id: "other",
                        text: "Other",
                        parent: "Structural Relationships",
                    },
                ],
            },
        };

        render(<SidebarLeft />);
        fireEvent.click(screen.getByRole("button", { name: "Filter" }));

        const options = screen
            .getByRole("group", { name: "Relationships" })
            .querySelectorAll(".relationships-option span");
        expect(Array.from(options, (option) => option.textContent)).toEqual([
            "Alias",
            "Member Of",
            "Released On",
            "Sublabel Of",
        ]);
        expect(
            screen.getByRole("checkbox", {
                name: "Structural Relationships",
            }),
        ).toBeInTheDocument();
        expect(
            screen.queryByRole("checkbox", { name: "Relationships" }),
        ).not.toBeInTheDocument();
        expect(
            screen.getByRole("checkbox", { name: "Production" }),
        ).toBeInTheDocument();
    });

    it("checks the roles marked selected in the page tree", () => {
        window.dgRoles = {
            core: {
                data: [
                    { id: "Production", text: "Production", parent: "#" },
                    {
                        id: "Structural Relationships",
                        text: "Structural Relationships",
                        parent: "#",
                    },
                    {
                        id: "1",
                        text: "Alias",
                        parent: "Structural Relationships",
                        state: { selected: true },
                    },
                    {
                        id: "2",
                        text: "Member Of",
                        parent: "Structural Relationships",
                        state: { selected: true },
                    },
                    {
                        id: "3",
                        text: "Released On",
                        parent: "Structural Relationships",
                        state: { selected: false },
                    },
                    {
                        id: "4",
                        text: "Sublabel Of",
                        parent: "Structural Relationships",
                        state: { selected: false },
                    },
                    {
                        id: "5",
                        text: "Producer",
                        parent: "Production",
                        state: { selected: true },
                    },
                ],
            },
        };

        render(<SidebarLeft />);
        fireEvent.click(screen.getByRole("button", { name: "Filter" }));

        expect(screen.getByRole("checkbox", { name: "Alias" })).toBeChecked();
        expect(
            screen.getByRole("checkbox", { name: "Member Of" }),
        ).toBeChecked();
        expect(
            screen.getByRole("checkbox", { name: "Released On" }),
        ).not.toBeChecked();
        expect(
            screen.getByRole("checkbox", { name: "Sublabel Of" }),
        ).not.toBeChecked();

        fireEvent.click(screen.getByText("Production"));
        expect(
            screen.getByRole("checkbox", { name: "Producer" }),
        ).toBeChecked();
    });

    it("clears selected roles and requests a new network from the roles reset", () => {
        window.dgRoles = {
            core: {
                data: [
                    { id: "Production", text: "Production", parent: "#" },
                    {
                        id: "Structural Relationships",
                        text: "Structural Relationships",
                        parent: "#",
                    },
                    {
                        id: "alias",
                        text: "Alias",
                        parent: "Structural Relationships",
                        state: { selected: true },
                    },
                    {
                        id: "producer",
                        text: "Producer",
                        parent: "Production",
                        state: { selected: true },
                    },
                ],
            },
        };

        render(<SidebarLeft />);
        fireEvent.click(screen.getByRole("button", { name: "Filter" }));

        const reset = screen.getByRole("button", { name: "Reset roles" });
        expect(screen.getByText("Roles")).toContainElement(reset);
        expect(screen.getByRole("checkbox", { name: "Alias" })).toBeChecked();
        fireEvent.click(screen.getByText("Production"));
        expect(
            screen.getByRole("checkbox", { name: "Producer" }),
        ).toBeChecked();

        fireEvent.click(reset);

        expect(
            screen.getByRole("checkbox", { name: "Producer" }),
        ).not.toBeChecked();
        expect(screen.getByRole("checkbox", { name: "Alias" })).toBeChecked();
        expect(window.dispatchEvent).not.toHaveBeenCalled();

        vi.advanceTimersByTime(INIT.DEBOUNCE_DELAY);

        expect(window.dispatchEvent).toHaveBeenCalledTimes(1);
        const dispatchedEvent = vi.mocked(window.dispatchEvent).mock
            .calls[0][0];
        expect(dispatchedEvent).toBeInstanceOf(RequestNetworkEvent);
    });

    it("requests a new network after the year range changes", () => {
        render(<SidebarLeft />);
        fireEvent.click(screen.getByRole("button", { name: "Filter" }));

        fireEvent.change(screen.getByLabelText("Minimum year"), {
            target: { value: "1970" },
        });

        expect(screen.getByText("1970")).toBeInTheDocument();
        expect(window.dispatchEvent).not.toHaveBeenCalled();

        vi.advanceTimersByTime(INIT.DEBOUNCE_DELAY);

        expect(window.dispatchEvent).toHaveBeenCalledTimes(1);
        const dispatchedEvent = vi.mocked(window.dispatchEvent).mock
            .calls[0][0];
        expect(dispatchedEvent).toBeInstanceOf(RequestNetworkEvent);
    });

    it("starts and stops the layout from the layout section icons", () => {
        render(<SidebarLeft />);
        fireEvent.click(screen.getByRole("button", { name: "Layout" }));

        fireEvent.click(screen.getByRole("button", { name: "Start layout" }));
        fireEvent.click(screen.getByRole("button", { name: "Stop layout" }));

        expect(restartForceLayout).toHaveBeenCalledWith(
            FORCE.SIMULATION.ALPHA / 10.0,
        );
        expect(stopForceLayout).toHaveBeenCalledTimes(1);
    });

    it("calls printSvg function when Print button is clicked", () => {
        render(<SidebarLeft />);

        fireEvent.click(screen.getByRole("button", { name: "Print" }));
        fireEvent.click(
            within(
                document.getElementById("sidebar-print-panel") as HTMLElement,
            ).getByRole("button", { name: "Print" }),
        );

        expect(printSvg).toHaveBeenCalledTimes(1);
        expect(printSvg).toHaveBeenCalledWith(
            musigreeManager.svgDimensions[0],
            musigreeManager.svgDimensions[1],
        );
    });
});
