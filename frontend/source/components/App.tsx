/** @jsxImportSource react */
import React, { lazy, Suspense, useEffect, useRef, useState } from "react";
import { useTour } from "@reactour/tour";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import "bootstrap/dist/css/bootstrap.min.css";

import { Header } from "./Layout/Header.tsx";
import { SidebarLeft } from "./Layout/SidebarLeft";
import { SidebarRight } from "./Layout/SidebarRight";
import { NetworkView } from "./Visualization/NetworkView";
import LoadingAnimation from "./Visualization/LoadingAnimation";
import { NetworkProvider } from "../contexts/NetworkContext";
import { WindowProvider } from "../contexts/WindowContext";
import { useWindow } from "../contexts/useWindow";
import { LoadingProvider } from "../contexts/LoadingContext";
import { EntityProvider } from "../contexts/EntityContext";
import { DOM_IDS, FSM } from "../constants";
import { setSvgSize } from "../svg";
import { resetNetworkTransform } from "@/network/init.ts";
import { musigreeManager } from "@/core/singletons";
import { MusigreeTourProvider } from "./Tour";

/** Lazy-load heavy conditional UI (bundle-dynamic-imports) */
const HelpModal = lazy(() =>
    import("./Modals/HelpModal").then((m) => ({ default: m.HelpModal })),
);

/** Versioned localStorage key for return-visitor flag (client-localstorage-schema) */
const HAS_VISITED_BEFORE_KEY = "hasVisitedBefore:v1";

/**
 * Inner App component that uses WindowContext
 * This component is inside WindowProvider and can use the useWindow hook
 */
const AppContent: React.FC = (): React.ReactElement => {
    const [showHelpModal, setShowHelpModal] = useState<boolean>(false);
    const [_isReturnVisitor, setIsReturnVisitor] = useState<boolean>(false);
    const [isSidebarRightCollapsed, setIsSidebarRightCollapsed] =
        useState<boolean>(false);
    const { state: windowState } = useWindow();
    const { setIsOpen, setCurrentStep } = useTour();
    const startTourFrameRef = useRef<number | null>(null);

    // Check if this is a return visitor
    useEffect(() => {
        let hasVisitedBefore: string | null = null;
        try {
            hasVisitedBefore = localStorage.getItem(HAS_VISITED_BEFORE_KEY);
        } catch {
            // Private browsing, quota, or disabled; treat as first visit
        }
        if (!hasVisitedBefore) {
            try {
                localStorage.setItem(HAS_VISITED_BEFORE_KEY, "true");
            } catch {
                // Ignore; treat as first visit
            }
        } else {
            setIsReturnVisitor(true);
        }

        return (): void => {
            if (startTourFrameRef.current !== null) {
                cancelAnimationFrame(startTourFrameRef.current);
            }
        };
    }, []);

    // Navbar height CSS var is updated by WindowContext's single resize handler (client-event-listeners)

    const handleShowHelp = (): void => {
        setShowHelpModal(true);
    };

    const handleHideHelp = (): void => {
        setShowHelpModal(false);
    };

    const handleStartTourFromHelp = (): void => {
        setShowHelpModal(false);
        if (startTourFrameRef.current !== null) {
            cancelAnimationFrame(startTourFrameRef.current);
        }
        // Wait until the help modal has unmounted so the tour can highlight the page.
        startTourFrameRef.current = requestAnimationFrame(() => {
            startTourFrameRef.current = null;
            setCurrentStep(0);
            setIsOpen(true);
        });
    };

    const handleToggleSidebarRight = (): void => {
        const newCollapsedState = !isSidebarRightCollapsed;
        setIsSidebarRightCollapsed(newCollapsedState);
        musigreeManager.isSidebarRightCollapsed = newCollapsedState;

        // Setup window dimensions on SVG element
        setSvgSize(DOM_IDS.SVG_ID);

        resetNetworkTransform();

        // Dispatch custom resize event
        window.dispatchEvent(new CustomEvent(FSM.EVENTS.RESIZE));
    };

    return (
        <NetworkProvider>
            <LoadingProvider>
                <EntityProvider>
                    <Container fluid className="d-flex flex-column h-sm-100">
                        <Row>
                            <Header onShowHelp={handleShowHelp} />
                        </Row>

                        <Row className="flex-sm-nowrap d-flex flex-column flex-sm-row h-sm-100">
                            {/* Mobile stacks main, right, then left. From sm up the row is left, main, right. */}
                            <div className="sidebar-left-container p-0 order-3 order-sm-1">
                                <SidebarLeft />
                            </div>

                            <div className="main-container p-0 order-1 order-sm-2">
                                <div className="flex-sm-column flex-row h-sm-100">
                                    <NetworkView />
                                    <LoadingAnimation />
                                </div>
                            </div>

                            <div
                                className={`${
                                    isSidebarRightCollapsed
                                        ? "sidebar-right-container-collapsed"
                                        : "sidebar-right-container"
                                } p-0 order-sm-3 order-2`}
                            >
                                <div className="flex-sm-column flex-row h-sm-100">
                                    {/* sidebar right panel */}
                                    <SidebarRight
                                        isCollapsed={isSidebarRightCollapsed}
                                        isMobile={windowState.isMobile}
                                        onToggleCollapse={
                                            handleToggleSidebarRight
                                        }
                                    />
                                </div>
                            </div>
                        </Row>

                        {showHelpModal ? (
                            <Suspense fallback={null}>
                                <HelpModal
                                    show={showHelpModal}
                                    onHide={handleHideHelp}
                                    onStartTour={handleStartTourFromHelp}
                                />
                            </Suspense>
                        ) : null}
                    </Container>
                </EntityProvider>
            </LoadingProvider>
        </NetworkProvider>
    );
};

/**
 * Main App component that serves as the container for the React application.
 */
const App: React.FC = (): React.ReactElement => {
    return (
        <MusigreeTourProvider>
            <WindowProvider>
                <AppContent />
            </WindowProvider>
        </MusigreeTourProvider>
    );
};

export default App;
