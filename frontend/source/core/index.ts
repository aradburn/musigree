import {
    musigreeManager,
    networkManager,
    relationsManager,
} from "./singletons";

// Export manager classes for direct instantiation if needed
export { MusigreeManager } from "./MusigreeManager";
export { NetworkManager } from "./NetworkManager";
export { RelationsManager } from "./RelationsManager";

// Re-export singletons
export { musigreeManager, networkManager, relationsManager };

// Helper function used in svg.test.ts
export const getSelectedNodeKey = (): string | undefined => {
    const key = networkManager.selectedNodeKey;
    return typeof key === "string" ? key : undefined;
};
