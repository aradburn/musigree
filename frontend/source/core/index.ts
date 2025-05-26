import { musigreeManager } from "./MusigreeManager";
import { networkManager } from "./NetworkManager";
import { relationsManager } from "./RelationsManager";

export * from "./MusigreeManager";
export * from "./NetworkManager";
export * from "./RelationsManager";

// Re-export singletons from their respective files
export { musigreeManager, networkManager, relationsManager };

// Helper function used in svg.test.ts
export const getSelectedNodeKey = (): string | undefined => {
    const key = networkManager.selectedNodeKey;
    return typeof key === "string" ? key : undefined;
};
