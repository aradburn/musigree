import { describe, it, expect } from "vitest";
import {
    DOM_IDS,
    SVG_IDS,
    SVG,
    MARKER,
    GRADIENT,
    COLOR,
    TIMING,
    EXPORT,
    LOADING,
    TYPEAHEAD,
    TREE,
    RELATIONS,
    FSM,
    INIT,
    API,
    MESSAGE,
    FORCE,
} from "../constants";

describe("constants", () => {
    describe("DOM_IDS", () => {
        it("should export all expected DOM IDs", () => {
            expect(DOM_IDS.SVG_CONTAINER).toBe("svg-container-fluid");
            expect(DOM_IDS.SVG_CONTAINER_ID).toBe("#svg-container-fluid");
            expect(DOM_IDS.SVG).toBe("svg");
            expect(DOM_IDS.SVG_ID).toBe("#svg");
            expect(DOM_IDS.REQUEST_RANDOM).toBe("request-random");
            expect(DOM_IDS.START_LAYOUT).toBe("start-layout");
            expect(DOM_IDS.STOP_LAYOUT).toBe("stop-layout");
            expect(DOM_IDS.PRINT).toBe("print");
            expect(DOM_IDS.NAV_TOP).toBe("nav-top");
            expect(DOM_IDS.MODAL_HELP).toBe("modal-help");
            expect(DOM_IDS.ROLES_OVERLAY).toBe("roles-overlay");
            expect(DOM_IDS.ROLES_PANEL).toBe("roles-panel");
            expect(DOM_IDS.ROLES_CONTAINER).toBe("roles-container");
            expect(DOM_IDS.ENTITY_DETAILS_OVERLAY).toBe(
                "entity-details-overlay",
            );
            expect(DOM_IDS.ENTITY_DETAILS_PANEL).toBe("entity-details-panel");
            expect(DOM_IDS.ENTITY_DETAILS).toBe("entity-details");
        });
    });

    describe("SVG_IDS", () => {
        it("should export all expected SVG IDs", () => {
            expect(SVG_IDS.ARROWHEAD).toBe("arrowhead");
            expect(SVG_IDS.AGGREGATE).toBe("aggregate");
            expect(SVG_IDS.RADIAL_GRADIENT).toBe("radial-gradient");
            expect(SVG_IDS.LOADING_LAYER).toBe("loading-layer");
            expect(SVG_IDS.RELATIONS_LAYER).toBe("relations-layer");
        });
    });

    describe("SVG", () => {
        it("should export SVG constants with correct values", () => {
            expect(SVG.VIEWPORT_SIZE_MULTIPLIER).toBe(3.0);
            expect(SVG.SCALING_MULTIPLIER).toBe(0.6);
        });
    });

    describe("MARKER", () => {
        it("should export marker constants with correct values", () => {
            expect(MARKER.VIEWBOX).toBe("-5 -5 10 10");
            expect(MARKER.WIDTH).toBe(5);
            expect(MARKER.HEIGHT).toBe(5);
            expect(MARKER.ARROWHEAD_REFX).toBe(4);
            expect(MARKER.AGGREGATE_REFX).toBe(5);
            expect(MARKER.REFY).toBe(0);
            expect(MARKER.STROKE_WIDTH).toBe(1.5);
        });
    });

    describe("GRADIENT", () => {
        it("should export gradient constants with correct structure", () => {
            expect(GRADIENT.COLOR).toBe("#333");
            expect(GRADIENT.STOPS).toHaveLength(4);
            expect(GRADIENT.STOPS[0]).toEqual({
                offset: "0%",
                opacity: "1.0",
            });
        });
    });

    describe("COLOR", () => {
        it("should export color constants with correct values", () => {
            expect(COLOR.MIN_INDEX).toBe(0);
            expect(COLOR.MAX_INDEX).toBe(8);
            expect(COLOR.ARTIST_DISTANCE_OFFSET).toBe(1);
            expect(COLOR.LABEL_DISTANCE_OFFSET).toBe(2);
            expect(COLOR.DEFAULT_LINK_DISTANCE.ZERO).toBe(2);
            expect(COLOR.DEFAULT_LINK_DISTANCE.OTHER).toBe(5);
        });
    });

    describe("TIMING", () => {
        it("should export timing constants with correct values", () => {
            expect(TIMING.QUICK_MESSAGE_CLEAR).toBe(10);
            expect(TIMING.LONG_MESSAGE_CLEAR).toBe(10000);
            expect(TIMING.ANIMATION_DURATION).toBe(1000);
            expect(TIMING.ANIMATION_DELAY_MULTIPLIER).toBe(100);
            expect(TIMING.TYPEAHEAD_DEBOUNCE).toBe(1000);
            expect(TIMING.RADIAL_TRANSITION.DURATION).toBe(1000);
            expect(TIMING.RADIAL_TRANSITION.DELAY_MULTIPLIER).toBe(25);
        });
    });

    describe("EXPORT", () => {
        it("should export export constants with correct values", () => {
            expect(EXPORT.SCALE_FACTOR).toBe(2);
        });
    });

    describe("LOADING", () => {
        it("should export loading constants with correct values", () => {
            expect(LOADING.BAR_HEIGHT).toBe(500);
            expect(LOADING.BAR_HEIGHT_MIN_SCALE).toBe(0.1);
            expect(LOADING.ARC_COUNT).toBe(20);
            expect(LOADING.MAX_ROTATION_RATE).toBe(0.28);
        });
    });

    describe("TYPEAHEAD", () => {
        it("should export typeahead constants with correct values", () => {
            expect(TYPEAHEAD.MIN_QUERY_LENGTH).toBe(4);
            expect(TYPEAHEAD.MAX_RESULTS).toBe(1000);
            expect(TYPEAHEAD.API_ENDPOINT).toBe("/api/search/%QUERY");
            expect(TYPEAHEAD.QUERY_WILDCARD).toBe("%QUERY");
            expect(TYPEAHEAD.ELEMENT_ID).toBe("typeahead");
            expect(TYPEAHEAD.CLEAR_BUTTON_SELECTOR).toBe("#search .clear");
        });
    });

    describe("TREE", () => {
        it("should export tree constants with correct values", () => {
            expect(TREE.PADDING_LEFT).toBe(20);
            expect(TREE.MARGIN).toBe(5);
            expect(TREE.ICON_SIZE).toBe(16);
            expect(TREE.TREE_STYLES).toBe("tree-styles");
            expect(TREE.CLASS_NAMES.ROOT).toBe("tree-root");
            expect(TREE.CLASS_NAMES.NODE).toBe("tree-node");
            expect(TREE.CLASS_NAMES.CONTENT).toBe("tree-content");
            expect(TREE.CLASS_NAMES.CHECKBOX).toBe("tree-checkbox");
            expect(TREE.CLASS_NAMES.ICON).toBe("tree-icon");
            expect(TREE.CLASS_NAMES.TEXT).toBe("tree-text");
            expect(TREE.CLASS_NAMES.CHILDREN).toBe("tree-children");
        });
    });

    describe("RELATIONS", () => {
        it("should export relations constants with correct values", () => {
            expect(RELATIONS.SCALE.MIN_MULTIPLIER).toBe(0.25);
            expect(RELATIONS.SCALE.EXPONENT).toBe(0.25);
            expect(RELATIONS.DIMENSIONS.DIVISOR).toBe(3);
            expect(RELATIONS.DIMENSIONS.TEXT_OFFSET).toBe(5);
            expect(RELATIONS.ANGLES.START_DEGREES).toBe(-90);
            expect(RELATIONS.ANGLES.HALF_CIRCLE).toBe(180);
            expect(RELATIONS.ANGLES.FULL_CIRCLE).toBe(360);
            expect(RELATIONS.ANGLES.TWO_PI).toBe(2 * Math.PI);
            expect(RELATIONS.ZOOM.MIN_SCALE).toBe(1);
            expect(RELATIONS.ZOOM.MAX_SCALE).toBe(8);
        });
    });

    describe("FSM", () => {
        it("should export FSM constants with correct values", () => {
            expect(FSM.STATES.UNINITIALIZED).toBe("uninitialized");
            expect(FSM.STATES.VIEWING_NETWORK).toBe("state-viewing-network");
            expect(FSM.STATES.REQUESTING_NETWORK).toBe(
                "state-requesting-network",
            );
            expect(FSM.STATES.REQUESTING_RADIAL).toBe(
                "state-requesting-radial",
            );
            expect(FSM.STATES.REQUESTING_RANDOM).toBe(
                "state-requesting-random",
            );
            expect(FSM.STATES.VIEWING_RADIAL).toBe("state-viewing-radial");
            expect(FSM.EVENTS.REQUEST_NETWORK).toBe("musigree:request-network");
            expect(FSM.EVENTS.REQUEST_RANDOM).toBe("musigree:request-random");
            expect(FSM.EVENTS.SELECT_ENTITY).toBe("musigree:select-entity");
            expect(FSM.EVENTS.SHOW_NETWORK).toBe("musigree:show-network");
            expect(FSM.EVENTS.SHOW_RADIAL).toBe("musigree:show-radial");
            expect(FSM.EVENTS.RESIZE).toBe("musigree:resize");
        });
    });

    describe("INIT", () => {
        it("should export init constants with correct values", () => {
            expect(INIT.DEBOUNCE_DELAY).toBe(250);
            expect(INIT.MESSAGE_CLEAR_DELAY).toBe(5000);
            expect(INIT.DEFAULT_ALPHA).toBe(0.1);
            expect(INIT.TOOLTIP_TRIGGER).toBe("hover");
        });
    });

    describe("API", () => {
        it("should export API constants with correct structure", () => {
            expect(API.RANDOM_MAX).toBe(1000000);
            expect(typeof API.ENDPOINTS.NETWORK).toBe("function");
            expect(typeof API.ENDPOINTS.RANDOM).toBe("function");
            expect(typeof API.ENDPOINTS.RELATIONS).toBe("function");
            expect(typeof API.ENDPOINTS.ENTITY).toBe("function");
        });

        it("should generate correct network endpoint", () => {
            expect(API.ENDPOINTS.NETWORK("artist", "123")).toBe(
                "/api/artist/network/123",
            );
            expect(API.ENDPOINTS.NETWORK("label", "456")).toBe(
                "/api/label/network/456",
            );
        });

        it("should generate correct random endpoint", () => {
            expect(API.ENDPOINTS.RANDOM()).toBe("/api/random");
        });

        it("should generate correct relations endpoint", () => {
            expect(API.ENDPOINTS.RELATIONS("artist", "123")).toBe(
                "/api/artist/relations/123",
            );
            expect(API.ENDPOINTS.RELATIONS("label", "456")).toBe(
                "/api/label/relations/456",
            );
        });

        it("should generate correct entity endpoint", () => {
            expect(API.ENDPOINTS.ENTITY("artist", "123")).toBe(
                "/api/artist/details/123",
            );
            expect(API.ENDPOINTS.ENTITY("label", "456")).toBe(
                "/api/label/details/456",
            );
        });
    });

    describe("MESSAGE", () => {
        it("should export message constants with correct structure", () => {
            expect(MESSAGE.CONTAINER_ID).toBe("message-container");
            expect(MESSAGE.TYPES.PRIMARY).toBe("primary");
            expect(MESSAGE.TYPES.SUCCESS).toBe("success");
            expect(MESSAGE.TYPES.ERROR).toBe("danger");
            expect(MESSAGE.ALERT_CLASS.BASE).toBe("alert");
            expect(MESSAGE.BUTTON.CLOSE_CLASS).toBe("btn-close");
        });
    });

    describe("FORCE", () => {
        it("should export force constants with correct values", () => {
            expect(FORCE.NODE.STRENGTH).toBe(-800);
            expect(FORCE.NODE.STRENGTH_CLUSTER).toBe(100);
            expect(FORCE.NODE.STRENGTH_INTERMEDIATE).toBe(-80);
            expect(FORCE.DISTANCE.MAX).toBe(2000);
            expect(FORCE.DISTANCE.LINK).toBe(60);
            expect(FORCE.DISTANCE.LINK_ALIAS).toBe(-100);
            expect(FORCE.DISTANCE.LINK_RELEASED_ON).toBe(180);
            expect(FORCE.COLLIDE.ITERATIONS).toBe(2);
            expect(FORCE.COLLIDE.BUFFER).toBe(14);
            expect(FORCE.SIMULATION.THETA).toBe(0.9);
            expect(FORCE.SIMULATION.ALPHA).toBe(1.0);
            expect(FORCE.SIMULATION.ALPHA_DECAY).toBe(0.03);
            expect(FORCE.SIMULATION.VELOCITY_DECAY).toBe(0.24);
            expect(FORCE.LINK.ITERATIONS).toBe(3);
            expect(FORCE.LINK.ROLES.ALIAS).toBe("Alias");
            expect(FORCE.LINK.ROLES.RELEASED_ON).toBe("Released On");
            expect(FORCE.MULTIPLIER.NODE_STRENGTH_BASE).toBe(0.4);
            expect(FORCE.MULTIPLIER.NODE_STRENGTH_SCALE).toBe(20.0);
            expect(FORCE.MULTIPLIER.LINK_STRENGTH_SCALE).toBe(20.0);
            expect(FORCE.MULTIPLIER.GRAVITY_STRENGTH_SCALE).toBe(20.0);
        });
    });
});
