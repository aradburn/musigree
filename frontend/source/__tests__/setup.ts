// This file configures the test environment for act() calls
import { afterEach } from "vitest";
import { cleanup } from "@testing-library/react";
import "@testing-library/jest-dom";

// Extend Window interface to include IS_REACT_ACT_ENVIRONMENT property
declare global {
    interface Window {
        IS_REACT_ACT_ENVIRONMENT: boolean;
    }
}

// Automatically unmount React trees after each test
afterEach(() => {
    cleanup();
});

// Configure the test environment for act()
window.IS_REACT_ACT_ENVIRONMENT = true;
