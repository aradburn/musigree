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
 * Creates a lazy proxy for a manager instance.
 * The proxy does not cache the instance itself: each access goes through
 * `createInstance`, which owns the singleton. That lets `resetSingletons`
 * drop the current instance and have the next access construct a new one.
 */
function createLazyProxy<T extends object>(createInstance: () => T): T {
    return new Proxy({} as T, {
        get(_target: T, prop: string | symbol): unknown {
            const instance = createInstance();
            const value = (instance as Record<string | symbol, unknown>)[prop];
            if (typeof value === "function") {
                return (value as (...args: unknown[]) => unknown).bind(
                    instance,
                );
            }
            return value;
        },
        set(_target: T, prop: string | symbol, value: unknown): boolean {
            const instance = createInstance();
            (instance as Record<string | symbol, unknown>)[prop] = value;
            return true;
        },
        has(_target: T, prop: string | symbol): boolean {
            return prop in createInstance();
        },
        ownKeys(_target: T): ArrayLike<string | symbol> {
            return Reflect.ownKeys(createInstance());
        },
        getOwnPropertyDescriptor(
            _target: T,
            prop: string | symbol,
        ): PropertyDescriptor | undefined {
            return Reflect.getOwnPropertyDescriptor(createInstance(), prop);
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
