/** @jsxImportSource react */
import type { FC } from "react";
import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom";
import { useTour } from "@reactour/tour";
import { MusigreeTourProvider } from "../MusigreeTourProvider";

const setupTourTargets = (): void => {
    document.body.innerHTML = `
        <div id="musigree"></div>
        <nav id="nav-top"></nav>
        <input id="musigree-search" />
        <main id="svg-container-fluid"></main>
        <div data-tour="random"></div>
        <div data-tour="help"></div>
    `;
};

const OpenTourButton: FC = () => {
    const { setCurrentStep, setIsOpen } = useTour();

    return (
        <button
            type="button"
            onClick={() => {
                setCurrentStep(0);
                setIsOpen(true);
            }}
        >
            Open tour
        </button>
    );
};

describe("MusigreeTourProvider", () => {
    beforeEach(() => {
        setupTourTargets();
    });

    it("does not open the tour automatically", async () => {
        render(
            <MusigreeTourProvider>
                <div>App content</div>
            </MusigreeTourProvider>,
        );

        await waitFor(() => {
            expect(screen.getByText("App content")).toBeInTheDocument();
        });
        expect(
            screen.queryByText(/Welcome to Musigree/i),
        ).not.toBeInTheDocument();
    });

    it("closes the tour when the user skips", async () => {
        const user = userEvent.setup();

        render(
            <MusigreeTourProvider>
                <OpenTourButton />
            </MusigreeTourProvider>,
        );

        await user.click(screen.getByRole("button", { name: /open tour/i }));

        const skipButton = await screen.findByRole("button", {
            name: /skip tour/i,
        });
        await user.click(skipButton);

        await waitFor(() => {
            expect(
                screen.queryByText(/Welcome to Musigree/i),
            ).not.toBeInTheDocument();
        });
    });

    it("shows End Tour on the last step and closes the tour", async () => {
        const user = userEvent.setup();

        render(
            <MusigreeTourProvider>
                <OpenTourButton />
            </MusigreeTourProvider>,
        );

        await user.click(screen.getByRole("button", { name: /open tour/i }));
        expect(
            screen.queryByRole("button", { name: /end tour/i }),
        ).not.toBeInTheDocument();

        const stepCount = 5;
        for (let step = 0; step < stepCount - 1; step += 1) {
            await user.click(
                screen.getByRole("button", { name: /go to next step/i }),
            );
        }

        const endTourButton = await screen.findByRole("button", {
            name: /end tour/i,
        });
        expect(endTourButton).toHaveClass("btn-primary", "tour-end-button");
        expect(
            screen.queryByRole("button", { name: /go to next step/i }),
        ).not.toBeInTheDocument();

        await user.click(endTourButton);

        await waitFor(() => {
            expect(
                screen.queryByText(/Open Help anytime/i),
            ).not.toBeInTheDocument();
        });
    });
});
