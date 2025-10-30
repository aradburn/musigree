/** @jsxImportSource react */
import React, { useState, useEffect } from "react";
import { Container, Row } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";

import { Header } from "./Layout/Header.tsx";
import { SidebarLeft } from "./Layout/SidebarLeft";
import { SidebarRight } from "./Layout/SidebarRight";
import { HelpModal, WelcomeModal, WhoModal } from "./Modals/index";
import { NetworkView } from "./Visualization/NetworkView";
import { LoadingAnimation } from "./Visualization";
import { RolesOverlay, EntityDetailsOverlay } from "./Overlays";
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
    const [showWelcomeModal, setShowWelcomeModal] = useState<boolean>(false);
    const [showWhoModal, setShowWhoModal] = useState<boolean>(false);
    const [showRolesOverlay, setShowRolesOverlay] = useState<boolean>(false);
    const [showEntityDetailsOverlay, setShowEntityDetailsOverlay] =
        useState<boolean>(false);
    const [isReturnVisitor, setIsReturnVisitor] = useState<boolean>(false);
    const [rolesConfig, setRolesConfig] = useState<TreeConfig | undefined>(
        undefined,
    );

    // Check if this is a return visitor and load roles data
    useEffect(() => {
        // Check for return visitor status
        const hasVisitedBefore = localStorage.getItem("hasVisitedBefore");
        if (!hasVisitedBefore) {
            // First time visitor - show welcome modal
            setShowWelcomeModal(true);
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
        const handleShowEntityDetails = (): void =>
            setShowEntityDetailsOverlay(true);
        const handleHideEntityDetails = (): void =>
            setShowEntityDetailsOverlay(false);

        window.addEventListener("musigree:show-roles-overlay", handleShowRoles);
        window.addEventListener("musigree:hide-roles-overlay", handleHideRoles);
        window.addEventListener(
            "musigree:show-entity-details-overlay",
            handleShowEntityDetails,
        );
        window.addEventListener(
            "musigree:hide-entity-details-overlay",
            handleHideEntityDetails,
        );

        return (): void => {
            window.removeEventListener(
                "musigree:show-roles-overlay",
                handleShowRoles,
            );
            window.removeEventListener(
                "musigree:hide-roles-overlay",
                handleHideRoles,
            );
            window.removeEventListener(
                "musigree:show-entity-details-overlay",
                handleShowEntityDetails,
            );
            window.removeEventListener(
                "musigree:hide-entity-details-overlay",
                handleHideEntityDetails,
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

    const handleHideWelcome = (): void => {
        setShowWelcomeModal(false);
    };

    const handleShowWho = (): void => {
        setShowWhoModal(true);
    };

    const handleHideWho = (): void => {
        setShowWhoModal(false);
    };

    return (
        <WindowProvider>
            <NetworkProvider>
                <LoadingProvider>
                    <EntityProvider>
                        <Container fluid className="h-100 d-flex flex-column">
                            <Row>
                                <Header
                                    onShowHelp={handleShowHelp}
                                    onShowWho={handleShowWho}
                                />
                            </Row>

                            <Row
                                className="flex-grow-1 flex-nowrap"
                                style={{ minHeight: 0 }}
                            >
                                <SidebarLeft />

                                <div className="h-100 px-0 flex-grow-1 col-auto">
                                    <NetworkView />
                                    <LoadingAnimation />
                                </div>

                                <SidebarRight />

                                {/* Use the React components for overlays */}
                                <RolesOverlay
                                    roles={rolesConfig}
                                    show={showRolesOverlay}
                                    onHide={(): void =>
                                        setShowRolesOverlay(false)
                                    }
                                />
                                <EntityDetailsOverlay
                                    show={showEntityDetailsOverlay}
                                    onHide={(): void =>
                                        setShowEntityDetailsOverlay(false)
                                    }
                                />
                            </Row>

                            <HelpModal
                                show={showHelpModal}
                                onHide={handleHideHelp}
                            />
                            <WhoModal
                                show={showWhoModal}
                                onHide={handleHideWho}
                            />
                            <WelcomeModal
                                show={showWelcomeModal}
                                onHide={handleHideWelcome}
                                isReturnVisitor={isReturnVisitor}
                            />
                        </Container>
                    </EntityProvider>
                </LoadingProvider>
            </NetworkProvider>
        </WindowProvider>
    );
};

export default App;
