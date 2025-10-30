import { describe, it, expect } from "vitest";
import React from "react";
import { render, screen } from "@testing-library/react";
import { Details } from "../../Layout/Details";
import type { EntityData } from "../../../entities";

describe("Details", () => {
    it("renders placeholder when no entity", () => {
        render(<Details entity={null} />);
        expect(screen.getByText(/Details/i)).toBeInTheDocument();
    });

    it("renders fields from EntityData", () => {
        const entity: EntityData = {
            id: 123,
            type: "artist",
            name: "Test Artist",
            metadata: {},
            entities: {},
            relation_counts: { members: 2, aliases: 1 },
            countries: "UK",
            genres: "Electronic",
            styles: "House",
        };

        render(<Details entity={entity} />);

        expect(screen.getByText("Test Artist")).toBeInTheDocument();
        expect(screen.getByText("artist")).toBeInTheDocument();
        expect(screen.getByText("UK")).toBeInTheDocument();
        expect(screen.getByText("Electronic")).toBeInTheDocument();
        expect(screen.getByText("House")).toBeInTheDocument();
        expect(screen.getByText(/members: 2/i)).toBeInTheDocument();
        expect(screen.getByText(/aliases: 1/i)).toBeInTheDocument();
    });
});
