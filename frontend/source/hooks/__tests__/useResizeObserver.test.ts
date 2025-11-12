import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useResizeObserver } from "../useResizeObserver";
import { createRef } from "react";

describe("useResizeObserver", () => {
    let observeSpy: ReturnType<typeof vi.fn>;
    let disconnectSpy: ReturnType<typeof vi.fn>;
    let callback: ResizeObserverCallback;

    beforeEach(() => {
        observeSpy = vi.fn();
        disconnectSpy = vi.fn();

        class MockResizeObserver implements ResizeObserver {
            constructor(cb: ResizeObserverCallback) {
                callback = cb;
            }
            observe: (
                target: Element,
                options?: ResizeObserverOptions,
            ) => void = observeSpy as (
                target: Element,
                options?: ResizeObserverOptions,
            ) => void;
            disconnect: () => void = disconnectSpy as () => void;
            unobserve = vi.fn();
        }

        global.ResizeObserver =
            MockResizeObserver as unknown as typeof ResizeObserver;
        if (global.window) {
            global.window.ResizeObserver =
                MockResizeObserver as unknown as typeof ResizeObserver;
        }
    });

    afterEach(() => {
        vi.restoreAllMocks();
    });

    it("should return initial size with undefined width and height", () => {
        const ref = createRef<HTMLDivElement>();
        const { result } = renderHook(() => useResizeObserver({ ref }));

        expect(result.current.width).toBeUndefined();
        expect(result.current.height).toBeUndefined();
    });

    it("should observe the element when ref is available", () => {
        const div = document.createElement("div");
        const ref = { current: div };

        renderHook(() => useResizeObserver({ ref }));

        expect(observeSpy).toHaveBeenCalledWith(div, { box: "content-box" });
    });

    it("should not observe when ref is null", () => {
        const ref = { current: null };

        renderHook(() => useResizeObserver({ ref }));

        expect(observeSpy).not.toHaveBeenCalled();
    });

    it("should not observe when ResizeObserver is not available", () => {
        const div = document.createElement("div");
        const ref = { current: div };

        // Testing when ResizeObserver is not available
        delete (global as { ResizeObserver?: unknown }).ResizeObserver;
        if (global.window) {
            delete (global.window as { ResizeObserver?: unknown })
                .ResizeObserver;
        }

        renderHook(() => useResizeObserver({ ref }));

        expect(observeSpy).not.toHaveBeenCalled();
    });

    it("should use content-box as default box option", () => {
        const div = document.createElement("div");
        const ref = { current: div };

        renderHook(() => useResizeObserver({ ref }));

        expect(observeSpy).toHaveBeenCalledWith(div, { box: "content-box" });
    });

    it("should use border-box when specified", () => {
        const div = document.createElement("div");
        const ref = { current: div };

        renderHook(() => useResizeObserver({ ref, box: "border-box" }));

        expect(observeSpy).toHaveBeenCalledWith(div, { box: "border-box" });
    });

    it("should use device-pixel-content-box when specified", () => {
        const div = document.createElement("div");
        const ref = { current: div };

        renderHook(() =>
            useResizeObserver({ ref, box: "device-pixel-content-box" }),
        );

        expect(observeSpy).toHaveBeenCalledWith(div, {
            box: "device-pixel-content-box",
        });
    });

    it("should update size when ResizeObserver callback is called with contentBoxSize array", async () => {
        const div = document.createElement("div");
        const ref = { current: div };

        const { result } = renderHook(() => useResizeObserver({ ref }));

        // Wait for the effect to run and set up the observer
        await waitFor(() => {
            expect(callback).toBeDefined();
        });

        const mockEntry = {
            contentBoxSize: [{ inlineSize: 100, blockSize: 200 }],
            borderBoxSize: [],
            devicePixelContentBoxSize: [],
            contentRect: { width: 100, height: 200 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry], {} as ResizeObserver);
        });

        await waitFor(() => {
            expect(result.current.width).toBe(100);
            expect(result.current.height).toBe(200);
        });
    });

    it("should update size when ResizeObserver callback is called with borderBoxSize array", async () => {
        const div = document.createElement("div");
        const ref = { current: div };

        const { result } = renderHook(() =>
            useResizeObserver({ ref, box: "border-box" }),
        );

        await waitFor(() => {
            expect(callback).toBeDefined();
        });

        const mockEntry = {
            borderBoxSize: [{ inlineSize: 150, blockSize: 250 }],
            contentBoxSize: [],
            devicePixelContentBoxSize: [],
            contentRect: { width: 150, height: 250 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry], {} as ResizeObserver);
        });

        await waitFor(() => {
            expect(result.current.width).toBe(150);
            expect(result.current.height).toBe(250);
        });
    });

    it("should update size when ResizeObserver callback is called with devicePixelContentBoxSize array", async () => {
        const div = document.createElement("div");
        const ref = { current: div };

        const { result } = renderHook(() =>
            useResizeObserver({ ref, box: "device-pixel-content-box" }),
        );

        await waitFor(() => {
            expect(callback).toBeDefined();
        });

        const mockEntry = {
            devicePixelContentBoxSize: [{ inlineSize: 200, blockSize: 300 }],
            contentBoxSize: [],
            borderBoxSize: [],
            contentRect: { width: 200, height: 300 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry], {} as ResizeObserver);
        });

        await waitFor(() => {
            expect(result.current.width).toBe(200);
            expect(result.current.height).toBe(300);
        });
    });

    it("should update size when ResizeObserver callback is called with non-array contentBoxSize (Firefox)", async () => {
        const div = document.createElement("div");
        const ref = { current: div };

        const { result } = renderHook(() => useResizeObserver({ ref }));

        await waitFor(() => {
            expect(callback).toBeDefined();
        });

        const mockEntry = {
            contentBoxSize: { inlineSize: 120, blockSize: 220 },
            borderBoxSize: {},
            devicePixelContentBoxSize: {},
            contentRect: { width: 120, height: 220 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry], {} as ResizeObserver);
        });

        await waitFor(() => {
            expect(result.current.width).toBe(120);
            expect(result.current.height).toBe(220);
        });
    });

    it("should fallback to contentRect when contentBoxSize is not available", async () => {
        const div = document.createElement("div");
        const ref = { current: div };

        const { result } = renderHook(() => useResizeObserver({ ref }));

        await waitFor(() => {
            expect(callback).toBeDefined();
        });

        const mockEntry = {
            contentBoxSize: undefined,
            borderBoxSize: [],
            devicePixelContentBoxSize: [],
            contentRect: { width: 300, height: 400 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry], {} as ResizeObserver);
        });

        await waitFor(() => {
            expect(result.current.width).toBe(300);
            expect(result.current.height).toBe(400);
        });
    });

    it("should not update size when dimensions have not changed", async () => {
        const div = document.createElement("div");
        const ref = { current: div };

        const { result } = renderHook(() => useResizeObserver({ ref }));

        await waitFor(() => {
            expect(callback).toBeDefined();
        });

        const mockEntry1 = {
            contentBoxSize: [{ inlineSize: 100, blockSize: 200 }],
            borderBoxSize: [],
            devicePixelContentBoxSize: [],
            contentRect: { width: 100, height: 200 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry1], {} as ResizeObserver);
        });

        await waitFor(() => {
            expect(result.current.width).toBe(100);
            expect(result.current.height).toBe(200);
        });

        // Call again with same dimensions
        act(() => {
            callback([mockEntry1], {} as ResizeObserver);
        });

        // Should still be the same (no change detected)
        await waitFor(() => {
            expect(result.current.width).toBe(100);
            expect(result.current.height).toBe(200);
        });
    });

    it("should call onResize callback when provided", async () => {
        const div = document.createElement("div");
        const ref = { current: div };
        const onResize = vi.fn();

        renderHook(() => useResizeObserver({ ref, onResize }));

        await waitFor(() => {
            expect(callback).toBeDefined();
        });

        const mockEntry = {
            contentBoxSize: [{ inlineSize: 100, blockSize: 200 }],
            borderBoxSize: [],
            devicePixelContentBoxSize: [],
            contentRect: { width: 100, height: 200 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry], {} as ResizeObserver);
        });

        await waitFor(() => {
            expect(onResize).toHaveBeenCalledWith({ width: 100, height: 200 });
        });
    });

    it("should not call setSize when onResize callback is provided", () => {
        const div = document.createElement("div");
        const ref = { current: div };
        const onResize = vi.fn();

        const { result } = renderHook(() =>
            useResizeObserver({ ref, onResize }),
        );

        const mockEntry = {
            contentBoxSize: [{ inlineSize: 100, blockSize: 200 }],
            borderBoxSize: [],
            devicePixelContentBoxSize: [],
            contentRect: { width: 100, height: 200 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry], {} as ResizeObserver);
        });

        // Size should remain undefined since onResize is used instead
        expect(result.current.width).toBeUndefined();
        expect(result.current.height).toBeUndefined();
        expect(onResize).toHaveBeenCalledWith({ width: 100, height: 200 });
    });

    it("should disconnect observer on unmount", () => {
        const div = document.createElement("div");
        const ref = { current: div };

        const { unmount } = renderHook(() => useResizeObserver({ ref }));

        unmount();

        expect(disconnectSpy).toHaveBeenCalled();
    });

    it("should handle edge case with zero dimensions", async () => {
        const div = document.createElement("div");
        const ref = { current: div };

        const { result } = renderHook(() => useResizeObserver({ ref }));

        await waitFor(() => {
            expect(callback).toBeDefined();
        });

        const mockEntry = {
            contentBoxSize: [{ inlineSize: 0, blockSize: 0 }],
            borderBoxSize: [],
            devicePixelContentBoxSize: [],
            contentRect: { width: 0, height: 0 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry], {} as ResizeObserver);
        });

        await waitFor(() => {
            expect(result.current.width).toBe(0);
            expect(result.current.height).toBe(0);
        });
    });

    it("should handle undefined dimensions in contentBoxSize", async () => {
        const div = document.createElement("div");
        const ref = { current: div };

        const { result } = renderHook(() => useResizeObserver({ ref }));

        await waitFor(() => {
            expect(callback).toBeDefined();
        });

        const mockEntry = {
            contentBoxSize: undefined,
            borderBoxSize: undefined,
            devicePixelContentBoxSize: undefined,
            contentRect: { width: 100, height: 200 },
        } as unknown as ResizeObserverEntry;

        act(() => {
            callback([mockEntry], {} as ResizeObserver);
        });

        await waitFor(() => {
            expect(result.current.width).toBe(100);
            expect(result.current.height).toBe(200);
        });
    });
});
