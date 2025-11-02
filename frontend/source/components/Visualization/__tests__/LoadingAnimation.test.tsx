import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock d3 module
vi.mock("d3", () => {
    return {
        select: vi.fn(),
        arc: vi.fn(),
        timer: vi.fn(),
        scaleLinear: vi.fn(),
        scaleOrdinal: vi.fn(),
        extent: vi.fn(),
        interpolate: vi.fn(),
        interpolateGreys: vi.fn(
            (t: number) =>
                `rgb(${Math.floor(t * 255)}, ${Math.floor(t * 255)}, ${Math.floor(t * 255)})`,
        ),
        color: vi.fn((color: string) => ({
            copy: vi.fn((opts: any) => ({ ...opts, toString: () => color })),
        })),
        schemeCategory10: ["#000000", "#111111", "#222222"],
    };
});

// Mock the loading context
vi.mock("../../../contexts/useLoading", () => ({
    useLoading: vi.fn(),
}));

// Mock the musigreeManager
vi.mock("../../../core", () => ({
    musigreeManager: {
        svgDimensions: [800, 600],
    },
}));

// Import after all mocks
import { render } from "@testing-library/react";
import "@testing-library/jest-dom";
import LoadingAnimation from "../LoadingAnimation";
import * as loadingContext from "../../../contexts/useLoading";
import * as d3 from "d3";
import { LOADING, TIMING, SVG_IDS, DOM_IDS } from "../../../constants";

// Create a factory for chainable mock objects
const createChainableMock = () => {
    const mock = {
        // Basic D3 selection methods
        empty: vi.fn().mockReturnValue(false),
        append: vi.fn(),
        attr: vi.fn(),
        node: vi.fn(),
        remove: vi.fn(),
        selectAll: vi.fn(),
        data: vi.fn(),
        enter: vi.fn(),
        exit: vi.fn(),

        // D3 transition methods
        transition: vi.fn(),
        duration: vi.fn(),
        delay: vi.fn(),
        attrTween: vi.fn(),

        // D3 scale methods
        domain: vi.fn(),
        range: vi.fn(),

        // D3 arc methods
        startAngle: vi.fn(),
        endAngle: vi.fn(),
        innerRadius: vi.fn(),
        outerRadius: vi.fn(),

        // Additional utility methods
        size: vi.fn().mockReturnValue(10),
        each: vi.fn((fn) => {
            fn && fn({}, 0);
            return mock;
        }),

        // Additional Selection methods needed for TypeScript
        select: vi.fn(),
        filter: vi.fn(),
        merge: vi.fn(),
        selectChild: vi.fn(),
        property: vi.fn(),
        classed: vi.fn(),
        text: vi.fn(),
        html: vi.fn(),
        call: vi.fn(),
        on: vi.fn(),
        dispatch: vi.fn(),
    };

    // Setup method chaining
    Object.keys(mock).forEach((key) => {
        if (
            typeof mock[key] === "function" &&
            key !== "empty" &&
            key !== "size" &&
            key !== "each"
        ) {
            mock[key].mockReturnValue(mock);
        }
    });

    // Mock node to return an object with remove method
    mock.node.mockReturnValue({ remove: vi.fn() });

    return mock as unknown as d3.Selection<any, unknown, null, undefined>;
};

// Define the type for the arc generator mock
type MockArcType = {
    (data: any): string;
    startAngle: (angle: any) => MockArcType;
    endAngle: (angle: any) => MockArcType;
    innerRadius: (radius: any) => MockArcType;
    outerRadius: (radius: any) => MockArcType;
    centroid?: (data: any) => [number, number];
    cornerRadius?: (radius: any) => MockArcType;
    padAngle?: (angle: any) => MockArcType;
};

