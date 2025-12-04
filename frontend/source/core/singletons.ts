/**
 * Singleton instances of core managers
 * This file creates the singleton instances to avoid circular dependencies
 * Uses lazy initialization to support testing
 */

import { MusigreeManager } from "./MusigreeManager";
import { NetworkManager } from "./NetworkManager";
import { RelationsManager } from "./RelationsManager";

// Lazy initialization variables
let _musigreeManager: MusigreeManager | null = null;
let _networkManager: NetworkManager | null = null;
let _relationsManager: RelationsManager | null = null;

/**
 * Creates a lazy proxy for a manager instance
 */
function createLazyProxy<T extends object>(createInstance: () => T): T {
    let instance: T | undefined;

    return new Proxy({} as T, {
        get(_target: T, prop: string | symbol): unknown {
            if (!instance) {
                instance = createInstance();
            }
            const value = (instance as Record<string | symbol, unknown>)[prop];
            if (typeof value === "function") {
                return (value as (...args: unknown[]) => unknown).bind(
                    instance,
                );
            }
            return value;
        },
        set(_target: T, prop: string | symbol, value: unknown): boolean {
            if (!instance) {
                instance = createInstance();
            }
            (instance as Record<string | symbol, unknown>)[prop] = value;
            return true;
        },
        has(_target: T, prop: string | symbol): boolean {
            if (!instance) {
                instance = createInstance();
            }
            return prop in instance;
        },
        ownKeys(_target: T): ArrayLike<string | symbol> {
            if (!instance) {
                instance = createInstance();
            }
            return Reflect.ownKeys(instance);
        },
        getOwnPropertyDescriptor(
            _target: T,
            prop: string | symbol,
        ): PropertyDescriptor | undefined {
            if (!instance) {
                instance = createInstance();
            }
            return Reflect.getOwnPropertyDescriptor(instance, prop);
        },
    });
}

// Create lazy singleton instances
export const musigreeManager = createLazyProxy(() => {
    if (!_musigreeManager) {
        _musigreeManager = new MusigreeManager();
    }
    return _musigreeManager;
});

export const networkManager = createLazyProxy(() => {
    if (!_networkManager) {
        _networkManager = new NetworkManager();
    }
    return _networkManager;
});

export const relationsManager = createLazyProxy(() => {
    if (!_relationsManager) {
        _relationsManager = new RelationsManager();
    }
    return _relationsManager;
});

/**
 * Utility function to reset singletons (useful for testing)
 */
export const resetSingletons = (): void => {
    if (_networkManager?.dispose) {
        _networkManager.dispose();
    }
    if (_relationsManager?.dispose) {
        _relationsManager.dispose();
    }

    _musigreeManager = null;
    _networkManager = null;
    _relationsManager = null;
};
