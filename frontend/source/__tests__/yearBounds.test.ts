import { describe, expect, it, afterEach } from "vitest";
import {
    YEAR_TRACK_MAX,
    YEAR_TRACK_MIN,
    applyInitialYearBoundsFromSearch,
    getSelectedYearBounds,
    getYearQuery,
    isFullYearTrack,
    updateSelectedYearBounds,
} from "../yearBounds";

describe("yearBounds", () => {
    afterEach(() => {
        updateSelectedYearBounds({
            minYear: YEAR_TRACK_MIN,
            maxYear: YEAR_TRACK_MAX,
        });
    });

    it("omits a year query when the slider covers the whole track", () => {
        expect(isFullYearTrack()).toBe(true);
        expect(getYearQuery()).toBeUndefined();
    });

    it("returns both bounds when the range is narrower than the track", () => {
        updateSelectedYearBounds({ minYear: 1970, maxYear: 1979 });

        expect(getYearQuery()).toEqual({ minYear: 1970, maxYear: 1979 });
    });

    it("keeps the minimum from crossing above the maximum", () => {
        updateSelectedYearBounds({ minYear: 1990, maxYear: 1980 });

        expect(getYearQuery()).toEqual({ minYear: 1980, maxYear: 1990 });
    });

    it("seeds both bounds from min_year and max_year in the page search", () => {
        applyInitialYearBoundsFromSearch(
            "?roles=Producer&min_year=1970&max_year=1979",
        );

        expect(getSelectedYearBounds()).toEqual({
            minYear: 1970,
            maxYear: 1979,
        });
    });

    it("keeps the unset end of the track when only one year is in the search", () => {
        applyInitialYearBoundsFromSearch("?min_year=1985");
        expect(getSelectedYearBounds()).toEqual({
            minYear: 1985,
            maxYear: YEAR_TRACK_MAX,
        });

        updateSelectedYearBounds({
            minYear: YEAR_TRACK_MIN,
            maxYear: YEAR_TRACK_MAX,
        });

        applyInitialYearBoundsFromSearch("?max_year=1962");
        expect(getSelectedYearBounds()).toEqual({
            minYear: YEAR_TRACK_MIN,
            maxYear: 1962,
        });
    });

    it("keeps the track end when the other year parameter is not a year", () => {
        applyInitialYearBoundsFromSearch("?min_year=1970&max_year=nope");

        expect(getSelectedYearBounds()).toEqual({
            minYear: 1970,
            maxYear: YEAR_TRACK_MAX,
        });
    });

    it("leaves the current bounds when the search has no usable years", () => {
        updateSelectedYearBounds({ minYear: 1950, maxYear: 1960 });

        applyInitialYearBoundsFromSearch("");
        applyInitialYearBoundsFromSearch("?roles=Producer");
        applyInitialYearBoundsFromSearch("?min_year=nope&max_year=");

        expect(getSelectedYearBounds()).toEqual({
            minYear: 1950,
            maxYear: 1960,
        });
    });

    it("clamps search years onto the slider track", () => {
        applyInitialYearBoundsFromSearch("?min_year=1800&max_year=2100");

        expect(getSelectedYearBounds()).toEqual({
            minYear: YEAR_TRACK_MIN,
            maxYear: YEAR_TRACK_MAX,
        });
    });
});
