import { useEffect, useRef, useState } from "react";
import type { RefObject } from "react";

type Size = {
    width: number | undefined;
    height: number | undefined;
};

type UseResizeObserverOptions<T extends HTMLElement = HTMLElement> = {
    ref: RefObject<T>;
    onResize?: (size: Size) => void;
    box?: "border-box" | "content-box" | "device-pixel-content-box";
};

const initialSize: Size = {
    width: undefined,
    height: undefined,
};

export function useResizeObserver<T extends HTMLElement = HTMLElement>(
    options: UseResizeObserverOptions<T>,
): Size {
    const { ref, box = "content-box" } = options;
    const [size, setSize] = useState<Size>(initialSize);
    const previousSize = useRef<Size>({ ...initialSize });
    const onResize = useRef<((size: Size) => void) | undefined>(undefined);
    onResize.current = options.onResize;

    useEffect(() => {
        if (!ref.current) return;

        if (typeof window === "undefined" || !("ResizeObserver" in window))
            return;

        const observer = new ResizeObserver(([entry]) => {
            const boxProp =
                box === "border-box"
                    ? "borderBoxSize"
                    : box === "device-pixel-content-box"
                      ? "devicePixelContentBoxSize"
                      : "contentBoxSize";

            const newWidth = extractSize(entry, boxProp, "inlineSize");
            const newHeight = extractSize(entry, boxProp, "blockSize");

            const hasChanged =
                previousSize.current.width !== newWidth ||
                previousSize.current.height !== newHeight;

            if (hasChanged) {
                const newSize: Size = { width: newWidth, height: newHeight };
                previousSize.current.width = newWidth;
                previousSize.current.height = newHeight;

                if (onResize.current) {
                    onResize.current(newSize);
                } else {
                    setSize(newSize);
                }
            }
        });

        observer.observe(ref.current, { box });

        return (): void => {
            observer.disconnect();
        };
    }, [box, ref]);

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
