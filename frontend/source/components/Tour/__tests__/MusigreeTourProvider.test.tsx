/** @jsxImportSource react */
import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { MusigreeTourProvider } from "../MusigreeTourProvider";
import { ONBOARDING_TOUR_COMPLETED_KEY } from "../constants";

const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
};

Object.defineProperty(window, "localStorage", { value: localStorageMock });

const renderTourTargets = (): void => {
    document.body.innerHTML = `
        <nav id="nav-top"></nav>
        <input id="musigree-search" />
        <main id="svg-container-fluid"></main>
        <div data-tour="random"></div>
        <div data-tour="help"></div>
    `;
};

describe("MusigreeTourProvider", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorageMock.getItem.mockReturnValue(null);
        renderTourTargets();
    });

    it("shows the welcome step for first-time visitors", async () => {
        render(
            <MusigreeTourProvider>
                <div>App content</div>
            </MusigreeTourProvider>,
        );

        expect(
            await screen.findByText(/Welcome to Musigree/i),
        ).toBeInTheDocument();
    });

    it("does not show the tour for returning visitors", async () => {
        localStorageMock.getItem.mockReturnValue("true");

        render(
            <MusigreeTourProvider>
                <div>App content</div>
            </MusigreeTourProvider>,
        );

        await waitFor(() => {
            expect(localStorageMock.getItem).toHaveBeenCalledWith(
                ONBOARDING_TOUR_COMPLETED_KEY,
            );
        });
        expect(
            screen.queryByText(/Welcome to Musigree/i),
        ).not.toBeInTheDocument();
    });

    it("marks the tour complete when the user skips", async () => {
        const user = userEvent.setup();

        render(
            <MusigreeTourProvider>
                <div>App content</div>
            </MusigreeTourProvider>,
        );

        const skipButton = await screen.findByRole("button", {
            name: /skip tour/i,
        });
        await user.click(skipButton);

        expect(localStorageMock.setItem).toHaveBeenCalledWith(
            ONBOARDING_TOUR_COMPLETED_KEY,
            "true",
        );
        await waitFor(() => {
            expect(
                screen.queryByText(/Welcome to Musigree/i),
            ).not.toBeInTheDocument();
        });
    });
});
