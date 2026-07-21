import type { LinkKey, NodeKey, SimData } from "./data";

// Graph size limits
const MAX_NODES_BEFORE_PRUNING = 600; // Maximum nodes before pruning is triggered
const MAX_LINKS_BEFORE_PRUNING = 1800; // Maximum links before pruning is triggered
const MAX_ALIAS_LINKS_BEFORE_PRUNING = 100; // Maximum links before pruning is triggered

export const pruneSimData = (simData: SimData): SimData => {
    // Get some useful stats
    const distances: number[] = [];
    const distance_counts = [0, 0, 0, 0, 0, 0];
    Array.from(simData.nodeMap.values()).forEach((node) => {
        if (node.distance !== undefined) {
            distances.push(node.distance);
            if (node.distance < distance_counts.length) {
                distance_counts[node.distance]++;
            }
        }
    });
    simData.maxDistance = Math.max(...distances);
    //     console.log("maxDistance: ", simData.maxDistance);
    //     console.log("distance_counts: ", distance_counts);
    console.log("pruning initial node size: ", simData.nodeMap.size);
    console.log("pruning initial link size: ", simData.linkMap.size);

    for (const maxDist of [3, 2, 1]) {
        for (const minLinks of [1, 2, 3, 4, 5, 10, 100, 1000000]) {
            simData = prune(simData, maxDist, minLinks);
        }
    }

    const aliasLinkCount = Array.from(simData.linkMap.keys()).filter((key) => {
        const parts = key.split("-");
        const role = parts.slice(2, 2 + parts.length - 4).join("-");
        return role == "alias";
    }).length;
    if (aliasLinkCount > MAX_ALIAS_LINKS_BEFORE_PRUNING) {
        console.log("alias size  : ", aliasLinkCount);
    }
    console.log("pruning final node size  : ", simData.nodeMap.size);
    console.log("pruning final link size  : ", simData.linkMap.size);

    //     console.log("processNetworkData output nodes:", simData.nodeMap);
    //     console.log("processNetworkData output links:", simData.linkMap);

    return simData;
};

/**
 * Prunes the network to keep it within size limits
 * @param {number} maxDist - Maximum distance from center to keep
 * @param {number} minLinks - Minimum number of links to keep a node
 */
const prune = (
    simData: SimData,
    maxDist: number,
    minLinks: number,
): SimData => {
    if (
        simData.nodeMap.size > MAX_NODES_BEFORE_PRUNING ||
        simData.linkMap.size > MAX_LINKS_BEFORE_PRUNING
    ) {
        //         console.log("pruning maxDist: " + maxDist + ", minLinks: " + minLinks);
        const nodeKeysToPrune: NodeKey[] = [];
        const nodeKeyDistancesToPrune: number[] = [];
        Array.from(simData.nodeMap.values()).forEach((node) => {
            //             console.log("  node: dist" + node.distance + ", links len: " + node.links.length);
            if (
                node.distance &&
                node.distance >= maxDist &&
                node.links &&
                node.links.length <= minLinks
            ) {
                //                 console.log("    node pruned: dist: " + node.distance + ", links len: " + node.links.length);
                nodeKeysToPrune.push(node.key);
                nodeKeyDistancesToPrune.push(node.distance);
            }
        });
        // Check if all nodes to be removed are at distance 1
        const abortPruning = nodeKeyDistancesToPrune.every((val) => val === 1);
        if (abortPruning) {
            nodeKeysToPrune.length = 0;
            console.log("    aborted pruning");
        }

        nodeKeysToPrune.forEach((key) => {
            simData.nodeMap.delete(key);
        });
        console.log("pruned nodes: ", nodeKeysToPrune.length);

        const linkKeysToPrune: LinkKey[] = [];
        const intermediateNodesToPrune: NodeKey[] = [];
        const intermediateLinksToPrune: NodeKey[] = [];

        Array.from(simData.linkMap.values()).forEach((link) => {
            if (
                (link.source && nodeKeysToPrune.includes(link.source.key)) ||
                (link.target && nodeKeysToPrune.includes(link.target.key))
            ) {
                linkKeysToPrune.push(link.key);
                link.source.hasMissing = true;
                link.target.hasMissing = true;
                link.source.missing = (link.source.missing ?? 0) + 1;
                link.target.missing = (link.target.missing ?? 0) + 1;
            }
        });

        linkKeysToPrune.forEach((key) => {
            intermediateNodesToPrune.push(key);
            simData.linkMap.delete(key);
        });
        //         console.log("pruned links: ", linkKeysToPrune.length);

        intermediateNodesToPrune.forEach((key) => {
            simData.nodeMap.delete(key);
        });
        //         console.log(
        //             "pruned intermediate nodes: ",
        //             intermediateNodesToPrune.length,
        //         );

        Array.from(simData.linkMap.values()).forEach((link) => {
            if (
                (link.source &&
                    intermediateNodesToPrune.includes(link.source.key)) ||
                (link.target &&
                    intermediateNodesToPrune.includes(link.target.key))
            ) {
                intermediateLinksToPrune.push(link.key);
                link.source.hasMissing = true;
                link.target.hasMissing = true;
                link.source.missing = (link.source.missing ?? 0) + 1;
                link.target.missing = (link.target.missing ?? 0) + 1;
            }
        });

        intermediateLinksToPrune.forEach((key) => {
            simData.linkMap.delete(key);
        });
        //         console.log(
        //             "pruned intermediate links: ",
        //             intermediateLinksToPrune.length,
        //         );

        //         console.log(
        //             `node size after pruning (maxDist: ${maxDist}, minLinks: ${minLinks}): `,
        //             simData.nodeMap.size,
        //         );
        //         console.log(
        //             `link size after pruning (maxDist: ${maxDist}, minLinks: ${minLinks}): `,
        //             simData.linkMap.size,
        //         );
    }
    return simData;
};
