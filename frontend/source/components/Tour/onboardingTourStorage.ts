import { ONBOARDING_TOUR_COMPLETED_KEY } from "./constants";

/** Returns whether the user has already completed or skipped the onboarding tour. */
export const isOnboardingTourCompleted = (): boolean => {
    try {
        return localStorage.getItem(ONBOARDING_TOUR_COMPLETED_KEY) === "true";
    } catch {
        // Private browsing, quota, or disabled storage
        return false;
    }
};

/** Persists onboarding tour completion so it is not shown again. */
export const markOnboardingTourCompleted = (): void => {
    try {
        localStorage.setItem(ONBOARDING_TOUR_COMPLETED_KEY, "true");
    } catch {
        // Ignore; tour may reappear on next visit if storage is unavailable
    }
};
