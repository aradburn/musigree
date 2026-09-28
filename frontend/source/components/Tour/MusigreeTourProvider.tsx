/** @jsxImportSource react */
import React from "react";
import { components, TourProvider } from "@reactour/tour";
import { onboardingTourSteps } from "./steps";

const TOUR_ACCENT_COLOR = "#2F4F4F";
const TOUR_SURFACE_COLOR = "#F9FBFA";

type NavigationProps = React.ComponentProps<typeof components.Navigation>;

const TourNextButton: NonNullable<NavigationProps["nextButton"]> = ({
    Button,
    currentStep,
    stepsLength,
    setIsOpen,
}) => {
    const isLastStep = currentStep === stepsLength - 1;
    if (!isLastStep) {
        return <Button />;
    }

    return (
        <button
            type="button"
            className="btn btn-primary btn-sm tour-end-button"
            onClick={() => {
                setIsOpen(false);
            }}
        >
            End Tour
        </button>
    );
};

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

/** Wraps the app with reactour. The intro tour is started from the help modal. */
export const MusigreeTourProvider: React.FC<MusigreeTourProviderProps> = ({
    children,
}) => {
    return (
        <TourProvider
            steps={onboardingTourSteps}
            components={{ Navigation: TourNavigation }}
            nextButton={TourNextButton}
            showBadge={false}
            showDots={false}
            showCloseButton
            scrollSmooth
            styles={{
                popover: (base) => ({
                    ...base,
                    border: `0.2rem solid ${TOUR_ACCENT_COLOR}`,
                    borderRadius: 8,
                    padding: "2rem",
                    maxWidth: "32rem",
                    "--reactour-accent": TOUR_ACCENT_COLOR,
                    backgroundColor: TOUR_SURFACE_COLOR,
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
            {children}
        </TourProvider>
    );
};
