import type {StepType} from "@reactour/tour";
import {DOM_IDS} from "@/constants.ts";

/** Lightweight first-visit tour highlighting core Musigree UI. */
export const onboardingTourSteps: StepType[] = [
    {
        selector: "#musigree",
        content: (
            <div className="h4 mb-0">
                <p>
                    Welcome to Musigree, an interactive visualization of Bands,
                    Artists and Labels.
                </p>
                <p>
                    This short tour shows how to explore the connections.
                </p>
            </div>
        ),
        position: "center",
        padding: {popover: [0, 0]},
    },
    {
        selector: "#musigree-search",
        content: (
            <div className="h4 mb-0">
                <p>
                    Search for artists, bands, or labels.
                </p>
                <p>
                    Select a result to visualize the network of connections to
                    other
                    artists, bands and labels.
                </p>
            </div>
        ),
        position: "bottom",
        padding: {popover: [6, 10]},
    },
    {
        selector: `#${DOM_IDS.SVG_CONTAINER}`,
        content: (
            <div className="h4 mb-0">
                <p>
                    The graph network area shows the relationships between
                    artists,
                    bands and
                    labels.
                </p>
                <p>
                    <i className="bi bi-arrows-move fs-3"></i> &nbsp;&nbsp;Drag
                    the
                    background
                    to pan around the network.
                </p>
                <p>
                    <i className="bi bi-zoom-in fs-3"></i> &nbsp;&nbsp;Zoom in
                    or &nbsp;&nbsp;
                    <i className="bi bi-zoom-out fs-3"></i> &nbsp;&nbsp;Zoom
                    out by
                    using
                    the mouse-wheel.
                </p>
                <p>
                    <i className="bi bi-diagram-3 fs-3"></i> &nbsp;&nbsp;Double-click
                    nodes to
                    recentre the network on that node.
                </p>
            </div>
        ),
        position: "center",
    },
    {
        selector: '[data-tour="random"]',
        content: (
            <div className="h4 mb-0">
                <p>
                    Not sure where to start?
                </p>
                <p>
                    Use <b>Random</b> to jump to a surprise band or artist.
                </p>
            </div>
        ),
        position: "bottom",
    },
    {
        selector: '[data-tour="help"]',
        content: (
            <div className="h4 mb-0">
                <p>
                    Open <b>Help</b> anytime for symbol meanings and navigation
                    tips.
                </p>
            </div>
        ),
        position: "bottom",
    },
];
