import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { act } from "react-dom/test-utils";
import { SidebarRight } from "../../Layout/SidebarRight";
import { EntityProvider } from "../../../contexts/EntityContext";
import type { EntityData } from "../../../entities";

describe("SidebarRight + EntityProvider integration", () => {
    it("shows updated details after event dispatch", async () => {
        render(
            <EntityProvider>
                <SidebarRight />
            </EntityProvider>,
        );

        // Initially shows placeholder title "Details"
        expect(screen.getByText(/Details/i)).toBeInTheDocument();

        const entity: EntityData = {
            id: 42,
            type: "artist",
            name: "Integration Artist",
            metadata: {},
            entities: {},
            relation_counts: { members: 3 },
            countries: "UK",
            genres: "Electronic",
            styles: "House",
        };

        await act(async () => {
            window.dispatchEvent(
                new CustomEvent<EntityData>("musigree:entity-details-updated", {
                    detail: entity,
                }),
            );
        });

        // Title updates to entity name
        await waitFor(() =>
            expect(screen.getByText("Integration Artist")).toBeInTheDocument(),
        );
        // Some fields
        expect(screen.getByText("artist")).toBeInTheDocument();
        expect(screen.getByText("UK")).toBeInTheDocument();
        expect(screen.getByText("Electronic")).toBeInTheDocument();
        expect(screen.getByText("House")).toBeInTheDocument();
        expect(screen.getByText(/members: 3/i)).toBeInTheDocument();
    });
});
