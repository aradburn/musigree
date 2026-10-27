import { describe, expect, it, afterEach } from "vitest";
import {
    YEAR_TRACK_MAX,
    YEAR_TRACK_MIN,
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
});
