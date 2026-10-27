/** @jsxImportSource react */
import React, { useState } from "react";
import {
    YEAR_TRACK_MAX,
    YEAR_TRACK_MIN,
    getSelectedYearBounds,
    updateSelectedYearBounds,
} from "../../yearBounds";
import type { YearBounds } from "../../yearBounds";

interface YearRangeSliderProps {
    onChange: () => void;
}

type ActiveThumb = "min" | "max";

const TRACK_SPAN = YEAR_TRACK_MAX - YEAR_TRACK_MIN;

/**
 * Dual-thumb year slider. Both thumbs start at the ends of the track.
 * Moving either thumb stores the inclusive range and notifies the parent.
 */
export const YearRangeSlider: React.FC<YearRangeSliderProps> = ({
    onChange,
}) => {
    const [bounds, setBounds] = useState<YearBounds>(() =>
        getSelectedYearBounds(),
    );
    const [activeThumb, setActiveThumb] = useState<ActiveThumb>("max");

    const commit = (next: YearBounds, thumb: ActiveThumb): void => {
        updateSelectedYearBounds(next);
        setBounds(getSelectedYearBounds());
        setActiveThumb(thumb);
        onChange();
    };

    const handleMinChange = (
        event: React.ChangeEvent<HTMLInputElement>,
    ): void => {
        const nextMin = Number(event.target.value);
        commit(
            {
                minYear: Math.min(nextMin, bounds.maxYear),
                maxYear: bounds.maxYear,
            },
            "min",
        );
    };

    const handleMaxChange = (
        event: React.ChangeEvent<HTMLInputElement>,
    ): void => {
        const nextMax = Number(event.target.value);
        commit(
            {
                minYear: bounds.minYear,
                maxYear: Math.max(nextMax, bounds.minYear),
            },
            "max",
        );
    };

    // Ratios match the range thumb centers: each thumb travels
    // (track width - thumb width), starting half a thumb in from the edge.
    const minRatio = (bounds.minYear - YEAR_TRACK_MIN) / TRACK_SPAN;
    const maxRatio = (bounds.maxYear - YEAR_TRACK_MIN) / TRACK_SPAN;

    return (
        <div className="year-range">
            <div className="year-range-labels">
                <span>{bounds.minYear}</span>
                <span>{bounds.maxYear}</span>
            </div>
            <div className="year-range-track">
                <div className="year-range-rail" />
                <div
                    className="year-range-highlight"
                    style={
                        {
                            "--year-min-ratio": minRatio,
                            "--year-max-ratio": maxRatio,
                        } as React.CSSProperties
                    }
                />
                <input
                    id="year-range-min"
                    className="year-range-input"
                    type="range"
                    min={YEAR_TRACK_MIN}
                    max={YEAR_TRACK_MAX}
                    step={1}
                    value={bounds.minYear}
                    aria-label="Minimum year"
                    style={{ zIndex: activeThumb === "min" ? 4 : 3 }}
                    onPointerDown={(): void => setActiveThumb("min")}
                    onChange={handleMinChange}
                />
                <input
                    id="year-range-max"
                    className="year-range-input"
                    type="range"
                    min={YEAR_TRACK_MIN}
                    max={YEAR_TRACK_MAX}
                    step={1}
                    value={bounds.maxYear}
                    aria-label="Maximum year"
                    style={{ zIndex: activeThumb === "max" ? 4 : 3 }}
                    onPointerDown={(): void => setActiveThumb("max")}
                    onChange={handleMaxChange}
                />
            </div>
        </div>
    );
};

export default YearRangeSlider;
