/** @jsxImportSource react */
import React, {
    useReducer,
    useEffect,
    useCallback,
    useMemo,
    useRef,
} from "react";
import type { ReactNode } from "react";
import { networkManager, musigreeManager } from "../core/singletons";
import type { SimNode, SimLink } from "../network/data";
import { FORCE } from "../constants";
import * as d3 from "d3";
import { clamp } from "../utils";
import {
    NetworkContext,
    initialState,
    networkReducer,
} from "./networkContextInstance";

// Provider component
interface NetworkProviderProps {
    children: ReactNode;
}

export const NetworkProvider = ({
    children,
}: NetworkProviderProps): React.ReactElement => {
    const [state, dispatch] = useReducer(networkReducer, initialState);

    // Create a ref to always track the latest state
    const stateRef = useRef(state);

    // Update the ref whenever state changes
    useEffect(() => {
        stateRef.current = state;
    }, [state]);

    // Helper functions for force layout manipulation, memoized with useCallback
    const setupChargeForce = useCallback((nodeStrength: number): void => {
        if (!networkManager.forceLayout) {
            console.error("forceLayout not setup yet");
            return;
        }

        const nodeStrengthMultiplier =
            nodeStrength / FORCE.MULTIPLIER.NODE_STRENGTH_SCALE +
            FORCE.MULTIPLIER.NODE_STRENGTH_BASE;
        console.log(
            "setupChargeForce nodeStrengthMultiplier:",
            nodeStrengthMultiplier,
        );

        networkManager.forceLayout.force(
            "charge",
            d3
                .forceManyBody<SimNode>()
                .strength(calculateNodeStrength)
                .distanceMax(FORCE.DISTANCE.MAX)
                .theta(FORCE.SIMULATION.THETA),
        );

        // Helper function for node strength calculation
        function calculateNodeStrength(d: SimNode): number {
            const baseStrength = d.isIntermediate
                ? FORCE.NODE.STRENGTH_INTERMEDIATE
                : d.cluster
                  ? FORCE.NODE.STRENGTH_CLUSTER
                  : FORCE.NODE.STRENGTH;

            const isLevelOne = d.distance == 1;
            const levelOneBoost = isLevelOne
                ? 0.01 * d.radius * d.radius * d.radius * d.radius
                : 0;
            const intermediateMultiplier = d.isIntermediate ? 0.05 : 0.1;
            const strength =
                baseStrength * nodeStrengthMultiplier -
                d.radius *
                    d.radius *
                    d.radius *
                    intermediateMultiplier *
                    nodeStrengthMultiplier -
                levelOneBoost;
            //             console.log("setupChargeForce radius:", d.radius);
            //             console.log("setupChargeForce strength:", strength);
            return strength;
        }
    }, []);

    const setupLinkForce = useCallback((linkStrength: number): void => {
        if (!networkManager.forceLayout) return;
        console.log("setupLinkForce:", linkStrength);

        const linkStrengthMultiplier =
            linkStrength / FORCE.MULTIPLIER.LINK_STRENGTH_SCALE;

        networkManager.forceLayout.force(
            "link",
            d3
                .forceLink<SimNode, SimLink>()
                .id((d) => d.key || "")
                .links(Array.from(networkManager.data.linkMap.values()))
                .distance(calculateLinkDistance)
                .iterations(FORCE.LINK.ITERATIONS),
        );

        // Helper function for link distance calculation
        function calculateLinkDistance(d: SimLink): number {
            let distance = FORCE.DISTANCE.LINK;
            //             const isInner = Math.min(d.source.distance, d.target.distance) == 0;
            const isInner = d.distance == 0;
            const innerDistance = isInner ? 0 : 0;
            if (d.role === FORCE.LINK.ROLES.ALIAS) {
                distance = FORCE.DISTANCE.LINK_ALIAS;
            } else if (d.role === FORCE.LINK.ROLES.RELEASED_ON) {
                distance = FORCE.DISTANCE.LINK_RELEASED_ON;
            } else if (d.isSpline) {
                distance =
                    d.distance < 1
                        ? FORCE.DISTANCE.LINK / 5
                        : FORCE.DISTANCE.LINK / 10;
            }

            const minRadius = Math.min(d.source.radius, d.target.radius);
            // const maxRadius = Math.max(d.source.radius, d.target.radius);
            // const combinedRadius = d.source.radius + d.target.radius;
            const strength =
                distance * linkStrengthMultiplier +
                minRadius * 10.0 * linkStrengthMultiplier +
                innerDistance;
            return strength * 0.7;
        }
    }, []);

    const setupGravityForce = useCallback((gravityStrength: number): void => {
        if (!networkManager.forceLayout) return;
        console.log("setupGravityForce:", gravityStrength);

        const gravStrengthMultiplier =
            gravityStrength / FORCE.MULTIPLIER.GRAVITY_STRENGTH_SCALE;

        networkManager.forceLayout
            .force(
                "x",
                d3
                    .forceX<SimNode>(musigreeManager.svgDimensions[0] / 2)
                    .strength(calculateGravityStrength),
            )
            .force(
                "y",
                d3
                    .forceY<SimNode>(musigreeManager.svgDimensions[1] / 2)
                    .strength(calculateGravityStrength),
            );

        // Helper function for gravity strength calculation
        function calculateGravityStrength(d: SimNode): number {
            var dist = d.distance ? 4 - clamp(d.distance, 0, 3) : 1.0;
            var scaling = dist / 10.0;
            var minDimension = Math.min(
                musigreeManager.svgDimensions[0],
                musigreeManager.svgDimensions[1],
            );
            var maxDimension = Math.max(
                musigreeManager.svgDimensions[0],
                musigreeManager.svgDimensions[1],
            );
            var xyScale = minDimension / maxDimension;
            var maxDist = Math.hypot(
                musigreeManager.svgDimensions[0] / 2.0,
                musigreeManager.svgDimensions[1] / 2.0,
            );
            var radialDistance =
                musigreeManager.svgDimensions[0] >=
                musigreeManager.svgDimensions[1]
                    ? Math.hypot(
                          d.x - musigreeManager.svgDimensions[0] / 2.0,
                          (d.y - musigreeManager.svgDimensions[1] / 2.0) *
                              xyScale *
                              xyScale,
                      )
                    : Math.hypot(
                          (d.x - musigreeManager.svgDimensions[0] / 2.0) *
                              xyScale *
                              xyScale,
                          d.y - musigreeManager.svgDimensions[1] / 2.0,
                      );
            var scaledRadialDistance = (maxDist - radialDistance) / maxDist;
            //             var radialDistance =
            //                 (maxDimension -
            //                     Math.max(
            //                         Math.abs(d.x - musigreeManager.svgDimensions[0] / 2.0),
            //                         Math.abs(d.y - musigreeManager.svgDimensions[1] / 2.0),
            //                     )) /
            //                 maxDimension;
            var result =
                scaledRadialDistance * scaling * gravStrengthMultiplier * 0.5;
            // console.log(d.x, d.y);
            // console.log(result);
            return result;
        }
    }, []);

    // Initialize forces when component mounts or when the force layout changes
    useEffect(() => {
        // Check if forceLayout exists before trying to set up forces
        if (networkManager.forceLayout) {
            console.log("Initializing network forces from React context");

            // Set up initial force values from current state
            const currentState = stateRef.current;
            setupChargeForce(currentState.nodeStrength);
            setupLinkForce(currentState.linkStrength);
            setupGravityForce(currentState.gravityStrength);
        } else {
            console.log(
                "Force layout not initialized yet, will set up forces when ready",
            );
        }
    }, [setupChargeForce, setupLinkForce, setupGravityForce]);

    // Setup event listener for force layout initialization
    useEffect(() => {
        const handleForceLayoutInitialized = (): void => {
            console.log("Force layout initialized, setting up forces");
            // Set up initial force values from current state
            const currentState = stateRef.current;
            setupChargeForce(currentState.nodeStrength);
            setupLinkForce(currentState.linkStrength);
            setupGravityForce(currentState.gravityStrength);
        };

        window.addEventListener(
            "musigree:force-layout-initialized",
            handleForceLayoutInitialized,
        );

        return (): void => {
            window.removeEventListener(
                "musigree:force-layout-initialized",
                handleForceLayoutInitialized,
            );
        };
    }, [setupChargeForce, setupLinkForce, setupGravityForce]);

    // Setup event listener for reset forces event
    useEffect(() => {
        const handleSetForces = (): void => {
            console.log("Received set forces event");
            dispatch({ type: "SET_FORCES" });
            // Use the ref to get current state values
            const currentState = stateRef.current;
            setupChargeForce(currentState.nodeStrength);
            setupLinkForce(currentState.linkStrength);
            setupGravityForce(currentState.gravityStrength);
        };

        window.addEventListener("musigree:set-forces", handleSetForces);

        const handleResetForces = (): void => {
            console.log("Received reset forces event");
            dispatch({ type: "RESET_FORCES" });
            setupChargeForce(initialState.nodeStrength);
            setupLinkForce(initialState.linkStrength);
            setupGravityForce(initialState.gravityStrength);
        };

        window.addEventListener("musigree:reset-forces", handleResetForces);

        return (): void => {
            window.removeEventListener("musigree:set-forces", handleSetForces);
            window.removeEventListener(
                "musigree:reset-forces",
                handleResetForces,
            );
        };
    }, [setupChargeForce, setupLinkForce, setupGravityForce]);

    // Define setForces and resetForces as separate callbacks with proper dependencies
    const setForces = useCallback((): void => {
        dispatch({ type: "SET_FORCES" });
        // Use the ref to get current state values
        const currentState = stateRef.current;
        setupChargeForce(currentState.nodeStrength);
        setupLinkForce(currentState.linkStrength);
        setupGravityForce(currentState.gravityStrength);
    }, [dispatch, setupChargeForce, setupLinkForce, setupGravityForce]);

    const resetForces = useCallback((): void => {
        dispatch({ type: "RESET_FORCES" });
        setupChargeForce(initialState.nodeStrength);
        setupLinkForce(initialState.linkStrength);
        setupGravityForce(initialState.gravityStrength);
    }, [dispatch, setupChargeForce, setupLinkForce, setupGravityForce]);

    // Memoize the context value to prevent unnecessary re-renders of consumers
    const contextValue = useMemo(
        () => ({
            state,
            dispatch,
            setupChargeForce,
            setupLinkForce,
            setupGravityForce,
            setForces,
            resetForces,
        }),
        [
            state,
            dispatch,
            setupChargeForce,
            setupLinkForce,
            setupGravityForce,
            setForces,
            resetForces,
        ],
    );

    return (
        <NetworkContext.Provider value={contextValue}>
            {children}
        </NetworkContext.Provider>
    );
};
