import { vi } from "vitest";
import "@testing-library/jest-dom";

// Mock console.log to reduce noise during tests
vi.spyOn(console, "log").mockImplementation(() => {});

// Mock window methods used by D3 if needed
Object.defineProperty(window, "getComputedStyle", {
    value: (): { getPropertyValue: (prop: string) => string } => ({
        getPropertyValue: (_prop: string): string => "",
    }),
});
