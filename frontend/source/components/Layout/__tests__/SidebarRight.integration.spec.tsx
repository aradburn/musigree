import React from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { act } from "react-dom/test-utils";

import { SidebarRight } from "../../Layout/SidebarRight";
import { EntityProvider } from "../../../contexts/EntityContext";
import type { EntityData } from "../../../entities";

const INTRO_TITLE = "MUSIGREE";
const INTRO_BODY =
    "is an interactive visualization of the relationships between musicians, bands and labels.";

const sampleEntity: EntityData = {
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

const renderSidebar = (): void => {
    render(
        <EntityProvider>
            <SidebarRight
                isCollapsed={false}
                isMobile={false}
                onToggleCollapse={(): void => undefined}
            />
        </EntityProvider>,
    );
};

const dispatchEntity = async (entity: EntityData | null): Promise<void> => {
    await act(async () => {
        window.dispatchEvent(
            new CustomEvent<EntityData | null>(
                "musigree:entity-details-updated",
                {
                    detail: entity,
                },
            ),
        );
    });
};

describe("SidebarRight + EntityProvider integration", () => {
    beforeEach(() => {
        window.history.pushState({}, "", "/");
    });

    it("shows the intro instead of Details when the URL has no query", () => {
        renderSidebar();

        const title = screen.getByText(INTRO_TITLE);
        expect(title).toBeInTheDocument();
        expect(title).toHaveClass("h3");
        const intro = title.closest("p");
        expect(intro).toHaveClass("text-center");
        expect(intro?.querySelector("br")).toBeInTheDocument();
        expect(title.nextElementSibling?.tagName).toBe("BR");
        expect(screen.getByText(INTRO_BODY)).toHaveClass("h4");
        expect(intro?.parentElement).toHaveClass(
            "justify-content-center",
            "flex-fill",
        );
        expect(screen.queryByText("Details")).not.toBeInTheDocument();
        expect(
            screen.queryByRole("button", { name: "Close sidebar" }),
        ).not.toBeInTheDocument();
    });

    it("shows Details immediately when the URL has query parameters", () => {
        window.history.pushState({}, "", "/?roles=Alias");
        renderSidebar();

        expect(screen.getByText("Details")).toBeInTheDocument();
        expect(screen.queryByText(INTRO_TITLE)).not.toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: "Close sidebar" }),
        ).toBeInTheDocument();
    });

    it("shows updated details after the network receives them", async () => {
        renderSidebar();

        expect(screen.getByText(INTRO_TITLE)).toBeInTheDocument();
        expect(
            screen.queryByRole("button", { name: "Close sidebar" }),
        ).not.toBeInTheDocument();

        await dispatchEntity(sampleEntity);

        expect(
            await screen.findByText("Integration Artist"),
        ).toBeInTheDocument();
        expect(screen.queryByText(INTRO_TITLE)).not.toBeInTheDocument();
        expect(screen.getByText("Artist")).toBeInTheDocument();
        expect(screen.getByText("UK")).toBeInTheDocument();
        expect(screen.getByText("Electronic")).toBeInTheDocument();
        expect(screen.getByText("House")).toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: "Close sidebar" }),
        ).toBeInTheDocument();
    });

    it("keeps Details visible after they have been received", async () => {
        renderSidebar();

        await dispatchEntity(sampleEntity);
        expect(
            await screen.findByText("Integration Artist"),
        ).toBeInTheDocument();

        await dispatchEntity(null);

        expect(screen.getByText("Details")).toBeInTheDocument();
        expect(screen.queryByText(INTRO_TITLE)).not.toBeInTheDocument();
        expect(
            screen.getByRole("button", { name: "Close sidebar" }),
        ).toBeInTheDocument();
    });

    it("shows the open button when the sidebar is collapsed", () => {
        render(
            <EntityProvider>
                <SidebarRight
                    isCollapsed={true}
                    isMobile={false}
                    onToggleCollapse={(): void => undefined}
                />
            </EntityProvider>,
        );

        expect(
            screen.getByRole("button", { name: "Open sidebar" }),
        ).toBeInTheDocument();
        expect(screen.queryByText(INTRO_TITLE)).not.toBeInTheDocument();
    });
});
