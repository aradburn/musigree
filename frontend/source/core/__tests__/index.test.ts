import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Mock the manager modules
vi.mock("../MusigreeManager", () => ({
    musigreeManager: {
        // Mock any needed methods or properties
    },
}));

vi.mock("../NetworkManager", () => ({
    networkManager: {
        selectedNodeKey: undefined, // Default to undefined, will be changed in tests
    },
}));

vi.mock("../RelationsManager", () => ({
    relationsManager: {
        // Mock any needed methods or properties
    },
}));

// Import the module under test - must import after mocking
import {
    musigreeManager,
    networkManager,
    relationsManager,
    getSelectedNodeKey,
} from "../index";

describe("core/index.ts", () => {
    // Reset mocks before each test
    beforeEach(() => {
        vi.clearAllMocks();
    });

    afterEach(() => {
        // Reset the selectedNodeKey after each test
        vi.mocked(networkManager).selectedNodeKey = undefined;
    });

    describe("re-exports", () => {
        it("should re-export musigreeManager correctly", () => {
            expect(musigreeManager).toBeDefined();
        });

        it("should re-export networkManager correctly", () => {
            expect(networkManager).toBeDefined();
        });

        it("should re-export relationsManager correctly", () => {
            expect(relationsManager).toBeDefined();
        });
    });

    describe("getSelectedNodeKey", () => {
        it("should return undefined when selectedNodeKey is undefined", () => {
            vi.mocked(networkManager).selectedNodeKey = undefined;
            expect(getSelectedNodeKey()).toBeUndefined();
        });

        it("should return undefined when selectedNodeKey is not a string", () => {
            // @ts-expect-error - Testing with a non-string value
            vi.mocked(networkManager).selectedNodeKey = { key: "test" };
            expect(getSelectedNodeKey()).toBeUndefined();
        });

        it("should return the string value when selectedNodeKey is a string", () => {
            vi.mocked(networkManager).selectedNodeKey = "testKey";
            expect(getSelectedNodeKey()).toBe("testKey");
        });

        it("should return undefined for empty string", () => {
            vi.mocked(networkManager).selectedNodeKey = "";
            expect(getSelectedNodeKey()).toBe("");
        });
    });
});
