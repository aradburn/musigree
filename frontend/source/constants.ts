// DOM Element IDs
export const DOM_IDS = {
    SVG_CONTAINER: "svg-container-fluid",
    SVG_CONTAINER_ID: "#svg-container-fluid",
    SVG: "svg",
    SVG_ID: "#svg",
    REQUEST_RANDOM: "request-random",
    START_LAYOUT: "start-layout",
    STOP_LAYOUT: "stop-layout",
    PRINT: "print",
    NAV_TOP: "nav-top",
    MODAL_HELP: "modal-help",
    ROLES_OVERLAY: "roles-overlay",
    ROLES_PANEL: "roles-panel",
    ROLES_CONTAINER: "roles-container",
    ENTITY_DETAILS_OVERLAY: "entity-details-overlay",
    ENTITY_DETAILS_PANEL: "entity-details-panel",
    ENTITY_DETAILS: "entity-details",
};

// SVG Element IDs
export const SVG_IDS = {
    ARROWHEAD: "arrowhead",
    AGGREGATE: "aggregate",
    RADIAL_GRADIENT: "radial-gradient",
    LOADING_LAYER: "loading-layer",
    RELATIONS_LAYER: "relations-layer",
};

// Constants for viewport and SVG scaling
export const SVG = {
    VIEWPORT_SIZE_MULTIPLIER: 3.0,
    SCALING_MULTIPLIER: 0.6,
};

// SVG Marker Constants
export const MARKER = {
    VIEWBOX: "-5 -5 10 10",
    WIDTH: 5,
    HEIGHT: 5,
    ARROWHEAD_REFX: 4,
    AGGREGATE_REFX: 5,
    REFY: 0,
    STROKE_WIDTH: 1.5,
};

// Gradient Constants
export const GRADIENT = {
    COLOR: "#333",
    STOPS: [
        { offset: "0%", opacity: "1.0" },
        { offset: "50%", opacity: "0.333" },
        { offset: "75%", opacity: "0.111" },
        { offset: "100%", opacity: "0.0" },
    ],
};

// Color Range Constants
export const COLOR = {
    MIN_INDEX: 0,
    MAX_INDEX: 8,
    ARTIST_DISTANCE_OFFSET: 1,
    LABEL_DISTANCE_OFFSET: 2,
    DEFAULT_LINK_DISTANCE: {
        ZERO: 2,
        OTHER: 5,
    },
};

// Timing Constants
export const TIMING = {
    QUICK_MESSAGE_CLEAR: 10,
    LONG_MESSAGE_CLEAR: 10000,
    ANIMATION_DURATION: 1000,
    ANIMATION_DELAY_MULTIPLIER: 100,
    TYPEAHEAD_DEBOUNCE: 1000,
    RADIAL_TRANSITION: {
        DURATION: 1000,
        DELAY_MULTIPLIER: 25,
    },
};

// Export Image Constants
export const EXPORT = {
    SCALE_FACTOR: 2,
};

// Loading Animation Constants
export const LOADING = {
    BAR_HEIGHT: 500,
    BAR_HEIGHT_MIN_SCALE: 0.1, // 1/10
    ARC_COUNT: 20,
    MAX_ROTATION_RATE: 0.2,
};

// Typeahead Constants
export const TYPEAHEAD = {
    MIN_QUERY_LENGTH: 4,
    MAX_RESULTS: 1000,
    API_ENDPOINT: "/api/search/%QUERY",
    QUERY_WILDCARD: "%QUERY",
    ELEMENT_ID: "typeahead",
    CLEAR_BUTTON_SELECTOR: "#search .clear",
};

// Tree Component Constants
export const TREE = {
    PADDING_LEFT: 20,
    MARGIN: 5,
    ICON_SIZE: 16,
    TREE_STYLES: "tree-styles",
    CLASS_NAMES: {
        ROOT: "tree-root",
        NODE: "tree-node",
        CONTENT: "tree-content",
        CHECKBOX: "tree-checkbox",
        ICON: "tree-icon",
        TEXT: "tree-text",
        CHILDREN: "tree-children",
    },
};

