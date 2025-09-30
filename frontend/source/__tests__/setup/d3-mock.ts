import { vi } from "vitest";

/**
 * Comprehensive D3 mock for Vitest tests
 * This mock provides all the D3 functions needed by the Musigree application
 */

// Mock for D3 arc generator
const createMockArc = (): any => {
    const arcInstance = {
        innerRadius: vi.fn().mockReturnThis(),
        outerRadius: vi.fn().mockReturnThis(),
        startAngle: vi.fn().mockReturnThis(),
        endAngle: vi.fn().mockReturnThis(),
        centroid: vi.fn().mockReturnValue([0, 0]),
    };

    // Ensure all methods return the same instance to maintain chaining
    arcInstance.innerRadius.mockReturnValue(arcInstance);
    arcInstance.outerRadius.mockReturnValue(arcInstance);
    arcInstance.startAngle.mockReturnValue(arcInstance);
    arcInstance.endAngle.mockReturnValue(arcInstance);

    return arcInstance;
};

// Mock for D3 selections - creates a chainable mock
const createSelectionMock = (): any => {
    const selectionMock: any = {
        select: vi.fn().mockReturnThis(),
        selectAll: vi.fn().mockReturnThis(),
        append: vi.fn().mockReturnThis(),
        attr: vi.fn().mockReturnThis(),
        style: vi.fn().mockReturnThis(),
        classed: vi.fn().mockReturnThis(),
        text: vi.fn().mockReturnThis(),
        html: vi.fn().mockReturnThis(),
        data: vi.fn().mockReturnThis(),
        join: vi.fn().mockReturnThis(),
        enter: vi.fn().mockReturnThis(),
        exit: vi.fn().mockReturnThis(),
        merge: vi.fn().mockReturnThis(),
        remove: vi.fn().mockReturnThis(),
        raise: vi.fn().mockReturnThis(),
        lower: vi.fn().mockReturnThis(),
        each: vi.fn().mockReturnThis(),
        filter: vi.fn().mockReturnThis(),
        sort: vi.fn().mockReturnThis(),
        datum: vi.fn().mockReturnThis(),
        on: vi.fn().mockReturnThis(),
        call: vi.fn().mockReturnThis(),
        transition: vi.fn().mockReturnThis(),
        duration: vi.fn().mockReturnThis(),
        delay: vi.fn().mockReturnThis(),
        ease: vi.fn().mockReturnThis(),
        empty: vi.fn().mockReturnValue(false),
        node: vi.fn().mockReturnValue(document.createElement("div")),
        nodes: vi.fn().mockReturnValue([]),
        size: vi.fn().mockReturnValue(1),
    };

    // Make functions return the same object to ensure spies are preserved
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
    selectionMock.append.mockReturnValue(selectionMock);
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
    selectionMock.select.mockReturnValue(selectionMock);
    // eslint-disable-next-line @typescript-eslint/no-unsafe-call, @typescript-eslint/no-unsafe-member-access
    selectionMock.selectAll.mockReturnValue(selectionMock);

    return selectionMock;
};

// Mock for D3 scales
const mockScale = (): any => ({
    domain: vi.fn().mockReturnThis(),
    range: vi.fn().mockReturnThis(),
    nice: vi.fn().mockReturnThis(),
    ticks: vi.fn().mockReturnValue([]),
    tickFormat: vi.fn().mockReturnValue(() => ""),
    invert: vi.fn().mockReturnValue(0),
    copy: vi.fn().mockReturnThis(),
    exponent: vi.fn().mockReturnThis(), // Add exponent for scaleSqrt
});

// Mock for D3 force simulation
const mockSimulation = (): any => ({
    nodes: vi.fn().mockReturnThis(),
    links: vi.fn().mockReturnThis(),
    force: vi.fn().mockReturnThis(),
    alpha: vi.fn().mockReturnThis(),
    alphaTarget: vi.fn().mockReturnThis(),
    alphaMin: vi.fn().mockReturnThis(),
    alphaDecay: vi.fn().mockReturnThis(),
    velocityDecay: vi.fn().mockReturnThis(),
    restart: vi.fn().mockReturnThis(),
    stop: vi.fn().mockReturnThis(),
    tick: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    find: vi.fn().mockReturnValue(null),
});

// Mock for D3 forces
const mockForce = (): any => ({
    strength: vi.fn().mockReturnThis(),
    radius: vi.fn().mockReturnThis(),
    distance: vi.fn().mockReturnThis(),
    iterations: vi.fn().mockReturnThis(),
    theta: vi.fn().mockReturnThis(),
    distanceMin: vi.fn().mockReturnThis(),
    distanceMax: vi.fn().mockReturnThis(),
});

// Mock for D3 zoom behavior
const mockZoom = (): any => ({
    extent: vi.fn().mockReturnThis(),
    scaleExtent: vi.fn().mockReturnThis(),
    translateExtent: vi.fn().mockReturnThis(),
    clickDistance: vi.fn().mockReturnThis(),
    tapDistance: vi.fn().mockReturnThis(),
    wheelDelta: vi.fn().mockReturnThis(),
    filter: vi.fn().mockReturnThis(),
    touchable: vi.fn().mockReturnThis(),
    duration: vi.fn().mockReturnThis(),
    interpolate: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    transform: vi.fn(),
    translateBy: vi.fn().mockReturnThis(),
    translateTo: vi.fn().mockReturnThis(),
    scaleBy: vi.fn().mockReturnThis(),
    scaleTo: vi.fn().mockReturnThis(),
});

