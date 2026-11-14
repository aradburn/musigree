/** @jsxImportSource react */
import React, { useEffect, useState } from "react";
import { useEntity } from "@/contexts/useEntity.ts";
import Details from "@/components/Layout/Details.tsx";

/** Shown in the right column until the network delivers entity details. */
const SIDEBAR_INTRO_TITLE = "MUSIGREE";
const SIDEBAR_INTRO_BODY =
    "is an interactive visualization of the relationships between musicians, bands and labels.";

interface SidebarRightProps {
    isCollapsed: boolean;
    isMobile: boolean;
    onToggleCollapse: () => void;
}

/**
 * True when the page was opened with a non-empty query string.
 * An empty search (`""` or `"?"`) is treated as no parameters.
 */
const hasUrlQueryParameters = (): boolean => {
    return new URLSearchParams(window.location.search).toString().length > 0;
};

/**
 * SidebarRight component provides a display for entity details.
 * Supports collapsing to show only an Info icon.
 */
export const SidebarRight: React.FC<SidebarRightProps> = ({
    isCollapsed,
    isMobile,
    onToggleCollapse,
}) => {
    const { state } = useEntity();
    // A query string means the visit already targets a filtered view, so
    // Details is shown immediately. Otherwise wait for the first entity.
    const [detailsVisible, setDetailsVisible] = useState(hasUrlQueryParameters);

    useEffect(() => {
        if (state.entity) {
            setDetailsVisible(true);
        }
    }, [state.entity]);

    if (isCollapsed) {
        return (
            <div className="p-2 d-flex h-sm-100 justify-content-center align-items-start">
                <button
                    type="button"
                    className="btn btn-link text-light px-1 pt-0 pb-1"
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
            <div className="flex-fill ms-auto d-flex gap-2 flex-column">
                {!isMobile && detailsVisible ? (
                    <div className="d-flex justify-content-end mt-0 me-3 position-absolute end-0">
                        <button
                            type="button"
                            className="btn btn-link text-light ps-1 pe-2 pt-0 pb-1"
                            onClick={onToggleCollapse}
                            aria-label="Close sidebar"
                            title="Close sidebar"
                        >
                            <i className="bi bi-x-circle fs-3"></i>
                        </button>
                    </div>
                ) : null}

                <div
                    className={
                        detailsVisible
                            ? "flex-fill overflow-x-hidden overflow-y-auto"
                            : "flex-fill overflow-x-hidden overflow-y-auto d-flex flex-column"
                    }
                >
                    {detailsVisible ? (
                        <Details entity={state.entity} isMobile={isMobile} />
                    ) : (
                        <div className="flex-fill d-flex flex-column justify-content-center text-light">
                            <p className="mb-0 text-center">
                                <span className="h3 mb-0">
                                    {`${SIDEBAR_INTRO_TITLE} `}
                                </span>
                                <br />
                                <span className="h4">{SIDEBAR_INTRO_BODY}</span>
                            </p>
                        </div>
                    )}
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
