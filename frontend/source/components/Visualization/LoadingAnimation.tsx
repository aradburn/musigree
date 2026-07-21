/** @jsxImportSource react */
import { useRef, useEffect } from "react";
import * as d3 from "d3";
import { useLoading } from "../../contexts/useLoading";
import { LOADING, TIMING, SVG_IDS, DOM_IDS } from "../../constants";
import { musigreeManager } from "../../core/singletons";

/**
 * Interface for arc data used in the loading animation
 */
interface ArcData {
    active: boolean;
    startAngle: number;
    endAngle: number;
    rotationRate: number;
    targetInnerRadius: number;
    targetOuterRadius: number;
    innerRadius?: number;
    outerRadius?: number;
    hasTimer?: boolean;
    timer?: d3.Timer;
}

/**
 * LoadingAnimation component that renders a D3.js-based loading animation
 * This component replaces the jQuery-based loading.ts implementation
 */
const LoadingAnimation = (): null => {
    const svgRef = useRef<SVGGElement | null>(null);
    const { isLoading } = useLoading();
    const initializedRef = useRef<boolean>(false);
    const arcRef = useRef<d3.Arc<unknown, ArcData>>(d3.arc<unknown, ArcData>());
    const barHeightRef = useRef<number>(LOADING.BAR_HEIGHT);
    const dataRef = useRef<ArcData[]>([]);
    const timersRef = useRef<d3.Timer[]>([]);

    // Initialize the loading animation
    useEffect(() => {
        const svgElement = d3.select(DOM_IDS.SVG_ID);
        if (!svgElement.empty() && !initializedRef.current) {
            const svgWidth = musigreeManager.svgDimensions[0];
            const svgHeight = musigreeManager.svgDimensions[1];
            const layer = svgElement
                .append("g")
                .attr("id", SVG_IDS.LOADING_LAYER)
                .attr("class", "centered")
                .attr(
                    "transform",
                    `translate(${svgWidth / 2},${svgHeight / 2})`,
                );

            svgRef.current = layer.node();
            initializedRef.current = true;

            arcRef.current = d3
                .arc<unknown, ArcData>()
                .startAngle((d) => d.startAngle)
                .endAngle((d) => d.endAngle)
                .innerRadius((d) => d.innerRadius || 0)
                .outerRadius((d) => d.outerRadius || 0);
        }

        return (): void => {
            // Clean up timers when component unmounts
            timersRef.current.forEach((timer) => timer.stop());
            timersRef.current = [];

            // Remove the loading layer
            if (initializedRef.current && svgRef.current) {
                d3.select(svgRef.current).remove();
                initializedRef.current = false;
            }
        };
    }, []);

    // Generate random data for the loading animation arcs
    const makeArray = (): [ArcData[], [number, number]] => {
        const values: number[] = [];
        const data: ArcData[] = [];

        data.push({
            active: true,
            startAngle: 0,
            endAngle: 2 * Math.PI,
            rotationRate: 0,
            targetInnerRadius: 0,
            targetOuterRadius: 1.0,
        });

        for (let i = 0; i < LOADING.ARC_COUNT; i++) {
            const pair = [
                Math.random() * 0.1,
                Math.min(Math.random() * 2.0, 1.0),
            ].sort();
            values.push(pair[0], pair[1]);

            const startAngle = 2 * Math.PI * Math.random();
            data.push({
                active: true,
                startAngle: startAngle,
                endAngle: startAngle + Math.PI + Math.PI * Math.random(),
                rotationRate: LOADING.MAX_ROTATION_RATE,
                targetInnerRadius: pair[0],
                targetOuterRadius: pair[1],
            });
        }
        return [data, d3.extent(values) as [number, number]];
    };

    // Update the loading animation based on isLoading state
    useEffect(() => {
        if (!initializedRef.current || !svgRef.current) return;

        const [data, extent] = isLoading
            ? makeArray()
            : [[], [0, 0] as [number, number]];
        dataRef.current = data;

        // Update the page loading element
        const pageLoadingElement = document.getElementById("page-loading");
        if (pageLoadingElement) {
            pageLoadingElement.style.display = isLoading ? "block" : "none";
        }

        // Update the loading animation
        update(data, extent);
        // update is stable enough for loading toggles; recreating it each render is intentional
        // eslint-disable-next-line react-hooks/exhaustive-deps -- only re-run when isLoading changes
    }, [isLoading]);

    // Update the loading animation with new data
    const update = (data: ArcData[], extent: [number, number]): void => {
        if (!svgRef.current) return;

        const barScale = d3
            .scaleLinear()
            .domain(extent)
            .range([
                barHeightRef.current * LOADING.BAR_HEIGHT_MIN_SCALE,
                barHeightRef.current,
            ]);

        const layer = d3.select(svgRef.current);
        const dataSelection = layer
            .selectAll<SVGPathElement, ArcData>("path")
            .data(data);

        const selectionEnter = dataSelection.enter();
        transitionEnter(selectionEnter);
        transitionExit(dataSelection.exit());

        const updatedSelection = layer
            .selectAll<SVGPathElement, ArcData>("path")
            .data(data);

        transitionUpdate(updatedSelection, barScale);

        if (selectionEnter.size() > 0 && isLoading) {
            rotate(updatedSelection);
        }
    };

    // Handle the entry transition for new arcs
    const transitionEnter = (
        selection: d3.Selection<d3.EnterElement, ArcData, SVGGElement, unknown>,
    ): void => {
        //         const scale = d3.scaleOrdinal(d3.schemeCategory10);
        //         const scale = d3.scaleOrdinal(d3.schemeGreys[9]);
        const colorScheme = d3.interpolateGreys;
        selection
            .append("path")
            .attr("class", "arc")
            .attr("d", (d) => arcRef.current(d))
            .attr("fill", (d, i) =>
                i == 0
                    ? "#777777FF"
                    : d3
                          .color(colorScheme(Math.random() * 0.5 + 0.5))
                          .copy({ opacity: 0.5 })
                          .formatHex8(),
            )
            //             .attr("fill", (_, i) => scale(((i % 9) + 8).toString()))
            .each((d, i) => {
                d.innerRadius = i == 0 ? 0.0 : d.targetInnerRadius / 2.0;
                d.outerRadius = d.targetOuterRadius / 2.0;
                d.hasTimer = false;
            });
    };

    // Animate transitions for updating arcs
    const transitionUpdate = (
        selection: d3.Selection<SVGPathElement, ArcData, SVGGElement, unknown>,
        barScale: d3.ScaleLinear<number, number>,
    ): void => {
        selection
            .transition()
            .duration(TIMING.ANIMATION_DURATION / 5.0)
            //             .delay(
            //                 (_, i) =>
            //                     (selection.size() - i) * TIMING.ANIMATION_DELAY_MULTIPLIER,
            //             )
            .attrTween("d", (d, i): ((t: number) => string) => {
                const inner = d3.interpolate(
                    d.innerRadius || 0,
                    barScale(d.targetInnerRadius),
                );
                const outer = d3.interpolate(
                    d.outerRadius || 0,
                    barScale(d.targetOuterRadius),
                );
                return (t: number): string => {
                    d.innerRadius = i == 0 ? inner(0.0) : inner(t);
                    d.outerRadius = outer(t);
                    return arcRef.current(d);
                };
            });
    };

    // Handle the exit transition for removed arcs
    const transitionExit = (
        selection: d3.Selection<SVGPathElement, ArcData, SVGGElement, unknown>,
    ): void => {
        selection
            .transition()
            .duration(TIMING.ANIMATION_DURATION)
            .attrTween("d", (d, i): ((t: number) => string) => {
                const inner = d3.interpolate(d.innerRadius, 0);
                const outer = d3.interpolate(d.outerRadius, 0);
                return (t: number): string => {
                    d.innerRadius = i == 0 ? inner(0.0) : inner(t);
                    d.outerRadius = outer(t);
                    return arcRef.current(d);
                };
            })
            .remove();
    };

    // Animate rotation for active arcs
    const rotate = (
        selection: d3.Selection<SVGPathElement, ArcData, SVGGElement, unknown>,
    ): void => {
        // Stop any existing timers
        timersRef.current.forEach((timer) => timer.stop());
        timersRef.current = [];

        selection.each(function (d) {
            if (d.hasTimer) return;

            d.hasTimer = true;
            const path = d3.select(this);
            const timer = d3.timer((_elapsed) => {
                const delta = d.rotationRate;
                d.startAngle += delta;
                d.endAngle += delta;
                path.attr("d", arcRef.current(d));

                // Stop the timer if the component is unmounted or loading is done
                if (!isLoading || !initializedRef.current) {
                    timer.stop();
                    return true;
                }
                return false;
            });

            timersRef.current.push(timer);
            d.timer = timer;
        });
    };

    return null; // This component doesn't render any visible DOM elements directly
};

export default LoadingAnimation;
