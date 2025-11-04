import React from "react";
import { describe, it, expect } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { act } from "react-dom/test-utils";
import { EntityProvider } from "../EntityContext";
import { useEntity } from "../useEntity";
import type { EntityData } from "../../entities";

const Consumer: React.FC = () => {
    const { state } = useEntity();
    return <div data-testid="entity-name">{state.entity?.name ?? "-"}</div>;
};

describe("EntityProvider", () => {
    it("updates context on musigree:entity-details-updated", async () => {
        render(
            <EntityProvider>
                <Consumer />
            </EntityProvider>,
        );

        // Initially placeholder
        expect(screen.getByTestId("entity-name").textContent).toBe("-");

        const entity: EntityData = {
            id: 1,
            type: "artist",
            name: "Entity One",
            metadata: {},
            entities: {},
            relation_counts: {},
            countries: "US",
            genres: null,
            styles: null,
        };

        await act(async () => {
            const evt = new CustomEvent<EntityData>(
                "musigree:entity-details-updated",
                { detail: entity },
            );
            window.dispatchEvent(evt);
        });

        await waitFor(() => {
            expect(screen.getByTestId("entity-name").textContent).toBe(
                "Entity One",
            );
        });
    });
});
