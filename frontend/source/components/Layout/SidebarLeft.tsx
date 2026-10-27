/** @jsxImportSource react */
import React, {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";
import { printSvg } from "../../print";
import { musigreeManager } from "../../core/singletons";
import { FORCE, INIT } from "../../constants";
import { RequestNetworkEvent } from "../../network/events";
import { restartForceLayout, stopForceLayout } from "../../network/forceLayout";
import {
    convertRolesToArboristFormat,
    rememberRelationships,
    splitRoleTree,
    updateSelectedRoleIds,
} from "../../roles";
import type { TreeConfig } from "../../roles";
import ForceControls from "../Visualization/ForceControls";
import RelationshipsFilter from "./RelationshipsFilter";
import RolesFilter from "./RolesFilter";
import YearRangeSlider from "./YearRangeSlider";

/**
 * Left sidebar: filter, layout, and print accordions.
 * Sections start closed. The column scrolls when the open content is taller
 * than the viewport. Filter changes reload the current network after a
 * short debounce.
 */
export const SidebarLeft: React.FC = () => {
    const [rolesConfig, setRolesConfig] = useState<TreeConfig | undefined>(
        () =>
            typeof window.dgRoles === "undefined" ? undefined : window.dgRoles,
    );
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [isLayoutOpen, setIsLayoutOpen] = useState(false);
    const [isPrintOpen, setIsPrintOpen] = useState(false);
    const refreshTimerRef = useRef<number | null>(null);

    useEffect(() => {
        if (typeof window.dgRoles !== "undefined") {
            setRolesConfig(window.dgRoles);
        }
        return (): void => {
            if (refreshTimerRef.current !== null) {
                window.clearTimeout(refreshTimerRef.current);
            }
        };
    }, []);

    const { relationships, roles } = useMemo(
        () => splitRoleTree(rolesConfig),
        [rolesConfig],
    );

    useEffect(() => {
        if (!roles && relationships.length === 0) {
            return;
        }
        if (roles) {
            convertRolesToArboristFormat(roles);
        }
        rememberRelationships(relationships);
        updateSelectedRoleIds(
            [...(roles?.core.data ?? []), ...relationships]
                .filter((node) => node.state?.selected)
                .map((node) => node.id),
        );
    }, [relationships, roles]);

    const requestFilteredNetwork = useCallback((): void => {
        if (refreshTimerRef.current !== null) {
            window.clearTimeout(refreshTimerRef.current);
        }
        refreshTimerRef.current = window.setTimeout(() => {
            refreshTimerRef.current = null;
            window.dispatchEvent(new RequestNetworkEvent("", true));
        }, INIT.DEBOUNCE_DELAY);
    }, []);

    const handleStartLayout = (): void => {
        restartForceLayout(FORCE.SIMULATION.ALPHA / 10.0);
    };

    const handleStopLayout = (): void => {
        stopForceLayout();
    };

    const handlePrint = (): void => {
        printSvg(
            musigreeManager.svgDimensions[0],
            musigreeManager.svgDimensions[1],
        );
    };

    return (
        <div className="sidebar-left p-2 text-light">
            <div className="accordion sidebar-accordion">
                <div className="accordion-item">
                    <h4 className="accordion-header">
                        <button
                            type="button"
                            className={`accordion-button ${isFilterOpen ? "" : "collapsed"}`}
                            aria-expanded={isFilterOpen}
                            aria-controls="sidebar-filter-panel"
                            onClick={() => {
                                setIsFilterOpen((open) => !open);
                            }}
                        >
                            <i
                                className="bi bi-funnel me-2"
                                aria-hidden="true"
                            ></i>
                            Filter
                        </button>
                    </h4>
                    <div
                        id="sidebar-filter-panel"
                        className={`accordion-collapse collapse ${isFilterOpen ? "show" : ""}`}
                        hidden={!isFilterOpen}
                    >
                        <div className="accordion-body">
                            <label
                                className="h6 d-block mb-1"
                                htmlFor="year-range-min"
                            >
                                Years
                            </label>
                            <YearRangeSlider
                                onChange={requestFilteredNetwork}
                            />
                            <div className="h6 mt-3 mb-1">Relationships</div>
                            <RelationshipsFilter
                                relationships={relationships}
                                onSelectionChange={requestFilteredNetwork}
                            />
                            <RolesFilter
                                roles={roles}
                                onSelectionChange={requestFilteredNetwork}
                            />
                        </div>
                    </div>
                </div>
                <div className="accordion-item">
                    <h4 className="accordion-header">
                        <button
                            type="button"
                            className={`accordion-button ${isLayoutOpen ? "" : "collapsed"}`}
                            aria-expanded={isLayoutOpen}
                            aria-controls="sidebar-layout-panel"
                            onClick={() => {
                                setIsLayoutOpen((open) => !open);
                            }}
                        >
                            <i
                                className="bi bi-sliders me-2"
                                aria-hidden="true"
                            ></i>
                            Layout
                        </button>
                    </h4>
                    <div
                        id="sidebar-layout-panel"
                        className={`accordion-collapse collapse ${isLayoutOpen ? "show" : ""}`}
                        hidden={!isLayoutOpen}
                    >
                        <div className="accordion-body">
                            <div className="d-flex align-items-center justify-content-end gap-2 mb-2">
                                <div
                                    className="navbar-text p-0"
                                    role="button"
                                    aria-label="Start layout"
                                    onClick={handleStartLayout}
                                >
                                    <i className="fs-5 bi-lightning"></i>
                                </div>
                                <div
                                    className="navbar-text p-0"
                                    role="button"
                                    aria-label="Stop layout"
                                    onClick={handleStopLayout}
                                >
                                    <i className="fs-5 bi-sign-stop"></i>
                                </div>
                            </div>
                            <ForceControls />
                        </div>
                    </div>
                </div>
                <div className="accordion-item">
                    <h4 className="accordion-header">
                        <button
                            type="button"
                            className={`accordion-button ${isPrintOpen ? "" : "collapsed"}`}
                            aria-expanded={isPrintOpen}
                            aria-controls="sidebar-print-panel"
                            onClick={() => {
                                setIsPrintOpen((open) => !open);
                            }}
                        >
                            <i
                                className="bi bi-printer me-2"
                                aria-hidden="true"
                            ></i>
                            Print
                        </button>
                    </h4>
                    <div
                        id="sidebar-print-panel"
                        className={`accordion-collapse collapse ${isPrintOpen ? "show" : ""}`}
                        hidden={!isPrintOpen}
                    >
                        <div className="accordion-body">
                            <button
                                type="button"
                                className="btn btn-outline-light"
                                onClick={handlePrint}
                            >
                                <i
                                    className="bi bi-printer me-2"
                                    aria-hidden="true"
                                ></i>
                                Print
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default SidebarLeft;
