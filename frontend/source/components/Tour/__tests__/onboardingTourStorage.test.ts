import { describe, it, expect, beforeEach, vi } from "vitest";
import { ONBOARDING_TOUR_COMPLETED_KEY } from "../constants";
import {
    isOnboardingTourCompleted,
    markOnboardingTourCompleted,
} from "../onboardingTourStorage";

const localStorageMock = {
    getItem: vi.fn(),
    setItem: vi.fn(),
};

Object.defineProperty(window, "localStorage", { value: localStorageMock });

describe("onboardingTourStorage", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("returns false when tour completion key is absent", () => {
        localStorageMock.getItem.mockReturnValue(null);
        expect(isOnboardingTourCompleted()).toBe(false);
        expect(localStorageMock.getItem).toHaveBeenCalledWith(
            ONBOARDING_TOUR_COMPLETED_KEY,
        );
    });

    it("returns true when tour completion key is set", () => {
        localStorageMock.getItem.mockReturnValue("true");
        expect(isOnboardingTourCompleted()).toBe(true);
    });

    it("marks the onboarding tour as completed", () => {
        markOnboardingTourCompleted();
        expect(localStorageMock.setItem).toHaveBeenCalledWith(
            ONBOARDING_TOUR_COMPLETED_KEY,
            "true",
        );
    });

    it("treats getItem errors as not completed", () => {
        localStorageMock.getItem.mockImplementation(() => {
            throw new Error("QuotaExceededError");
        });
        expect(isOnboardingTourCompleted()).toBe(false);
    });

    it("ignores setItem errors when marking completed", () => {
        localStorageMock.setItem.mockImplementation(() => {
            throw new Error("QuotaExceededError");
        });
        expect(() => markOnboardingTourCompleted()).not.toThrow();
    });
});
