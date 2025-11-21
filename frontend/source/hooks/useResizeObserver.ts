import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";

// Debug flag - set to false to disable console logs
const DEBUG = false;

type Size = {
    width: number | undefined;
    height: number | undefined;
};

type UseResizeObserverOptions<T extends HTMLElement = HTMLElement> = {
    ref: RefObject<T>;
    onResize?: (size: Size) => void;
    box?: "border-box" | "content-box" | "device-pixel-content-box";
    trigger?: unknown; // Optional trigger to force re-measurement when changed
};

const initialSize: Size = {
    width: undefined,
    height: undefined,
};

export function useResizeObserver<T extends HTMLElement = HTMLElement>(
    options: UseResizeObserverOptions<T>,
): Size {
    const { ref, box = "content-box", trigger } = options;
    const [size, setSize] = useState<Size>(initialSize);
    const previousSize = useRef<Size>({ ...initialSize });
    const onResize = useRef<((size: Size) => void) | undefined>(undefined);
    onResize.current = options.onResize;
    const observerRef = useRef<ResizeObserver | null>(null);
    const observedElementRef = useRef<T | null>(null);
    const windowResizeHandlerRef = useRef<(() => void) | null>(null);
    // Track element availability to trigger effect re-run when element becomes available
    const [elementKey, setElementKey] = useState(0);
    const lastCheckedElementRef = useRef<T | null>(null);
    const lastTriggerRef = useRef<unknown>(undefined);

    // Poll for element availability - check on every render if element changed
    useEffect(() => {
        const checkElement = (): void => {
            const currentElement = ref.current;
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Polling effect running",
                    "currentElement:",
                    currentElement,
                    "lastChecked:",
                    lastCheckedElementRef.current,
                );
            }
            if (
                currentElement &&
                currentElement !== lastCheckedElementRef.current
            ) {
                if (DEBUG) {
                    console.log(
                        "[useResizeObserver] Element became available, incrementing elementKey",
                    );
                }
                lastCheckedElementRef.current = currentElement;
                setElementKey((prev) => prev + 1);
            } else if (!currentElement && lastCheckedElementRef.current) {
                if (DEBUG) {
                    console.log(
                        "[useResizeObserver] Element became unavailable, incrementing elementKey",
                    );
                }
                lastCheckedElementRef.current = null;
                setElementKey((prev) => prev + 1);
            }
        };

        // Check immediately
        checkElement();

        // Also check after a frame to catch elements that become available after render
        const rafId = requestAnimationFrame(() => {
            checkElement();
        });

        return (): void => cancelAnimationFrame(rafId);
    });

    // Helper function to measure element size
    const measureElement = (element: T): Size | null => {
        const rect = element.getBoundingClientRect();
        let measuredWidth: number | undefined;
        let measuredHeight: number | undefined;

        if (box === "border-box") {
            measuredWidth = rect.width;
            measuredHeight = rect.height;
        } else {
            // For content-box, we need to subtract padding and border
            const styles = window.getComputedStyle(element);
            const paddingTop = parseFloat(styles.paddingTop) || 0;
            const paddingBottom = parseFloat(styles.paddingBottom) || 0;
            const paddingLeft = parseFloat(styles.paddingLeft) || 0;
            const paddingRight = parseFloat(styles.paddingRight) || 0;
            const borderTop = parseFloat(styles.borderTopWidth) || 0;
            const borderBottom = parseFloat(styles.borderBottomWidth) || 0;
            const borderLeft = parseFloat(styles.borderLeftWidth) || 0;
            const borderRight = parseFloat(styles.borderRightWidth) || 0;

            measuredWidth =
                rect.width -
                paddingLeft -
                paddingRight -
                borderLeft -
                borderRight;
            measuredHeight =
                rect.height -
                paddingTop -
                paddingBottom -
                borderTop -
                borderBottom;
        }

        // Return null if dimensions are invalid
        if (
            (measuredWidth === undefined || measuredWidth <= 0) &&
            (measuredHeight === undefined || measuredHeight <= 0)
        ) {
            return null;
        }

        if (DEBUG) {
            console.log("measured width: ", measuredWidth);
            console.log("measured height: ", measuredHeight);
        }

        return {
            width: measuredWidth,
            height: measuredHeight,
        };
    };

    // Helper function to update size
    const updateSize = (newSize: Size): void => {
        // Check if size has changed
        // This handles the initial case: undefined !== number is true
        const hasChanged =
            previousSize.current.width !== newSize.width ||
            previousSize.current.height !== newSize.height;

        if (DEBUG) {
            console.log(
                "[useResizeObserver] updateSize called",
                "newSize:",
                newSize,
                "previousSize:",
                previousSize.current,
                "hasChanged:",
                hasChanged,
            );
        }

        if (hasChanged) {
            previousSize.current.width = newSize.width;
            previousSize.current.height = newSize.height;

            if (onResize.current) {
                if (DEBUG) {
                    console.log(
                        "[useResizeObserver] Calling onResize callback",
                        "width:",
                        newSize.width,
                        "height:",
                        newSize.height,
                    );
                }
                onResize.current(newSize);
            } else {
                if (DEBUG) {
                    console.log(
                        "[useResizeObserver] Updating state",
                        "width:",
                        newSize.width,
                        "height:",
                        newSize.height,
                    );
                }
                setSize(newSize);
            }
        } else {
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Size hasn't changed, skipping update",
                );
            }
        }
    };

    // Helper function to update size from ResizeObserver entry
    const updateSizeFromEntry = (entry: ResizeObserverEntry): void => {
        const boxProp =
            box === "border-box"
                ? "borderBoxSize"
                : box === "device-pixel-content-box"
                  ? "devicePixelContentBoxSize"
                  : "contentBoxSize";

        const newWidth = extractSize(entry, boxProp, "inlineSize");
        const newHeight = extractSize(entry, boxProp, "blockSize");

        updateSize({ width: newWidth, height: newHeight });
    };

    useEffect(() => {
        if (DEBUG) {
            console.log(
                "[useResizeObserver] Effect running",
                "element:",
                ref.current,
                "trigger:",
                trigger,
                "elementKey:",
                elementKey,
            );
        }
        const element = ref.current;
        if (!element) {
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Element not available, cleaning up",
                );
            }
            // Clean up if element is no longer available
            if (observerRef.current) {
                observerRef.current.disconnect();
                observerRef.current = null;
                observedElementRef.current = null;
            }
            if (windowResizeHandlerRef.current) {
                window.removeEventListener(
                    "resize",
                    windowResizeHandlerRef.current,
                );
                windowResizeHandlerRef.current = null;
            }

            // If trigger is truthy (e.g., show=true), the element should be available soon
            // Retry checking for the element after a short delay
            if (trigger) {
                if (DEBUG) {
                    console.log(
                        "[useResizeObserver] Trigger is truthy but element not available, will retry",
                    );
                }
                const retryTimeout = setTimeout(() => {
                    const retryElement = ref.current;
                    if (retryElement) {
                        if (DEBUG) {
                            console.log(
                                "[useResizeObserver] Element became available on retry, incrementing elementKey",
                            );
                        }
                        setElementKey((prev) => prev + 1);
                    }
                }, 50);

                return (): void => clearTimeout(retryTimeout);
            }

            return;
        }
        if (DEBUG) {
            console.log(
                "[useResizeObserver] Element available:",
                element,
                "observedElement:",
                observedElementRef.current,
            );
        }

        // Check if trigger changed - if so, force a re-measurement
        const triggerChanged = lastTriggerRef.current !== trigger;
        if (DEBUG) {
            console.log(
                "[useResizeObserver] Trigger changed:",
                triggerChanged,
                "lastTrigger:",
                lastTriggerRef.current,
                "currentTrigger:",
                trigger,
            );
        }
        lastTriggerRef.current = trigger;

        // If we're already observing this element and trigger hasn't changed, don't set up again
        if (
            observedElementRef.current === element &&
            observerRef.current &&
            !triggerChanged
        ) {
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Already observing same element, skipping setup",
                );
            }
            return;
        }

        // If trigger changed and we're already observing, force a measurement
        if (
            observedElementRef.current === element &&
            observerRef.current &&
            triggerChanged
        ) {
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Trigger changed, forcing re-measurement",
                );
            }
            // Force immediate measurement
            const immediateSize = measureElement(element);
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Immediate measurement result:",
                    immediateSize,
                );
            }
            if (immediateSize) {
                updateSize(immediateSize);
            }
            // Also schedule measurement after layout
            requestAnimationFrame(() => {
                if (DEBUG) {
                    console.log(
                        "[useResizeObserver] requestAnimationFrame callback executing",
                    );
                }
                const measuredSize = measureElement(element);
                if (measuredSize) {
                    updateSize(measuredSize);
                }
            });
            // Don't set up observer again, just return
            return;
        }

        // Clean up previous observer if we're observing a different element
        if (observerRef.current && observedElementRef.current !== element) {
            observerRef.current.disconnect();
            observerRef.current = null;
        }
        if (windowResizeHandlerRef.current) {
            window.removeEventListener(
                "resize",
                windowResizeHandlerRef.current,
            );
            windowResizeHandlerRef.current = null;
        }

        if (typeof window === "undefined") return;

        if (DEBUG) {
            console.log("[useResizeObserver] Setting up observer for element");
        }
        // Perform immediate measurement
        const immediateSize = measureElement(element);
        if (DEBUG) {
            console.log(
                "[useResizeObserver] Immediate measurement:",
                immediateSize,
            );
        }
        if (immediateSize) {
            updateSize(immediateSize);
        } else {
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Immediate measurement returned null",
                );
            }
        }

        // Set up ResizeObserver if available
        if ("ResizeObserver" in window) {
            const observer = new ResizeObserver(([entry]) => {
                updateSizeFromEntry(entry);
            });

            observer.observe(element, { box });
            observerRef.current = observer;
            observedElementRef.current = element;

            // Force an initial measurement via ResizeObserver by triggering a layout
            // Some browsers don't fire ResizeObserver immediately on observe()
            // Requesting animation frame ensures the element is laid out
            requestAnimationFrame(() => {
                const measuredSize = measureElement(element);
                if (measuredSize) {
                    updateSize(measuredSize);
                }
            });
        }

        // Set up window resize listener as backup
        const handleWindowResize = (): void => {
            const measuredSize = measureElement(element);
            if (measuredSize) {
                updateSize(measuredSize);
            }
        };

        window.addEventListener("resize", handleWindowResize);
        windowResizeHandlerRef.current = handleWindowResize;

        // Also check after a short delay in case element wasn't fully laid out
        const timeoutId = setTimeout(() => {
            const measuredSize = measureElement(element);
            if (measuredSize) {
                updateSize(measuredSize);
            }
        }, 100);

        return (): void => {
            clearTimeout(timeoutId);
            if (observerRef.current) {
                observerRef.current.disconnect();
                observerRef.current = null;
                observedElementRef.current = null;
            }
            if (windowResizeHandlerRef.current) {
                window.removeEventListener(
                    "resize",
                    windowResizeHandlerRef.current,
                );
                windowResizeHandlerRef.current = null;
            }
        };
        // elementKey is included to trigger re-run when element becomes available
        // trigger is included to force re-measurement when it changes
    }, [box, ref, elementKey, trigger]);

    return size;
}

type BoxSizesKey = keyof Pick<
    ResizeObserverEntry,
    "borderBoxSize" | "contentBoxSize" | "devicePixelContentBoxSize"
>;

function extractSize(
    entry: ResizeObserverEntry,
    box: BoxSizesKey,
    sizeType: keyof ResizeObserverSize,
): number | undefined {
    if (!entry[box]) {
        if (box === "contentBoxSize") {
            return entry.contentRect[
                sizeType === "inlineSize" ? "width" : "height"
            ];
        }
        return undefined;
    }

    // Handle different browser implementations of ResizeObserver
    if (Array.isArray(entry[box])) {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-return, @typescript-eslint/no-unsafe-member-access
        return entry[box][0][sizeType];
    } else {
        // Firefox implements a different structure
        return entry[box][sizeType] as number;
    }
}
