# React Performance & Best Practices – Implementation Plan

Phased plan to update the frontend against the **Vercel React Best Practices** skill. Tasks are ordered from critical to
optional. Reference: `.cursor/skills/vercel-react-best-practices/`.

---

## Overview

| Phase | Focus                                         | Impact         | Rule prefix             | Status  |
|-------|-----------------------------------------------|----------------|-------------------------|---------|
| 1     | Barrel imports, defer third-party             | CRITICAL       | `bundle-`               | Done    |
| 2     | Conditional render, localStorage, event dedup | MEDIUM–HIGH    | `rendering-`, `client-` | Done    |
| 3     | Dynamic imports, optional client tweaks       | MEDIUM         | `bundle-`, `client-`    | Done    |
| 4     | Hoist JSX, Activity, react-bootstrap, passive | LOW / optional | `rendering-`, `client-` | Partial |

---

## Phase 1: Critical (Bundle & Third-Party)

### 1.1 Replace barrel imports with direct imports

**Rule:** `bundle-barrel-imports` – Import from concrete modules to improve tree-shaking and build/load time.

#### Component barrels

- [x] **Header → Search**
    - **File:** `frontend/source/components/Layout/Header.tsx`
    - **Current:** `import { SearchInput } from "../Search";`
    - **Action:** Change to `import SearchInput from "../Search/SearchInput";` (or the actual default/named export).
    - **Note:** If `Search/index.ts` is kept as a public API, document that decision; otherwise prefer this direct
      import.

- [x] **App → Visualization**
    - **File:** `frontend/source/components/App.tsx`
    - **Current:** `import { LoadingAnimation } from "./Visualization";`
    - **Action:** Change to `import LoadingAnimation from "./Visualization/LoadingAnimation";` (or the actual export).

#### Core barrel

- [x] **print.ts**
    - **File:** `frontend/source/print.ts`
    - **Current:** `import { musigreeManager, networkManager } from "./core";`
    - **Action:** `import { musigreeManager, networkManager } from "./core/singletons";`

- [x] **WindowContext.tsx**
    - **File:** `frontend/source/contexts/WindowContext.tsx`
    - **Current:** `import { musigreeManager } from "../core";`
    - **Action:** `import { musigreeManager } from "../core/singletons";`

- [x] **svg.ts**
    - **File:** `frontend/source/svg.ts`
    - **Current:** `import { musigreeManager } from "./core/index";`
    - **Action:** `import { musigreeManager } from "./core/singletons";`

- [x] **All other files importing from `"../core"` or `"./core"`**
    - **Action:** Grep for `from ["'].*\/core["']` and replace with `from "./core/singletons"` or direct module (e.g.
      `MusigreeManager` from `./core/MusigreeManager`) as appropriate.
    - **Files updated:** `NetworkView.tsx`, `SidebarLeft.tsx`, `LoadingAnimation.tsx`, `relations.ts`, `print.test.ts`,
      `WindowContext.test.tsx`, `svg.test.ts`, `Sidebar.test.tsx`, `relations.test.ts`; test mocks updated to
      `core/singletons`.

**Verification:** Run `frontend` build and tests; confirm no broken imports.

---

### 1.2 Defer analytics (load after hydration / first interaction)

**Rule:** `bundle-defer-third-party` – Analytics should not block initial bundle or first paint.

- [x] **Defer analytics module usage**
    - **File:** `frontend/source/fsm/MusigreeFSM.ts`
    - **Current:** Top-level `import { track } from "../analytics";` and synchronous `track(...)` calls.
    - **Implemented (Option A):** Removed top-level analytics import; added `getTrack()` that dynamic-imports
      `../analytics` on first use and caches the promise. Call site:
      `getTrack().then((track) => track("network", { key: networkData.center.key }));`. Analytics chunk now loads on
      first track call.

- [x] **Tests**
    - **File:** `frontend/source/fsm/__tests__/MusigreeFSM.spec.ts`
    - **Action:** Ensure analytics mock still applies; adjust if `track` is now called asynchronously or via a lazy
      wrapper. (Existing `vi.mock("../../analytics")` applies to dynamic import; no test change needed.)

**Verification:** Confirm analytics still fires; measure or inspect that the analytics chunk loads after main app (e.g.
via Network tab or bundle analyzer).

---

## Phase 2: Medium–High (Rendering, Storage, Events)

### 2.1 Conditional rendering: use ternary (or null) instead of `&&`

**Rule:** `rendering-conditional-render` – Avoid rendering `0` or `NaN` when using `condition && <JSX>`.

#### SearchInput.tsx

- [x] **File:** `frontend/source/components/Search/SearchInput.tsx`
    - **~165:** `{query && (...)}` → `{query ? (...) : null}` (or keep `&&` only if `query` is always string; if it can
      be numeric, use ternary).
    - **~192:** `{loading && (...)}` → `{loading ? (...) : null}`.
    - **~207:** `{error && (...)}` → `{error ? (...) : null}`.
    - **~216:** `{query.length >= TYPEAHEAD.MIN_QUERY_LENGTH && (...)}` → use ternary for the block.
    - **~222:** `{!loading && !error && results.length > 0 && (...)}` → use ternary (e.g.
      `!loading && !error && results.length > 0 ? (...) : null`).

