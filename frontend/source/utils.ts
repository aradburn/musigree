/**
 * Clamps a value between a minimum and maximum
 */
export const clamp = (value: number, min: number, max: number): number => {
    return Math.max(min, Math.min(max, value));
};

/**
 * Debounces a function call
 */
export const debounce = <T extends (...args: Parameters<T>) => void>(
    func: T,
    wait: number,
): ((...args: Parameters<T>) => void) => {
    let timeout: number | null = null;
    return (...args: Parameters<T>) => {
        if (timeout) window.clearTimeout(timeout);
        timeout = window.setTimeout(() => func(...args), wait);
    };
};
