import { describe, it, expect, vi, beforeEach } from "vitest";
import type { FSMInstance } from "../types";

// Create a mock implementation of MusigreeFSM
const mockMusigreeFSM = vi.fn().mockImplementation(() => ({
    state: "uninitialized",
    handle: vi.fn(),
    handleError: vi.fn(),
    showNetwork: vi.fn(),
    showRadial: vi.fn(),
    transition: vi.fn(),
    requestNetwork: vi.fn(),
    requestRelations: vi.fn(),
    requestEntity: vi.fn(),
    requestRandom: vi.fn(),
    selectEntity: vi.fn(),
    loadInlineData: vi.fn(),
    toggleRadial: vi.fn(),
    toggleNetwork: vi.fn(),
    toggleLoading: vi.fn(),
    toggleFilter: vi.fn(),
    pushState: vi.fn(),
    on: vi.fn(),
}));

// Mock the MusigreeFSM class
vi.mock("../MusigreeFSM", () => ({
    MusigreeFSM: mockMusigreeFSM,
}));

describe("FSM Module", () => {
    // Use let to allow reassignment in each test
    let fsmModule: { fsm: FSMInstance | undefined; initFSM: () => void };

    beforeEach(async () => {
        // Reset the mocks and module between tests
        vi.clearAllMocks();
        vi.resetModules();

        // Import the module freshly for each test
        fsmModule = await import("../index");
    });

    it("fsm should be undefined before initFSM is called", () => {
        // Check that fsm is undefined initially
        expect(fsmModule.fsm).toBeUndefined();
    });

    it("should create a MusigreeFSM when initFSM is called", () => {
        // Call initFSM
        fsmModule.initFSM();

        // Check that MusigreeFSM constructor was called
        expect(mockMusigreeFSM).toHaveBeenCalledTimes(1);
    });

    it("fsm should be defined after initFSM is called", () => {
        // Call initFSM
        fsmModule.initFSM();

        // Check that fsm is defined
        expect(fsmModule.fsm).toBeDefined();
    });

    it("fsm should implement the FSMInstance interface", () => {
        // Call initFSM
        fsmModule.initFSM();

        // Check fsm has all the required properties of FSMInstance
        const { fsm } = fsmModule;

        // State property
        expect(fsm).toHaveProperty("state");

        // Method properties with function checks
        const methodProps = [
            "handle",
            "handleError",
            "showNetwork",
            "showRadial",
            "transition",
            "requestNetwork",
            "requestRelations",
            "requestEntity",
            "requestRandom",
            "selectEntity",
            "loadInlineData",
            "toggleRadial",
            "toggleNetwork",
            "toggleLoading",
            "toggleFilter",
            "pushState",
            "on",
        ];

        methodProps.forEach((prop) => {
            expect(fsm).toHaveProperty(prop);
            expect(typeof fsm[prop as keyof FSMInstance]).toBe("function");
        });
    });
});
