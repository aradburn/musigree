import { networkManager } from "../core/singletons";
import { getOuterRadius } from "./node";
import type { APINetworkDataResponse } from "../api";

/**
 * Enum for node types in the network graph
 */
export enum NodeType {
    Artist = "artist",
    Label = "label",
}

export type NodeKey = string;
export type LinkKey = string;

interface DraggableNodeBase {
    dragx: number;
    dragy: number;
    x: number;
    y: number;
    fx: number | null;
    fy: number | null;
}

export type DraggableNode = NetworkNode & DraggableNodeBase;

/**
 * Properties added to nodes by D3's force simulation
 */
interface SimulationProps extends DraggableNodeBase {
    vx: number;
    vy: number;
    index: number;
    isIntermediate: boolean;
    cluster: number;
    fixed: boolean;
    missing: number;
    hasMissing: boolean;
    links: NetworkLink[];
    highlighted: boolean;
    selected: boolean;
}

/**
 * Node type with simulation properties
 */
export type SimNode = NetworkNode & SimulationProps;

/**
 * Link type for force simulation
 */
export interface SimLink
    extends Omit<NetworkLink, "source" | "target" | "intermediate"> {
    source: SimNode;
    target: SimNode;
    role: string;
    isSpline: boolean;
    distance: number;
    intermediate: SimNode;
    highlighted: boolean;
    selected: boolean;
}

/**
 * Core network data structure
 */
export interface SimData {
    center: NetworkNode;
    nodeMap: Map<NodeKey, SimNode>;
    linkMap: Map<LinkKey, SimLink>;
    maxDistance: number;
}

export interface NetworkNode {
    key: NodeKey;
    name: string;
    type: NodeType;
    size: number;
    x: number;
    y: number;
    missing: number;
    hasMissing: boolean;
    lastClickTime: number;
    lastTouchTime: number;
    distance: number;
    radius: number;
    links: NetworkLink[];
    cluster: number;
    fixed: boolean;
    isIntermediate: boolean;
    // pages?: unknown;
}

export interface NetworkLink {
    key: LinkKey;
    source: NetworkNode;
    target: NetworkNode;
    role: string;
    distance: number;
    isSpline: boolean;
    intermediate: NetworkNode;
    // pages?: unknown;
}

// Processed network data
export interface NetworkData {
    nodeMap: Map<NodeKey, NetworkNode>;
    center: NetworkNode;
    linkMap: Map<LinkKey, NetworkLink>;
    maxDistance: number;
}

export interface NetworkCenter {
    center: NodeKey;
}

export const processAPINetworkDataResponse = (
    apiNetworkDataResponse: APINetworkDataResponse,
): NetworkData => {
    //     console.log(
    //         "processAPINetworkDataResponse input apiNetworkDataResponse:",
    //         apiNetworkDataResponse,
    //     );

    if (
        !apiNetworkDataResponse ||
        !Array.isArray(apiNetworkDataResponse.nodes) ||
        !Array.isArray(apiNetworkDataResponse.links)
    ) {
        throw new Error("Invalid network data format");
    }

    // Process nodes and links
    const nodeMap = new Map<NodeKey, NetworkNode>();
    const processedNodes = apiNetworkDataResponse.nodes.map((node) => {
        const size = typeof node.size === "number" ? node.size : 10;
        const distance = typeof node.distance === "number" ? node.distance : 0;
        const processedNode: NetworkNode = {
            key: node.key,
            name: node.name,
            type: node.type === "artist" ? NodeType.Artist : NodeType.Label,
            size: size,
            x: 0,
            y: 0,
            distance: distance,
            radius: 0,
            links: [] as NetworkLink[],
            cluster: node.cluster,
            missing: node.missing,
            hasMissing: node.missing > 0 ? true : false,
            lastClickTime: 0,
            lastTouchTime: 0,
            isIntermediate: false,
            fixed: false,
        };
        nodeMap.set(node.key, processedNode);
        return processedNode;
    });

    //     console.log("nodeMap:", nodeMap);

    const linkMap = new Map<LinkKey, NetworkLink>();
    const processedLinks = apiNetworkDataResponse.links.map((link) => {
        const source = nodeMap.get(link.source);
        const target = nodeMap.get(link.target);
        if (!source || !target) {
            console.log("Invalid link:", link);
            console.log("source:", source);
            console.log("target:", target);
            throw new Error("Invalid link: missing source or target node");
        }
        const processedLink: NetworkLink = {
            key: link.key,
            role: link.role,
            source,
            target,
            distance: Math.min(source.distance, target.distance),
            isSpline: false,
            intermediate: undefined,
        };
        linkMap.set(link.key, processedLink);
        return processedLink;
    });

    //     console.log("processedLinks:", processedLinks);

    // Update node links after all links are processed
    processedLinks.forEach((link) => {
        const sourceNode = nodeMap.get(link.source.key);
        const targetNode = nodeMap.get(link.target.key);
        //         console.log("sourceNode:", sourceNode);
        //         console.log("targetNode:", targetNode);
        if (sourceNode && targetNode) {
            if (sourceNode.links === undefined)
                sourceNode.links = [] as NetworkLink[];
            if (targetNode.links === undefined)
                targetNode.links = [] as NetworkLink[];
            sourceNode.links.push(link);
            targetNode.links.push(link);
            //             console.log("updated sourceNode links:", sourceNode.links);
            //             console.log("updated targetNode links:", targetNode.links);
        }
    });

    //     console.log("updated nodeMap:", nodeMap);

    const center = processedNodes.find(
        (n) => n.key === apiNetworkDataResponse.center.key,
    );
    if (!center) {
        throw new Error("Center node not found");
    }

    const networkData: NetworkData = {
        nodeMap,
        center,
        linkMap,
        maxDistance: Math.max(...processedNodes.map((n) => n.distance)),
    };
    //     console.log(
    //         "processAPINetworkDataResponse output networkData:",
    //         networkData,
    //     );

    return networkData;
};