// Mock for D3 drag behavior
const mockDrag = (): any => ({
    container: vi.fn().mockReturnThis(),
    filter: vi.fn().mockReturnThis(),
    touchable: vi.fn().mockReturnThis(),
    subject: vi.fn().mockReturnThis(),
    clickDistance: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
});

// Mock for D3 transition
const mockTransition = (): any => ({
    duration: vi.fn().mockReturnThis(),
    delay: vi.fn().mockReturnThis(),
    ease: vi.fn().mockReturnThis(),
    attr: vi.fn().mockReturnThis(),
    style: vi.fn().mockReturnThis(),
    text: vi.fn().mockReturnThis(),
    tween: vi.fn().mockReturnThis(),
    remove: vi.fn().mockReturnThis(),
    on: vi.fn().mockReturnThis(),
    selection: vi.fn().mockReturnThis(),
    transition: vi.fn().mockReturnThis(),
    end: vi.fn().mockResolvedValue(undefined),
});

// Comprehensive D3 mock object
export const d3Mock = {
    // Selection methods
    select: vi.fn(() => createSelectionMock()),
    selectAll: vi.fn(() => createSelectionMock()),

    // Scales
    scaleLinear: vi.fn(() => mockScale()),
    scaleOrdinal: vi.fn(() => mockScale()),
    scaleBand: vi.fn(() => mockScale()),
    scaleTime: vi.fn(() => mockScale()),
    scaleSqrt: vi.fn(() => mockScale()),
    scaleLog: vi.fn(() => mockScale()),
    scalePow: vi.fn(() => mockScale()),

    // Colors
    schemeCategory10: ["#1f77b4", "#ff7f0e", "#2ca02c"],
    schemeSet3: ["#8dd3c7", "#ffffb3", "#bebada"],

    // Array/data manipulation
    group: vi.fn().mockReturnValue(new Map()),
    rollup: vi.fn().mockReturnValue(new Map()),
    sort: vi.fn().mockReturnValue([]),
    extent: vi.fn().mockReturnValue([0, 100]),
    min: vi.fn().mockReturnValue(0),
    max: vi.fn().mockReturnValue(100),
    sum: vi.fn().mockReturnValue(0),
    mean: vi.fn().mockReturnValue(0),
    median: vi.fn().mockReturnValue(0),
    ascending: vi.fn(),
    descending: vi.fn(),
    range: vi.fn().mockReturnValue([]),

    // Geometry
    arc: vi.fn(() => createMockArc()),
    line: vi.fn().mockReturnThis(),
    area: vi.fn().mockReturnThis(),
    pie: vi.fn().mockReturnValue([]),
    polygonHull: vi.fn().mockReturnValue([]),

    // Force simulation
    forceSimulation: vi.fn(() => mockSimulation()),
    forceManyBody: vi.fn(() => mockForce()),
    forceLink: vi.fn(() => mockForce()),
    forceCenter: vi.fn(() => mockForce()),
    forceCollide: vi.fn(() => mockForce()),
    forceX: vi.fn(() => mockForce()),
    forceY: vi.fn(() => mockForce()),
    forceRadial: vi.fn(() => mockForce()),

    // Behaviors
    zoom: vi.fn(() => mockZoom()),
    drag: vi.fn(() => mockDrag()),

    // Transitions
    transition: vi.fn(() => mockTransition()),

    // Transform/Zoom
    zoomIdentity: {
        k: 1,
        x: 0,
        y: 0,
        scale: vi.fn().mockReturnThis(),
        translate: vi.fn().mockReturnThis(),
        toString: vi.fn().mockReturnValue("translate(0,0) scale(1)"),
        invert: vi.fn().mockReturnValue([0, 0]),
    },
    zoomTransform: vi.fn().mockReturnValue({
        k: 1,
        x: 0,
        y: 0,
        invert: vi.fn().mockReturnValue([0, 0]),
        toString: vi.fn().mockReturnValue("translate(0,0) scale(1)"),
    }),

    // Easings
    easeLinear: vi.fn(),
    easeQuad: vi.fn(),
    easeCubic: vi.fn(),
    easeElastic: vi.fn(),
    easeBounce: vi.fn(),
    easeBack: vi.fn(),
    easeSin: vi.fn(),
    easeExp: vi.fn(),
    easeCircle: vi.fn(),

    // Time/Date
    timeFormat: vi.fn().mockReturnValue(() => ""),
    timeParse: vi.fn().mockReturnValue(() => new Date()),

    // Interpolation
    interpolate: vi.fn((a: any, b: any) => (t: any) => a + (b - a) * t),
    interpolateNumber: vi.fn((a: any, b: any) => (t: any) => a + (b - a) * t),
    interpolateString: vi.fn().mockReturnValue(() => ""),

    // Misc
    csv: vi.fn().mockResolvedValue([]),
    json: vi.fn().mockResolvedValue({}),
    format: vi.fn().mockReturnValue(() => ""),
    formatPrefix: vi.fn().mockReturnValue(() => ""),

    // Internals used by the app
    InternMap: Map,
    InternSet: Set,
};

// Export the mock for use in vi.mock
export default d3Mock;