// Relations Visualization Constants
export const RELATIONS = {
    SCALE: {
        MIN_MULTIPLIER: 0.25, // 1/4
        EXPONENT: 0.25,
    },
    DIMENSIONS: {
        DIVISOR: 3, // For barHeight calculation
        TEXT_OFFSET: 5,
    },
    ANGLES: {
        START_DEGREES: -90,
        HALF_CIRCLE: 180,
        FULL_CIRCLE: 360,
        TWO_PI: 2 * Math.PI,
    },
    ZOOM: {
        MIN_SCALE: 1,
        MAX_SCALE: 8,
    },
};

// FSM State Constants
export const FSM = {
    STATES: {
        UNINITIALIZED: "uninitialized",
        VIEWING_NETWORK: "state-viewing-network",
        REQUESTING_NETWORK: "state-requesting-network",
        REQUESTING_RADIAL: "state-requesting-radial",
        REQUESTING_RANDOM: "state-requesting-random",
        VIEWING_RADIAL: "state-viewing-radial",
    },
    EVENTS: {
        REQUEST_NETWORK: "musigree:request-network",
        REQUEST_RANDOM: "musigree:request-random",
        SELECT_ENTITY: "musigree:select-entity",
        SHOW_NETWORK: "musigree:show-network",
        SHOW_RADIAL: "musigree:show-radial",
        RESIZE: "musigree:resize",
    },
};

// Initialization Constants
export const INIT = {
    DEBOUNCE_DELAY: 250,
    MESSAGE_CLEAR_DELAY: 5000,
    DEFAULT_ALPHA: 0.1,
    TOOLTIP_TRIGGER: "hover" as const,
};

// API Constants
export const API = {
    ENDPOINTS: {
        NETWORK: (entityType: string, entityId: string): string =>
            `/api/${entityType}/network/${entityId}`,
        RANDOM: (): string => `/api/random`,
        RELATIONS: (entityType: string, entityId: string): string =>
            `/api/${entityType}/relations/${entityId}`,
        ENTITY: (entityType: string, entityId: string): string =>
            `/api/${entityType}/details/${entityId}`,
    },
    RANDOM_MAX: 1000000,
};

// Message Constants
export const MESSAGE = {
    CONTAINER_ID: "message-container",
    TYPES: {
        PRIMARY: "primary",
        SECONDARY: "secondary",
        SUCCESS: "success",
        INFO: "info",
        WARNING: "warning",
        ERROR: "danger",
        DANGER: "danger",
        LIGHT: "light",
        DARK: "dark",
    },
    ALERT_CLASS: {
        BASE: "alert",
        DISMISSIBLE: "alert-dismissible",
        FADE: "fade",
        SHOW: "show",
    },
    BUTTON: {
        CLOSE_CLASS: "btn-close",
        DISMISS_ATTR: "data-bs-dismiss",
        ARIA_LABEL: "Close",
    },
};

// Force Layout Constants
export const FORCE = {
    NODE: {
        STRENGTH: -800, // Repulsion strength between nodes
        STRENGTH_CLUSTER: 100, // Repulsion strength between cluster nodes
        STRENGTH_INTERMEDIATE: -80, // Repulsion strength for intermediate nodes (NODE_STRENGTH / 10)
    },
    DISTANCE: {
        MAX: 2000, // Maximum distance for force calculations
        LINK: 60, // Default link distance
        LINK_ALIAS: -100, // Distance for alias relationships
        LINK_RELEASED_ON: 180, // Distance for "Released On" relationships (LINK_DISTANCE * 3)
    },
    COLLIDE: {
        ITERATIONS: 2, // Number of collision detection iterations
        BUFFER: 14, // Extra space around nodes for collision detection
    },
    SIMULATION: {
        THETA: 0.9, // Barnes-Hut approximation criterion
        ALPHA: 1.0, // Initial simulation temperature
        ALPHA_DECAY: 0.03, // Rate at which simulation cools down
        VELOCITY_DECAY: 0.24, // Friction coefficient for node movement
    },
    LINK: {
        ITERATIONS: 3, // Number of iterations for link force calculation
        ROLES: {
            ALIAS: "Alias",
            RELEASED_ON: "Released On",
        },
    },
    MULTIPLIER: {
        NODE_STRENGTH_BASE: 0.4,
        NODE_STRENGTH_SCALE: 20.0,
        LINK_STRENGTH_SCALE: 20.0,
        GRAVITY_STRENGTH_SCALE: 20.0,
    },
};