#### RolesOverlay.tsx

- [x] **File:** `frontend/source/components/Overlays/RolesOverlay.tsx`
    - **~355:** `{containerHeight !== undefined && (...)}` → `{containerHeight !== undefined ? (...) : null}`.
    - **~442:** `{arboristData.length === 0 && show && (...)}` → use explicit ternary so no falsy value is rendered.

**Verification:** Run frontend tests and manually check search and overlay UI (empty states, loading, errors).

---

### 2.2 localStorage: version key and wrap in try/catch

**Rule:** `client-localstorage-schema` – Version keys and minimize stored data; handle private browsing and quota.

- [x] **App.tsx**
    - **File:** `frontend/source/components/App.tsx`
    - **Implemented:** Added `HAS_VISITED_BEFORE_KEY = "hasVisitedBefore:v1"`; wrapped `getItem`/`setItem` in try/catch;
      on catch treat as first visit or ignore (no throw). Minimal flag only.

- [x] **Tests**
    - **File:** `frontend/source/components/__tests__/App.test.tsx`
    - **Implemented:** Mock and assertions use `"hasVisitedBefore:v1"`; added tests "handles localStorage getItem
      throwing" and "handles localStorage setItem throwing" to cover try/catch.

**Verification:** First-time and return-visitor behavior unchanged; test in a private window to confirm no uncaught
exceptions.

---

### 2.3 Deduplicate global `resize` listeners

**Rule:** `client-event-listeners` – Prefer a single global listener shared by multiple concerns.

- [x] **Single resize handler**
    - **Current:** `WindowContext` registers `window.addEventListener("resize", handleResize)`; `AppContent` in
      `App.tsx` registers `window.addEventListener("resize", updateNavbarHeightVar)`.
    - **Action:** Consolidate so one place owns the `resize` listener and updates both:
        - Window dimensions (existing `WindowContext` logic), and
        - Navbar height CSS variable (existing `updateNavbarHeightVar` in App).
    - **Options:**
        - **A:** Move `updateNavbarHeightVar` into `WindowContext` and call it from the same debounced resize handler;
          remove the second effect from `App.tsx`.
        - **B:** Small shared module that registers one `resize` listener and runs a list of callbacks (e.g. from
          WindowContext and App); both register their callbacks there.
    - **Implemented (Option A):** `updateNavbarHeightVar` moved to `WindowContext.tsx`; called from the same debounced
      `handleResize` and on mount. Second resize effect removed from `App.tsx`.

- [x] **Tests**
    - **Files:** `frontend/source/contexts/__tests__/WindowContext.test.tsx`,
      `frontend/source/components/__tests__/App.test.tsx`, and any tests that mock `window.addEventListener`.
    - **Action:** Update expectations so only one `resize` listener is registered; assert both behaviors (dimensions +
      navbar height) still run. (WindowContext tests: single `addEventListener("resize")` call; new tests for
      `--navbar-height` on mount and in `handleResize`.)

**Verification:** Resize window; confirm layout and navbar height update; confirm only one `resize` listener in
devtools.

---

## Phase 3: Medium (Dynamic Imports & Optional Client)

### 3.1 Dynamic import for heavy below-the-fold or conditional UI

**Rule:** `bundle-dynamic-imports` – Use `React.lazy` (and Suspense) for heavy components that are not needed for first
paint.

- [x] **RolesOverlay**
    - **File:** `frontend/source/components/App.tsx` (and possibly
      `frontend/source/components/Overlays/RolesOverlay.tsx`).
    - **Current:** Static import of `RolesOverlay`.
    - **Action:**
      `const RolesOverlay = React.lazy(() => import("./Overlays/RolesOverlay").then(m => ({ default: m.RolesOverlay })));` (
      or default export). Wrap usage in `<Suspense fallback={null}>` (or a minimal placeholder) so the overlay loads
      when first shown.
    - **Implemented:** Lazy + Suspense; rendered only when `showRolesOverlay` is true so the chunk loads on first open.

- [x] **HelpModal**
    - **File:** `frontend/source/components/App.tsx`.
    - **Current:** Static import of `HelpModal`.
    - **Action:** Same pattern: `React.lazy(() => import("./Modals/HelpModal")...)` and wrap in `<Suspense>`.
    - **Implemented:** Lazy + Suspense; rendered only when `showHelpModal` is true.

- [ ] **Optional: NetworkView / LoadingAnimation**
    - **Action:** Only consider if bundle analysis shows meaningful gain; they are central to the main view and may be
      needed immediately. If deferred, use `React.lazy` and a clear loading UX.

