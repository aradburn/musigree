import type {LinkKey, NetworkCenter, NodeKey} from "./network/data";
import type {EntityData} from "./entities";
import type {RelationsData} from "./relations";
import type {YearQuery} from "./yearBounds";
import {API} from "./constants";

interface APINetworkNode {
    cluster?: number;
    distance?: number;
    id: string;
    key: NodeKey;
    links?: APINetworkLink[];
    missing?: number;
    name: string;
    size: number;
    type: string; // Allow string for backwards compatibility with API (NodeType is a subset of string)
}

interface APINetworkLink {
    key: LinkKey;
    role: string;
    years: number[];
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

const appendFilters = (
    params: URLSearchParams,
    roles: string[],
    years?: YearQuery,
): void => {
    if (roles.length > 0) {
        params.set("roles", roles.join(","));
    }
    if (years) {
        params.set("min_year", String(years.minYear));
        params.set("max_year", String(years.maxYear));
    }
};

const getNetworkURL = (
    entityKey: NodeKey,
    roles: string[],
    years?: YearQuery,
): string => {
    const [entityType, entityId] = entityKey.split("-");
    const url = API.ENDPOINTS.NETWORK(entityType, entityId);
    const params = new URLSearchParams();
    appendFilters(params, roles, years);
    const query = params.toString();
    return query ? `${url}?${query}` : url;
};

const getRandomURL = (roles: string[], years?: YearQuery): string => {
    const params = new URLSearchParams();
    params.set("r", String(Math.floor(Math.random() * API.RANDOM_MAX)));
    appendFilters(params, roles, years);
    return `${API.ENDPOINTS.RANDOM()}?${params.toString()}`;
};

const getRelationsURL = (entityKey: NodeKey): string => {
    const [entityType, entityId] = entityKey.split("-");
    return API.ENDPOINTS.RELATIONS(entityType, entityId);
};

const getEntityURL = (entityKey: NodeKey): string => {
    const [entityType, entityId] = entityKey.split("-");
    return API.ENDPOINTS.ENTITY(entityType, entityId);
};

export const fetchAPINetwork = async (
    entityKey: NodeKey,
    roles: string[],
    years?: YearQuery,
): Promise<APINetworkDataResponse> => {
    const url = getNetworkURL(entityKey, roles, years);

    const response = await fetch(url);
    if (!response.ok) throw new Error(response.statusText);
    return (await response.json()) as APINetworkDataResponse;
};

export const fetchAPIRandom = async (
    roles: string[],
    years?: YearQuery,
): Promise<NetworkCenter> => {
    const url = getRandomURL(roles, years);

    const response = await fetch(url);
    if (!response.ok) throw new Error(response.statusText);
    return (await response.json()) as NetworkCenter;
};

export const fetchAPIRelations = async (
    entityKey: NodeKey,
): Promise<RelationsData> => {
    const url = getRelationsURL(entityKey);

    const response = await fetch(url);
    if (!response.ok) throw new Error(response.statusText);
    return (await response.json()) as RelationsData;
};

export const fetchAPIEntity = async (
    entityKey: NodeKey,
): Promise<EntityData> => {
    const url = getEntityURL(entityKey);

    const response = await fetch(url);
    if (!response.ok) throw new Error(response.statusText);
    return (await response.json()) as EntityData;
};
