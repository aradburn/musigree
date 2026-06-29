/** @jsxImportSource react */
import React from "react";
import { components, TourProvider } from "@reactour/tour";
import { onboardingTourSteps } from "./steps";
import { OnboardingTourController } from "./OnboardingTourController";
import { markOnboardingTourCompleted } from "./onboardingTourStorage";

type NavigationProps = React.ComponentProps<typeof components.Navigation>;

const TourNavigation: React.FC<NavigationProps> = (props) => {
    const { setIsOpen, currentStep, steps } = props;

    return (
        <div>
            <components.Navigation {...props} />
            <div className="d-flex flex-row align-items-center justify-content-between px-0 py-0 mt-2">
                <span>
                    <button
                        type="button"
                        className="btn btn-link btn-sm text-secondary p-0"
                        onClick={() => setIsOpen(false)}
                    >
                        Skip tour
                    </button>
                </span>
                <span className="mb-0">
                    Step {currentStep + 1} of {steps.length}
                </span>
            </div>
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
            showBadge={false}
            showDots={false}
            showCloseButton
            scrollSmooth
            beforeClose={() => {
                markOnboardingTourCompleted();
            }}
            styles={{
                popover: (base) => ({
                    ...base,
                    border: "0.2rem solid #2F4F4F",
                    borderRadius: 8,
                    padding: "2rem",
                    maxWidth: "32rem",
                    "--reactour-accent": "#2F4F4F",
                    backgroundColor: "#F9FBFA",
                    className: "tour-popover",
                }),
                maskWrapper: (base) => ({
                    ...base,
                    color: "#2F4F4FAA",
                }),
                maskArea: (base) => ({
                    ...base,
                    rx: 8,
                }),
            }}
            padding={{ popover: [-30, -20] }}
        >
            <OnboardingTourController />
            {children}
        </TourProvider>
    );
};