describe("LoadingAnimation", () => {
    let mockPageLoadingElement: { style: { display: string } };
    let mockSvgElement;
    let chainableMock;

    beforeEach(() => {
        vi.resetAllMocks();

        // Create the chainable mock inside beforeEach
        chainableMock = createChainableMock();

        // Set up mock implementations
        vi.spyOn(d3, "select").mockReturnValue(chainableMock);

        // Mock arc to return a function that can be called with data
        const arcFunction = vi.fn(
            (data) => "arc-path",
        ) as unknown as MockArcType;
        // Add chainable methods to the arc function
        arcFunction.startAngle = vi.fn().mockReturnValue(arcFunction);
        arcFunction.endAngle = vi.fn().mockReturnValue(arcFunction);
        arcFunction.innerRadius = vi.fn().mockReturnValue(arcFunction);
        arcFunction.outerRadius = vi.fn().mockReturnValue(arcFunction);
        vi.spyOn(d3, "arc").mockReturnValue(
            arcFunction as unknown as d3.Arc<unknown, unknown>,
        );

        vi.spyOn(d3, "timer").mockImplementation((callback) => {
            // Call the callback once with elapsed time 0
            callback && callback(0);
            // Return a timer object with a stop method
            return {
                stop: vi.fn(),
                restart: vi.fn(),
            };
        });
        vi.spyOn(d3, "scaleLinear").mockReturnValue(chainableMock);

        // Create a properly typed ScaleOrdinal mock
        const scaleOrdinalMock = (() =>
            "#000000") as unknown as d3.ScaleOrdinal<string, unknown>;
        scaleOrdinalMock.domain = vi.fn().mockReturnValue(scaleOrdinalMock);
        scaleOrdinalMock.range = vi.fn().mockReturnValue(scaleOrdinalMock);
        scaleOrdinalMock.unknown = vi.fn().mockReturnValue(scaleOrdinalMock);
        scaleOrdinalMock.copy = vi.fn().mockReturnValue(scaleOrdinalMock);
        vi.spyOn(d3, "scaleOrdinal").mockReturnValue(scaleOrdinalMock);

        vi.spyOn(d3, "extent").mockReturnValue([0, 1]);

        // Type cast the interpolate function to avoid type errors
        vi.spyOn(d3, "interpolate").mockImplementation(
            (a: any, b: any) => (t: number) => a + (b - a) * t,
        );

        // Set up mock element and getElementById
        mockPageLoadingElement = { style: { display: "none" } };
        document.getElementById = vi.fn().mockImplementation((id) => {
            if (id === "page-loading") {
                return mockPageLoadingElement;
            }
            return null;
        });

        // Create a mock SVG element for testing
        mockSvgElement = createChainableMock();
        vi.mocked(d3.select).mockReturnValue(mockSvgElement);

        // Default loading state is false
        vi.mocked(loadingContext.useLoading).mockReturnValue({
            isLoading: false,
            showLoading: vi.fn(),
            hideLoading: vi.fn(),
            toggleLoading: vi.fn(),
        });
    });

    afterEach(() => {
        vi.clearAllMocks();
    });

    it("initializes correctly when rendered", () => {
        render(<LoadingAnimation />);

        // Verify D3 was initialized properly
        expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_ID);
        expect(d3.arc).toHaveBeenCalled();

        // Verify the arc function is configured correctly
        const arcMock = vi.mocked(d3.arc).mock.results[0].value;
        expect(arcMock.startAngle).toHaveBeenCalled();
        expect(arcMock.endAngle).toHaveBeenCalled();
        expect(arcMock.innerRadius).toHaveBeenCalled();
        expect(arcMock.outerRadius).toHaveBeenCalled();
    });

    it("creates loading animation when isLoading is true", () => {
        // Set loading state to true
        vi.mocked(loadingContext.useLoading).mockReturnValue({
            isLoading: true,
            showLoading: vi.fn(),
            hideLoading: vi.fn(),
            toggleLoading: vi.fn(),
        });

        render(<LoadingAnimation />);

        // Verify that SVG container is initialized
        expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_ID);

        // Verify that page loading indicator is displayed
        expect(mockPageLoadingElement.style.display).toBe("block");

        // Verify extent function is called for data range calculation
        expect(d3.extent).toHaveBeenCalled();

        // Verify that timer is created for animation when loading
        // The rotate function should be called which creates timers
        expect(d3.timer).toHaveBeenCalled();
    });

    it("does not create loading animation when isLoading is false", () => {
        render(<LoadingAnimation />);

        // Verify basic initialization still happens
        expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_ID);

        // Verify that page loading indicator remains hidden
        expect(mockPageLoadingElement.style.display).toBe("none");

        // With isLoading false, extent doesn't get called because makeArray isn't called
        expect(d3.extent).not.toHaveBeenCalled();

        // No timer should be created for animation in this case
        expect(d3.timer).not.toHaveBeenCalled();
    });

    it("updates animation when isLoading state changes", () => {
        // Start with loading false
        const { rerender } = render(<LoadingAnimation />);
        expect(mockPageLoadingElement.style.display).toBe("none");

        // Update to loading true
        vi.mocked(loadingContext.useLoading).mockReturnValue({
            isLoading: true,
            showLoading: vi.fn(),
            hideLoading: vi.fn(),
            toggleLoading: vi.fn(),
        });

        rerender(<LoadingAnimation />);
        expect(mockPageLoadingElement.style.display).toBe("block");
        expect(d3.extent).toHaveBeenCalled();
        expect(d3.timer).toHaveBeenCalled();

        // Update back to loading false
        vi.mocked(loadingContext.useLoading).mockReturnValue({
            isLoading: false,
            showLoading: vi.fn(),
            hideLoading: vi.fn(),
            toggleLoading: vi.fn(),
        });

        rerender(<LoadingAnimation />);
        expect(mockPageLoadingElement.style.display).toBe("none");
    });

    it("cleans up resources when unmounted", () => {
        // Mock timer.stop to track calls
        const mockTimerStop = vi.fn();
        vi.mocked(d3.timer).mockReturnValue({
            stop: mockTimerStop,
            restart: vi.fn(),
        });

        // Set loading to true to initialize timers and SVG elements
        vi.mocked(loadingContext.useLoading).mockReturnValue({
            isLoading: true,
            showLoading: vi.fn(),
            hideLoading: vi.fn(),
            toggleLoading: vi.fn(),
        });

        const { unmount } = render(<LoadingAnimation />);

        // Render will create timers, now simulate unmount
        unmount();

        // Timer.stop should be called during cleanup
        expect(mockTimerStop).toHaveBeenCalled();
    });

    it("handles scenario when SVG element doesn't exist", () => {
        // Mock select to return an empty selection
        const emptyMock = createChainableMock();
        vi.mocked(emptyMock.empty).mockReturnValue(true);
        vi.mocked(d3.select).mockReturnValue(emptyMock);

        render(<LoadingAnimation />);

        // SVG element is not found, so no further D3 operations should be performed
        expect(d3.select).toHaveBeenCalledWith(DOM_IDS.SVG_ID);
        expect(d3.arc).toHaveBeenCalled(); // Arc function is still created
    });

    it("tests the makeArray function for data generation", () => {
        // Set loading state to true
        vi.mocked(loadingContext.useLoading).mockReturnValue({
            isLoading: true,
            showLoading: vi.fn(),
            hideLoading: vi.fn(),
            toggleLoading: vi.fn(),
        });

        render(<LoadingAnimation />);

        // Verify extent function is called for data range calculation with appropriate array
        expect(d3.extent).toHaveBeenCalled();
        expect(d3.extent).not.toHaveBeenCalledWith([]);
    });

    it("adds arcs with correct attributes", () => {
        // Set loading state to true to trigger arc creation
        vi.mocked(loadingContext.useLoading).mockReturnValue({
            isLoading: true,
            showLoading: vi.fn(),
            hideLoading: vi.fn(),
            toggleLoading: vi.fn(),
        });

        render(<LoadingAnimation />);

        // Verify that paths are appended with correct attributes
        const selectAllMock = vi.mocked(mockSvgElement.selectAll);
        expect(selectAllMock).toHaveBeenCalledWith("path");

        // Verify that the arc function is called to generate paths
        expect(d3.arc).toHaveBeenCalled();
    });

    it("handles transitions correctly", () => {
        // Set loading state to true
        vi.mocked(loadingContext.useLoading).mockReturnValue({
            isLoading: true,
            showLoading: vi.fn(),
            hideLoading: vi.fn(),
            toggleLoading: vi.fn(),
        });

        render(<LoadingAnimation />);

        // Check if transition-related methods are called
        const dataMock = vi.mocked(mockSvgElement.selectAll).mock.results[0]
            .value;
        expect(dataMock.transition).toHaveBeenCalled();

        // The implementation now uses different durations for different transitions:
        // - transitionUpdate: TIMING.ANIMATION_DURATION / 5.0 (200)
        // - transitionExit: TIMING.ANIMATION_DURATION (1000)
        expect(dataMock.duration).toHaveBeenCalledWith(
            TIMING.ANIMATION_DURATION / 5.0, // 200
        );
        expect(dataMock.duration).toHaveBeenCalledWith(
            TIMING.ANIMATION_DURATION, // 1000
        );
    });
});
