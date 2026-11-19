import { describe, it, expect, vi, afterEach } from "vitest";
import { act, render, screen, fireEvent, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { RolesFilter } from "../RolesFilter";
import {
    getSelectedRoles,
    rememberRelationships,
    resetFiltersForRandomArtist,
    updateSelectedRoleIds,
} from "../../../roles";
import type { TreeConfig } from "../../../roles";

const roles: TreeConfig = {
    core: {
        data: [
            {
                id: "production",
                text: "Production",
                state: { selected: true },
            },
            {
                id: "producer",
                text: "Producer",
                parent: "production",
                state: { selected: true },
            },
        ],
    },
};

describe("RolesFilter", () => {
    afterEach(() => {
        updateSelectedRoleIds([]);
    });

    it("updates the selected roles and notifies the parent", async () => {
        const onSelectionChange = vi.fn();
        render(
            <RolesFilter roles={roles} onSelectionChange={onSelectionChange} />,
        );

        // The tree measures itself before the checkbox is in the document.
        const production = await screen.findByRole("checkbox", {
            name: "Production",
        });
        fireEvent.click(production);

        await waitFor(() => {
            expect(onSelectionChange).toHaveBeenCalledTimes(1);
        });
        expect(getSelectedRoles()).not.toContain("Production");
    });

    it("grows to fit open rows instead of a fixed viewport", () => {
        render(<RolesFilter roles={roles} onSelectionChange={vi.fn()} />);

        const tree = document.querySelector(".roles-tree");
        expect(tree).toBeInstanceOf(HTMLElement);
        const closedHeight = Number.parseFloat(
            (tree as HTMLElement).style.height,
        );
        expect(closedHeight).toBeGreaterThan(0);
        expect(
            document.querySelector(".roles-filter-tree"),
        ).not.toHaveAttribute("style");

        fireEvent.click(screen.getByText("Production"));

        const openHeight = Number.parseFloat(
            (tree as HTMLElement).style.height,
        );
        expect(openHeight).toBeGreaterThan(closedHeight);
    });

    it("keeps selections that belong to another filter", () => {
        updateSelectedRoleIds(["alias"]);
        const onSelectionChange = vi.fn();
        render(
            <RolesFilter roles={roles} onSelectionChange={onSelectionChange} />,
        );

        fireEvent.click(screen.getByRole("checkbox", { name: "Production" }));

        expect(getSelectedRoles()).toContain("alias");
        expect(getSelectedRoles()).not.toContain("Production");
    });

    it("clears every role in the tree and notifies the parent", () => {
        updateSelectedRoleIds(["alias"]);
        const onSelectionChange = vi.fn();
        render(
            <RolesFilter roles={roles} onSelectionChange={onSelectionChange} />,
        );

        const heading = screen.getByText("Roles");
        const reset = screen.getByRole("button", { name: "Reset roles" });
        expect(heading).toHaveClass("h6");
        expect(heading).toContainElement(reset);
        expect(heading.lastElementChild).toBe(reset);
        expect(
            reset.querySelector("i.bi-arrow-counterclockwise"),
        ).toBeInTheDocument();

        fireEvent.click(screen.getByText("Production"));
        expect(
            screen.getByRole("checkbox", { name: "Producer" }),
        ).toBeChecked();

        fireEvent.click(reset);

        expect(
            screen.getByRole("checkbox", { name: "Production" }),
        ).not.toBeChecked();
        expect(
            screen.getByRole("checkbox", { name: "Producer" }),
        ).not.toBeChecked();
        expect(getSelectedRoles()).toEqual(["alias"]);
        expect(onSelectionChange).toHaveBeenCalledTimes(1);
    });

    it("clears the role tree when a random artist is requested", () => {
        rememberRelationships([
            { id: "alias", text: "Alias" },
            { id: "member", text: "Member Of" },
            { id: "released", text: "Released On" },
        ]);
        updateSelectedRoleIds(["alias", "released"]);
        const onSelectionChange = vi.fn();
        render(
            <RolesFilter roles={roles} onSelectionChange={onSelectionChange} />,
        );

        fireEvent.click(screen.getByText("Production"));
        expect(
            screen.getByRole("checkbox", { name: "Producer" }),
        ).toBeChecked();

        act(() => {
            resetFiltersForRandomArtist();
        });

        expect(
            screen.getByRole("checkbox", { name: "Production" }),
        ).not.toBeChecked();
        expect(
            screen.getByRole("checkbox", { name: "Producer" }),
        ).not.toBeChecked();
        expect(onSelectionChange).not.toHaveBeenCalled();
        expect(getSelectedRoles()).toEqual(["Alias", "Member Of"]);
    });
});
