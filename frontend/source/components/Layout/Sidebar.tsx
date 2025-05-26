/** @jsxImportSource react */
import React from "react";
import { printSvg } from "../../svg";
import { musigreeManager } from "../../core";
import ForceControls from "../Visualization/ForceControls";

/**
 * Sidebar component that provides navigation and controls for the application.
 * It uses the NetworkContext to control the D3.js force layout.
 */
export const Sidebar: React.FC = () => {
    const handleShowDetails = (): void => {
        window.dispatchEvent(
            new CustomEvent("musigree:show-entity-details-overlay"),
        );
    };

    const handleShowRoles = (): void => {
        window.dispatchEvent(new CustomEvent("musigree:show-roles-overlay"));
    };

    const handlePrint = (): void => {
        printSvg(
            musigreeManager.svgDimensions[0],
            musigreeManager.svgDimensions[1],
        );
    };

    return (
        <div className="sidebar d-flex h-100 flex-sm-column flex-xl-column justify-content-evenly justify-content-sm-start justify-content-xl-start align-items-start align-items-sm-start align-items-xl-start bg-secondary-subtle p-2 text-light">
            {/* Details button */}
            <div
                className="navbar-text px-sm-0 px-2"
                role="button"
                onClick={handleShowDetails}
            >
                <i className="fs-5 bi-eye"></i>
                <span className="ms-1 d-none d-sm-inline">DETAILS</span>
            </div>

            {/* Roles button */}
            <div
                className="navbar-text px-sm-0 px-2"
                role="button"
                onClick={handleShowRoles}
            >
                <i className="fs-5 bi-person"></i>
                <span className="ms-1 d-none d-sm-inline">ROLES</span>
            </div>

            {/* Print button */}
            <div
                className="navbar-text px-sm-0 px-2 mb-sm-auto"
                role="button"
                onClick={handlePrint}
            >
                <i className="fs-5 bi-printer"></i>
                <span className="ms-1 d-none d-sm-inline">PRINT</span>
            </div>

            {/* Force Controls */}
            <ForceControls />
        </div>
    );
};

export default Sidebar;
