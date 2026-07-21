// This file configures the test environment for act() calls
import { vi } from "vitest";
import "@testing-library/jest-dom";
import { d3Mock } from "./setup/d3-mock";

// Extend Window interface to include IS_REACT_ACT_ENVIRONMENT property
declare global {
    interface Window {
        IS_REACT_ACT_ENVIRONMENT: boolean;
    }
}

// Configure the test environment for act()
window.IS_REACT_ACT_ENVIRONMENT = true;

// Global d3 mock
vi.mock("d3", () => ({
    default: d3Mock,
    ...d3Mock,
}));
