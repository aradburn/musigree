/** @jsxImportSource react */
import React from "react";
import { printSvg } from "../../print";
import { musigreeManager } from "../../core/singletons";
import ForceControls from "../Visualization/ForceControls";

/**
 * SidebarLeft component provides navigation and controls for the application.
 * It uses the NetworkContext to control the D3.js force layout.
 */
export const SidebarLeft: React.FC = () => {
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
        <div className="p-2 d-flex flex-fill h-100">
            <div
                className="col-auto d-flex flex-fill h-100
                            flex-sm-column flex-xl-column
                            justify-content-evenly
                            justify-content-sm-start justify-content-xl-start
                            align-items-start
                            align-items-sm-start align-items-xl-start
                            text-light"
            >
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
        </div>
    );
};

export default SidebarLeft;
