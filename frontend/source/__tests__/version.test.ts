import { describe, it, expect } from "vitest";
import { version } from "../version";

describe("version", () => {
    it("should export a version string", () => {
        expect(version).toBeDefined();
        expect(typeof version).toBe("string");
        expect(version.length).toBeGreaterThan(0);
    });

    it("should match semantic version pattern", () => {
        // Version should match pattern like "1.0.33"
        const versionPattern = /^\d+\.\d+\.\d+$/;
        expect(version).toMatch(versionPattern);
    });
});

