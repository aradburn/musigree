/** @jsxImportSource react */
import { useEffect, type FC } from "react";
import { useTour } from "@reactour/tour";
import { isOnboardingTourCompleted } from "./onboardingTourStorage";

/**
 * Opens the onboarding tour automatically for first-time visitors once the UI
 * has mounted and tour targets are present in the DOM.
 */
export const OnboardingTourController: FC = () => {
    const { setIsOpen } = useTour();

    useEffect(() => {
        if (isOnboardingTourCompleted()) {
            return;
        }

        const frameId = requestAnimationFrame(() => {
            setIsOpen(true);
        });

        return (): void => {
            cancelAnimationFrame(frameId);
        };
    }, [setIsOpen]);

    return null;
};