**Verification:** Build and check chunk splitting; confirm overlays/modals still work and show correct fallback while
loading.

---

### 3.2 Optional: Passive event listeners for touch/wheel

**Rule:** `client-passive-event-listeners` – Use `{ passive: true }` for touch/wheel when not calling
`preventDefault()`.

- [x] **Audit**
    - **Action:** If any new `addEventListener("touchstart"|"touchend"|"wheel", ...)` are added in React code (not D3),
      pass `{ passive: true }` unless the handler must call `preventDefault()`.
    - **Note:** Current code uses `resize` and `mousedown`; no change required for existing listeners. Document this
      rule for future touch/wheel listeners. D3 touch handlers remain on D3's `.on` API (not native `addEventListener`).

---

## Phase 4: Optional (Low-Impact Polish)

### 4.1 Hoist static JSX where beneficial

**Rule:** `rendering-hoist-jsx` – Extract static JSX to module scope to avoid re-creating on every render.

- [ ] **Audit**
    - **Files:** Loading placeholders, static SVG wrappers, simple repeated structures (e.g. in `LoadingAnimation`,
      `NetworkView`, or shared layout).
    - **Action:** Identify components that always render the same static JSX (e.g. a single `<div className="...">` or a
      fixed SVG). Move that JSX to a constant outside the component and reference it in the return. Skip if React
      Compiler is (or will be) enabled.

---

### 4.2 Use React `Activity` for frequently toggled overlays

**Rule:** `rendering-activity` – Use `<Activity mode={visible ? 'visible' : 'hidden'>` to preserve state/DOM when
toggling visibility.

- [ ] **RolesOverlay**
    - **File:** `frontend/source/components/Overlays/RolesOverlay.tsx` (or parent that conditionally renders it).
    - **Action:** If the overlay is toggled often and internal state (e.g. tree expansion) should persist, wrap content
      in `<Activity mode={show ? 'visible' : 'hidden'>` (React 19 API). Confirm API name/import in current React
      version.
    - **Deferred:** Lazy-load currently unmounts when closed; Activity can be revisited if tree expansion persistence
      becomes important.

- [ ] **HelpModal**
    - **File:** `frontend/source/components/App.tsx` or `frontend/source/components/Modals/HelpModal.tsx`.
    - **Action:** Same consideration for modal content if toggling visibility frequently and state should be preserved.

**Verification:** Toggle overlays/modals; confirm no regressions and that state is preserved when applicable.

---

### 4.3 react-bootstrap: prefer direct imports

**Rule:** Same principle as `bundle-barrel-imports` – Reduce cost of barrel imports from libraries.

- [x] **Replace barrel imports**
    - **Files:** `HelpModal.tsx` (`Modal`, `Button`), `SearchInput.tsx` (`Form`, `Spinner`, `Overlay`, `Popover`),
      `Header.tsx` (`Navbar`, `Container`, `OverlayTrigger`, `Tooltip`), `App.tsx` (`Container`, `Row`),
      `ForceControls.tsx` (`Form`).
    - **Current:** `import { X, Y } from "react-bootstrap";`
    - **Action:** Switch to `import X from "react-bootstrap/X";` (or the path react-bootstrap documents). `RolesOverlay`
      already uses `import Offcanvas from "react-bootstrap/Offcanvas";` – use that style elsewhere.
    - **Implemented:** All listed files now use direct `react-bootstrap/X` imports.

**Verification:** Build size and tests; confirm no visual or behavioral regressions.

---

## Additional high-impact fixes (post Phase 2 audit)

- [x] **Memoize WindowContext / LoadingContext provider values** – stable `useMemo` context objects; WindowContext uses
  `useCallback`/`useMemo` for resize handler and syncs `stateRef` during render.
- [x] **Set lookups in `network/pruning.ts`** – replace hot-path `.includes` with `Set.has`.
- [x] **AbortController in `useSearchApi`** – abort in-flight fetch on query change/unmount to avoid stale results.
- [x] **`useResizeObserver`** – only register `window` resize fallback when `ResizeObserver` is unavailable.
- [x] **App `musigreeManager` import** – use `@/core/singletons` instead of `@/core` barrel.

---

## Verification Checklist (All Phases)

- [x] `npm run build` (frontend) succeeds.
- [x] `npm run test` (frontend unit/integration) passes (affected suites verified).
- [x] `npm run lint` and `npm run check-types` pass.
- [x] Manual smoke: load app, resize, search, open/close overlays and modals, confirm analytics still fires.
- [ ] Optional: run bundle analyzer and compare before/after for Phase 1 and Phase 3.

---

## References

- Skill: `.cursor/skills/vercel-react-best-practices/SKILL.md`
- Rules: `.cursor/skills/vercel-react-best-practices/rules/*.md`
- Full rule list: `.cursor/skills/vercel-react-best-practices/AGENTS.md`
- Source of this plan: Vercel React Best Practices skill audit (no implementation changes applied at audit time).
