/** @jsxImportSource react */
import { describe, it, expect, beforeEach, vi, afterEach } from "vitest";
import { render, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom";
import { TourProvider } from "@reactour/tour";
import { OnboardingTourController } from "../OnboardingTourController";
import { ONBOARDING_TOUR_COMPLETED_KEY } from "../constants";

const setIsOpen = vi.fn();

vi.mock("@reactour/tour", async (importOriginal) => {
    const actual = await importOriginal<typeof import("@reactour/tour")>();
    return {
        ...actual,
        useTour: () => ({
            isOpen: false,
            currentStep: 0,
            steps: [],
            setIsOpen,
            setCurrentStep: vi.fn(),
            setSteps: vi.fn(),
            meta: "",
            setMeta: vi.fn(),
        }),
    };
});

const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
};

Object.defineProperty(window, "localStorage", { value: localStorageMock });

describe("OnboardingTourController", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        localStorageMock.getItem.mockReturnValue(null);
        vi.spyOn(window, "requestAnimationFrame").mockImplementation(
            (callback: FrameRequestCallback) => {
                callback(0);
                return 1;
            },
        );
        vi.spyOn(window, "cancelAnimationFrame").mockImplementation(() => {});
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("opens the tour for first-time visitors", async () => {
        render(
            <TourProvider steps={[]}>
                <OnboardingTourController />
            </TourProvider>,
        );

        await waitFor(() => {
            expect(setIsOpen).toHaveBeenCalledWith(true);
        });
    });

    it("does not open the tour for returning visitors", async () => {
        localStorageMock.getItem.mockReturnValue("true");

        render(
            <TourProvider steps={[]}>
                <OnboardingTourController />
            </TourProvider>,
        );

        await waitFor(() => {
            expect(localStorageMock.getItem).toHaveBeenCalledWith(
                ONBOARDING_TOUR_COMPLETED_KEY,
            );
        });
        expect(setIsOpen).not.toHaveBeenCalled();
    });
});
