import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// Store references to created instances for testing
declare global {
    var __createdInstances: {
        MusigreeManager?: any;
        NetworkManager?: any;
        RelationsManager?: any;
    };
    var __musigreeConstructorSpies: {
        MusigreeManager?: ReturnType<typeof vi.fn>;
        NetworkManager?: ReturnType<typeof vi.fn>;
        RelationsManager?: ReturnType<typeof vi.fn>;
    };
}

vi.mock("../MusigreeManager", () => {
    const spy = vi.fn().mockImplementation(function MockMusigreeManager(
        this: any,
    ) {
        const instance = {
            dispose: vi.fn(),
            someMethod: vi.fn().mockReturnValue("musigree-result"),
            someProperty: "musigree-property",
        };
        Object.assign(this, instance);
        if (!globalThis.__createdInstances) {
            globalThis.__createdInstances = {};
        }
        globalThis.__createdInstances.MusigreeManager = this;
        return this;
    });
    // Make it work with 'new'
    Object.setPrototypeOf(spy.prototype, Object.prototype);
    if (!globalThis.__musigreeConstructorSpies) {
        globalThis.__musigreeConstructorSpies = {};
    }
    globalThis.__musigreeConstructorSpies.MusigreeManager = spy;
    return {
        MusigreeManager: spy,
    };
});

vi.mock("../NetworkManager", () => {
    const spy = vi.fn().mockImplementation(function MockNetworkManager(
        this: any,
    ) {
        const instance = {
            dispose: vi.fn(),
            someMethod: vi.fn().mockReturnValue("network-result"),
            someProperty: "network-property",
        };
        Object.assign(this, instance);
        if (!globalThis.__createdInstances) {
            globalThis.__createdInstances = {};
        }
        globalThis.__createdInstances.NetworkManager = this;
        return this;
    });
    Object.setPrototypeOf(spy.prototype, Object.prototype);
    if (!globalThis.__musigreeConstructorSpies) {
        globalThis.__musigreeConstructorSpies = {};
    }
    globalThis.__musigreeConstructorSpies.NetworkManager = spy;
    return {
        NetworkManager: spy,
    };
});

vi.mock("../RelationsManager", () => {
    const spy = vi.fn().mockImplementation(function MockRelationsManager(
        this: any,
    ) {
        const instance = {
            dispose: vi.fn(),
            someMethod: vi.fn().mockReturnValue("relations-result"),
            someProperty: "relations-property",
        };
        Object.assign(this, instance);
        if (!globalThis.__createdInstances) {
            globalThis.__createdInstances = {};
        }
        globalThis.__createdInstances.RelationsManager = this;
        return this;
    });
    Object.setPrototypeOf(spy.prototype, Object.prototype);
    if (!globalThis.__musigreeConstructorSpies) {
        globalThis.__musigreeConstructorSpies = {};
    }
    globalThis.__musigreeConstructorSpies.RelationsManager = spy;
    return {
        RelationsManager: spy,
    };
});

// Import the module under test after mocking
import {
    musigreeManager,
    networkManager,
    relationsManager,
    resetSingletons,
} from "../singletons";

// Get references to the mocked constructors
import { MusigreeManager } from "../MusigreeManager";
import { NetworkManager } from "../NetworkManager";
import { RelationsManager } from "../RelationsManager";

// Helper to get constructor spies after imports
const getMusigreeManagerConstructor = () =>
    globalThis.__musigreeConstructorSpies?.MusigreeManager!;
const getNetworkManagerConstructor = () =>
    globalThis.__musigreeConstructorSpies?.NetworkManager!;
const getRelationsManagerConstructor = () =>
    globalThis.__musigreeConstructorSpies?.RelationsManager!;

// Type assertions for test properties
const testMusigreeManager = musigreeManager as any;
const testNetworkManager = networkManager as any;
const testRelationsManager = relationsManager as any;

