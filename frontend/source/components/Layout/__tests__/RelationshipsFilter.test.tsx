import { describe, it, expect, vi, afterEach } from "vitest";
import { act, render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { RelationshipsFilter } from "../RelationshipsFilter";
import {
    getSelectedRoles,
    resetFiltersForRandomArtist,
    updateSelectedRoleIds,
} from "../../../roles";
import type { TreeNode } from "../../../roles";

const relationships: TreeNode[] = [
    { id: "alias", text: "Alias", state: { selected: true } },
    { id: "member", text: "Member Of" },
    { id: "sublabel", text: "Sublabel Of" },
    { id: "released", text: "Released On" },
];

describe("RelationshipsFilter", () => {
    afterEach(() => {
        updateSelectedRoleIds([]);
    });

    it("lays the relationships out in two columns", () => {
        render(
            <RelationshipsFilter
                relationships={relationships}
                onSelectionChange={vi.fn()}
            />,
        );

        const options = screen
            .getByRole("group", { name: "Relationships" })
            .querySelectorAll(".relationships-option span");

        expect(Array.from(options, (option) => option.textContent)).toEqual([
            "Alias",
            "Member Of",
            "Sublabel Of",
            "Released On",
        ]);
        expect(screen.getByRole("checkbox", { name: "Alias" })).toBeChecked();
        expect(
            screen.getByRole("checkbox", { name: "Member Of" }),
        ).not.toBeChecked();
    });

    it("toggles a relationship without clearing other selected roles", () => {
        updateSelectedRoleIds(["producer"]);
        const onSelectionChange = vi.fn();
        render(
            <RelationshipsFilter
                relationships={relationships}
                onSelectionChange={onSelectionChange}
            />,
        );

        fireEvent.click(screen.getByRole("checkbox", { name: "Member Of" }));

        expect(onSelectionChange).toHaveBeenCalledTimes(1);
        const selected = getSelectedRoles();
        expect(selected).toContain("Member Of");
        expect(selected).toContain("Alias");
        expect(selected).toContain("producer");
    });

    it("checks only Alias and Member Of when a random artist is requested", () => {
        const onSelectionChange = vi.fn();
        render(
            <RelationshipsFilter
                relationships={relationships}
                onSelectionChange={onSelectionChange}
            />,
        );

        fireEvent.click(screen.getByRole("checkbox", { name: "Released On" }));
        onSelectionChange.mockClear();

        act(() => {
            resetFiltersForRandomArtist();
        });

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
        expect(onSelectionChange).not.toHaveBeenCalled();
        expect(getSelectedRoles()).toEqual(["Alias", "Member Of"]);
    });
});
