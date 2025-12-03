/**
 * Data structure for individual entity details returned from the API
 */
export interface EntityData {
    /** The unique identifier for the entity */
    id: number;
    /** The type of the entity (e.g., "artist", "label") */
    type: "artist" | "label";
    /** The name of the entity */
    name: string;
    /** Metadata associated with the entity */
    metadata: Record<string, unknown>; // TODO sort out types
    /** Related entities (aliases, groups, members, sublabels, etc.) */
    entities: Record<string, unknown>; // TODO maybe remove?
    /** Counts of various relationships the entity has */
    relation_counts: Record<string, number>;
    /** Countries associated with the entity */
    // eslint-disable-next-line @typescript-eslint/no-redundant-type-constituents
    countries: string | undefined;
    /** Genres associated with the entity */
    // eslint-disable-next-line @typescript-eslint/no-redundant-type-constituents
    genres: string | undefined;
    /** Styles associated with the entity */
    // eslint-disable-next-line @typescript-eslint/no-redundant-type-constituents
    styles: string | undefined;
}
