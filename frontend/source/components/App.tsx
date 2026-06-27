/** @jsxImportSource react */
import React, { useState, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";

import { Header } from "./Layout/Header.tsx";
import { SidebarLeft } from "./Layout/SidebarLeft";
import { SidebarRight } from "./Layout/SidebarRight";
import { HelpModal } from "./Modals/HelpModal";
import { NetworkView } from "./Visualization/NetworkView";
import LoadingAnimation from "./Visualization/LoadingAnimation";
import { RolesOverlay } from "./Overlays/RolesOverlay";
import { NetworkProvider } from "../contexts/NetworkContext";
import { WindowProvider } from "../contexts/WindowContext";
import { useWindow } from "../contexts/useWindow";
import { LoadingProvider } from "../contexts/LoadingContext";
import { EntityProvider } from "../contexts/EntityContext";
import { FSM, DOM_IDS } from "../constants";
import { setSvgSize } from "../svg";
import type { TreeConfig } from "../roles";
import { resetNetworkTransform } from "@/network/init.ts";
import { musigreeManager } from "../core/singletons";
import { MusigreeTourProvider } from "./Tour";

// Extending the Window interface is handled in init.ts already
// We're just importing the TreeConfig type for our internal usage

/** Versioned localStorage key for return-visitor flag (client-localstorage-schema) */
const HAS_VISITED_BEFORE_KEY = "hasVisitedBefore:v1";

/**
 * Inner App component that uses WindowContext
 * This component is inside WindowProvider and can use the useWindow hook
 */
const AppContent: React.FC = (): React.ReactElement => {
    const [showHelpModal, setShowHelpModal] = useState<boolean>(false);
    const [showRolesOverlay, setShowRolesOverlay] = useState<boolean>(false);
    const [_isReturnVisitor, setIsReturnVisitor] = useState<boolean>(false);
    const [rolesConfig, setRolesConfig] = useState<TreeConfig>();
    const [isSidebarRightCollapsed, setIsSidebarRightCollapsed] =
        useState<boolean>(false);
    const { state: windowState } = useWindow();

    // Check if this is a return visitor and load roles data
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

        // Get roles data from global variable
        if (window.dgRoles) {
            setRolesConfig(window.dgRoles);
        }

        // Event listeners for showing/hiding overlays
        const handleShowRoles = (): void => setShowRolesOverlay(true);
        const handleHideRoles = (): void => setShowRolesOverlay(false);

        window.addEventListener("musigree:show-roles-overlay", handleShowRoles);
        window.addEventListener("musigree:hide-roles-overlay", handleHideRoles);

        return (): void => {
            window.removeEventListener(
                "musigree:show-roles-overlay",
                handleShowRoles,
            );
            window.removeEventListener(
                "musigree:hide-roles-overlay",
                handleHideRoles,
            );
        };
    }, []);

    // Navbar height CSS var is updated by WindowContext's single resize handler (client-event-listeners)

    const handleShowHelp = (): void => {
        setShowHelpModal(true);
    };

    const handleHideHelp = (): void => {
        setShowHelpModal(false);
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
                            <div className="sidebar-left-container p-0 order-sm-1 d-none d-sm-block">
                                <div className="flex-sm-column flex-row h-sm-100">
                                    {/* sidebar left panel */}
                                    <SidebarLeft />
                                </div>
                            </div>

                            <div className="main-container flex-sm-fill p-0 order-sm-2 order-1">
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

                            {/* Use the React components for overlays */}
                            <RolesOverlay
                                roles={rolesConfig}
                                show={showRolesOverlay}
                                onHide={(): void => setShowRolesOverlay(false)}
                            />
                        </Row>

                        <HelpModal
                            show={showHelpModal}
                            onHide={handleHideHelp}
                        />
                    </Container>
                </EntityProvider>
            </LoadingProvider>
        </NetworkProvider>
    );
};

/**
 * Main App component that serves as the container for the React application.
 * During migration, this will gradually replace the existing jQuery-based UI.
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
