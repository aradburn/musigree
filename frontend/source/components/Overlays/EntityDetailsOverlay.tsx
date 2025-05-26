/** @jsxImportSource react */
import React, { useRef, useState, useEffect } from "react";
import Offcanvas from "react-bootstrap/Offcanvas";
import { DOM_IDS } from "../../constants";

// Define interface for the entity selected event detail
interface EntitySelectedEvent extends CustomEvent {
    detail: {
        name: string;
        url: string;
    };
}

export const EntityDetailsOverlay: React.FC<{
    show: boolean;
    onHide: () => void;
}> = ({ show, onHide }): React.ReactElement => {
    const entityDetailsPanelRef = useRef<HTMLDivElement>(null);
    const [navbarHeight, setNavbarHeight] = useState<number>(0);
    const [entityName, setEntityName] = useState<string>("");
    const [entityLink, setEntityLink] = useState<string>("#");

    // Effect to measure the navbar height when the component mounts or window resizes
    useEffect(() => {
        const updateNavbarHeight = (): void => {
            const navbar = document.querySelector("nav.navbar");
            if (navbar) {
                const height = navbar.getBoundingClientRect().height;
                setNavbarHeight(height);
            }
        };

        // Initial measurement
        updateNavbarHeight();

        // Update on window resize
        window.addEventListener("resize", updateNavbarHeight);

        // Cleanup
        return (): void => {
            window.removeEventListener("resize", updateNavbarHeight);
        };
    }, []);

    // Effect to listen for entity selection events
    useEffect(() => {
        // Handler for entity selected events
        const handleEntitySelected = (event: Event): void => {
            const entityEvent = event as EntitySelectedEvent;
            if (entityEvent.detail) {
                setEntityName(entityEvent.detail.name);
                setEntityLink(entityEvent.detail.url);
            }
        };

        // Listen for the custom entity-selected event
        window.addEventListener(
            "musigree:entity-selected",
            handleEntitySelected,
        );

        // Cleanup
        return (): void => {
            window.removeEventListener(
                "musigree:entity-selected",
                handleEntitySelected,
            );
        };
    }, []);

    const handleClose = (): void => {
        const event = new CustomEvent("musigree:hide-entity-details-overlay");
        window.dispatchEvent(event);
        onHide();
    };

    // Custom styles for the offcanvas component
    const offcanvasStyle = {
        top: `${navbarHeight}px`,
        height: `calc(100% - ${navbarHeight}px)`,
    };

    return (
        <Offcanvas
            id={DOM_IDS.ENTITY_DETAILS_OVERLAY}
            show={show}
            onHide={handleClose}
            placement="start"
            style={offcanvasStyle}
            className="entity-details-offcanvas"
            backdropClassName="entity-details-backdrop"
        >
            <Offcanvas.Header closeButton>
                <Offcanvas.Title id="entity-details-title">
                    Entity Details
                </Offcanvas.Title>
            </Offcanvas.Header>

            <Offcanvas.Body>
                {/* Entity details panel */}
                <div
                    id={DOM_IDS.ENTITY_DETAILS_PANEL}
                    className="panel slide-out"
                    ref={entityDetailsPanelRef}
                >
                    <div id="entity-details">
                        <p>
                            Name: <span id="entity-name">{entityName}</span>
                        </p>
                        <p>
                            <a
                                id="entity-link"
                                href={entityLink}
                                target="_blank"
                                rel="noopener noreferrer"
                            >
                                View on Discogs
                            </a>
                        </p>
                    </div>
                </div>
            </Offcanvas.Body>
        </Offcanvas>
    );
};
