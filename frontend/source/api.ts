import type { NodeKey, LinkKey } from "./network/data";
import type { NetworkCenter } from "./network/data";
import type { EntityData } from "./entities";
import type { RelationsData } from "./relations";
import type { NodeType } from "./network/data";
import { API } from "./constants";

interface APINetworkNode {
    cluster?: number;
    distance?: number;
    id: string;
    key: NodeKey;
    links?: APINetworkLink[];
    missing?: number;
    name: string;
    size: number;
    type: NodeType | string; // Allow string for backwards compatibility with API
}

interface APINetworkLink {
    key: LinkKey;
    role: string;
    source: NodeKey;
    target: NodeKey;
}

export interface APINetworkDataResponse {
    center: {
        key: NodeKey;
        name: string;
    };
    nodes: APINetworkNode[];
    links: APINetworkLink[];
}

const getNetworkURL = (entityKey: NodeKey, roles: string[]): string => {
    const [entityType, entityId] = entityKey.split("-");
    let url = API.ENDPOINTS.NETWORK(entityType, entityId);
    if (roles.length) {
        url += `?${new URLSearchParams({ roles: roles.join(",") }).toString()}`;
    }
    return url;
};

const getRandomURL = (roles: string[]): string => {
    const baseUrl = API.ENDPOINTS.RANDOM();
    let url = `${baseUrl}?r=${Math.floor(Math.random() * API.RANDOM_MAX)}`;
    if (roles.length) {
        url += `&${new URLSearchParams({ roles: roles.join(",") }).toString()}`;
    }
    return url;
};

const getEntityRelationsURL = (entityKey: NodeKey): string => {
    const [entityType, entityId] = entityKey.split("-");
    return API.ENDPOINTS.RELATIONS(entityType, entityId);
};

const getEntityDetailsURL = (entityKey: NodeKey): string => {
    const [entityType, entityId] = entityKey.split("-");
    return API.ENDPOINTS.DETAILS(entityType, entityId);
};

export const fetchAPINetwork = async (
    entityKey: NodeKey,
    roles: string[],
): Promise<APINetworkDataResponse> => {
    const url = getNetworkURL(entityKey, roles);

    const response = await fetch(url);
    if (!response.ok) throw new Error(response.statusText);
    return (await response.json()) as APINetworkDataResponse;
};

export const fetchAPIRandom = async (
    roles: string[],
): Promise<NetworkCenter> => {
    const url = getRandomURL(roles);

    const response = await fetch(url);
    if (!response.ok) throw new Error(response.statusText);
    return (await response.json()) as NetworkCenter;
};

export const fetchAPIRadial = async (
    entityKey: NodeKey,
): Promise<RelationsData> => {
    const url = getEntityRelationsURL(entityKey);

    const response = await fetch(url);
    if (!response.ok) throw new Error(response.statusText);
    return (await response.json()) as RelationsData;
};

export const fetchAPIEntityDetails = async (
    entityKey: NodeKey,
): Promise<EntityData> => {
    const url = getEntityDetailsURL(entityKey);

    const response = await fetch(url);
    if (!response.ok) throw new Error(response.statusText);
    return (await response.json()) as EntityData;
};
