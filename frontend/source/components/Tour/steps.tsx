import type {StepType} from "@reactour/tour";
import {DOM_IDS} from "../../constants";

/** Lightweight first-visit tour highlighting core Musigree UI. */
export const onboardingTourSteps: StepType[] = [
    {
        selector: "#nav-top",
        content: (
            <p className="mb-0">
                Welcome to Musigree. This short tour shows how to explore music
                industry connections from the Discogs database.
            </p>
        ),
    },
    {
        selector: "#musigree-search",
        content: (
            <p className="mb-0">
                Search for artists, bands, or labels. Pick a result to visualize
                the connections to other artists, bands and labels.
            </p>
        ),
    },
    {
        selector: `#${DOM_IDS.SVG_CONTAINER}`,
        content: (
            <p className="mb-0">
                The graph shows the relationships between artists, bands and
                labels.
                <br/>
                Drag the background to pan around the network.
                <br/>
                Zoom in or out by using the mouse-wheel.
                <br/>
                Double-click nodes to recentre the network on that node.
            </p>
        ),
    },
    {
        selector: '[data-tour="random"]',
        content: (
            <p className="mb-0">
                Not sure where to start? Use Random to jump to a surprise
                band or artist.
            </p>
        ),
    },
    {
        selector: '[data-tour="help"]',
        content: (
            <p className="mb-0">
                Open Help anytime for symbol meanings and navigation tips.
            </p>
        ),
    },
];
