import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { RolesFilter } from "../RolesFilter";
import { getSelectedRoles, updateSelectedRoleIds } from "../../../roles";
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

    it("updates the selected roles and notifies the parent", () => {
        const onSelectionChange = vi.fn();
        render(
            <RolesFilter roles={roles} onSelectionChange={onSelectionChange} />,
        );

        fireEvent.click(screen.getByRole("checkbox", { name: "Production" }));

        expect(onSelectionChange).toHaveBeenCalledTimes(1);
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
});
