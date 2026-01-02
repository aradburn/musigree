/** @jsxImportSource react */
import React from "react";
import { Details } from "./Details";
import { useEntity } from "../../contexts/useEntity";

interface SidebarRightProps {
    isCollapsed: boolean;
    onToggleCollapse: () => void;
}

/**
 * SidebarRight component provides a display for entity details.
 * Supports collapsing to show only an Info icon.
 */
export const SidebarRight: React.FC<SidebarRightProps> = ({
    isCollapsed,
    onToggleCollapse,
}) => {
    const { state } = useEntity();

    if (isCollapsed) {
        return (
            <div className="p-2 d-flex h-sm-100 justify-content-center align-items-start">
                <button
                    type="button"
                    className="btn btn-link text-dark p-2"
                    onClick={onToggleCollapse}
                    aria-label="Open sidebar"
                    title="Open sidebar"
                >
                    <i className="bi bi-info-circle fs-3"></i>
                </button>
            </div>
        );
    }

    return (
        <div className="p-2 d-flex h-sm-100">
            <div className="flex-fill ms-auto d-flex gap-2 flex-column text-dark">
                <div className="d-flex justify-content-end mt-0 me-3 position-absolute end-0">
                    <button
                        type="button"
                        className="btn btn-link text-dark p-2"
                        onClick={onToggleCollapse}
                        aria-label="Close sidebar"
                        title="Close sidebar"
                    >
                        <i className="bi bi-x-circle fs-3"></i>
                    </button>
                </div>
                <div className="flex-fill overflow-x-hidden overflow-y-auto">
                    {/* Details panel */}
                    <Details entity={state.entity} />
                </div>
                <div className="flex-shrink-0">
                    {/*<Advert*/}
                    {/*    adClient="ca-pub-5857652035840115"*/}
                    {/*    adSlot="3061976325"*/}
                    {/*/>*/}
                </div>
            </div>
        </div>
    );
};

export default SidebarRight;
