/** @jsxImportSource react */
import React from "react";
import { TourProvider, components } from "@reactour/tour";
import { onboardingTourSteps } from "./steps";
import { OnboardingTourController } from "./OnboardingTourController";
import { markOnboardingTourCompleted } from "./onboardingTourStorage";

type NavigationProps = React.ComponentProps<typeof components.Navigation>;

const TourNavigation: React.FC<NavigationProps> = (props) => {
    const { setIsOpen } = props;

    return (
        <div>
            <components.Navigation {...props} />
            <button
                type="button"
                className="btn btn-link btn-sm text-secondary p-0 mt-2"
                onClick={() => setIsOpen(false)}
            >
                Skip tour
            </button>
        </div>
    );
};

interface MusigreeTourProviderProps {
    children: React.ReactNode;
}

/** Wraps the app with reactour and first-visit onboarding behavior. */
export const MusigreeTourProvider: React.FC<MusigreeTourProviderProps> = ({
    children,
}) => {
    return (
        <TourProvider
            steps={onboardingTourSteps}
            components={{ Navigation: TourNavigation }}
            showBadge
            showCloseButton
            scrollSmooth
            beforeClose={() => {
                markOnboardingTourCompleted();
            }}
            styles={{
                popover: (base) => ({
                    ...base,
                    borderRadius: 8,
                    padding: 16,
                    maxWidth: 320,
                }),
                maskArea: (base) => ({
                    ...base,
                    rx: 8,
                }),
            }}
        >
            <OnboardingTourController />
            {children}
        </TourProvider>
    );
};