/**
 * Processes the NetworkData data to create nodes and links for the force layout
 * @param {NetworkData} networkData - The network data object containing nodes and links
 */
export const convertNetworkDataToSimData = (
    networkData: NetworkData,
): SimData => {
    //     console.log("convertNetworkDataToSimData input:", networkData);

    const newNodeMap = new Map<NodeKey, SimNode>();
    const newLinkMap = new Map<LinkKey, SimLink>();
    const newSimData: SimData = {
        center: networkData.center,
        nodeMap: newNodeMap,
        linkMap: newLinkMap,
        maxDistance: 0,
    };

    // Setup node size
    networkData.nodeMap.forEach((node) => {
        const simNode: SimNode = {
            key: node.key,
            isIntermediate: false,
            size: node.size,
            name: node.name,
            type: node.type,
            x: networkManager.newNodeCoords[0],
            y: networkManager.newNodeCoords[1],
            distance: node.distance,
            radius: 0,
            missing: node.missing,
            hasMissing: node.hasMissing,
            lastClickTime: node.lastClickTime,
            lastTouchTime: node.lastTouchTime,
            links: node.links,
            cluster: node.cluster,
            fixed: node.fixed,
            vx: 0,
            vy: 0,
            index: 0,
            dragx: 0,
            dragy: 0,
            fx: null,
            fy: null,
            highlighted: false,
            selected: false,
        };
        simNode.radius = getOuterRadius(simNode);
        newNodeMap.set(node.key, simNode);
    });

    // Setup links, add intermediate node at center of link
    networkData.linkMap.forEach((link) => {
        const sourceNode = newNodeMap.get(link.source.key);
        const targetNode = newNodeMap.get(link.target.key);

        if (link.role !== "Alias") {
            const role = link.role?.toLowerCase().replace(/\s+/g, "-") ?? "";
            const intermediateNode: SimNode = {
                key: link.key,
                isIntermediate: true,
                size: 0,
                name: "",
                type: NodeType.Artist, // Default type
                x: networkManager.newNodeCoords[0],
                y: networkManager.newNodeCoords[1],
                distance: 0,
                radius: 0,
                missing: 0,
                hasMissing: false,
                lastClickTime: 0,
                lastTouchTime: 0,
                links: [],
                cluster: undefined,
                fixed: false,
                vx: 0,
                vy: 0,
                index: 0,
                dragx: 0,
                dragy: 0,
                fx: null,
                fy: null,
                highlighted: false,
                selected: false,
            };

            const s2iSplineLink: SimLink = {
                isSpline: true,
                key: `${sourceNode.key}-${role}-[${targetNode.key}]`,
                source: sourceNode,
                target: intermediateNode,
                role: role,
                distance: 0,
                intermediate: undefined,
                highlighted: false,
                selected: false,
            };

            const i2tSplineLink: SimLink = {
                isSpline: true,
                key: `[${sourceNode.key}]-${role}-${targetNode.key}`,
                source: intermediateNode,
                target: targetNode,
                role: role,
                distance: 0,
                intermediate: undefined,
                highlighted: false,
                selected: false,
            };

            newNodeMap.set(intermediateNode.key, intermediateNode);
            newLinkMap.set(s2iSplineLink.key, s2iSplineLink);
            newLinkMap.set(i2tSplineLink.key, i2tSplineLink);

            const simLink: SimLink = {
                isSpline: false,
                key: link.key,
                source: sourceNode,
                target: targetNode,
                intermediate: intermediateNode,
                role: link.role,
                distance: link.distance,
                highlighted: false,
                selected: false,
            };
            newLinkMap.set(simLink.key, simLink);
        } else {
            const simLink: SimLink = {
                isSpline: false,
                key: link.key,
                source: sourceNode,
                target: targetNode,
                intermediate: undefined,
                role: link.role,
                distance: link.distance,
                highlighted: false,
                selected: false,
            };
            newLinkMap.set(simLink.key, simLink);
        }
    });
    console.log(
        "convertNetworkDataToSimData output after adding intermediate nodes: ",
        newSimData,
    );
    return newSimData;
};

export const updateGlobalData = (simData: SimData): void => {
    console.log("updateGlobalData input:", simData);

    networkManager.data.nodeMap = simData.nodeMap;
    networkManager.data.linkMap = simData.linkMap;
    networkManager.data.maxDistance = simData.maxDistance;
    networkManager.data.center = simData.center;
};

// export const setupSimData = (networkData: NetworkData): SimData => {
//     const simData = convertNetworkDataToSimData(networkData);
//     updateGlobalData(simData);
//     return simData;
// };
