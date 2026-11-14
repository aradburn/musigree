/**
 * Rolldown 1.3 turns Vite's `__VITE_PRELOAD__` marker into a unique identifier
 * by appending a hex hash. Vite 8.3 replaces only the `__VITE_PRELOAD__`
 * prefix, which leaves that hash glued to the replacement. The browser then
 * reports "identifier starts immediately after numeric literal".
 */
const ROLLODOWN_PRELOAD_HASH =
    /(__vite__mapDeps\(\[[0-9,]+\]\)|\[\])[0-9a-f]{32}(?![0-9a-f])/g;

export function stripRolldownPreloadMarker(code: string): string {
    return code.replace(ROLLODOWN_PRELOAD_HASH, "$1");
}
