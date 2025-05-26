import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { clamp, debounce } from "../utils";

describe("Utility Functions", () => {
    describe("clamp", () => {
        it("should return the value when it is within range", () => {
            expect(clamp(5, 0, 10)).toBe(5);
        });

        it("should return the minimum value when value is below range", () => {
            expect(clamp(-5, 0, 10)).toBe(0);
        });

        it("should return the maximum value when value is above range", () => {
            expect(clamp(15, 0, 10)).toBe(10);
        });

        it("should handle equal min and max values", () => {
            expect(clamp(5, 10, 10)).toBe(10);
        });

        it("should handle decimal numbers", () => {
            expect(clamp(1.5, 1, 2)).toBe(1.5);
            expect(clamp(0.5, 1, 2)).toBe(1);
            expect(clamp(2.5, 1, 2)).toBe(2);
        });
    });

    describe("debounce", () => {
        beforeEach(() => {
            vi.useFakeTimers();
        });

        afterEach(() => {
            vi.restoreAllMocks();
        });

        it("should call the function after the specified wait time", () => {
            const mockFn = vi.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn();
            expect(mockFn).not.toHaveBeenCalled();

            vi.advanceTimersByTime(100);
            expect(mockFn).toHaveBeenCalledTimes(1);
        });

        it("should only call the function once when called multiple times within wait period", () => {
            const mockFn = vi.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn();
            debouncedFn();
            debouncedFn();

            vi.advanceTimersByTime(50);
            expect(mockFn).not.toHaveBeenCalled();

            vi.advanceTimersByTime(50);
            expect(mockFn).toHaveBeenCalledTimes(1);
        });

        it("should call the function with the latest arguments", () => {
            const mockFn = vi.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn("first");
            debouncedFn("second");
            debouncedFn("third");

            vi.advanceTimersByTime(100);
            expect(mockFn).toHaveBeenCalledWith("third");
        });

        it("should reset the timer when called again", () => {
            const mockFn = vi.fn();
            const debouncedFn = debounce(mockFn, 100);

            debouncedFn();
            vi.advanceTimersByTime(50);

            debouncedFn();
            vi.advanceTimersByTime(50);
            expect(mockFn).not.toHaveBeenCalled();

            vi.advanceTimersByTime(50);
            expect(mockFn).toHaveBeenCalledTimes(1);
        });
    });
});
