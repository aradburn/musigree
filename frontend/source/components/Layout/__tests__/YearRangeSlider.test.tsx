import { describe, it, expect, vi, afterEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import { YearRangeSlider } from "../YearRangeSlider";
import {
    YEAR_TRACK_MAX,
    YEAR_TRACK_MIN,
    getSelectedYearBounds,
    updateSelectedYearBounds,
} from "../../../yearBounds";

describe("YearRangeSlider", () => {
    afterEach(() => {
        updateSelectedYearBounds({
            minYear: YEAR_TRACK_MIN,
            maxYear: YEAR_TRACK_MAX,
        });
        window.history.pushState({}, "", "/");
    });

    it("returns both thumbs to the ends of the track", () => {
        const onChange = vi.fn();
        render(<YearRangeSlider onChange={onChange} />);

        const heading = screen.getByText("Years");
        const reset = screen.getByRole("button", { name: "Reset years" });
        expect(heading).toHaveClass("h6");
        expect(heading).toContainElement(reset);
        expect(heading.lastElementChild).toBe(reset);
        expect(
            reset.querySelector("i.bi-arrow-counterclockwise"),
        ).toBeInTheDocument();

        fireEvent.change(screen.getByLabelText("Minimum year"), {
            target: { value: "1975" },
        });
        fireEvent.change(screen.getByLabelText("Maximum year"), {
            target: { value: "1990" },
        });
        onChange.mockClear();

        fireEvent.click(reset);

        expect(screen.getByLabelText("Minimum year")).toHaveValue(
            String(YEAR_TRACK_MIN),
        );
        expect(screen.getByLabelText("Maximum year")).toHaveValue(
            String(YEAR_TRACK_MAX),
        );
        expect(screen.getByText(String(YEAR_TRACK_MIN))).toBeInTheDocument();
        expect(screen.getByText(String(YEAR_TRACK_MAX))).toBeInTheDocument();
        expect(getSelectedYearBounds()).toEqual({
            minYear: YEAR_TRACK_MIN,
            maxYear: YEAR_TRACK_MAX,
        });
        expect(onChange).toHaveBeenCalledTimes(1);
    });
});
