/** @jsxImportSource react */
import React, { useState, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";

import { Header } from "./Layout/Header.tsx";
import { SidebarLeft } from "./Layout/SidebarLeft";
import { SidebarRight } from "./Layout/SidebarRight";
import { HelpModal } from "./Modals/HelpModal";
import { NetworkView } from "./Visualization/NetworkView";
import { LoadingAnimation } from "./Visualization";
import { RolesOverlay } from "./Overlays/RolesOverlay";
import { NetworkProvider } from "../contexts/NetworkContext";
import { WindowProvider } from "../contexts/WindowContext";
import { LoadingProvider } from "../contexts/LoadingContext";
import { EntityProvider } from "../contexts/EntityContext";
import type { TreeConfig } from "../roles";

// Extending the Window interface is handled in init.ts already
// We're just importing the TreeConfig type for our internal usage

/**
 * Main App component that serves as the container for the React application.
 * During migration, this will gradually replace the existing jQuery-based UI.
 */
const App: React.FC = (): React.ReactElement => {
    const [showHelpModal, setShowHelpModal] = useState<boolean>(false);
    const [showRolesOverlay, setShowRolesOverlay] = useState<boolean>(false);
    const [_isReturnVisitor, setIsReturnVisitor] = useState<boolean>(false);
    const [rolesConfig, setRolesConfig] = useState<TreeConfig>();

    // Check if this is a return visitor and load roles data
    useEffect(() => {
        // Check for return visitor status
        const hasVisitedBefore = localStorage.getItem("hasVisitedBefore");
        if (!hasVisitedBefore) {
            // First time visitor - show welcome modal
            localStorage.setItem("hasVisitedBefore", "true");
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

    // Add this new effect for updating CSS variable with navbar height
    useEffect(() => {
        const updateNavbarHeightVar = (): void => {
            const navbar = document.querySelector("nav.navbar");
            if (navbar) {
                const height = navbar.getBoundingClientRect().height;
                document.documentElement.style.setProperty(
                    "--navbar-height",
                    `${height}px`,
                );
            }
        };

        // Initial update
        updateNavbarHeightVar();

        // Update on resize
        window.addEventListener("resize", updateNavbarHeightVar);

        return (): void => {
            window.removeEventListener("resize", updateNavbarHeightVar);
        };
    }, []);

    const handleShowHelp = (): void => {
        setShowHelpModal(true);
    };

    const handleHideHelp = (): void => {
        setShowHelpModal(false);
    };

    return (
        <WindowProvider>
            <NetworkProvider>
                <LoadingProvider>
                    <EntityProvider>
                        <Container
                            fluid
                            className="d-flex flex-column h-sm-100"
                        >
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

                                <div className="sidebar-right-container p-0 order-sm-3 order-2">
                                    <div className="flex-sm-column flex-row h-sm-100">
                                        {/* sidebar right panel */}
                                        <SidebarRight />
                                    </div>
                                </div>

                                {/* Use the React components for overlays */}
                                <RolesOverlay
                                    roles={rolesConfig}
                                    show={showRolesOverlay}
                                    onHide={(): void =>
                                        setShowRolesOverlay(false)
                                    }
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
        </WindowProvider>
    );
};

export default App;
