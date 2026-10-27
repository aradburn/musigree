/**
 * Selected release-year bounds for the network filter.
 * A span that covers the whole slider track means no year constraint.
 */

/** First year on the slider track. */
export const YEAR_TRACK_MIN = 1900;

/** Last year on the slider track. */
export const YEAR_TRACK_MAX = 2030;

export interface YearBounds {
    minYear: number;
    maxYear: number;
}

/** Bounds narrow enough to send as min_year and max_year. */
export interface YearQuery {
    minYear: number;
    maxYear: number;
}

const clampYear = (year: number): number =>
    Math.min(YEAR_TRACK_MAX, Math.max(YEAR_TRACK_MIN, year));

let selectedYearBounds: YearBounds = {
    minYear: YEAR_TRACK_MIN,
    maxYear: YEAR_TRACK_MAX,
};

export const getSelectedYearBounds = (): YearBounds => ({
    minYear: selectedYearBounds.minYear,
    maxYear: selectedYearBounds.maxYear,
});

export const updateSelectedYearBounds = (bounds: YearBounds): void => {
    const minYear = clampYear(Math.min(bounds.minYear, bounds.maxYear));
    const maxYear = clampYear(Math.max(bounds.minYear, bounds.maxYear));
    selectedYearBounds = { minYear, maxYear };
};

export const isFullYearTrack = (
    bounds: YearBounds = selectedYearBounds,
): boolean =>
    bounds.minYear <= YEAR_TRACK_MIN && bounds.maxYear >= YEAR_TRACK_MAX;

/**
 * Query bounds for the current selection.
 * Undefined when the slider still covers every year on the track.
 */
export const getYearQuery = (): YearQuery | undefined => {
    if (isFullYearTrack()) {
        return undefined;
    }
    return {
        minYear: selectedYearBounds.minYear,
        maxYear: selectedYearBounds.maxYear,
    };
};