describe("singletons.ts", () => {
    beforeEach(() => {
        // Reset singletons to ensure clean state
        resetSingletons();
    });

    afterEach(() => {
        // Clean up after each test
        resetSingletons();
    });

    describe("createLazyProxy", () => {
        it("should create a proxy that lazily initializes the instance", () => {
            // Access a property to trigger lazy initialization
            const result = testMusigreeManager.someMethod();

            expect(result).toBe("musigree-result");
            expect(
                globalThis.__createdInstances?.MusigreeManager?.someMethod,
            ).toHaveBeenCalled();
        });

        it("should reuse the same instance on subsequent accesses", () => {
            // First access
            const result1 = testMusigreeManager.someProperty;
            // Second access
            const result2 = testMusigreeManager.someProperty;

            expect(result1).toBe("musigree-property");
            expect(result2).toBe("musigree-property");
            // Should only create one instance
            expect(getMusigreeManagerConstructor()).toHaveBeenCalledTimes(1);
        });

        it("should properly bind methods to the instance", () => {
            const boundMethod = testMusigreeManager.someMethod;

            expect(typeof boundMethod).toBe("function");
            expect(boundMethod()).toBe("musigree-result");
            expect(
                globalThis.__createdInstances?.MusigreeManager?.someMethod,
            ).toHaveBeenCalled();
        });

        it("should handle property access through proxy", () => {
            const property = testMusigreeManager.someProperty;

            expect(property).toBe("musigree-property");
        });

        it("should handle property setting through proxy", () => {
            testMusigreeManager.someProperty = "new-value";

            expect(
                globalThis.__createdInstances?.MusigreeManager?.someProperty,
            ).toBe("new-value");
        });

        it("should handle 'in' operator through proxy", () => {
            const hasProperty = "someProperty" in testMusigreeManager;

            expect(hasProperty).toBe(true);
        });

        it("should handle Object.keys() through proxy", () => {
            const keys = Object.keys(testMusigreeManager);

            expect(Array.isArray(keys)).toBe(true);
        });

        it("should handle Object.getOwnPropertyDescriptor through proxy", () => {
            const descriptor = Object.getOwnPropertyDescriptor(
                testMusigreeManager,
                "someProperty",
            );

            expect(descriptor).toBeDefined();
        });

        it("should handle symbol properties", () => {
            const symbol = Symbol("test");
            testMusigreeManager[symbol] = "symbol-value";

            expect(testMusigreeManager[symbol]).toBe("symbol-value");
        });
    });

    describe("musigreeManager singleton", () => {
        it("should create MusigreeManager instance on first access", () => {
            // Access the manager to trigger initialization
            testMusigreeManager.someProperty;

            expect(getMusigreeManagerConstructor()).toHaveBeenCalledTimes(1);
        });

        it("should reuse the same MusigreeManager instance", () => {
            // Multiple accesses
            testMusigreeManager.someProperty;
            testMusigreeManager.someMethod();
            testMusigreeManager.someProperty;

            expect(getMusigreeManagerConstructor()).toHaveBeenCalledTimes(1);
        });
    });

    describe("networkManager singleton", () => {
        it("should create NetworkManager instance on first access", () => {
            // Access the manager to trigger initialization
            testNetworkManager.someProperty;

            expect(getNetworkManagerConstructor()).toHaveBeenCalledTimes(1);
        });

        it("should reuse the same NetworkManager instance", () => {
            // Multiple accesses
            testNetworkManager.someProperty;
            testNetworkManager.someMethod();
            testNetworkManager.someProperty;

            expect(getNetworkManagerConstructor()).toHaveBeenCalledTimes(1);
        });

        it("should handle method calls correctly", () => {
            const result = testNetworkManager.someMethod();

            expect(result).toBe("network-result");
            expect(
                globalThis.__createdInstances?.NetworkManager?.someMethod,
            ).toHaveBeenCalled();
        });
    });

    describe("relationsManager singleton", () => {
        it("should create RelationsManager instance on first access", () => {
            // Access the manager to trigger initialization
            testRelationsManager.someProperty;

            expect(getRelationsManagerConstructor()).toHaveBeenCalledTimes(1);
        });

        it("should reuse the same RelationsManager instance", () => {
            // Multiple accesses
            testRelationsManager.someProperty;
            testRelationsManager.someMethod();
            testRelationsManager.someProperty;

            expect(getRelationsManagerConstructor()).toHaveBeenCalledTimes(1);
        });

        it("should handle method calls correctly", () => {
            const result = testRelationsManager.someMethod();

            expect(result).toBe("relations-result");
            expect(
                globalThis.__createdInstances?.RelationsManager?.someMethod,
            ).toHaveBeenCalled();
        });
    });

    describe("resetSingletons", () => {
        it("should reset all singleton instances to null", () => {
            // Reset mock properties to original values
            if (globalThis.__createdInstances?.MusigreeManager) {
                globalThis.__createdInstances.MusigreeManager.someProperty =
                    "musigree-property";
            }
            if (globalThis.__createdInstances?.NetworkManager) {
                globalThis.__createdInstances.NetworkManager.someProperty =
                    "network-property";
            }
            if (globalThis.__createdInstances?.RelationsManager) {
                globalThis.__createdInstances.RelationsManager.someProperty =
                    "relations-property";
            }

            // Initialize all managers
            testMusigreeManager.someProperty;
            testNetworkManager.someProperty;
            testRelationsManager.someProperty;

            // Reset singletons
            resetSingletons();

            // Access managers again - should create new instances
            testMusigreeManager.someProperty;
            testNetworkManager.someProperty;
            testRelationsManager.someProperty;

            // Verify that the managers are accessible (this confirms they were recreated)
            expect(testMusigreeManager.someProperty).toBe("musigree-property");
            expect(testNetworkManager.someProperty).toBe("network-property");
            expect(testRelationsManager.someProperty).toBe(
                "relations-property",
            );
        });

        it("should call dispose method on NetworkManager if it exists", () => {
            // Initialize network manager by accessing it - this sets _networkManager
            testNetworkManager.someProperty;

            // Reset singletons - this should call dispose on _networkManager
            resetSingletons();

            expect(
                globalThis.__createdInstances?.NetworkManager?.dispose,
            ).toHaveBeenCalledTimes(1);
        });

        it("should call dispose method on RelationsManager if it exists", () => {
            // Initialize relations manager by accessing it - this sets _relationsManager
            testRelationsManager.someProperty;

            // Reset singletons - this should call dispose on _relationsManager
            resetSingletons();

            expect(
                globalThis.__createdInstances?.RelationsManager?.dispose,
            ).toHaveBeenCalledTimes(1);
        });

        it("should not call dispose on MusigreeManager (no dispose method)", () => {
            // Initialize musigree manager
            testMusigreeManager.someProperty;

            // Clear any previous dispose calls
            const musigreeInstance =
                globalThis.__createdInstances?.MusigreeManager;
            if (musigreeInstance?.dispose) {
                musigreeInstance.dispose.mockClear();
            }

            // Reset singletons
            resetSingletons();

            // MusigreeManager's dispose should not be called during reset
            // since resetSingletons only calls dispose on NetworkManager and RelationsManager
            expect(musigreeInstance?.dispose).not.toHaveBeenCalled();
        });

        it("should handle reset when managers are not initialized", () => {
            // Reset without initializing any managers
            expect(() => resetSingletons()).not.toThrow();
        });

        it("should handle reset when dispose methods don't exist", () => {
            // Create managers without dispose methods
            const mockManagerWithoutDispose = {
                someMethod: vi.fn(),
                someProperty: "test",
            } as any;

            getNetworkManagerConstructor().mockImplementationOnce(
                () => mockManagerWithoutDispose,
            );

            // Initialize and reset
            testNetworkManager.someProperty;
            expect(() => resetSingletons()).not.toThrow();
        });
    });

    describe("edge cases and error scenarios", () => {
        it("should handle undefined property access", () => {
            const result = testMusigreeManager.nonExistentProperty;

            expect(result).toBeUndefined();
        });

        it("should handle setting undefined properties", () => {
            testMusigreeManager.newProperty = "new-value";

            expect(testMusigreeManager.newProperty).toBe("new-value");
        });

        it("should handle function properties correctly", () => {
            const testFunction = vi.fn().mockReturnValue("test-result");
            testMusigreeManager.testFunction = testFunction;

            const result = testMusigreeManager.testFunction();

            expect(result).toBe("test-result");
            expect(testFunction).toHaveBeenCalled();
        });

        it("should handle non-function values correctly", () => {
            const nonFunctionValue = { nested: "object" };
            testMusigreeManager.nonFunction = nonFunctionValue;

            expect(testMusigreeManager.nonFunction).toBe(nonFunctionValue);
        });

        it("should handle multiple proxy operations in sequence", () => {
            // Test a sequence of operations
            testMusigreeManager.prop1 = "value1";
            testMusigreeManager.prop2 = "value2";
            const hasProp1 = "prop1" in testMusigreeManager;
            const keys = Object.keys(testMusigreeManager);
            const descriptor = Object.getOwnPropertyDescriptor(
                testMusigreeManager,
                "prop1",
            );

            expect(testMusigreeManager.prop1).toBe("value1");
            expect(testMusigreeManager.prop2).toBe("value2");
            expect(hasProp1).toBe(true);
            expect(Array.isArray(keys)).toBe(true);
            expect(descriptor).toBeDefined();
        });

        it("should maintain separate instances for different managers", () => {
            // Get current call counts
            const musigreeCallsBefore =
                globalThis.__createdInstances?.MusigreeManager?.someMethod?.mock
                    .calls.length;
            const networkCallsBefore =
                globalThis.__createdInstances?.NetworkManager?.someMethod?.mock
                    .calls.length;
            const relationsCallsBefore =
                globalThis.__createdInstances?.RelationsManager?.someMethod
                    ?.mock.calls.length;

            const musigreeResult = testMusigreeManager.someMethod();
            const networkResult = testNetworkManager.someMethod();
            const relationsResult = testRelationsManager.someMethod();

            expect(musigreeResult).toBe("musigree-result");
            expect(networkResult).toBe("network-result");
            expect(relationsResult).toBe("relations-result");

            // Each should have been called once more
            expect(
                globalThis.__createdInstances?.MusigreeManager?.someMethod,
            ).toHaveBeenCalledTimes(musigreeCallsBefore + 1);
            expect(
                globalThis.__createdInstances?.NetworkManager?.someMethod,
            ).toHaveBeenCalledTimes(networkCallsBefore + 1);
            expect(
                globalThis.__createdInstances?.RelationsManager?.someMethod,
            ).toHaveBeenCalledTimes(relationsCallsBefore + 1);
        });
    });

    describe("proxy trap coverage", () => {
        it("should handle get trap with function binding", () => {
            const boundMethod = testMusigreeManager.someMethod;
            const result = boundMethod();

            expect(typeof boundMethod).toBe("function");
            expect(result).toBe("musigree-result");
        });

        it("should handle get trap with non-function values", () => {
            // Reset the mock to ensure clean state
            if (globalThis.__createdInstances?.MusigreeManager) {
                globalThis.__createdInstances.MusigreeManager.someProperty =
                    "musigree-property";
            }
            const property = testMusigreeManager.someProperty;

            expect(property).toBe("musigree-property");
        });

        it("should handle set trap", () => {
            testMusigreeManager.testProperty = "test-value";

            expect(testMusigreeManager.testProperty).toBe("test-value");
        });

        it("should handle has trap", () => {
            const hasProperty = "someProperty" in testMusigreeManager;
            const hasNonExistent = "nonExistent" in testMusigreeManager;

            expect(hasProperty).toBe(true);
            expect(hasNonExistent).toBe(false);
        });

        it("should handle ownKeys trap", () => {
            const keys = Object.keys(testMusigreeManager);

            expect(Array.isArray(keys)).toBe(true);
        });

        it("should handle getOwnPropertyDescriptor trap", () => {
            const descriptor = Object.getOwnPropertyDescriptor(
                testMusigreeManager,
                "someProperty",
            );

            expect(descriptor).toBeDefined();
        });
    });
});
