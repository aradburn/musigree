// This file configures the test environment for act() calls
import { afterEach, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { d3Mock } from "./setup/d3-mock";

// Extend Window interface to include IS_REACT_ACT_ENVIRONMENT property
declare global {
    interface Window {
        IS_REACT_ACT_ENVIRONMENT: boolean;
    }
}

// Configure the test environment for act()
window.IS_REACT_ACT_ENVIRONMENT = true;

// React 19 act() and user-event wait on timers. A file that enables fake
// timers and does not restore them freezes later tests in this worker.
afterEach(() => {
    vi.useRealTimers();
});

// Global d3 mock
vi.mock("d3", () => ({
    default: d3Mock,
    ...d3Mock,
}));
