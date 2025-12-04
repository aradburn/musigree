import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { RefObject } from "react";

// Debug flag - set to false to disable console logs
const DEBUG = false;

type Size = {
    width: number;
    height: number;
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
    const observedElementRef = useRef<T>(null);
    const windowResizeHandlerRef = useRef<(() => void) | null>(null);
    const lastTriggerRef = useRef<unknown>(undefined);
    const rafIdRef = useRef<number | null>(null);
    const [elementVersion, setElementVersion] = useState(0);
    const lastCheckedElementRef = useRef<T | null>(null);
    const retryCountRef = useRef<number>(0);

    // Lightweight check to detect element changes - runs synchronously after render
    // This is not CPU-intensive because it only updates state if there's an actual change
    // and uses a ref to prevent infinite loops
    useLayoutEffect(() => {
        const currentElement = ref.current;
        // Only update if element actually changed
        if (currentElement !== lastCheckedElementRef.current) {
            lastCheckedElementRef.current = currentElement;
            // Only trigger re-setup if element is different from what we're observing
            if (currentElement !== observedElementRef.current) {
                setElementVersion((prev) => prev + 1);
            }
        }
    }, [ref]);

    // Helper function to measure element size
    const measureElement = (element: T): Size => {
        const rect = element.getBoundingClientRect();
        let measuredWidth: number;
        let measuredHeight: number;

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
            );
        }

        // Clean up any pending RAF
        if (rafIdRef.current !== null) {
            cancelAnimationFrame(rafIdRef.current);
            rafIdRef.current = null;
        }

        const element = ref.current;
        const lastObserved = observedElementRef.current;

        // Check if element changed (became null or different element)
        // This must happen before cleanup runs, so we can detect the change
        const elementChanged = lastObserved && lastObserved !== element;

        // Check if trigger changed - update ref early so retry chains can see the change
        const triggerChanged = lastTriggerRef.current !== trigger;
        const previousTrigger = lastTriggerRef.current;
        lastTriggerRef.current = trigger;

        // Clean up when trigger is explicitly false (e.g., overlay is hidden)
        // Only clean up if trigger is explicitly false (not undefined)
        if (trigger === false && lastObserved) {
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Trigger is false, cleaning up observers",
                );
            }
            if (observerRef.current) {
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
            observedElementRef.current = null;
            // Reset retry count when overlay is hidden
            retryCountRef.current = 0;
            // Don't set up new observers when trigger is explicitly false
            return (): void => {
                if (rafIdRef.current !== null) {
                    cancelAnimationFrame(rafIdRef.current);
                    rafIdRef.current = null;
                }
            };
        }

        if (!element) {
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Element not available, cleaning up",
                );
            }
            // Clean up if element is no longer available or changed
            // Always clean up when element becomes null to prevent resource leaks
            if (lastObserved) {
                if (observerRef.current) {
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
            }
            observedElementRef.current = null;

            // Only retry when trigger is not explicitly false - element should be available soon
            // Retry multiple times with RAF to handle cases where element takes time to appear (e.g., Bootstrap animations)
            if (trigger !== false) {
                if (DEBUG) {
                    console.log(
                        "[useResizeObserver] Trigger allows retry but element not available, will retry after frame",
                        "retryCount:",
                        retryCountRef.current,
                    );
                }
                // Store the trigger value at the time we set up the retry
                // This helps us detect if trigger changed from false to true
                const triggerAtRetryTime = trigger;
                const previousTriggerAtRetryTime = lastTriggerRef.current;
                const maxRetries = 10; // Retry up to 10 times (about 160ms at 60fps)

                // Recursive helper function to retry finding the element
                // Use lastTriggerRef to check current trigger state (not captured closure value)
                const retryFindElement = (attempt: number): void => {
                    // Check if trigger became false (overlay was hidden) - stop retrying
                    // Use lastTriggerRef to get current trigger value, not the captured one
                    if (lastTriggerRef.current === false) {
                        retryCountRef.current = 0;
                        if (DEBUG) {
                            console.log(
                                "[useResizeObserver] Trigger is false, stopping retry chain",
                            );
                        }
                        return;
                    }

                    if (attempt > maxRetries) {
                        retryCountRef.current = 0;
                        if (DEBUG) {
                            console.log(
                                "[useResizeObserver] Max retries reached, element still not available",
                            );
                        }
                        return;
                    }

                    rafIdRef.current = requestAnimationFrame(() => {
                        // Check again if trigger became false during RAF wait
                        if (lastTriggerRef.current === false) {
                            rafIdRef.current = null;
                            retryCountRef.current = 0;
                            if (DEBUG) {
                                console.log(
                                    "[useResizeObserver] Trigger became false during RAF, stopping retry",
                                );
                            }
                            return;
                        }

                        rafIdRef.current = null;
                        const checkElement = ref.current;
                        if (DEBUG) {
                            console.log(
                                "[useResizeObserver] RAF retry attempt",
                                attempt,
                                "element:",
                                checkElement,
                                "observedElement:",
                                observedElementRef.current,
                            );
                        }

                        if (
                            checkElement &&
                            checkElement !== observedElementRef.current
                        ) {
                            if (DEBUG) {
                                console.log(
                                    "[useResizeObserver] Element became available after",
                                    attempt,
                                    "attempt(s)",
                                );
                            }
                            // Reset retry count on success
                            retryCountRef.current = 0;
                            // If trigger changed from false to true, measure immediately
                            // This ensures we get the size even if triggerChanged is false in next effect run
                            if (
                                triggerAtRetryTime !== false &&
                                previousTriggerAtRetryTime === false
                            ) {
                                if (DEBUG) {
                                    console.log(
                                        "[useResizeObserver] Trigger changed from false to true, " +
                                            "measuring in RAF callback",
                                    );
                                }
                                const measuredSize =
                                    measureElement(checkElement);
                                if (measuredSize) {
                                    if (DEBUG) {
                                        console.log(
                                            "[useResizeObserver] Measured size in RAF:",
                                            measuredSize,
                                        );
                                    }
                                    updateSize(measuredSize);
                                }
                            }
                            if (DEBUG) {
                                console.log(
                                    "[useResizeObserver] Triggering elementVersion update",
                                );
                            }
                            setElementVersion((prev) => prev + 1);
                        } else {
                            // Element still not available, retry again (if trigger is still valid)
                            if (lastTriggerRef.current === false) {
                                retryCountRef.current = 0;
                                if (DEBUG) {
                                    console.log(
                                        "[useResizeObserver] Trigger became false, stopping retry chain",
                                    );
                                }
                                return;
                            }
                            retryCountRef.current = attempt;
                            if (DEBUG) {
                                console.log(
                                    "[useResizeObserver] Element still not available, retrying (",
                                    attempt + 1,
                                    "/",
                                    maxRetries,
                                    ")",
                                );
                            }
                            retryFindElement(attempt + 1);
                        }
                    });
                };

                // Start retry chain
                retryFindElement(1);
            } else {
                // Reset retry count when trigger is false
                retryCountRef.current = 0;
            }

            // Return cleanup function to ensure pending RAFs are cancelled when overlay is hidden
            return (): void => {
                if (rafIdRef.current !== null) {
                    cancelAnimationFrame(rafIdRef.current);
                    rafIdRef.current = null;
                }
            };
        }

        if (DEBUG) {
            console.log(
                "[useResizeObserver] Element available:",
                element,
                "observedElement:",
                observedElementRef.current,
            );
        }

        // Trigger change was already checked and updated above
        if (DEBUG) {
            console.log(
                "[useResizeObserver] Trigger changed:",
                triggerChanged,
                "lastTrigger:",
                previousTrigger,
                "currentTrigger:",
                trigger,
            );
        }

        // Clean up previous observer if we're observing a different element
        // Do this first so we can then check if we need to set up a new observer
        if (elementChanged) {
            if (observerRef.current) {
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
            // Clear observed element so we can set up new observer
            observedElementRef.current = null;
        }

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
        // Only if trigger is not explicitly false (undefined or truthy)
        if (
            observedElementRef.current === element &&
            observerRef.current &&
            triggerChanged &&
            trigger !== false
        ) {
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Trigger changed to truthy, forcing re-measurement",
                );
            }
            // Schedule measurement after layout
            rafIdRef.current = requestAnimationFrame(() => {
                rafIdRef.current = null;
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
            return;
        }

        if (typeof window === "undefined") return;

        if (DEBUG) {
            console.log("[useResizeObserver] Setting up observer for element");
        }

        // Perform immediate measurement
        const immediateSize = measureElement(element);
        if (immediateSize) {
            updateSize(immediateSize);
        }

        // If trigger changed from false to truthy (e.g., overlay was hidden and is now shown),
        // force an additional measurement after layout to ensure accurate size
        // This handles cases where the element becomes available after animation completes
        if (triggerChanged && trigger !== false && previousTrigger === false) {
            if (DEBUG) {
                console.log(
                    "[useResizeObserver] Trigger changed from false to truthy, scheduling delayed re-measurement",
                );
            }
            // Use RAF to ensure measurement happens after layout is complete
            rafIdRef.current = requestAnimationFrame(() => {
                rafIdRef.current = null;
                if (DEBUG) {
                    console.log(
                        "[useResizeObserver] Delayed re-measurement executing after trigger change",
                    );
                }
                const measuredSize = measureElement(element);
                if (measuredSize) {
                    updateSize(measuredSize);
                }
            });
        }

        // Set up ResizeObserver if available
        if ("ResizeObserver" in window) {
            const observer = new ResizeObserver(([entry]) => {
                updateSizeFromEntry(entry);
            });

            observer.observe(element, { box });
            observerRef.current = observer;
            observedElementRef.current = element;
            // ResizeObserver will fire automatically, no need for additional RAF
        }

        // Set up window resize listener as backup (works alongside ResizeObserver)
        const handleWindowResize = (): void => {
            const measuredSize = measureElement(element);
            if (measuredSize) {
                updateSize(measuredSize);
            }
        };

        // We already checked window is defined above (line 375)
        window.addEventListener("resize", handleWindowResize);
        windowResizeHandlerRef.current = handleWindowResize;

        // Delayed measurement as fallback in case element wasn't fully laid out
        // This works alongside ResizeObserver to catch edge cases
        const timeoutId = setTimeout(() => {
            const measuredSize = measureElement(element);
            if (measuredSize) {
                updateSize(measuredSize);
            }
        }, 100);

        return (): void => {
            // Clear timeout if it was set (only when ResizeObserver is not available)
            if (timeoutId !== undefined) {
                clearTimeout(timeoutId);
            }
            // Cancel any pending RAFs
            if (rafIdRef.current !== null) {
                cancelAnimationFrame(rafIdRef.current);
                rafIdRef.current = null;
            }
            // Always disconnect and clean up when effect re-runs or unmounts
            // This handles both unmount and element change cases
            if (observerRef.current) {
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
            // Note: Don't set observedElementRef.current = null here because
            // we need it to detect element changes in the next effect run
        };
        // elementVersion tracks when ref.current changes to trigger re-setup
        // trigger forces re-measurement when it changes
        // Note: This effect also checks ref.current directly, so it will work even
        // if elementVersion doesn't update (e.g., when element is available on first render)
    }, [box, ref, trigger, elementVersion]);

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
): number {
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
